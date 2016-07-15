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
# -*- coding=utf8 -*-

import sys
import requests

try:
    url, user, pw, ranker_id = sys.argv[1:5]
    ranker_url = '%s/v1/rankers/%s' % (url, ranker_id)
    response_obj = requests.get(ranker_url, auth=(user, pw), headers={'Accept': 'application/json'}).json()
    print (response_obj.get('status', 'UNRESOLVED'))
except Exception:
    print ('FAILED')
