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


import time
import requests

from retrieve_and_rank_scorer.query_document.query_document_scorer import QueryDocumentScorer
from retrieve_and_rank_scorer.scorer_exception import ScorerConfigurationException, ScorerRuntimeException
from collections import defaultdict
from multiprocessing import Lock


class NLCIntentScorer(QueryDocumentScorer):
    """
        Classes that use the Natural Language Classifier to create features

        Classify a query. Map a Solr Document (based on id) to a given class. If \
            one of the classes in the response matches the class of the Solr \
            document, then return the confidence
    """

    def __init__(self, name, short_name, description, service_url, service_username, service_password, classifier_id, **kwargs):
        """
            Create a feature based on the confidence of the natural language
            classifier.

            If no class_to_id_file is provided, then the class is assumed to
            be an id. Otherwise, the id is matched against the class and compared
            to the returned class

            Args:
                name, short_name, description (str): See superclass
                service_url (str): URL for the NLC service
                service_username (str): Username for the NLC service
                service_password (str): Password for the NLC service
                classifier_id (str): Id for the trained classifier
                id_to_class_csv_path (str): Path to a file mapping from an id \
                    to a class

            raise:
                ScorerConfigurationException, if:
                    - NLC is improperly configured
                    - Class mapping is improperly configured
        """
        super(NLCIntentScorer, self).__init__(name=name, short_name=short_name, description=description)
        self.validate_nlc(service_url, service_username, service_password, classifier_id)
        self.question_cache = defaultdict()
        self.cache_lock = Lock()
        self.cache_size = 10

    def validate_nlc(self, url, username, password, classifier_id):
        """ Validate the configuration of a single Natural Language Classifier instance

            args:
                url           (str) : Base url for the natural language classifier instance
                username      (str) : Username for the NLC instance
                password      (str) : Password for the NLC instance
                classifier_id (str) : If for the classifier
            raises:
                ScorerRuntimeException : If url, user, pw are invalid; if the classifier does not exist \
                    or is not currently taking requests
        """
        not_str = lambda x: not isinstance(x, str) and not isinstance(x, unicode)
        if not_str(url) or not_str(username) or not_str(password) or not_str(classifier_id):
            if not_str(url):
                message = 'url=%r is not valid' % url
            elif not_str(username):
                message = 'username=%r is not valid' % username
            elif not_str(password):
                message = 'password=%s is not valid' % password
            else:
                message = 'classifier_id=%s is not valid' % classifier_id
            raise ScorerConfigurationException(message)

        # Get the status of the classifier
        classifier_url = '%s/v1/classifiers/%s' % (url, classifier_id)
        resp = requests.get(classifier_url, headers={'Accept':'application/json'}, \
            auth=(username, password))
        if resp.ok:
            try:
                status = resp.json()['status']
                if status == 'Available':
                    self.service_url = url
                    self.service_username = username
                    self.service_password = password
                    self.classifier_id = classifier_id
                else:
                    description = resp.json()['status_description']
                    message = 'classifier_id=%s has status=%s, which is not "Available". status_description=%s' % \
                        (classifier_id, status, description)
                    raise ScorerConfigurationException(message)
            except Exception as e:
                raise ScorerConfigurationException(e.message)
        else:
            message = 'Error in pinging classifier. Reason : %s' % resp.reason
            raise ScorerConfigurationException(message)

    def classify(self, text):
        """ Classify an utterance. First check the cache, and then make a call \
                to the nlc classifier that is configured

            args:
                text(str): Text to be classified
            raise:
                ScorerRuntimeException: If we get invalid response
            return:
                json_resp (dict) : JSON Response from the classifier
        """

        # Check the cache
        with self.cache_lock:
            if text in self.question_cache:
                return self.question_cache[text][1]

        # Call the API
        classify_url = "%s/v1/classifiers/%s/classify" % (self.service_url, \
            self.classifier_id)
        resp = requests.get(classify_url, headers={'Accept': 'application/json'}, \
            params={'text': text}, auth=(self.service_username, self.service_password))
        if not resp.ok:
            message = 'Error when classifying text=%s. Reason : %s' % (text, \
                resp.reason)
            raise ScorerRuntimeException(message)
        else:
            # Update the cache and return
            try:
                json_resp = resp.json()
                with self.cache_lock:
                    if text not in self.question_cache:
                        if len(self.question_cache) >= self.cache_size:
                            oldest_key = sorted(self.question_cache.iteritems(), key=lambda x: x[1][0], \
                                reverse=False)[0][0]
                            del self.question_cache[oldest_key]
                        self.question_cache[text] = (time.time(), json_resp)
                return json_resp
            except Exception as e:
                raise ScorerRuntimeException(e.message)

    def doc_to_class(self, doc):
        """ Convert a single Solr Document into a class
            The default behavior is to pluck out the 'id' from the Solr Document

            args:
                doc (dict) : Single Solr Document. Keys are the fields
            raise:
                ScorerRuntimeException : If the id is not found
            return:
                class (str) : Class to compare to the NLC
        """
        if 'id' not in doc:
            raise ScorerRuntimeException('No id in Solr Document')
        return doc['id']

    def validate_query(self, query):
        """ Validate the params for the incoming Solr query. This method is invoked before . The expected default field required is the 'id'. This method should be overriden \
            by a subclass, if the fields are different

            args:
                query (dict) : Keys are the parameters of the request
            return:
                None
            raise:
                ScorerRuntimeException : If the fields in the document do no match the expected contents required \
                    by the scorer
        """
        if not isinstance(query, dict):
            message = 'query=%r is not of type dict' % query
            raise ScorerRuntimeException(message)
        elif not query.has_key('q'):
            message = 'query=%r does not contain the query text' % query
            raise ScorerRuntimeException(query)

    def validate_document(self, document):
        """ Validate the fields in the incoming Solr Document to be scored. This method is invoked before \
            each document arrives. The expected default field required is the 'id'. This method should be overriden \
            by a subclass, if the fields are different

            args:
                document (dict) : Keys are the fields for the Solr Document
            return:
                None
            raise:
                ScorerRuntimeException : If the fields in the document do no match the expected contents required \
                    by the scorer
        """
        if not isinstance(document, dict):
            message = 'document=%r is not of type dict' % document
            raise ScorerRuntimeException(message)
        else:
            for field in self.get_required_fields():
                if not document.has_key(field):
                    message = 'document=%r does not have the field=%r' % (document, field)
                    raise ScorerRuntimeException(message)

    def get_required_fields(self):
        return ['id']

    def score(self, query, document):
        """ Compute the score based on the NLC intent feature
            - Classify the query
            - Get the class associated with the document id
            - If the class associated with the document id is in the top X, \
                then return the confidence for that class

            args:
                query (dict): If query does not have the field 'q', the \
                    method will raise a ScorerRuntimeException
                document (dict): If document does not have the field 'id', the \
                    method will raise a ScorerRuntimeException
            raise:
                ScorerRuntimeException: If query is invalid, if document is invalid, other errors
            return:
                score (float) : The score/feature that is extracted
        """

        # Validate the document and the query
        self.validate_query(query)
        self.validate_document(document)

        try:
            # Get the class for the document
            doc_class = self.doc_to_class(document)

            # Classify the query and return the confidence, if there is a match
            resp_body = self.classify(query['q'])
            for klass in resp_body['classes']:
                if klass['class_name'] == doc_class:
                    return klass['confidence']
            return 0.0
        except Exception as e:
            raise ScorerRuntimeException(e)
# endclass NLCIntentScorer


class MultiNLCIntentScorer(QueryDocumentScorer):

    def __init__(self, name, short_name, description, field_name=None, field_to_nlc=None):
        """
            Create a feature based on the confidence of the natural language
            classifier.

            If no class_to_id_file is provided, then the class is assumed to
            be an id. Otherwise, the id is matched against the class and compared
            to the returned class

            Args:
                name, short_name, description (str): See superclass
                field_name (str) : Name of the field to extrac the value from
                field_to_nlc (dict) : Dictionary mapping the value of the field to a dictionary containing the
                    credentials

            raise:
                ScorerConfigurationException, if:
                    - NLC is improperly configured
                    - Class mapping is improperly configured
        """
        super(MultiNLCIntentScorer, self).__init__(name=name, short_name=short_name, description=description)
        self.field_name = field_name
        if field_to_nlc is None:
            field_to_nlc = {}
        self.configure_classifiers(field_to_nlc)

    def configure_classifiers(self, field_to_nlc):
        " Set up the different classifier objects "
        self.field_to_nlc = {}
        for (fv, sc) in field_to_nlc.iteritems():
            url, user, pw = sc['url'], sc['username'], sc['password']
            cl_id = sc['classifier_id']
            sis = NLCIntentScorer(name='name', short_name='short_name', description='simple_description',
                                  service_url=url, service_username=user, service_password=pw, classifier_id=cl_id) # single intent scorer
            self.field_to_nlc[fv] = sis

    def get_required_fields(self):
        scorers_fields = list()
        for nlc in self.field_to_nlc.values():
            scorers_fields.extend(nlc.get_required_fields())
        scorers_fields.append(self.field_name)
        return list(set(scorers_fields))

    def score(self, query, document):
        " Score a single query document pair "
        if document.has_key(self.field_name):
            fv = document[self.field_name] #MS
            if isinstance(fv, list) and len(list) > 1:
                raise ScorerRuntimeException('Document %r has more than two values for field %s' % (document, self.field_name))
            fv = fv if not isinstance(fv, list) else fv[0]
            if self.field_to_nlc.has_key(fv):
                scorer = self.field_to_nlc.get(fv)
                return scorer.score(query=query, document=document)
            else:
                return 0.0
        else:
            return 0.0
# endclass MultiNLCIntentScorer


class QuestionDocumentIntentAlignmentScorer(NLCIntentScorer):

    def __init__(self, name, short_name, description, service_url, service_username, service_password, classifier_id):
        """
        """
        super(QuestionDocumentIntentAlignmentScorer, self).__init__(name, short_name, description, service_url, \
                                                                    service_username, service_password, classifier_id)

        # TO DO : Provide name value pair of document titles against NLC class for your implementation

        self.title_name_to_doc_class = {
            '<Enter Document Title Name>':'<Enter NLC Class>',
        }

    def doc_to_class(self, doc):
        """ Given a Solr document, resolve it to the appropriate class
        """
        title = doc.get('title', 'NO_TITLE')
        if title != 'NO_TITLE':
            split_title = [t.strip() for t in title.split(':') if t.strip() != '']
            if not split_title:
                return 'NO_TITLE'
            end_title = split_title[-1]
            if end_title.lower() not in self.title_name_to_doc_class:
                return 'NO_CLASS'
            else:
                return self.title_name_to_doc_class.get(end_title.lower())
        else:
            return 'NO_TITLE'

    def validate_document(self, document):
        """ Raise if the document does not contain the title """
        if isinstance(document, dict):
            message = 'document=%r is not of type dict' % document
            raise ScorerRuntimeException(message)
        elif not document.has_key('title'):
            message = 'document=%r does not have the title' % document
            raise ScorerRuntimeException(message)

    def score(self, query, document):
        return NLCIntentScorer.score(self, query, document) # superclass method
#endclass QuestionDocumentIntentAlignmentScorer
