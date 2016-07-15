#!/usr/bin/env python
# Copyright 2016 IBM Corp. All Rights Reserved.
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
#
import csv
import subprocess
import json
import shlex
import os
import sys
import getopt

#remove the ranker training file (just in case it's left over from a previous run)
curdir = os.getcwd()
TRAININGDATA = curdir+'/../data/groundtruth/trainingdata.csv'
try:
    os.remove(TRAININGDATA)
except OSError:
    pass

CREDS = ''
CLUSTER = ''
COLLECTION = ''
RELEVANCE_FILE = ''
RANKERNAME = ''
ROWS = '10'
DEBUG = False
VERBOSE = ''

def usage():
    print ('train.py -u <username:password> -i <query relevance file> -c <solr cluster> -x <solr collection> -r [option_argument <solr rows per query>] -n <ranker name> -d [enable debug output for script] -v [ enable verbose output for curl]')

try:
    opts, args = getopt.getopt(sys.argv[1:], 'hdvu:i:c:x:n:r:', [
        'user=', 'inputfile=', 'cluster=', 'collection=', 'name=', 'rows='])
except getopt.GetoptError as err:
    print str(err)
    print usage()
    sys.exit(2)
for opt, arg in opts:
    if opt == '-h':
        usage()
        sys.exit()
    elif opt in ('-u', '--user'):
        CREDS = arg
    elif opt in ('-i', '--inputfile'):
        RELEVANCE_FILE = arg
    elif opt in ('-c', '--cluster'):
        CLUSTER = arg
    elif opt in ('-x', '--collection'):
        COLLECTION = arg
    elif opt in ('-n', '--name'):
        RANKERNAME = arg
    elif opt in ('-r', '--rows'):
        ROWS = arg
    elif opt == '-d':
        DEBUG = True
    elif opt == '-v':
        VERBOSE = '-v'

if not RELEVANCE_FILE or not CLUSTER or not COLLECTION or not RANKERNAME:
    print ('Required argument missing.')
    usage()
    sys.exit(2)

print ('Input file is %s' % (RELEVANCE_FILE))
print ('Solr cluster is %s' % (CLUSTER))
print ('Solr collection is %s' % (COLLECTION))
print ('Ranker name is %s' % (RANKERNAME))
print ('Rows per query %s' % (ROWS))

#constants used for the SOLR and Ranker URLs
BASEURL = 'https://gateway.watsonplatform.net/retrieve-and-rank/api/v1/'
SOLRURL = BASEURL+'solr_clusters/%s/solr/%s/fcselect' % (CLUSTER, COLLECTION)
RANKERURL = BASEURL+'rankers'

with open(RELEVANCE_FILE, 'rb') as csvfile:
    add_header = 'true'
    question_relevance = csv.reader(csvfile)
    with open(TRAININGDATA, 'a') as training_file:
        print ('Generating training data...')
        for row in question_relevance:
            if not row:
                continue
            question = row[0]
            relevance = ','.join(row[1:])
            curl_cmd = 'curl -k -s %s -u %s -d "q=%s&gt=%s&generateHeader=%s&rows=%s&returnRSInput=true&wt=json" "%s"' % (VERBOSE, CREDS, question, relevance, add_header, ROWS, SOLRURL)
            if DEBUG:
                print (curl_cmd)
            process = subprocess.Popen(shlex.split(curl_cmd), stdout=subprocess.PIPE)
            output = process.communicate()[0]
            if DEBUG:
                print (output)
            try:
                parsed_json = json.loads(output)
                training_file.write(parsed_json['RSInput'])
            except Exception:
                print ('Command:')
                print (curl_cmd)
                print ('Response:')
                print (output)
            add_header = 'false'
print ('Generating training data complete.')
