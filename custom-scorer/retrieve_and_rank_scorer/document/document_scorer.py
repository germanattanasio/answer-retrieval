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


class DocumentScorer(object):
    """
        Contains the class DocumentScorer, which is the base class for all scorers that:
            (1) Extract a specific signal from a single Solr Document
            (2) Want to be registered by the service as scorers

        All subclasses of DocumentScorer must override the score(doc) method, where
        doc contains the different fields for a given Solr Document
    """

    def __init__(self, name='DocumentScorer', short_name='ds', description='Description of the scorer'):
        """ Base class for any scorers that consume a Solr document and extract
            a specific signal from a Solr document

            args:
                name (str): Name of the Scorer
                short_name (str): Used for the header which is sent to ranker
                description (str): Description of the scorer
            raise:
                ValueError : If name, short_name or description is not "string"-like
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
            Get the required fields from the Solr document
            args:
                None
            return:
                List : Return a list of the required fields
        """
        raise NotImplementedError

    def score(self, document):
        """    Number of total words in a document. This is intended to be used as a fuzzy way to filter out
            useless documents

            args:
                document (dict): Contents of the solr document. The fields in the dictionary correspond
                to the different fields in the Solr Document
        """
        raise NotImplementedError
