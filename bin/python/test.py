#!/usr/bin/env python
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
# -*- coding=utf8 -*-

import sys
import logging
import os
import requests
import json
from requests import models
import csv
import argparse
import multiprocessing
from multiprocessing import pool as multi_pool
import datetime

# Loggers
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Counter(object):
    """ Simple counter object for managing the state """
    def __init__(self):
        self.lock = multiprocessing.Lock()
        self.val = multiprocessing.Value('i', 0)

    def increment(self):
        with self.lock:
            self.val.value += 1

    def get(self):
        with self.lock:
            return self.val.value

    def increment_and_get(self):
        with self.lock:
            self.val.value += 1
            return self.val.value


class SolrThread(object):
    """ Thread for a single query to be posted to retrieve and rank """
    def __init__(self, username, password, url, collection_name, cluster_id,
                 num_answers=10, fl='id,title', wt='json'):
        self.username = username
        self.password = password
        self.url = url
        self.collection_name = collection_name
        self.cluster_id = cluster_id
        self.default_num_answers = num_answers
        self.default_fl = fl
        self.default_wt = wt
        self.select_url = "%s/v1/solr_clusters/%s/solr/%s/select" % \
            (self.url, self.cluster_id, self.collection_name)
        self.counter = Counter()

    def __call__(self, *args):
        """ Re-rank the results. First entry of args should be a dictionary containing the query """
        try:
            obj = args[0]
            query = obj.get('query', None)
            if query is None:
                raise ValueError('No query passed in to Thread')
            fl = obj.get('fl', self.default_fl)
            wt = obj.get('wt', self.default_wt)
            params = {'q': query, 'wt': wt, 'fl': fl}
            resp = requests.get(self.select_url, params=params, auth=(self.username, self.password))
            return args, resp
        except Exception as e:
            logger.debug('Exception when retrieve results with args=%r. Exception=%r' % (args, e))
            return args, e
        finally:
            num_queries = self.counter.increment_and_get()
            if num_queries % 50 == 0:
                logger.debug('Num of Queries Retrieved = %d' % num_queries)
# endclass SolrThread


class RetrieveAndRankQueryThread(object):
    """ Thread for a single query to be posted to retrieve and rank """
    def __init__(self, username, password, url, collection_name, cluster_id, ranker_id,\
                num_answers=10, fl='id,title,subtitle,answer,answerScore', wt='json'):
        self.username = username
        self.password = password
        self.url = url
        self.collection_name = collection_name
        self.cluster_id = cluster_id
        self.ranker_id = ranker_id
        self.default_num_answers = num_answers
        self.default_fl = fl
        self.default_wt = wt
        self.fcselect_url = "%s/v1/solr_clusters/%s/solr/%s/fcselect" % (self.url, self.cluster_id, self.collection_name)
        self.counter = Counter()

    def __call__(self, *args):
        """ Re-rank the results. First entry of args should be a dictionary containing the query """
        try:
            obj = args[0]
            query = obj.get('query', None)
            if query is None:
                raise ValueError('No query passed in to Thread')
            fl = obj.get('fl', self.default_fl)
            wt = obj.get('wt', self.default_wt)
            params = {'q': query, 'wt': wt, 'ranker_id': self.ranker_id, 'fl': fl}
            resp = requests.get(self.fcselect_url, params=params, auth=(self.username, self.password))
            return args, resp
        except Exception as e:
            logger.debug('Exception when retrieve results with args=%r. Exception=%r' % (args, e))
            return args, e
        finally:
            num_queries = self.counter.increment_and_get()
            if num_queries % 50 == 0:
                logger.debug('Num of Queries Retrieved = %d' % num_queries)
# endclass RetrieveAndRankQuestionThread


def read_relevance_file(relevance_file):
    """ Output format --> [(question, [(id, rel)])] """
    gt = dict()
    with open(relevance_file, 'rt') as infile:
        succ_rows, failed_rows = 0, 0
        for row in csv.reader(infile):
            try:
                question = row[0]
                rel = [(row[2 * i + 1], row[2 * i + 2]) for i in range((len(row) - 1) / 2)]
                gt[question] = rel
                succ_rows += 1
            except Exception as e:
                logger.debug('Exception when reading in row=%s. Message=%r' % (row, e))
                failed_rows += 1
    return gt, (succ_rows, failed_rows)


def create_experiment_object(query_responses, relevance_dict):
    """ Write experiment responses to a file"""
    experiment_results = []
    for args, resp in query_responses:
        if isinstance(resp, models.Response):
            if resp.ok:
                json_resp = resp.json()
                status = json_resp.get('responseHeader', {}).get('status', 1)
                response_docs = json_resp.get('response', {}).get('docs', [])
                query = args[0].get('query', None)
                rel = relevance_dict.get(query, [])
                if status == 0 and response_docs and query and rel:
                    relevant_docs = {i: int(r) for i, r in rel}
                    for i, response_doc in enumerate(response_docs):
                        doc_id = response_doc['id']
                        response_docs[i]['relevance'] = relevant_docs.get(doc_id, 0)
                    output_obj = {'query': query, 'response_docs': response_docs, 'relevant_docs': relevant_docs}
                    experiment_results.append(output_obj)
                else:
                    logger.debug('args=%r, response=%r. Response is not status 0 or does not have docs' % (args, resp))
            else:
                logger.debug('args=%r, response=%r. Response is not ok. Reason = %r' % (args, resp, resp.reason))
        else:
            logger.debug('args=%r, response=%r. Response is not of type requests.models.Response' % (args, resp))
    logger.debug('Number of Questions in Final Experiment = %d' % len(experiment_results))
    return experiment_results


def parse_args():
    """ Parse args """
    parser = argparse.ArgumentParser(description='Run a test script against a Retrieve&Rank cluster')
    parser.add_argument('--username', type=str, help='Username for R&R service')
    parser.add_argument('--password', type=str, help='Password for R&R service')
    parser.add_argument('--url', type=str, help='URL for R&R service')
    parser.add_argument('--collection-name', type=str, help='Name of R&R Collection')
    parser.add_argument('--cluster-id', type=str, help='Id for Solr Cluster')
    parser.add_argument('--ranker-id', type=str, default=None, help='Id for Trained Ranker')
    parser.add_argument('--relevance-file', type=str, help='Path to relevance file for testing')
    parser.add_argument('--output-file', type=str, help='Path to output json file')
    parser.add_argument('--num-threads', type=int, default=10, help='Number of Threads to use')
    parser.add_argument('--fl', type=str, default='id,title,subtitle,answer,answerScore', help='Features to retrieve from the api call')
    parser.add_argument('--debug', action='store_true', default=False, help='Whether to debug or not')
    ns = parser.parse_args()
    if not os.path.isfile(ns.relevance_file) and not ns.relevance_file.endswith('csv'):
        raise ValueError('Relevance file %s does not exist or is not a csv' % ns.relevance_file)
    return ns.username, ns.password, ns.url, ns.collection_name, ns.cluster_id, \
        ns.ranker_id, ns.relevance_file, ns.output_file, ns.num_threads, ns.fl, ns.debug


def main():
    """ Main script """
    try:
        username, password, url, collection_name, cluster_id, ranker_id, relevance_path,\
            output_path, num_threads, fl, use_debug = parse_args()
        if use_debug:
            logger.info('Setting logger to level=DEBUG')
            logger.setLevel(logging.DEBUG)

        relevance_dict, (succ_rows, fail_rows) = read_relevance_file(relevance_path)
        logger.info('Total Number of Queries in Relevance File = %d' % (succ_rows + fail_rows))
        logger.info('Total Number of Queries being sent to re-rank API = %d' % succ_rows)
        if ranker_id:
            thread_obj = RetrieveAndRankQueryThread(username, password, url, \
                collection_name, cluster_id, ranker_id, fl=fl)
        else:
            thread_obj = SolrThread(username, password, url, collection_name, \
                cluster_id, fl=fl)
        thread_pool = multi_pool.ThreadPool(processes=num_threads)
        question_results = thread_pool.map_async(func=thread_obj,
                                                 iterable=[{'query': q} for (q, rel) in relevance_dict.iteritems()]).get()
        print ('Responses retrieved from Retrieve and Rank')
        experiment_entries = create_experiment_object(question_results, relevance_dict)
        experiment_metadata = {'ranker_id': ranker_id, 'solr_collection': collection_name, 'solr_cluster_id': cluster_id,
                               'username': username, 'password': password, 'url': url, 'time':str(datetime.datetime.now())}
        experiment_obj = dict(experiment_entries=experiment_entries, experiment_metadata=experiment_metadata)
        print ('Writing results to output_path=%r' % output_path)
        with open(output_path, 'wt') as outfile:
            json.dump(experiment_obj, outfile)
        print ('Exiting with status code 0')
        sys.exit(0)
    except Exception as e:
        logging.warning('Exception %r in main thread' % e)
        print ('Exiting with status code 1')
        sys.exit(1)


if __name__ == "__main__":
    main()
