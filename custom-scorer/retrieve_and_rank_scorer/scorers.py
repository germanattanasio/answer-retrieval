# Copyright 2016 IBM All Rights Reserved.
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


from retrieve_and_rank_scorer import utils
from retrieve_and_rank_scorer.scorer_exception import ScorerRuntimeException, ScorerTimeoutException
import numpy as np
from concurrent import futures

class Scorers(object):

    def __init__(self, feature_json_file, timeout=10, max_workers=10):
        """
            Pipeline that manages scoring of multiple custom feature scorers
            This is the API that almost all scorers will access when training \
                a Retrieve & Rank instance with custom features

            args:
                feature_json_file (str): Path to a feature configuration file. \
                    This file defines the pipeline of custom scorers used
            raise:
                ScorerConfigurationException : If any of the individual scorers raise during configuration, \
                    If the file feature_json_file cannot be found or is not of the proper type
        """
        scorer_dict = utils.load_from_file(feature_json_file)
        self._document_scorers = scorer_dict.get('document', [])
        self._query_scorers = scorer_dict.get('query', [])
        self._query_document_scorers = scorer_dict.get('query_document', [])
        self._timeout = timeout
        self._interval = 0.1
        self._thread_executor = futures.ThreadPoolExecutor(max_workers)

    def get_headers(self):
        " Get the custom headers "
        headers = list()
        headers.extend([scorer.short_name for scorer in self._document_scorers])
        headers.extend([scorer.short_name for scorer in self._query_scorers])
        headers.extend([scorer.short_name for scorer in self._query_document_scorers])
        return headers

    def get_required_fields(self):
        " Get the required fields for the underlying scorers "
        required_fields = list()
        for qs in self._query_scorers:
            required_fields.extend(qs.get_required_fields())
        for qds in self._query_document_scorers:
            required_fields.extend(qds.get_required_fields())
        return list(set(required_fields))

    def _score(self, scorer, *args, **kwargs):
        """ Score an individual item
            args:
                scorer (Scorer) : Scorer object
                args (list)     : List of additional unnamed args
                kwargs (dict)   : Dictionary of additional named args
            raise:
                ScorerRuntimeException : If scorer fails along the way
                ScorerTimeoutException : If scorer times out
            return:
                score (float) : Score
        """
        f = None
        try:
            f = self._thread_executor.submit(scorer.score, *args, **kwargs)
            return f.result(timeout=self._timeout)
        except futures.TimeoutError, e:
            if f is not None:
                f.cancel()
            raise ScorerTimeoutException('Scorer %r timed out', args, kwargs)
        except ScorerRuntimeException as e:
            raise e

    def scores(self, query, doc):
        """
            Score the query/document pair using all registered scorers

            args:
                query (dict): Dictionary containing contents of the query
                doc (dict): Dictionary containing contents of individual Solr Doc
            raises:
                ScorerRuntimeException: If there are any issues scoring \
                    individual query/document pairs
            returns:
                vect (numpy.ndarray): Numpy array containing the feature vectors
        """
        vect = list()

        # Score the docs
        for document_scorer in self._document_scorers:
            score = self._score(document_scorer, doc)
            vect.append(score)

        # Score the queries
        for query_scorer in self._query_scorers:
            score = self._score(query_scorer, query)
            vect.append(score)

        # Score the query-document pairs
        for query_document_scorer in self._query_document_scorers:
            score = self._score(query_document_scorer, query, doc)
            vect.append(score)

        return np.array(vect)
# endclass Scorers
