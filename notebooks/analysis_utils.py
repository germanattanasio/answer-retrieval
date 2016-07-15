#!/usr/bin/env python
# -*- coding=utf8 -*-

"""
    Author: Vincent Dowling
    Company: IBM
    Name: analysis_utils.py
    Description: A series of utilities for use in analyzying Retrieve and Rank Experiments. In particular, these
        are designed to be used with accompanying IPython Notebook
"""


# Runtime imports
import sys
import os
import random

# 3rd party imports
#import spacy; from spacy.en import English; nlp = English()
from nltk.corpus import stopwords; eng_sw = stopwords.words('english')
from string import punctuation
import requests
import numpy as np
import json
import pandas as pd
import matplotlib.pyplot as plt
import functools
import requests
import random
import seaborn as sns


"""
    --------------------------
    --------------------------
            CLASSES
    --------------------------
    --------------------------
"""


class QuestionCategorizer(object):
    def categorize(self, query):
        raise NotImplementedError
#endclass QuestionCategorizer


class DocumentCategorizer(object):
    def categorize(self, document):
        raise NotImplementedError
#endclass DocumentCategorizer


class DocChunkIterator(object):
    """
        Class for iterating through text based on the chunks in the documents
    """
    def __init__(self, txt, log=False):
        #self.doc = nlp(unicode(txt))
        self.doc = unicode(txt)
        self.token_map = {token.i: token for token in self.doc}
        self.chunk_map = dict()
        for chunk in self.doc.noun_chunks:
            self.chunk_map[chunk.start] = chunk
            for ci in range(chunk.start, chunk.end):
                if ci not in self.token_map:
                    if log:
                        print ('Could not find token %d, %s' % (ci, self.doc[ci]))
                else:
                    del self.token_map[ci]
        self.iterable = list()
        i = 0
        while i < len(self.doc):
            if i in self.token_map:
                token = self.token_map[i]
                self.iterable.append((False, token))
                i += 1
            else:
                chunk = self.chunk_map[i]
                self.iterable.append((True, chunk))
                i = chunk.end

    def __iter__(self):
        return iter(self.iterable)
# endclass DocIterator


class FancyHighlighter(object):
    def __init__(self, query, stopwords=eng_sw, punct=punctuation, use_lemma=True):
        doc = DocChunkIterator(query)
        self.lemma_map = dict()
        self.rules = create_highlighters(query, stopwords=stopwords, use_lemma=use_lemma)
        self.punct = punct
        self.stopwords = stopwords
        self.identity_rule = create_highlighter()

    def highlight(self, text):
        format_str = ''
        doc_iterator = DocChunkIterator(text)
        for (is_chunk, span) in doc_iterator:
            if is_chunk:
                chunk = span
                if chunk.lemma_.lower() in self.rules.keys():
                    rule = self.rules[chunk.lemma_.lower()]
                    format_str += rule(chunk)
                else:
                    for token in chunk:
                        rule = self.rules.get(token.lemma_.lower(), self.identity_rule)
                        format_str += rule(token)
            else:
                token = span
                rule = self.rules.get(token.lemma_.lower(), self.identity_rule)
                format_str += rule(token)
        return format_str
# endclass FancyHighlighter


class RetrieveAndRankService(object):
    def __init__(self, username, password, base_url, cluster_id, collection_name):
        self.username = username
        self.password = password
        self.base_url = base_url
        self.cluster_id = cluster_id
        self.collection_name = collection_name
        self.select_url = '%s/v1/solr_clusters/%s/solr/%s/select' % (base_url, cluster_id, collection_name)
        self.fcselect_url = '%s/v1/solr_clusters/%s/solr/%s/fcselect' % (base_url, cluster_id, collection_name)

    def select(self, query_params):
         return requests.get(self.select_url, params=query_params, auth=(self.username, self.password))

    def fcselect(self, query_params):
        return requests.get(self.fcselect_url, params=query_params, auth=(self.username, self.password))
# endclass RetrieveAndRankService


class RetrieveAndRankExperiment(object):
    def __init__(self, experiment_file_path):
        """ State associated with a single Retrieve & Rank Experiment

            args:
                experiment_file_path (str): Path to the experiment file
        """
        obj = json.load(open(experiment_file_path, 'rt'))
        self.experiment_entries = obj['experiment_entries']
        self.base_url = obj['experiment_metadata']['url']
        self.username = obj['experiment_metadata']['username']
        self.password = obj['experiment_metadata']['password']
        self.solr_cluster_id = obj['experiment_metadata']['solr_cluster_id']
        self.solr_collection = obj['experiment_metadata']['solr_collection']
        self.ranker_id = obj['experiment_metadata']['ranker_id']
        self.rr_service = RetrieveAndRankService(self.username, self.password, self.base_url,
                                                 self.solr_cluster_id, self.solr_collection)
#endclass RetrieveAndRankExperiment


"""
    --------------------------
    --------------------------
            FUNCTIONS
    --------------------------
    --------------------------
"""


def random_color():
    " Choose a random color "
    r = lambda: random.randint(0,255)
    return '#%02X%02X%02X' % (r(),r(),r())


def create_highlighter(color=None, is_bold=False, punct=None):
    " Highlighter is a function that adds markup to text with certain style elements "
    punct = [] if not punct else punct
    def _whitespace(span):
        if hasattr(span, '_whitespace'):
            return span._whitespace
        elif type(span) is spacy.tokens.spans.Span:
            last_token = span[len(span) - 1]
            if hasattr(last_token, '_whitespace'):
                return last_token._whitespace
        return ' '
    if color and is_bold:
        def _rule(span):
            return '<span style="color:%s;font-weight:bold">%s</span>%s' % (color, span.orth_, _whitespace(span))
    elif color and not is_bold:
        def _rule(span):
            return '<span style="color:%s">%s</span>%s' % (color, span.orth_, _whitespace(span))
    elif not color and is_bold:
        def _rule(span, punct=punct):
            return '<span style="font-weight:bold">%s</span>%s' % (span.orth_, _whitespace(span))
    else:
        def _rule(span):
            escape_chars = ['$']
            if span.orth_ in escape_chars:
                return '\%s%s' % (span.orth_, _whitespace(span))
            else:
                return '%s%s' % (span.orth_, _whitespace(span))
    return _rule


def create_highlighters(query, stopwords=None, use_lemma=True):
    " Define highlighters for chunks/tokens, to be applied to answer text"
    doc = nlp(unicode(query))
    txt_fmt_rules = dict()

    """
        Create format rules for the chunks in the query
    """
    for chunk in doc.noun_chunks:
        rc = random_color()
        if use_lemma: txt_fmt_rules[chunk.lemma_.lower()] = create_highlighter(color=rc, is_bold=True)
        else: txt_fmt_rules[chunk.text.lower()] = create_highlighter(color=rc, is_bold=True) # print a random color

    """
        Create format rules for the tokens in the query
    """
    for token in doc:
        if (stopwords and token.text.lower() in stopwords) or token.is_stop:
            continue
        else:
            if use_lemma: txt_fmt_rules[token.lemma_.lower()] = create_highlighter(is_bold=True) # print bold
            else: txt_fmt_rules[token.text.lower()] = create_highlighter(is_bold=True) # print bold
    return txt_fmt_rules


def highlight_results(query_params, rr_service, relevant_ids=None, num_shown=5, stopwords=None, punct=None):
    html_str = ''
    relevant_ids = relevant_ids if hasattr(relevant_ids, '__contains__') else []
    query = query_params['q']
    highlighter = FancyHighlighter(query, stopwords=stopwords, punct=punct)
    html_str += "<h2>Question</h2>"
    html_str += "<p>%s</p>" % highlighter.highlight(query).strip()
    responses = rr_service.select(query_params)
    docs = responses.json().get('response', {}).get('docs', [])
    html_str += "<h2>Relevant Documents Retrieved</h2>"
    ids_retrieved = list()
    for doc in docs:
        id = doc.get('id')
        if id in relevant_ids:
            ids_retrieved.append(id)
            title, score, text = doc.get('title')[0], doc.get('score'), doc.get('text')[0]
            html_str += "<p>Title : %s</p>" % title
            html_str += "<p>Text  : %s</p>" % highlighter.highlight(text).strip()
            html_str += "<p>Score : %r</p>" % score
            html_str += "<p></p>"

    " Relevant Documents that were not retrieved "
    if len(relevant_ids) > 0 and any(id not in ids_retrieved for id in relevant_ids):
        html_str += "<h2>Relevant Documents Not Retrieved</h2>"
        for id in filter(lambda x: x not in ids_retrieved, relevant_ids):
            query_params = {'q':'id:%s' % id, 'wt':'json', 'fl': 'id,title,text'}
            irrel_responses = rr_service.select(query_params)
            irrel_docs = irrel_responses.json().get('response', {}).get('docs', [])
            if len(irrel_docs) == 1:
                doc = irrel_docs[0]
                title, text = doc.get('title')[0], doc.get('text')[0]
                html_str += "<p>Title : %s</p>" % title
                html_str += "<p>Text  : %s</p>" % highlighter.highlight(text).strip()
                html_str += "<p></p>"

    " Irrelevant documents "
    html_str += "<h2>Irrelevant Documents</h2>"
    for doc in docs:
        id = doc.get('id')
        if id not in relevant_ids:
            title, score, text = doc.get('title')[0], doc.get('score'), doc.get('text')[0]
            html_str += "<p>Title : %s</p>" % title
            html_str += "<p>Text  : %s</p>" % highlighter.highlight(text).strip()
            html_str += "<p>Score : %r</p>" % score
            html_str += "<p></p>"
    return html_str


def dcg(r, entry, n):
    r = np.asarray(r)[:n]
    disc = np.log2(np.arange(2, r.size + 2))
    return np.sum(r / disc)


def idcg(r, entry, n, method='relative'):
    if method == 'relative':
        return dcg(sorted(r, reverse=True), entry, n)
    else:
        return dcg(sorted(entry['relevant_docs'].values(), reverse=True), entry, n)


def ndcg(r, entry, n=10, method='relative'):
    if method == 'relative' and sum(r) == 0:
        return 0
    else:
        return dcg(r, entry, n=n) / idcg(r, entry, n=n, method=method)


def experiment_ndcg(experiment, n=10, method='relative'):
    " Compute the NDCG over all experiment entries "
    ndcg_arr = [ndcg([doc['relevance'] for doc in entry['response_docs']], entry, n=n, method=method)
                for entry in experiment]
    return ndcg_arr


def experiment_average_ndcg(experiment, n=10, method='relative'):
    return np.mean(experiment_ndcg(experiment, n=n, method=method))


def number_relevant(entry, top_n=10, min_rel=1):
    return len(filter(lambda rd: rd['relevance'] >= min_rel, entry['response_docs'][:top_n])), \
           min(top_n, len(filter(lambda rel: rel >= min_rel, entry['relevant_docs'].values())))


def total_relevance_at_n(experiment_entries, n=10, strategy='average', min_rel=1):
    """
        total_rel_at_n_for_query = (# of relevant docs in top n) / min(n, # of relevant_docs)
        If strategy == 'average', then compute the above for all entries and average
        If strategy == 'total', will sum the numerate/denominator over all and return that result
    """
    if strategy not in ['average', 'total']:
        raise ValueError('Strategy must be average or total')
    results = map(lambda entry: number_relevant(entry, top_n=n, min_rel=min_rel), experiment_entries)
    if strategy == 'average':
        return np.mean([rel / float(total_rel) for (rel, total_rel) in results])
    else:
        return sum([rel for rel, total_rel in results]) / float(sum([total_rel for rel, total_rel in results]))


def relevance_at_n(experiment_entries, n=10, min_rel=1):
    " A document is relevant at n if it contains a relevant document in the top n"
    results = [number_relevant(entry, top_n=n, min_rel=min_rel) for entry in experiment_entries]
    return np.mean([1 if rel > 0 else 0 for rel, total_rel in results])

def plot_relevance_results(entries_mat, func=total_relevance_at_n, legend=[],
                            xlabel=None, ylabel=None, title=None):
    ind = np.arange(1, 11)
    labels = ind + 0.35
    total_rel_at_n = list()
    for entries in entries_mat:
        total_rel_at_n.append([func(entries, n=i) for i in ind])
    f, ax = plt.subplots(figsize=(9, 7))
    width = 0.80 / len(total_rel_at_n)
    delta = -0.40
    ax_legend = []
    color = iter(plt.cm.rainbow(np.linspace(0, 1 , len(total_rel_at_n))))
    for rels in total_rel_at_n:
        c = next(color)
        rects = ax.bar(ind + delta, rels, width=width, color=c, align='center')
        delta += width
        ax_legend.append(rects[0])
    ax.set_xlim(0, 11)
    if xlabel is not None:
        ax.set_xlabel(xlabel)
    if ylabel is not None:
        ax.set_ylabel(ylabel)
    if title is not None:
        ax.set_title(title)
    ax.set_yticks([i * 0.10 for i in range(11)])
    ax.set_yticklabels(["%d%%" % (i * 10) for i in range(11)])
    ax.set_xticks(ind)
    if len(legend) == len(ax_legend):
        ax.legend(ax_legend, legend)
        ax.set_ylim(0.0, 1.3)
    else:
        ax.set_ylim(0.0, 1.0)
