#!/usr/bin/env python
# Copyright 2016 IBM All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
from retrieve_and_rank_scorer.document.document_size_scorer import TotalDocumentWordsScorer
from retrieve_and_rank_scorer.document.document_upvote_scorer import UpVoteScorer
from retrieve_and_rank_scorer.document.document_rating_scorer import PopularityScorer

class TestStringMethods(unittest.TestCase):

    def test_document_size_scorer(self):
        scorer = TotalDocumentWordsScorer()
        small_doc = dict()
        big_doc = dict()
        small_doc['text'] = 'this is a small document'
        big_doc['text'] = 'this is a much larget document document'
        self.assertGreater(scorer.score(big_doc), scorer.score(small_doc))

    def test_upvote_scorer(self):
        scorer = UpVoteScorer()
        popular_doc = dict()
        unpopular_doc = dict()
        popular_doc['upModVotes'] = 1000
        unpopular_doc['upModVotes'] = 10
        self.assertGreater(scorer.score(popular_doc), scorer.score(unpopular_doc))


    def test_document_rating_scorer_accepted(self):
        scorer = PopularityScorer()
        accepted_doc = dict()
        unaccepted_doc = dict()
        accepted_doc['accepted'] = 1
        accepted_doc['views'] = 500
        unaccepted_doc['accepted'] = -1
        unaccepted_doc['views'] = 500
        self.assertGreater(scorer.score(accepted_doc), scorer.score(unaccepted_doc))


    def test_document_rating_scorer_views(self):
        scorer = PopularityScorer()
        popular_doc = dict()
        unpopular_doc = dict()
        popular_doc['views'] = 30000
        unpopular_doc['views'] = 10
        popular_doc['accepted'] = 1
        unpopular_doc['accepted'] = 1
        self.assertGreater(scorer.score(popular_doc), scorer.score(unpopular_doc))

if __name__ == '__main__':
    unittest.main()
