/**
 * Copyright 2015 IBM Corp. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the 'License");
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
/* global app:true */
'use strict';

$(document).ready(function () {
  var results_showing = 0;
  var isResultShown = false;
  var query_obj = [];
  var query_obj_size = 0;
  var footer_newClass = 'footer--inverted';
  var $randomQuery = $('.random-query');

  $.ajax({
    url: 'static/properties/query.properties',
    dataType: 'text',
    success: function (result) {
      var lines = result.split('\n');
      if ($('#query-list').find('li').length > 1) {
        return;
      }
      $.each(lines, function (n, line) {
        query_obj.push(line);
      });
      query_obj_size = $(query_obj).size();
      $randomQuery.removeClass('hide');
    }
  });

  //Create Random query
  $('.random-query, #random-query-large, #random-query-tos').click(function () {
    var rand_num = Math.floor(Math.random() * query_obj_size);
    if (this.className == 'random-query') {
      $('#query')[0].value = query_obj[rand_num];
      $('#query').focus();
    } else if (this.id == 'random-query-large') {
      $('#query-large')[0].value = query_obj[rand_num];
      $('#query-large').focus();
    } else {
      $('#query-tos')[0].value = query_obj[rand_num];
      $('#query-tos').focus();
    }

    setTimeout(function () {
      $('#retrieve_answers').trigger('click');
    }, 300);
  });

  //Capture enter key on Query input box
  $('#query, #query-large, #query-tos').focus().keydown(handleKeyDownEvent);

  function handleKeyDownEvent(e) {
    if (e.which != 13) {
      return true;
    } else {
      $('.compare-result').hide();
      $('#retrieve_answers').trigger('click');
      return false;
    }
  }

  //Load more answers is clicked
  $('#load-more').click(function () {
    results_showing = results_showing + 1;

    $($('#results').find('.row.hide')[0]).show('slow', function () {
      $($('#results').find('.row.hide')[0]).removeClass('hide');
      $('body').stop().animate({
        scrollTop: $('body')[0].scrollHeight
      }, 1000);
    });

    if (results_showing >= 6) {
      $('#load-more').hide();
    }
  });

  $('#retrieve_answers').unbind('click').bind('click', function () {
    var rows = $('#results').find('.row');
    for (var i = 0; i < rows.length; i++) {
      jQuery(rows[i]).remove();
    }
    results_showing = 1;
    $('#load-more').show();
    var query = $('#query').val().trim();
    if (query == '') {
      query = $('#query-large').val().trim();
    }
    if (query == '') {
      query = $('#query-tos').val().trim();
    }
    if (query == '') {
      return true;
    } else {
      $('#query-large').val(query);
    }

    $('.loading').fadeIn(500, function () {
      $('#query').val('');
      $('#query-tos').val('');
      $('footer').addClass(footer_newClass);
      $('#login-page').slideUp(500);
      $('#tos-page').slideUp(500);
      $('#answer_section').slideUp(10);
      //$('#home-page').slideDown(500);
      $('body').css('background', '#fff');
      $('footer').css('position', '');
      $('#home-page').show();
    });

    getData(query);
  });

  $('#otou').click(function () {
    if (isResultShown) {
      $('#query-tos').val($('#query-large').val());
      $('footer').css('position', '');
      $('#home-page').slideUp(500);
    } else {
      $('#query-tos').val($('#query').val());
      $('footer').addClass(footer_newClass);
      $('body').css('background', '#fff');
      $('#login-page').slideUp(500);
    }

    $('#tos-page').slideDown(500);
  });

  $('#close').click(function () {
    if (isResultShown) {
      $('#home-page').slideDown(500);
    } else {
      $('footer').removeClass(footer_newClass);
      $('body').css('background', '');
      //$('footer').css('position', 'fixed');
      $('#login-page').slideDown(500);
    }
    $('#tos-page').slideUp(500);
  });

  //Home Page
  $('#home').click(function () {
    $('#query').val('');
    $('#query-large').val('');
    $('#query-tos').val('');
    $('footer').removeClass(footer_newClass);
    $('#home-page').slideUp(500);
    $('#tos-page').slideUp(500);
    $('body').css('background', '');
    //$('footer').css('position', 'fixed');
    $('#login-page').slideDown(500);
    isResultShown = false;
  });

  //Create Model and Controller to call Watson API's
  function getData(query) {
    var model = new app.WatsonModel();
    var controller = new app.MainController(model);

    controller.retrieve_answers_apis(query);
    isResultShown = true;
  }
});
