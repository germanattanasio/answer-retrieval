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

import re
from retrieve_and_rank_scorer.query.query_scorer import QueryScorer
from spacy.en import English

class ProperNounRatioScorer(QueryScorer):
    """
        Contains scorers which capture properties of the queryType
        Example:
            - KeywordConfidenceScorer scores (from 0 to 1) the extent to which a query looks like a keyword
            - PolarQueryScorer scores (from 0 to 1) the extent to which a question is a Yes/No question
    """

    def __init__(self, name='ProperNounRatioScorer', short_name='pnrs', description='Proper Noun Ratio Scorer',
                 nlp=None):
        """
            Class that computes the ratio of proper nouns in a query
            The idea is that a query with a large fraction of proper nouns will tend to be a keyword query

            Args:
                name, short_name, description (str): See QueryScorer
                nlp (spacy.en.English): Tokenizes incoming text
        """
        super(ProperNounRatioScorer, self).__init__(name=name, short_name=short_name, description=description)
        if nlp:
            self.nlp_ = nlp
        else:
            self.nlp_ = English()

    def score(self, query):
        """
            Computes the fraction of proper nouns in the underlying query text
        """
        query_text = query['q']
        doc = self.nlp_(unicode(query_text))
        num_proper_nouns = 0
        for token in doc:
            if re.match('^NNP.*$', token.tag_):
                num_proper_nouns += 1
        return num_proper_nouns / float(len(doc))
