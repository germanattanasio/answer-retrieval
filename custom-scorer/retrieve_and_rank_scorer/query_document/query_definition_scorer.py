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
from spacy.en import English
from retrieve_and_rank_scorer.query_document.query_document_scorer import QueryDocumentScorer

class WhatIsScorer(QueryDocumentScorer):
    """
        If a question is a definition, score the extent to which there exists a single passage that answers that
        question
    """

    def __init__(self, name='WhatIsScorer', description='', short_name='wis', strategy='max'):
        """ If a question is of the form 'what is X' score the extent to which a single sentence
            in the answer is of the form 'X is ...'

            args:
                name, description, short_name (str): See QueryDocumentScorer
                strategy (str): The scoring strategy. Must be one of the following: 'max', 'average'
        """
        super(WhatIsScorer, self).__init__(name=name, description=description, short_name=short_name)
        self.strategy = strategy
        self.nlp = English()

    def mean(self, iterable):
        n = len(iterable)
        s = sum(iterable)
        return s / float(n)

    def get_required_fields(self):
        return ['text']

    def score(self, query, document):
        """ Score the definition overlap of the sentence
            Step 1: Extract the thing to be defined
            Step 2: Find and sentences that match
            Step 3: Compute the score
        """
        qt = query['q'] # query text
        qtm = re.match('^what is (.*)$', qt.lower())
        if qtm:
            qr = qtm.group(1) # query remainder
            dt = self.nlp(unicode(document['text']))
            ss = list() # sentence scores
            for sent in dt.sents:
                amt = '^%s (?:is|are|am|was) .*$' % qr # answer matcher text
                ss.append(1.0 if re.match(amt, sent.orth_.lower()) else 0.0)
            return self.mean(ss) if self.strategy == 'average' else max(ss)
        else:
            return 0.0
# endclass WhatIsScorer


class QueryDefinitionScorer(QueryDocumentScorer):
    def __init__(self, name='QueryDefinitionScorer', description='', short_name='qds', strategy='max'):
        """ If a question is of the form 'what is X' score the extent to which a single sentence
            in the answer is of the form 'X is ...'

            args:
                name, description, short_name (str): See QueryDocumentScorer
                strategy (str): The scoring strategy. Must be one of the following: 'max', 'average'
        """
        super(QueryDefinitionScorer, self).__init__(name=name, description=description, short_name=short_name)
        self.strategy = strategy
        self.nlp = English()

    def mean(self, iterable):
        n = len(iterable)
        s = sum(iterable)
        return s / float(n)

    def get_required_fields(self):
        return ['text']

    def to_be_defined(self, query, **kwargs):
        " Return the thing to be defined "
        if 'q' in query:
            qtm = re.match('^what (?:is|are|am|was) (.*)$', query['q'].lower())
            if qtm:
                return qtm.group(1)
            else:
                return None
        else:
            return None

    def sentence_definition_overlap(self, tbd, sent, **kwargs):
        " Does the sentence define the thing that is tbd (to be defined)? "
        sm = re.match('^(.*) (?:is|are|am|was) .*$', sent.lower())
        if sm:
            doc1 = self.nlp(unicode(sm.group(1)))
            doc2 = self.nlp(unicode(tbd))
            return doc1.similarity(doc2) # Might need to re-think this
        else:
            return 0.0

    def aggregate_score(self, ss, **kwargs):
        " Return the aggregate score, if given a list of sentence_overlap scores "
        return self.mean(ss) if self.strategy == 'average' else max(ss)

    def score(self, query, document):
        """ Score the definition overlap of the sentence
            Step 1: Is this a definition query?
            Step 2: If so, find the thing to be defined
            Step 3: For each sentence in the document text, score the sentence definition overlap
            Step 4: Score the entire thing
        """
        tbd = self.to_be_defined(query) # to-be-defined
        if tbd is None:
            return 0.0
        dt, ss = self.nlp(unicode(document['text'])), []
        for sent in dt.sents:
            sdo = self.sentence_definition_overlap(tbd, sent.orth_) # does this sentence define the thing to be defined?
            ss.append(sdo)
        return self.aggregate_score(ss)
# endclass QueryDefinitionScorer
