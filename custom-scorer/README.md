# Retrieve & Rank Scorer

## Getting Started
Install the retrieve and rank scorer using `pip`:

```bash
$ pip install .
```

## Description
This project is intended for the collective development of custom features for the Retrieve & Rank service on the Watson Developer Cloud Services. When you set up an instance of Retrieve & Rank, the documentation describes how to include a custom search handler as part of the Solr configuration (the convention is the handler is named ``/fcselect`) and this handler supports the generation of feature vectors that are to be used by the "Ranking" portion of the Retrieve & Rank service. This project supports the development of additional custom scorers (written in the Python programming language) to customize Retrieve & Rank

## Core Concepts
This project is designed to create custom "scorers" to enhance Retrieve & Rank. The term "scorer" is used synonymously with the term "feature extractor". Within the context of this project a scorer is a Python class which implements a method score(), and that method must produce a numerical value. There are 3 types of scorers that one can implement:

### DocumentScorer
A document scorer is a class whose input to the score method is a python dictionary whose keys correspond to the field entries for a single Solr document. Consider a class called DocumentLengthScorer, that scores the number of words in the text field of a Solr Document. This class would be used as follows:

```python
dls = DocumentLengthScorer(*args, **kwargs) # instantiate
sample_solr_doc = {'id':'1', 'text':'This is a sample document'} # Dictionary containing fields
dls.score(document=sample_solr_doc) # 5
```

To implement a DocumentScorer, subclass the class DocumentScorer in the module `retrieve_and_rank_scorer.document.document_scorer`. By
convention, when you are creating a custom subclass, please create a separate module within the package retrieve_and_rank_scorer.document.

### QueryScorer
A query scorer is a class whose input to the score method is a python dictionary whose keys correspond to the query params for a Solr query. Consider a class called `IsDefinitionQueryScorer`, that scores queries based on whether it thinks the underlying query text is asking for a 'definition'. This would look like the following:

```python
idqf = IsDefinitionQueryScorer(*args, **kwargs)
definition_query = {'q':'What is light?', 'rows':10, 'wt':'json'}
non_definition_query = {'q':'What are good restaurants in New York City?', 'rows':10, 'wt':'json'}
idqf.score(query=definition_query) # 1.0
idqf.score(query=non_definition_query) # 0.0
```

To implement a QueryScorer, subclass the class `QueryScorer` in the module `retrieve_and_rank_scorer.query.query_scorer`. By convention, each module within the package `retrieve_and_rank_scorer.query` corresponds to a separate of QueryScorers that are semantically grouped. If you are creating a scorer that is not related to the existing set of scorers, create a new module within the package `retrieve_and_rank_scorer.document.document_scorer`.

### QueryDocumentScorer
A query-document scorer is a class whose input to the score method is:
 1. a python dictionary whose keys correspond to the query params for a Solr query, and
 2. a python dictionary whose keys correspond to the field entries in a Solr document. Consider a class that scores the extent to which the "text" of a Solr document answers definitional questions. More specifically, the scorer will 1) identify if a query is asking for a definition and 2) if so, identify whether the document contains a likely definition or not. This would look like:

```python
# Define the scorer
ds = DefinitionalScorer(*args, **kwargs)
# Sample queries
new_york_definitional_query = {'q':'What is New York?'}
new_york_non_definitional_query = {'q':'Why is New York such a popular city?'}
# Sample document
new_york_definitional_document = {'id':'1', 'text':'New York is a state in the Northeast of the USA. It neighbors both Pennsylvania and Connecticut.'}
new_york_non_definitional_document = {'id':'2', 'text':'The most popular area in New York is New York City, which is the largest city in the US.'}
alaska_definitional_document = {'id':'3', 'text':'Alaska is the largest state in the USA. Alaska was formally made a state in 1959.'}
# Responses
ds.score(query=new_york_definitional_query, document=new_york_definitional_document) # High score because doc query looking for a definition and doc contains it
ds.score(query=new_york_definitional_query, document=new_york_non_definitional_document) # Low score, because doc doesn't contain a definition
ds.score(query=new_york_definitional_query, document=alaska_definitional_document) # Low score, because doc doesn't contain right definition
ds.score(query=new_york_non_definitional_query, document=new_york_definitional_document) # Low score, because query isn't looking for definition
```

To implement a `QueryDocumentScorer`, subclass the class QueryDocumentScorer in the module `retrieve_and_rank_scorer.query_document.query_document_scorer`. The same conventions on adding custom scorers apply as in the previous 2 cases.
