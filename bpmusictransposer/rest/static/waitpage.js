$(document).ready(function(){
  var target_uuid = $("#resultContainer").attr("target")
  var completed = false

  var set_state = function(status){
    $('#resultState').text(status);
  }

  var displayResults = function(){
    var result_display = $('<ul>')
    for(var x in {file: 'PDF', source: 'LilyPond file'}){
      result_display.append($('<li>').append($('<a>').attr('href', '/parse/result/' + target_uuid + '/' + x).text('Converted ' + x)))
    }
    $('#resultContainer').append(result_display)

    $('#resultContainer').append($('<object>')
      .attr('type', 'application/pdf')
      .attr('data', '/parse/result/' + target_uuid + '/file')
      .attr('width', 800)
      .attr('height', 1200)
    );
  }

  var checkSuccess = function(){
    $.ajax('/parse/result/' + target_uuid,
      {
        complete: function(response){
          console.error(response.responseText)
          state = JSON.parse(response.responseText)['status']
          responseClasses = {};
          set_state(state)
          var waittime = {
            'Complete': Number.MAX_VALUE,
            'Failed': Number.MAX_VALUE,
            'Queued': 500,
            'Processing': 2500
          }[state]
          if(!['Complete', 'Failed'].includes(state)){
            setTimeout(checkSuccess, waittime)
          } else {
            displayResults()
          }
        },
        contentType: 'application/json',
        dataType: 'json'
      });
    };
  checkSuccess();
})
