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

# Scorer to reflect the number of up votes a document received
class UpVoteScorer(DocumentScorer):

    def __init__(self, name='DocumentScorer', short_name='ds', description='Description of the scorer',
                 include_stop=False):
        """ Base class for any scorers that consume a Solr document and extract
            a specific signal from a Solr document

            Args:
                name (str): Name of the Scorer
                short_name (str): Used for the header which is sent to ranker
                description (str): Description of the scorer
        """
        super(UpVoteScorer, self).__init__(name=name, short_name=short_name, description=description)

    def get_required_fields(self):
        pass

    def score(self, document):
        up_vote = document['upModVotes']
        ret = 0.0
        if up_vote is not None:
            if up_vote == 0:
                ret = 0.0
            elif 0 < up_vote <= 3:
                ret = 0.15
            elif 3 < up_vote <= 5:
                ret = 0.35
            elif 5 < up_vote <= 8:
                ret = 0.55
            elif 8 < up_vote <= 11:
                ret = 0.75
            elif 11 < up_vote <= 14:
                ret = 0.85
            elif up_vote > 14:
                ret = 1.0
        else:
            ret = 0.0

        return ret
