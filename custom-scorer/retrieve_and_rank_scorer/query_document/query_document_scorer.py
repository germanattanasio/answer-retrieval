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

class QueryDocumentScorer(object):
    """
        Contains the class QueryDocumentScorer, which is the base class for all scorers that:
            (1) Look at the overlap between a query and document,
            (2) Want to be registered by the service as scorers

        All subclasses of QueryDocumentScorer must override the score(query, doc) method
    """

    def __init__(self, name='QueryDocumentScorer', short_name='qds',
                 description='Description of the scorer'):
        """ Base class for any scorers that want to consume both a Solr document and a Solr query
            Any classes that subclass this method must override the score method

            Args:
                name (str): Name of the Scorer
                short_name (str): Used for the header which is sent to ranker
                description (str): Description of the scorer
        """
        self.name_ = name
        self.short_name_ = short_name
        self.description_ = description

    @property
    def name(self):
        return self.name_

    @property
    def short_name(self):
        return self.short_name_

    @property
    def description(self):
        return self.description_

    def get_required_fields(self):
        """
            args:
                None
            return:
                List : Return a list of the required fields
        """
        raise NotImplementedError

    def score(self, query, document):
        """    Create a score for a given query/document. This score will be added as a feature for this query/document
            pair

            Example Scores (that one could create)
                - Number of words overlapping from a common dictionary between the query and the document body
                - If the query contains a specific entity, the number of sentences in the document body that contain
                    that entity as the subject

            Args:
                query (dict): Dictionary containing the contents of the solr query. This is expected to be the exact
                    dictionary that was used for the query parameters when making a call to /select
                document (dict): Contents of the solr document
        """
        raise NotImplementedError
#endclass QueryDocumentScorer
