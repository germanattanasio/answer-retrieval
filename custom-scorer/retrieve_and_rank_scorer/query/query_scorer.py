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
#

class QueryScorer(object):
    """
        Contains the class QueryScorer, which is the base class for all scorers:
            (1) Extract a signal from the query alone
            (2) Registered by the service

        All subclasses must override score(query)
    """

    def __init__(self, name='QueryScorer', short_name='qs',
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

    def score(self, query):
        """    Create a score for a given query. This score will be added as a
            feature for each document (for a given query)

            Example Scores (that one could create)
                - If an application typically has two types of questions, a
                confidence that the question is one type or another

            Args:
                query (dict): Dictionary containing the contents of the solr query. This is expected to be the exact
                    dictionary that was used for the query parameters when making a call to /select
        """
        raise NotImplementedError
