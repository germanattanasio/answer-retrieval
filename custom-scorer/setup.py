#!/usr/bin/env python
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

from setuptools import setup
from setuptools import find_packages

__version__ = '0.0.1'

setup(
	name='retrieve-and-rank-scorer',
	version=__version__,
    license='Apache 2.0',
    install_requires=['requests>=2.0, <3.0', 'spacy>=0.100.0, <1.0',
                      'numpy>=1.11.1, <2.0', 'futures>=3.0'],
	description='Custom Scorers for the IBM Watson Retrieve & Rank service',
	packages=find_packages(),
    zip_safe=True
)
