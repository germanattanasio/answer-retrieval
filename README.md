# Answer Retrieval [![Build Status](https://travis-ci.org/watson-developer-cloud/answer-retrieval.svg?branch=master)](https://travis-ci.org/watson-developer-cloud/answer-retrieval)

This repository contains a **Starter Kit** (SK) that is
designed to show you how to create your own answer retrieval
application for [StackExchange](http://stackexchange.com/), using the
[Retrieve and Rank](http://www.ibm.com/smarterplanet/us/en/ibmwatson/developercloud/retrieve-rank.html)(R&R)
service, a cognitive API from the Watson Developer Cloud. Information
retrieval applications enable users to search for content in specific
information sources. Creating an answer retrieval system has
historically been a very complex technique requiring lots of
configuration and lots of expert tuning. This starter kit uses the
Retrieve and Rank API to support the entire process of creating such a
system, from uploading your data to evaluating results, including
training your answer retrieval system.

# Note: 
Only after completing the steps defined below in table of contents, you will be able to deploy the application to Bluemix using the button below:

[![Deploy to Bluemix](https://bluemix.net/deploy/button.png)](https://bluemix.net/deploy?repository=https://github.com/watson-developer-cloud/answer-retrieval.git)

## Table of Contents
  - [How this app works](#how-this-app-works)
  - [Getting started](#getting-started)
  - [Running the notebooks](#running-the-notebooks)
  - [Exploring with the UI](#exploring-with-the-ui)
  - [Using your own data](#using-your-own-data)
  - [Improving relevance](#improving-relevance)


## How this app works
This starter kit uses Jupyter Notebook, a web application that allows you to
create and share documents that contain code, visualizations, and
explanatory text. (Jupyter Notebook was formely known as iPython
Notebook.) Jupyter Notebook automatically executes specific sections
of Python code that are embedded in a notebook, displaying the results
of those commands in a highlighted section below each code block. The
Jupyter notebooks in this SK show you the process of building a custom
ranker for the data on
[Travel Stack Exchange](http://travel.stackexchange.com/).

This SK has three primary components:

* Two
[Jupyter notebooks](https://ipython.org/notebook.html), which show you
the process of building an answer retrieval system using
the Watson
[Retrieve and Rank](http://www.ibm.com/smarterplanet/us/en/ibmwatson/developercloud/retrieve-rank.html)
service.  These notebooks are:
    - `Answer Retrieval` which shows how to create a basic SOLR collection and enhance it with a ranker
    - `Custom Scorer`, which shows how to add custom features to your ranker
Once you have completed the notebooks, you can launch a simple application
that shows how the answer retrieval
system performs. Specifically, the application compares
[SOLR](http://lucene.apache.org/solr/), a common open-source
Information Retrieval system, with Retrieve and Rank's ranker, which
reranks search results to be in an order more salient to a particular
user. It also shows how you can extend the basic ranker with custom
features that consider domain-specific information.

* Bash shell scripts that enable you to train a ranker on data from
[any StackExchange](#using-your-own-data) question and answer
site.

* Python code to help you extract other content from StackExchange and
pre-process it for use with the Retrieve and Rank service.

Once you complete the notebooks and understand the format of data
expected by the Retrieve and Rank API, you should be able to train
Retrieve and Rank on any dataset.

## Getting started
Before diving into the Jupyter notebooks, you should make sure you
have all the prerequisites installed, and are familiar with the
directory structure of the git repository that contains this SK.

### Prerequisites
You will need the following in order to use this SK:

- A Unix-based OS (or Cygwin)
- [Git](https://git-scm.com/downloads)
- [Node.js](https://www.continuum.io/downloads)
- [python](https://www.python.org/downloads/)
- [Anaconda](https://www.continuum.io/downloads) - Installing this package also installs the [Jupyter notebook](http://jupyter.readthedocs.io/en/blatest/install.html) package, which includes `iPython` (now referred to as `jupyter`)
- [A bluemix account](https://console.ng.bluemix.net/)
- [An instance of the Retrieve and Rank service](https://console.ng.bluemix.net/catalog/services/retrieve-and-rank/)

If you are using a Linux system, the `git`, `anaconda`, `python`, and
`node.js` packages may be installable through your system's package
manager.

### Checking out the repository for this SK

Use `git` to clone the repository for this SK to your local machine. For example, using a command-line version of git, the command that you would execute is the following:

```
git clone git@github.com:watson-developer-cloud/answer-retrieval.git
```

### Directory Structure of the repository
The directory that you created when cloning the git repository for this SK contains the following subdirectories:
- `bin\` contains various bash and python scripts for interacting with the R&R API
- `config\` contains a configuration that tells SOLR how the StackExchange data is structured.
- `custom-scorer\`
contains the code necessary to train scorers for R&R that use custom features
- `data\` contains sample StackExchange data that is pre-processed for
use by the Retrieve and Rank service. This data will be automatically
uploaded to the Retrieve and Rank service as part of the Python code
in the **Config** section of the **Answer Retrieval** notebook.
- `notebooks\` contains the iPython notebooks
- `static\` contains the static website assets, css, js, html

### Installing dependencies for the application

1. Install the dependencies using `pip`.

    ```sh
    pip install -r requirements.txt
    pip install -r notebooks/requirements.txt
    ```
2. Create a `.env` using `.env.example` as example. You will need credentials for the Retrieve and Rank service.

3. Start the application.

    ```sh
    python server.py
    ```

## Running the notebooks
The Jupyter notebooks show you the process of creating an information
retrieval system, step-by-step, automatically executing specified
sections of Python code. We used Jupyter notebooks because they
encourage experimentation, which is an important part of developing
any machine learning system.

You will need credentials in order to use R&R. These can be obtained
after creating an account in (Bluemix)(http://bluemix.net) and
creating an instance of the service in account. After these are done,
you can click the "Service Credentials" entry in the left-hand
navigation for that service in Bluemix to see your R&R Credentials.

Before starting the notebook, please add the username and password
from the credentials for the instance of the Retrieve and Rank service
that to created to the json file `credentials.json`. This file is
located in the `config` directory of this SK's repository. This
enables the notebooks to use these values throughout all of the code
blocks in the notebook.

To start the notebooks, make sure you are in the root directory of
your `git` checkout of the SK repository, and execute the command
`jupyter notebook`. This will start the Jupyter notebook server, and
open a browser window. Once the browser window is open, click on
`notebooks`, and then open the notebook labeled `Answer-
Retrieval.ipynb`. Follow the instructions in there to create your own
ranker.

### Using the Sample Data

The **Populate the Collection** section of the **Answer Retrieval** notebook loads sample data into the Solr collection that was created by previous code blocks in that Notebook. This sample data is located in the `config` directory of the repository for this SK.

### Exploring with the UI
**Important:** The UI will not have any rankers to display results for until you have stepped through the iPython notebooks.

Now that you have completed the iPython notebooks, you have 2 ways to search your data: basic SOLR and a Ranker with custom scoring features. If you want to explore how all of these different rankers can perform, you just have to modify a few things in the UI. **Complete this once UI done**

## Using your own data
If you want to train rankers with data from other StackExchange sites, you first need to [download the dumps](https://archive.org/download/stackexchange). Once you have chosen a dump, you can use `bin/python/extract_stackexchange_dump.py` to convert it into a R&R-compatible format. If you wish to use another data source, consult the [Retrieve and Rank documentationn](http://www.ibm.com/smarterplanet/us/en/ibmwatson/developercloud/doc/retrieve-rank/), which explains how R&R expects incoming data to be formatted.

## Improving relevance

It is often necessary to look for additional features in your dataset
that can be used to provide information to the ranker that can
instruct it on how to identify results that are more relevant to
others. These are implemented as a set of custom features known as
custom scorers.  In the case of the Stack Exchange community support
scenario that was used to collect the sample adata for this SK, you
have access to metadata about each answer. Examples of this sort of
metadata include the following:

- **User Reputation**: a rough measurement of how much the community trusts an expert author. Community users gain reputation points when a question that they have asked is voted up, an answer that they have made is voted up, an answer that they have made is accepted, and other criteria.
- **UpVotes** : the number of times that someone other than the expert has accepted an expert's answer as a pertinent response.
- **DownVotes**: the number of times that someone other than the expert has rejected an expert's answer as a pertinent response.
- **Number of Views**: the overall popularity of the related topic/question
- **Answer Accepted**: a Boolean that identifies whether the answer provided by the expert was accepted by the original author

Metadata such as the items in the preceding list can be used to create
custom features that provide information to the ranker which it can
use to enhance learning about the problem domain. If the metadata has
a strong correlation to predicting relevance, you should see
improvements to overall relevance metrics.

The custom features that you can create for a Retrieve and Rank
implementation typically fall into 3 categories:

- Document
- Query
- Query and Document

You can write custom scorers using any of the following:

- DocumentScorer - A document scorer is a class whose input to the score method is a field or fields for a single Solr document. Consider a class called DocumentViews, which creates a score based on the number of views for a given topics and is represented a field in the Solr document.
- QueryScorer - A query scorer is a class whose input to the score method is a set of query params for a Solr query. Consider a class called IsQueryOnTopicScorer, which scores queries based on whether it thinks the underlying query text is on topic for the application domain.
- QueryDocumentScorer - A query-document scorer is a class whose input to the score method is 1) a set of query params for a Solr query, and 2) a field or fields for a Solr document. Consider a class that scores the extent to which the "text" of a Solr document answers definitional questions. More specifically, the scorer will 1) identify if a query is asking for a definition and 2) if so, identify whether the document contains a likely definition or not.

The custom scorer notebook provided here as part of this starter kit
provides access to a custom scoring framework allowing you to extract
new features for the purposes of training a ranker.

### Using Retrieve and Rank Custom Scorers

#### Description
This project enables the usage of custom features within the Retrieve & Rank service on Bluemix. This project was built in the Python programming language and uses the Flask micro-framework. To use this application, there is a Python script called `server.py`, which exposes two endpoints to be consumed by the application that uses it.

#### Application Architecture
The Flask server that is created within the script `server.py` is intended to run as a "sidecar" within the rest of the application; that is, the parent application will make REST API calls to this "sidecar" service rather than making direct calls to the deployed Retrieve & Rank service. The principal difference is that the Flask server will handle the integration/injection of
custom features that have been registered.

#### Steps to get set up

There are 4 steps to set up the server to integrate custom features:

* Configure your environment. The python flask server is already setup to run and extract features from custom scorers. The custom scorers are packaged as wheel package and need to be installed whenever a new custom scorerer is created.

* Identify the custom scorers for your application. A custom scorer is a Python class that extracts a signal that is to be used for the ranker. There are 3 types of scorers supported:

  1. "QueryDocument" Scorer - Extracts a signal/score based on both the contents of a query and the contents of a Solr Document
  2. "Document" Scorer - Extracts a signal based on the contents of the Solr Document alone
  3. "Query" Scorer - Extracts a signal based on the contents of the query alone

To make sure that the server has the most up to date scorers, go to the 'Custom Scorer' notebook and follow instructions to build and install the wheels package.

* Create a configuration file (see `config/features.json` as an example) to configure your application to consume these scorers. The configuration file must be a json file and
must contain a "scorers" field, which is a list of individual scorer configurations. For each of the scorers that you identified in the previous step, the scorer configuration is a JSON object
that must define the following:
    * an 'init_args' json object, whose fields are the arguments to the constructor for the scorer
    * a 'type' field, which should be either 'query', 'document' or 'query_document', depending on the type of scorer. The type is used to identify the package
    within the 'retrieve_and_rank_scorer' project that contains the appropriate scorer
    * a 'module' field, which is the name of the python module which contains the scorer
    * a 'class' field, which is the name of the scorer class
For comparison, the `config/features.json` contains a single Document scorer, in the module document, with the class UpVoteScorer. This is to extract feature based on the positive votes that a post has received.

* Start the Flask server by running the command

    ```sh
    python server.py
    ```

## Privacy Notice

Sample web applications that include the cf_deployment_tracker package included here may be configured to track deployments to [IBM Bluemix](https://www.bluemix.net/) and other Cloud Foundry platforms. The following information is sent to a [Deployment Tracker](https://github.com/IBM-Bluemix/cf-deployment-tracker-service) service on each deployment:

* Python package version
* Python repository URL
* Application Name (`application_name`)
* Space ID (`space_id`)
* Application Version (`application_version`)
* Application URIs (`application_uris`)
* Labels of bound services
* Number of instances for each bound service and associated plan information

This data is collected from the `server.py` file in the sample application and the `VCAP_APPLICATION` and `VCAP_SERVICES` environment variables in IBM Bluemix and other Cloud Foundry platforms. This data is used by IBM to track metrics around deployments of sample applications to IBM Bluemix to measure the usefulness of our examples, so that we can continuously improve the content we offer to you. Only deployments of sample applications that include code to ping the Deployment Tracker service will be tracked.
