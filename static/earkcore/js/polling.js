/**
 * polling.js
 *
 * Basic functions for starting a task, polling the task status, and acting upon successful task execution or reporting about task status information.
 */


/**
 * Function to poll task processing state
 */
var pollstate = function (poll_interval, in_task_id, success_func, update_func, poll_request_url) {
    var ready = false;
    $(document).ready(function() {
          var PollState = function(task_id) {
              setTimeout(function(){
                  $.ajax({
                      url: poll_request_url,
                      type: "POST",
                      data: "task_id=" + task_id,
                  }).success(function(resp_data){
                      window.console.log("Task state: " + resp_data.state);
                      if(resp_data.success) {
                          if(resp_data.state == 'SUCCESS') {
                              window.console.log("Task result:");
                              window.console.log(resp_data.result)
                              success_func(resp_data.result);
                              ready = true;
                          } else if(resp_data.state == 'PENDING') {
                                window.console.log("Checking task status of task: " + task_id);
                                update_func(resp_data.info);
                          } else if(resp_data.state == 'FAILURE') {
                                window.console.log("An error occurred in task: " + task_id);
                                update_func({'errmsg': "Task execution failed!"});
                          } else {
                            window.console.log("task state: " + resp_data.state);
                          }
                      } else {
                        window.console.log("Poll error: "+resp_data.errmsg)
                         ready = true;
                      }
                      // recursive call
                      if(!ready) { window.console.log("PollState-task_id("+task_id+")"); PollState(task_id); }
                  });
              }, poll_interval);
          }
          if(!ready) { window.console.log("PollState-in_task_id("+in_task_id+")");  PollState(in_task_id); }
      });
}.bind(this);



/**
 * Function to get data requires "request_url" to be defined
 */
var request_func = function() {
   window.console.log("Get data request url: " + this.request_url);

   var success_func = function(resp_data) {


     if(resp_data.success) {
         window.console.log("Task accepted, task id: " + resp_data.id);
         this.poll_func(this.poll_interval, resp_data.id, this.success_func, this.update_func, this.poll_request_url);
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
