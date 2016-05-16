/**
 * polling.js
 *
 * Basic polling functions
 */


/**
 * Function to get data requires "get_data_url" to be defined
 */
var get_data_func = function() {
   window.console.log("Get data request url: " + get_data_url);
   $.ajax({
    url: get_data_url,
    method: "POST",
    async: true,
    data: get_data_params,
    success: function(resp_data){
     if(resp_data.success) {
         window.console.log("Task accepted, task id: " + resp_data.id);
         pollstate(resp_data.id);
     } else {
        window.console.log(resp_data.errmsg);
        window.console.log(resp_data.errdetail);
     }
    }
   });
   // only execute ajax request, do not submit form
   return false;
};


/**
 * Function to poll task processing state
 * Requires "poll_request_url" to be defined and a success function poll_success_func(resp_data.result) to process the
 * result in case of success.
 */
function pollstate(in_task_id) {
    var ready = false;
    $(document).ready(function() {
          var PollState = function(task_id) {
              // poll every second
              setTimeout(function(){
                  window.console.log("Polling state of current task: "+task_id);
                  $.ajax({
                      url: poll_request_url,
                      type: "POST",
                      data: "task_id=" + task_id,
                  }).success(function(resp_data){
                      window.console.log(resp_data.state);
                      if(resp_data.success) {
                          if(resp_data.state == 'SUCCESS') {
                              window.console.log("Task status: success");
                              window.console.log("Result: " + resp_data.result);
                              var json_result = JSON.parse(resp_data.result);
                              poll_success_func(json_result);
                              ready = true;
                          } else if(resp_data.state == 'PENDING') {
                                // check again if task still pending
                                setTimeout(function(){ pollstate(task_id) }, 3000);
                          } else {
                            window.console.log("In progress ...");
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