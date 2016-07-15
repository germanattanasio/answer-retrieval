/**
 * Copyright 2016 IBM Corp. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/*globals Promise:true*/

(function (app) {

  app.WatsonModel = function () {
    this._pendingRequests = [];
  };

  app.WatsonModel.prototype.retrieve_and_rank_custom_ranker = function (query, deferred) {
    var retrieve_and_rank_custom_ranker = this._sendRequest('/api/custom_ranker', { q: query });
    return new Promise(function () {
      retrieve_and_rank_custom_ranker.then(function (response) {
        deferred.resolve(response.response);
      }).catch(function (reason) {
        deferred.reject(reason);
      });
    });

  };

  app.WatsonModel.prototype.retrieve_and_rank_solr = function (query, deferred) {
    var retrieve_and_rank_solr = this._sendRequest('/api/solr', { q: query });
    return new Promise(function () {
      retrieve_and_rank_solr.then(function (response) {
        deferred.resolve(response);
      }).catch(function (reason) {
        deferred.reject(reason);
      });
    });

  };

  app.WatsonModel.prototype._convertOptionsToQuery = function (options, queryStr) {
    if (!queryStr) {
      queryStr = '';
    }
    var sep = queryStr.length ? '&' : '';

    for (var attr in options) {
      if (options.hasOwnProperty(attr)) {
        queryStr += sep + encodeURIComponent(attr) + '=';
        queryStr += encodeURIComponent(options[attr]);
        sep = '&';
      }
    }
    return queryStr;
  };

  app.WatsonModel.prototype._createRequestURL = function (baseUrl, options) {
    var queryStr = this._convertOptionsToQuery(options);
    var defaultQueryOptions = {};
    queryStr = this._convertOptionsToQuery(defaultQueryOptions, queryStr);
    if (queryStr.length) {
      queryStr = '?' + queryStr;
    }
    return baseUrl + queryStr;
  };

  app.WatsonModel.prototype._removePendingRequest = function (req) {
    var index = this._pendingRequests.indexOf(req);
    if (index !== -1) {
      this._pendingRequests.splice(index, 1);
    }
  };

  app.WatsonModel.prototype._sendRequest = function (url, options) {
    var requestURL = this._createRequestURL(url, options);
    var self = this;
    return new Promise(function (resolve, reject) {

      var req = new XMLHttpRequest();
      req.addEventListener('load', function () {
        self._removePendingRequest(req);
        if (this.status >= 200 && this.status < 300) {
          var responseObj = JSON.parse(this.responseText);
          resolve(responseObj);
        } else {
          reject(this);
        }
      });

      req.open('GET', requestURL, true);
      req.send();
      self._pendingRequests.push(req);
    });
  };

})(window.app || (window.app = {}));
