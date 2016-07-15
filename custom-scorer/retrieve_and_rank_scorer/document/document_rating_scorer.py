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

from retrieve_and_rank_scorer.document.document_scorer import DocumentScorer

# Scorer to score to compute the popularity of a post/document using number of views and answers provided
class PopularityScorer(DocumentScorer):

    def __init__(self, name='DocumentScorer', short_name='ds', description='Description of the scorer',
                 include_stop=False):
        """ Base class for any scorers that consume a Solr document and extract
            a specific signal from a Solr document

            Args:
                name (str): Name of the Scorer
                short_name (str): Used for the header which is sent to ranker
                description (str): Description of the scorer
        """
        super(PopularityScorer, self).__init__(name=name, short_name=short_name, description=description)

    def get_required_fields(self):
        pass

    def score(self, document):
        views = document['views']
        accepted = document['accepted']

        if views is not None:
            # if no views, then assuming it is a low rating
            if views < 0:
                return 0.0
            elif 100 < views <= 2000 and accepted < 0:
                return 0.25
            elif 0 < views <= 2000 and accepted > 0:
                return 0.5
            elif 2000 < views <= 5000 and accepted > 0:
                return 0.75
            elif views > 5000 and accepted > 0:
                return 1
