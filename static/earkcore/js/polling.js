/**
 * polling.js
 *
 * Basic functions for starting a task, polling the task status, and acting upon successful task execution or reporting about task status information.
 */

/**
 * Function to get data requires "request_url" to be defined
 */
var request_func = function() {
    window.console.log("Get data request url: " + this.request_url);

   var req_func_timer = null;

   var success_func = function(resp_data) {
     if(resp_data.success) {
         window.console.log("Task accepted, task id: " + resp_data.id);

         pollstate(resp_data.id, this.success_func, this.update_func, this.poll_request_url, this.req, req_func_timer);
     } else {
        window.console.log(resp_data.errmsg);
        window.console.log(resp_data.errdetail);
     }
    }.bind(this);

   $.ajax({
    url: this.request_url,
    method: "POST",
    async: true,
    data: this.request_params,
    success: success_func,
   });
   // only execute ajax request, do not submit form

   return false;
};

/**
 * Function to poll task processing state
 */
function pollstate(in_task_id, success_func, update_func, poll_request_url, req_func_timer) {
    var ready = false;
    $(document).ready(function() {
          var PollState = function(task_id) {
              req_func_timer = setTimeout(function(){
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
                              window.console.log(resp_data.result)
                              success_func(resp_data.result);
                              window.clearTimeout(req_func_timer);
                              ready = true;
                          } else if(resp_data.state == 'PENDING') {
                                window.console.log("Checking task status of task: " + task_id);
                                window.console.log(resp_data.info.last_task);
                                update_func(resp_data.info);
                          } else {
                            window.console.log("task state: " + resp_data.state);
                          }
                      } else {
                        reportError(resp_data.errmsg)
                         ready = true;
                      }
                      // recursive call
                      if(!ready) { PollState(task_id); }
                  });
              }, 10000);
          }
          if(!ready) { PollState(in_task_id); }
      });
}