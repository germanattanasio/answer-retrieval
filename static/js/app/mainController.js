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

(function (app) {
  'use strict';
  app.MainController = function (model) {
    this.model = model;
  };

  //Call Watson Retrieve And Rank API's
  app.MainController.prototype.retrieve_answers_apis = function (query) {

    var self = this;
    var custom_ranker = function () {
      var deferred = new $.Deferred();
      self.model.retrieve_and_rank_custom_ranker(query, deferred); //Watson Retrieve And Rank Custom Ranker API
      return deferred;
    };
    var solr = function () {
      var deferred = new $.Deferred();
      self.model.retrieve_and_rank_solr(query, deferred); //Watson Retrieve And Rank Solr API
      return deferred;
    };

    $.when(custom_ranker(), solr())
      .done(function (resCustomRanker, resSolr) {
        if (resCustomRanker.numFound == 0 && resSolr.numFound == 0) {
          $('.loading').fadeOut(500, function () {
            $('#answer_section').show('slow');
            return true;
          });
        }

        showResponseBoxColumns(resCustomRanker, '#box-custom-ranker');
        showResponseBoxColumns(resSolr, '#box-solr');
        $('.loading').fadeOut(500, function () {
          $('#answer_section').show('slow');
        });
      });
  };

  //Show list of boxes to the ui using API response
  function showResponseBoxColumns(response, parentBoxClass) {

    $(response.docs).each(function (i, doc) {
      var box = $('#answer_section').find('#box').clone().removeClass('hide').addClass('box').attr('id', '');
      var rowIndex = i + 1;
      if ($('#row' + rowIndex).length == 0) {
        addRow(rowIndex);
      }
      if (i != 0) {
        $('#row' + rowIndex).addClass('hide');
      }
      $(box).find('.box-text').text(trimAnswer(doc.answer[0]));
      $(box).find('.circle').text(i + 1);

      var diff = doc.upModVotes[0] - doc.downModVotes[0];
      $(box).find('#number-difference').text(diff);
      if (diff < 0) {
        $(box).find('#number-difference').removeClass('up-number').addClass('down-number');
        $(box).find('.rank-icon').attr('src', 'static/images/rank-down.svg');
      }

      $(box).find('.full-answer').click({
        doc: doc
      }, fullAnswer);
      if (parentBoxClass === '#box-solr') {
        $(box).find('.watson-icon').attr('src', 'static/images/solr.svg').addClass('solr-icon');
        $(box).find('img').attr('title', 'Solr Search ranker out of the box');
        $(box).find('.circle').attr('title', 'Rank difference between Ranker and Solr results" should be the text');
      }
      if ($('#row' + rowIndex).find(parentBoxClass).find('.box').length == 0) {
        $('#row' + rowIndex).find(parentBoxClass).append(box);
      }
    });
  }

  function addRow(index) {
    var row = $('#answer_section').find('#row').clone().attr('id', 'row' + index).addClass('row').removeClass('hide');
    $('#results').append(row);
    var fullAns = $('#answer_section').find('#fullAnswer').clone().attr('id', 'fullAnswer' + index).addClass('fullAnswer');
    row.append(fullAns);
  }

  function fullAnswer(event) {
    $('.selected-box').removeClass('selected-box').removeAttr('selected');
    var fullAns = $(this).parent().parent().parent().find('.fullAnswer');
    if ($(this).hasClass('hideAnswer')) {
      $(fullAns).fadeOut(500);

      $(this).text('See full answer');
      $(this).removeClass('hideAnswer');
      return;
    }
    if ($('#results').find('.hideAnswer').length > 0) {
      jQuery($('#results').find('.hideAnswer')[0]).text('See full answer').removeClass('hideAnswer');
      var answerPanes = $('#results').find('.fullAnswer');
      for (var i = 0; i < answerPanes.length; i++) {
        $(answerPanes[i]).fadeOut('slow');
      }
    }
    $(this).parent().addClass('selected-box').attr('selected', true);
    $(this).addClass('hideAnswer').text('Hide answer');

    var d = event.data.doc;
    $(fullAns.find('.result-title')[0]).text(d['title'][0]);
    $(fullAns.find('.result-subtitle')[0]).text(d['subtitle'][0]);
    $(fullAns.find('.result-answer')[0]).text(d['answer'][0]);
    $(fullAns.find('.result-upvotes')[0]).text(d['upModVotes'][0]);
    $(fullAns.find('.result-downvotes')[0]).text(d['downModVotes'][0]);
    $(fullAns.find('.result-reputation')[0]).text(d['userReputation'][0]);
    $(fullAns.find('.result-url')[0]).text('http://travel.stackexchange.com/questions/' + d['id']);
    $(fullAns.find('.result-url')[0]).attr('href', 'http://travel.stackexchange.com/questions/' + d['id']);
    $(fullAns.find('.result-username')[0]).text(d['username'][0]);
    if (d['userId'] != null) {
      $(fullAns.find('.result-username')[0]).attr('href', 'http://travel.stackexchange.com/users/' + d['userId'][0]);
    } else {
      $(fullAns.find('.result-username')[0]).attr('href', '#');
    }

    if (d['authorUsername'] != null && d['authorUserId'] != null) {
      $(fullAns.find('.author-username')[0]).text(d['authorUsername'][0]);
      $(fullAns.find('.author-username')[0]).attr('href', 'http://travel.stackexchange.com/users/' + d['authorUserId'][0]);
      $(fullAns.find('.author-username')[0]).parent().removeClass('hide');
    } else {
      $(fullAns.find('.author-username')[0]).parent().addClass('hide');
    }

    if (d['accepted'][0] == 0) {
      $(fullAns.find('.result-accepted')[0]).text('NO');
    } else {
      $(fullAns.find('.result-accepted')[0]).text('YES');
    }

    if ($(this).parent().parent()[0].id == 'box-solr') {
      $(fullAns).find('#this-is-why').addClass('hide');
    } else {
      $(fullAns).find('#this-is-why').removeClass('hide');
    }
    $(fullAns).fadeIn(500);
  }

  //Trim answer size up to 170 characters.
  function trimAnswer(s) {
    var maxSize = 140;
    if (s.length > maxSize) {
      return s.substr(0, maxSize) + ' ...';
    } else {
      return s;
    }
  }

})(window.app || (window.app = {}));
