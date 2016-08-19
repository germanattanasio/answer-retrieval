#!/usr/bin/env python
#
# Copyright 2016 IBM Corp. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# -*- coding: utf-8 -*-

import csv
import copy
import time
import os
import requests
this_dir = os.path.dirname(__file__)

class FcSelect(object):
    def __init__(self, scorers, service_url, service_username, service_password,
                 cluster_id, collection_name, answer_directory, default_rerank_rows = 10,
                 default_search_rows = 30, default_fl = 'id,title,text'):
        """
            Class that manages custom feature scorers

            Args:
                scorers (retrieve_and_rank_scorer.scorers.Scorers): Scorers object, which is \
                    used to score individual query/document pairs
                service_url, service_username, service_password (str): Credentials \
                    for the different services
                cluster_id (str): Id for the Solr Cluster
                collection_name (str): Name of the Solr Collection
        """
        self.scorers_ = scorers
        self.service_url_ = service_url
        self.service_username_ = service_username
        self.service_password_ = service_password
        self.cluster_id_ = cluster_id
        self.collection_name_ = collection_name

        if not os.path.isabs(answer_directory):
            self.answer_directory_ = os.path.realpath('{0}/../{1}'.format(this_dir, answer_directory))
        else:
            self.answer_directory_ = answer_directory

        print self.answer_directory_
        self.default_rerank_rows_ = default_rerank_rows
        self.default_search_rows_ = default_search_rows
        self.default_fl_ = default_fl


    def fcselect(self, **kwargs):
        """
            /fcselect endpoint

            Args:
                kwargs (dict): Contains the same query params as are supported \
                    by the traditional fcselect endpoint
        """
        # Re-rank the answers
        if kwargs.has_key('ranker_id'):
            return self.rerank(**kwargs)

        # Parameters
        q           = self.get_query_value(kwargs, 'q')
        search_rows = self.get_query_value(kwargs, 'rows', self.default_search_rows_)
        gt          = self.get_query_value(kwargs, 'gt')
        fl          = self.get_query_value(kwargs, 'fl', self.default_fl_)

        # Determine the parameters to send to the classifier
        required_fields = self.scorers_.get_required_fields()
        required_fields.append('featureVector')
        required_fields.extend([x.strip() for x in fl.split(',')])
        non_return_fields = set(required_fields) - {'featureVector'} - set([x.strip() for x in fl.split(',')])
        required_fl = ','.join(list(set(required_fields)))

        # Call fcselect
        params_no_rs = {'q': q, 'rows': search_rows, 'fl': required_fl, 'gt': gt, 'wt': 'json'}
        params_rs = copy.copy(params_no_rs)
        generate_header, return_rs_input = False, False
        if kwargs.has_key('generateHeader'):
            generate_header = kwargs.get('generateHeader')
            params_rs['generateHeader'] = generate_header if type(generate_header) is not list else generate_header[0]
            generate_header = True if params_rs['generateHeader'] == 'true' else False
        if kwargs.has_key('returnRSInput'):
            return_rs_input = kwargs.get('returnRSInput')
            params_rs['returnRSInput'] = return_rs_input if type(return_rs_input) is not list else return_rs_input[0]
            return_rs_input = True
        time_1 = time.time()
        fcselect_json = self.service_fcselect(params_no_rs)
        time_2 = time.time()
        print ("Time for Service Call #1 = %.4f" % (time_2 - time_1))

        # Modify individual feature vectors
        score_map, score_list = dict(), list()
        times = list()
        prev_time = time_2
        for i, doc in enumerate(fcselect_json.get('response', {}).get('docs', [])):
            feature_doc = self.prepare_document(doc, fl)
            fv = doc.get('featureVector')
            new_scores = self.scorers_.scores(params_rs, feature_doc)
            fv += ' ' + ' '.join('%.4f' % x if x > 0.0 else '0.0' for x in new_scores)
            fcselect_json['response']['docs'][i]['featureVector'] = fv
            for field_value in fcselect_json['response']['docs'][i].keys():
                if field_value in non_return_fields:
                    del fcselect_json['response']['docs'][i][field_value]
            score_map[doc.get('id')] = new_scores
            score_list.append(new_scores)
            times.append(time.time() - prev_time)
            prev_time = time.time()
        time_3 = time.time()
        print ('Time for the first 10 in the loop = %r' % times[:10])
        print ('Time to extract the new features = %.4f' % (time_3 - time_2))

        # Modify RSInput
        if return_rs_input:
            fcselect_json_rs = self.service_fcselect(params_rs)
            time_4 = time.time()
            print ('Time for service call #2 = %.4f' % (time_4 - time_3))
            rs_input_splits = fcselect_json_rs['RSInput'].split('\n')
            rs_input_modified = ''
            score_index, rs_split_index = 0, 0
            while score_index < len(score_list) and rs_split_index < len(rs_input_splits):
                if rs_split_index == 0 and generate_header:

                    # Old headers
                    base_header = rs_input_splits[rs_split_index]
                    base_header_string = ','.join(base_header.split(',')[:-1])
                    ground_truth_header = base_header.split(',')[-1]
                    rs_split_index += 1

                    # New header (s)
                    new_headers = self.scorers_.get_headers()
                    new_header_string = ','.join(new_headers)

                    # Combine
                    rs_input_modified += base_header_string + ','
                    rs_input_modified += new_header_string + ','
                    rs_input_modified += ground_truth_header + '\n'
                else:
                    # Get the splits
                    rs_input_split = rs_input_splits[rs_split_index]
                    if rs_input_split.strip() != '':
                        base_feat_string = ','.join(rs_input_split.split(',')[:-1])
                        relevance = rs_input_split.split(',')[-1]
                        rs_split_index += 1

                        # Get new scores
                        new_scores = score_list[score_index]
                        new_score_string = ','.join('%.4f' % x if x > 0.0 else '0.0' for x in new_scores)
                        score_index += 1

                        # Combine
                        rs_input_modified += base_feat_string + ','
                        rs_input_modified += new_score_string + ','
                        rs_input_modified += relevance + '\n'
                    else:
                        rs_split_index += 1
                        score_index += 1
            fcselect_json['RSInput'] = rs_input_modified
            time_5 = time.time()
            print ('Time for Creating RS String = %.4f' % (time_5 - time_4))
        return fcselect_json

    def get_query_value(self, dct, arg, default_value=None):
        if arg not in dct.keys():
            if default_value is not None:
                return default_value
            else:
                raise ValueError('arg = %r is not in dct = %r' % (arg, dct))
        val = dct[arg]
        if type(val) is list:
            return val[0]
        else:
            return val

    def rerank(self, **kwargs):
        """ Re-rank the incoming query """
        # Extract the parameters
        ranker_id = self.get_query_value(kwargs, 'ranker_id')
        q = self.get_query_value(kwargs, 'q')
        search_rows = self.get_query_value(kwargs, 'search_rows', self.default_search_rows_)

        # Get the appropriate values
        fl = self.get_query_value(kwargs, 'fl', self.default_fl_)
        required_fields = self.scorers_.get_required_fields()
        required_fields.append('featureVector')
        required_fields.extend([x.strip() for x in fl.split(',')])
        required_fl = ','.join(list(set(required_fields)))

        # Make a call to fcselect and get the features plus other parameters
        fcselect_params = {'q': q, 'rows': search_rows, 'fl': required_fl, 'wt': 'json', \
            'generateHeader': 'true', 'returnRSInput':'true'}
        fcselect_json = self.service_fcselect(fcselect_params)

        if type(fcselect_json) is not dict:
            raise ValueError('Response object %r is type %r and is not a dictionary' % (fcselect_json, type(fcselect_json)))
        elif 'RSInput' not in fcselect_json:
            raise ValueError('Response object %r does not contain key "RSInput"' % fcselect_json)
        else:
            rs_input_splits = fcselect_json['RSInput'].split('\n')
            if len(rs_input_splits) == 0:
                raise ValueError('RSInput value %r is not split by new line character' % fcselect_json['RSInput'])
            full_header = rs_input_splits[0] + ',' + ','.join(self.scorers_.get_headers())

        # Score the documents/queries

        features = list()
        for i, doc in enumerate(fcselect_json.get('response', {}).get('docs', [])):
            feature_doc = self.prepare_document(doc, fl)
            fv = doc.get('featureVector').split(' ')
            new_scores = self.scorers_.scores(fcselect_params, feature_doc)
            fv.extend([str(x) for x in new_scores])
            features.append((doc.get('id'), fv))

        # Write to a CSV
        file_path = os.path.join(self.answer_directory_, 'answer_%d.csv' % time.time())
        self.write_to_answer_csv(file_path, full_header.split(','), features)

        # Call the re-rank API
        rerank_resp = requests.post('%s/v1/rankers/%s/rank' % (self.service_url_, ranker_id), \
            auth=(self.service_username_, self.service_password_), \
            headers={'Accept':'application/json'}, \
            files={'answer_data': open(file_path, 'rb')})
        if rerank_resp.ok:
            print ('Response is ok')
            if 'answers' not in rerank_resp.json():
                raise ValueError('No answers contained in response=%r' % rerank_resp.json())
            else:
                answers = rerank_resp.json()['answers']
                return self.order_answers_by_id(answers, fl)
        else:
            raise rerank_resp.raise_for_status()

    def order_answers_by_id(self, answers, fl):
        """ Retrieve the reranked answers by id"""
        ids = map(lambda e: e['answer_id'], answers)
        id_to_answer = {a['answer_id']:a for a in answers}
        id_to_index = {id: i for i, id in enumerate(ids)}
        fq = ' '.join(['id:%s' % (str(id)) for id in ids])
        params = {'q': fq, 'fl':fl, 'wt':'json'}
        resps = self.service_select(params=params)
        modified_docs = list()
        for doc in resps['response']['docs']:
            answer = id_to_answer.get(doc['id'])
            order = id_to_index.get(doc['id'])
            modified_doc = copy.copy(doc)
            modified_doc['confidence'] = answer['confidence']
            modified_docs.insert(order, modified_doc)
        resps['response']['docs'] = modified_docs
        return resps

    def fcselect_default(self, **kwargs):

        q           = self.get_query_value(kwargs, 'q')
        search_rows = self.get_query_value(kwargs, 'rows', self.default_search_rows_)
        fl          = self.get_query_value(kwargs, 'fl', self.default_fl_)
        ranker_id   = self.get_query_value(kwargs,'ranker_id')
        fcselect_params = {'q': q, 'fl': fl, 'ranker_id': ranker_id, 'wt': 'json'}

        fcselect_json = self.service_fcselect(fcselect_params)
        return fcselect_json

    def service_fcselect(self, params, timeout=10):
        url = '%s/v1/solr_clusters/%s/solr/%s/fcselect' % (self.service_url_,
            self.cluster_id_, self.collection_name_)
        resp = requests.post(url, data=params, auth=(self.service_username_, self.service_password_), timeout=timeout)
        if resp.ok:
            return resp.json()
        else:
            raise resp.raise_for_status()

    def service_select(self, params, timeout=10):
        url = '%s/v1/solr_clusters/%s/solr/%s/select' % (self.service_url_,
            self.cluster_id_, self.collection_name_)
        resp = requests.get(url, params=params, auth=(self.service_username_, self.service_password_), timeout=timeout)
        if resp.ok:
            return resp.json()
        else:
            raise resp.raise_for_status()

    def prepare_document(self, doc, fl):
        """
            Prepare a document to be consumed by a scorer

            args:
                doc (dict): This is the object that is returned in the response \
                    by the /fcselect API
        """
        modified_doc = dict()
        for fn in set(fl.split(',')) - {'featureVector'}:
            fv = doc.get(fn)
            modified_doc[fn] = fv if type(fv) is not list else fv[0]
        return modified_doc

    def write_to_answer_csv(self, file_path, headers, scores):
        """
            Write to an answer CSV

            Args:
                file_path (str): Path to the output file
                headers (list): Headers to write
                scores (list): List of feature scores
        """
        with open(file_path, 'wt') as outfile:
            writer = csv.writer(outfile, delimiter=',', quoting=csv.QUOTE_NONE)
            writer.writerow(headers)
            for (doc_id, feature_scores) in scores:
                writer.writerow([doc_id] + feature_scores)
#endclass FcSelect
