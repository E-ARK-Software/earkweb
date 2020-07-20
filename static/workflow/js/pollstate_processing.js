var ok_sign = ' <span class="glyphicon glyphicon-ok-sign" aria-hidden="true" style="color:#169816"/>';
var err_sign = ' <span class="glyphicon glyphicon-warning-sign" aria-hidden="true" style="color:red"/>';
var pending_sign = ' <span class="glyphicon glyphicon-time" aria-hidden="true" style="color:gray"/>';
var subitem_sign = '<span class="glyphicon glyphicon-chevron-right" aria-hidden="true" style="color:gray"/> ';


function setFinalState(success, message, t_id) {
    $('#progress').val(100);
    var msg = message  + "<br/>Task id: <a target='_blank' href='"+flowerServiceUrl+"task/"+t_id+"'>"+t_id+"</a>"
    if(success) {
        $('#confirmation').html('<span class="emph success">Success</span>: '+msg);
        $('#progress').addClass("ready");
    } else {
        $('#confirmation').html('<span class="fail emph">Error</span>: task execution failed!');
        $("#errordiv").show();
        $("#error").html(msg);
        $('#progress').addClass("error");
    }
    return success;
}

/**
 * required: pollingUrl
 */
function pollstate(in_task_id) {
    var ready = false;
    $("#childjobs").hide();
    $("#errordiv").hide();
    $(document).ready(function() {
        $("#errordiv").hide();
        var PollState = function(task_id) {
            // poll
            setTimeout(function() {
                window.console.log("Polling state of current task: " + task_id);
                $.ajax({
                    url: pollingUrl,
                    type: "POST",
                    data: "task_id=" + task_id,
                }).success(function(resp_data) {
                    window.console.log(resp_data);
                    if (resp_data.success) {
                        if (typeof(resp_data.progress) !== "undefined")
                            $('#progress').val(resp_data.progress);
                        if (resp_data.state == "SUCCESS") {
                            setFinalState(true, task_ready_msg, task_id);
                            ready = true;
                        } else if (resp_data.state == "FAILURE") {
                            setFinalState(false, resp_data.errmsg, task_id);
                            ready = true;
                        } else {
                            // check again if task still pending
                            setTimeout(function() {
                                pollstate(task_id)
                            }, 1000);
                        }
                    } else {
                        setFinalState(false, resp_data.errmsg, task_id);
                        ready = true;
                    }
                    // recursive call
                    if (!ready) {
                        PollState(task_id);
                    }
                });
            }, 1000);
        }
        if (!ready) {
            PollState(in_task_id);
        }
    });
}