function updateProgressInfo(percent) {
    $( '#pg' ).removeClass( "pgsuccess" );
    window.console.log("Progress: "+percent+"%");
    window.document.getElementById("pg").style = 'width:' + percent + '%; background-color: #AD2624';
    $('#st').html("In progress: "+percent+"%");
}
function updateStatusInfo(status, result, log, err) {
    window.console.log(status)
    window.console.log(result)
    if(status == 'SUCCESS') {
        var pg =  window.document.getElementById("pg");
        pg.style = 'width: 100%';
        $('#log').html(log)
        $('#err').html(err)
        $("#st").visible();
        if(result) {
            $('#st').html("Finished successfully");
            $( '#pg' ).addClass( "pgsuccess" );
        } else
            $( '#st' ).html("Finished with error");
    }
    updateTable();
}

function reportError(errmsg) {
    $("#error").visible();
    $('#errmsg').html(errmsg)
}

/**
 * Poll task processing state
 */
function pollstate(in_task_id) {
    var ready = false;
    $(document).ready(function() {
          var PollState = function(task_id) {
              // poll every second
              setTimeout(function(){
                  window.console.log("Polling state of current task: "+task_id);
                  $.ajax({
                      url: "/earkweb/workflow/poll_state",
                      type: "POST",
                      data: "task_id=" + task_id,
                  }).success(function(resp_data){
                      if(resp_data.success) {
                          if(resp_data.state == 'SUCCESS') {
                              updateStatusInfo(resp_data.state, resp_data.result, resp_data.log, resp_data.err);
                              ready = true;
                          } else if(resp_data.state == 'PENDING') {
                                // check again if task still pending
                                setTimeout(function(){ pollstate(task_id) }, 3000);
                          } else {
                            updateProgressInfo(resp_data.info.process_percent);
                          }
                      } else {
                        reportError(resp_data.errmsg)
                         ready = true;
                      }
                      // recursive call
                      if(!ready) { PollState(task_id); }
                  });
              }, 1000);
          }
          if(!ready) { PollState(in_task_id); }
      });
}