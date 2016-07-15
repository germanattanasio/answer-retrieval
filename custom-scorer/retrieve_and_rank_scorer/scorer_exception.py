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

class ScorerConfigurationException(Exception):
    """
        Define exceptions to be used by various services.

        ScorerConfigurationException: Raised if a Scorer is improperly configured
        ScorerRuntimeException: Raised if a Scorer has a runtime error
    """

    def __init__(self, message):
        """ Wrapper exception for configuration issues. Should be raised if:
                1) Inputs to the constructor of a scorer are bad,
                2) Invariant to scorer is violated
                etc.
        """
        super(ScorerConfigurationException, self).__init__(message)
# endclass ScorerConfigurationException


class ScorerRuntimeException(Exception):
    def __init__(self, message):
        """ Wrapper exception for general runtime issues for a scorer. Should be raised if:
                1) Input to an api method (likely .score) is invalid
                2) Unforeseen problems prevent properly scoring a query, document, query/document pair
        """
        super(ScorerRuntimeException, self).__init__(message)
# endclass ScorerRuntimeException


class ScorerTimeoutException(ScorerRuntimeException):
    def __init__(self, message, args, kwargs):
        """ Should be raised if a scorer times out
        """
        super(ScorerTimeoutException, self).__init__(message)
        self._args = args
        self._kwargs = kwargs
#endclass ScorerTimeoutException
