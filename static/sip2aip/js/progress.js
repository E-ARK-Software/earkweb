function updateProgressInfo(percent) {
    window.console.log("we are at: "+percent);
    window.document.getElementById("pg").style = 'width:' + percent + '%';
    $('#st').html("In progress: "+percent+"%");
}
function updateStatusInfo(status, log, err) {
    if(status == 'SUCCESS') {
        window.document.getElementById("pg").style = 'width: 100%';
        $('#log').html(log)
        $('#err').html(err)
        $('#st').html("Finished");
    }
}


function pollstate(in_task_id) {

    $(document).ready(function() {
          var PollState = function(task_id) {
              // poll every second
              setTimeout(function(){

                  window.console.log("current task: "+task_id);

                  $.ajax({
                      url: "/earkweb/sip2aip/poll_state",
                      type: "POST",
                      data: "task_id=" + task_id,
                  }).success(function(task){

                      if(task.state == 'PROGRESS') {
                          updateProgressInfo(task.result.process_percent);
                      } else {

                      window.console.log(task);
                       window.console.log("log: "+task.log);
                       window.console.log("err: "+task.err);

                          updateStatusInfo(task.state, task.log, task.err);
                      }

                      // recursive call
                      PollState(task_id);
                  });

              }, 1000);
          }
          PollState(in_task_id);
      });

}
