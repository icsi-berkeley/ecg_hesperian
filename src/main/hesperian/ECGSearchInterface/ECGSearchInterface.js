$(document).ready(function() {
  var ecgLoadingIcon = "<div id='resultboxgoogle-ecg' style='text-align:center'> \
                          <div class='loading-icon'> \
                            <div></div> \
                            <div></div> \
                            <div></div> \
                          </div> \
                        </div>"

  var googleReady = false;
  var onGoogleReady = [];


  function executeQuery(query, container_id, cleanup) {
    if (!googleReady) {
      onGoogleReady.push(function() { executeQuery(query, container_id, cleanup); });
      return;
    }

    google.search.cse.element.render({
      div: container_id,
      tag: 'searchresults-only',
      gname: container_id
    });
    google.search.cse.element.getElement(container_id).execute(query);

    $('#' + container_id).on('DOMNodeInserted', function() {
      $('#' + container_id + ' .loading-icon').remove();
      $('#' + container_id).css('text-align', 'initial');

      if (cleanup) {
        $('#' + container_id + ' .gsc-above-wrapper-area').remove();
        $('#' + container_id + ' .gsc-cursor-box').remove();
        $('#' + container_id + ' .gcsc-branding').remove();
        if ($('#' + container_id + ' .gs-spelling').length != 0) {
          $('#' + container_id + ' .gs-spelling').parent().remove();
        }

        // Change display property to avoid NotFoundError missing Node glitch when loading results
        if ($('#' + container_id + ' .gsc-expansionArea').length != 0) {
          $('#' + container_id + ' .gsc-expansionArea').css('display', 'none');
        }
      }
    });
  }

  function executeQueries(queries, container_id, cleanup) {
    if (!googleReady) {
      onGoogleReady.push(function() { executeQueries(queries, container_id, cleanup); });
      return;
    }

    google.search.cse.element.render({
      div: container_id,
      tag: 'searchresults-only',
      gname: container_id
    });

    console.log(queries);
    var idx = 0;
    function attemptQuery(idx) {
      console.log("Attempting query: " + queries[idx]);
      google.search.cse.element.getElement(container_id).clearAllResults();
      var query = queries[idx];
      google.search.cse.element.getElement(container_id).execute(query);
    }

    attemptQuery(idx);

    $('#' + container_id).on('DOMNodeInserted', function() {
      $('#' + container_id + ' .loading-icon').remove();
      $('#' + container_id).css('text-align', 'initial');

      if (cleanup) {
        $('#' + container_id + ' .gsc-above-wrapper-area').remove();
        $('#' + container_id + ' .gsc-cursor-box').remove();
        $('#' + container_id + ' .gcsc-branding').remove();
        if ($('#' + container_id + ' .gs-spelling').length != 0) {
          $('#' + container_id + ' .gs-spelling').parent().remove();
        }

        // Change display property to avoid NotFoundError missing Node glitch when loading results
        if ($('#' + container_id + ' .gsc-expansionArea').length != 0) {
          $('#' + container_id + ' .gsc-expansionArea').css('display', 'none');
          // check if no results here becuase the results must have loaded by now
          if ($('#' + container_id + ' .gs-no-results-result').length != 0 && idx + 1 < queries.length) {
            idx = idx + 1;
            $('#' + container_id + ' .gs-no-results-result').remove();
            attemptQuery(idx);
          }
        }
      }
    });
  }

  function renderClarification(clarification) {
    if (clarification['type'] == 'MC') {
      var text = clarification['text'];
      var options = clarification['options'].split("|");
      var mc_question_html = '<div data-type="' + clarification['type'] + '" \
                                   data-field="' + clarification['field'] + '" \
                                   class="clarification-question"> \
                                <p>Improve your results:</p> \
                                <h4>' + text + '</h4>';
      for (var i = 0; i < options.length; i++) {
        mc_question_html += '<input type="radio" name="ecg-clarification" \
                                                 id="clr-' + options[i] + '" \
                                                 value="' + options[i] + '">';
        mc_question_html += '<label for="clr-' + options[i] + '">' + options[i] + '</label>';
      }
      mc_question_html += '<div id="clarify-button" class="disabled">Submit</div></div>';
      $('#resultboxecg').prepend(mc_question_html);
      $('.clarification-question input[type=radio]').one('change', function() {
        $('#clarify-button').removeClass('disabled').addClass('enabled');
        $('#clarify-button').on('click', executeECGSearch);
      });
    }
  }

  function getClarificationInformation() {
    if ($('.clarification-question').length == 0)
      return null;
    var clarInfo = {
      'field': $('.clarification-question').data('field'),
      'type': $('.clarification-question').data('type'),
      'text': $('.clarification-question h4').text(),
      'val': null
    };
    if ($('.clarification-question input[type=radio]:checked').length > 0)
      clarInfo['val'] = $('.clarification-question input[type=radio]:checked').val();
    return clarInfo;
  }

  function processResponse(response) {
    sessionStorage.setItem('sid', response['sid']);
    if ('queries' in response)
      executeQueries(response['queries'], 'resultboxgoogle-ecg', true);
    if ('clarification' in response)
      renderClarification(response['clarification']);
    if ('fail' in response && response['fail'] == 'true') {
      console.log(response);
      failResponse();
    }
  }

  function failResponse() {
    $('#resultboxgoogle-ecg .loading-icon').remove();
    $('#resultboxgoogle-ecg').text('Unable to load ECG results');
  }

  function setupECGSearchInterface() {
    $('#bodyContent').addClass('ecgsearch');

    var cse_id = '011247967266094844877:t00ovurowh4';

    // Setup Google CSE Scripts
    (function() {
      var gcse = document.createElement('script');
      gcse.type = 'text/javascript';
      gcse.async = true;
      gcse.src = 'https://cse.google.com/cse.js?cx=' + cse_id;
      var s = document.getElementsByTagName('script')[0];
      s.parentNode.insertBefore(gcse, s);
    })();

    window.__gcse = {
      callback: function() {
        googleReady = true;
        if (onGoogleReady.length != 0) {
          for (var i = 0; i < onGoogleReady.length; i++) {
            onGoogleReady[i]();
          }
        }
      }
    };
  }

  function executeECGSearch() {
    var request = {
    	'action': 'ECGSearchInterfaceAPI',
    	'format': 'json',
      'query' : $('#ooui-1').val(), // Gets the value in the search box
      'sid'   : sessionStorage.getItem('sid'),
    };

    // Mediawiki API seems to require everything to be flattened
    var clarification = getClarificationInformation();
    if (clarification != null) {
      $.extend(request, {
        'clarification' : 1,
        'clarification_field' : clarification['field'],
        'clarification_type' : clarification['type'],
        'clarification_text' : clarification['text'],
        'clarification_val' : clarification['val']
      });
    } else {
      // weird bug with getAllowedParams makes this an integer
      request['clarification'] = 0;
    }

    $('#resultboxecg').html(ecgLoadingIcon);

    $.get('/w/api.php', request).done(function(response) {
      console.log(response);
      if ('ECGSearchInterfaceAPI' in response)
        processResponse(response['ECGSearchInterfaceAPI']);
      else {
        console.log(response);
        failResponse();
      }
    }).fail(failResponse);
  }

  function executeGoogleSearch() {
    executeQuery($('#ooui-1').val(), 'resultboxgoogle-std', false);
  }

  setupECGSearchInterface();
  executeECGSearch();
  executeGoogleSearch();
});
