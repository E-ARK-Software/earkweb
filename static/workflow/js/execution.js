var ok_sign = ' <span class="fas fa-check-circle" aria-hidden="true" style="color:#169816"/>';
var err_sign = ' <span class="fas fa-exclamation-circle" aria-hidden="true" style="color:red"/>';
var pending_sign = ' <span class="fas fa-clock" aria-hidden="true" style="color:gray"/>';
var subitem_sign = '<span class="fas fa-chevron-right" aria-hidden="true" style="color:gray"/> ';

/**
 * Poll task processing state
 */
function pollstate(in_task_id) {
    var ready = false;
    $(document).ready(function() {
          var PollState = function(task_id) {
              // poll
              setTimeout(function(){
                  window.console.log("Polling state of current task: "+task_id);
                  $.ajax({
                      url: "/earkweb/submission/poll_state",
                      type: "POST",
                      data: "task_id=" + task_id,
                      success: function(resp_data){
                      if(resp_data.success) {
                          var atLeastOnePending = false;
                          var atLeastOneFailure = false;
                          var allSuccess = true;
                          $("#childjobs").empty();

                          for (var i = 0; i < resp_data.task_list.length; i++) {
                            child_task_info = resp_data.task_list[i]

                            child_status = child_task_info["state"]
                            child_task_id = child_task_info["uuid"]
                            child_task_name = child_task_info["name"]

                            //child_status = child_task_tuple[child_task_id];
                            if(child_status=='PENDING')
                                atLeastOnePending = true;
                            if(child_status!='SUCCESS')
                                allSuccess = false;
                            if(child_status=='FAILURE')
                                atLeastOneFailure = true;

                            window.console.log("Task: "+child_task_id+", Status: "+child_status);
                            var link = "http://"+flowerHost+":"+flowerPort+flowerPath+"task/"+child_task_id;
                            var child_task_item = '<a href="'+link+'" target="new">' + child_task_name + '</a>';
                            var outcomeSign = (child_status=='SUCCESS') ? ok_sign : (child_status=='FAILURE') ? err_sign : pending_sign;

                            var row = '<div class="row"><div class="col">'+subitem_sign+child_task_item+'</div><div class="col">'+outcomeSign+'</div></div>';

                            $("#childjobs").append(row);
                          }
                          // All success or at least one failure: stop polling
                          if(allSuccess || atLeastOneFailure) {
                              $('#confirmation').text(pipeline_ready_msg)
                              updateTable();
                              ready = true;
                          } else if(atLeastOnePending) {
                                // check again if task still pending
                                setTimeout(function(){ pollstate(task_id) }, 3000);
                          } else {
                            window.console.log("Processing ...");
                          }
                      } else {
                        $( "#error" ).html(resp_data.errmsg);
                         ready = true;
                      }
                      // recursive call
                      if(!ready) { PollState(task_id); }
                  }
                  });
              }, 3000);
          }
          if(!ready) { PollState(in_task_id); }
      });
}

$( document ).ready(function() {
    $( "#starting" ).on( "click", function() {
        $("#error").invisible();
        $('#starting').attr("disabled", "disabled");
        $( "#confirmation" ).html(ingestProcessStartedMessage);
        $.ajax({
            url: "/earkweb/submission/apply_task/",
            method: "POST",
            async: true,
            data: {'selected_ip': current_ip},
            success: function(resp_data){
             if(resp_data.success) {
                 $("#error").invisible();
                 window.console.log("Acceptance confirmation, task id: " + resp_data.id);
                 var link = "http://"+flowerHost+":"+flowerPort+flowerPath+"task/"+resp_data.id;
                 var task_item = '<a href="'+link+'" target="new">ingest_pipeline</a>';
                 var row = '<div class="row"><div class="col">'+task_item+'</div><div class="col">'+ok_sign+'</div></div>';
                  $("#ingestjobid").append(row);
                 pollstate(resp_data.id);
             } else {
                $("#error").visible();
                $("#errmsg").html(resp_data.errmsg)
                $("#err").html(resp_data.errdetail)
             }
            },
            error: function(resp_data){
                var errData = resp_data.responseJSON;
                window.console.log("Error");
                window.console.log(resp_data.responseJSON);
                $("#error").visible();
                $("#errmsg").html(errData.errmsg)
                $("#errdetail").html(errData.errdetail);
                $( "#confirmation" ).invisible();
            }
            });
            // only execute ajax request, do not submit form
            return false;
    });
});
