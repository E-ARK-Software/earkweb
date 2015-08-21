function updateProgressInfo(percent) {
    window.console.log("Progress: "+percent+"%");
    window.document.getElementById("pg").style = 'width:' + percent + '%';
    $('#st').html("In progress: "+percent+"%");
}
function updateStatusInfo(status, result, log, err) {
    window.console.log(status)
    window.console.log(result)
    if(status == 'SUCCESS') {
        window.document.getElementById("pg").style = 'width: 100%';
        $('#log').html(log)
        $('#err').html(err)
        $("#st").visible();
        if(result)
            $('#st').html("Finished successfully");
        else
            $('#st').html("Finished with error");
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
                      url: "/earkweb/sip2aip/poll_state",
                      type: "POST",
                      data: "task_id=" + task_id,
                  }).success(function(resp_data){
                      if(resp_data.success) {
                          if(resp_data.state == 'PROGRESS') {
                              updateProgressInfo(resp_data.info.process_percent);
                          } else {
                              updateStatusInfo(resp_data.state, resp_data.result, resp_data.log, resp_data.err);
                              ready = true;
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

/**
 * Update data table
 * current_ip variable must be provided (global scope)
 */
function updateTable() {
    $.ajax({
        url: "/earkweb/sip2aip/ip_detail_table",
        type: "POST",
        data: "pkg_id="+current_ip,
    }).success(function(table_html){
        $('#ip-detail-table').html(table_html);
    });
}
