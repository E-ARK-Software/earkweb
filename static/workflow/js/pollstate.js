var ok_sign = ' <span class="glyphicon glyphicon-ok-sign" aria-hidden="true" style="color:green"/>';
var err_sign = ' <span class="glyphicon glyphicon-warning-sign" aria-hidden="true" style="color:red"/>';
var pending_sign = ' <span class="glyphicon glyphicon-time" aria-hidden="true" style="color:gray"/>';
var subitem_sign = '<span class="glyphicon glyphicon-chevron-right" aria-hidden="true" style="color:gray"/> ';

/**
 * Poll task processing state
 */
function pollstate(in_task_id) {
    var ready = false;
    $("#childjobs").hide();
    $("#errordiv").hide();
    $(document).ready(function() {
        $("#errordiv").hide();
        var progressbar = $('#progress');
        var PollState = function(task_id) {
            // poll
            setTimeout(function() {
                window.console.log("Polling state of current task: " + task_id);
                $.ajax({
                    url: "/earkweb/submission/poll_state",
                    type: "POST",
                    data: "task_id=" + task_id,
                }).success(function(resp_data) {
                    window.console.log(resp_data);
                    if (resp_data.success) {
                        var atLeastOnePending = false;
                        var atLeastOneFailure = false;
                        var allSuccess = true;

                        if (typeof(resp_data.progress) !== "undefined")
                            progressbar.val(resp_data.progress);

                        $("#childjobs").empty();
                        if (typeof(resp_data.child_task_ids) !== "undefined") {
                            $("#childjobs").show();
                            for (var i = 0; i < resp_data.child_task_ids.length; i++) {
                                child_task_info = resp_data.child_task_ids[i]

                                child_status = child_task_info["status"]
                                child_task_id = child_task_info["taskid"]
                                child_task_name = child_task_info["name"]

                                //child_status = child_task_tuple[child_task_id];
                                if (child_status == 'PENDING')
                                    atLeastOnePending = true;
                                if (child_status != 'SUCCESS')
                                    allSuccess = false;
                                if (child_status == 'FAILURE')
                                    atLeastOneFailure = true;

                                window.console.log("Task: " + child_task_id + ", Status: " + child_status);
                                var link = "http://" + flowerHost + ":" + flowerPort + flowerPath + "task/" + child_task_id;
                                var child_task_item = '<a href="' + link + '" target="new">' + child_task_name + '</a>';
                                var outcomeSign = (child_status == 'SUCCESS') ? ok_sign : (child_status == 'FAILURE') ? err_sign : pending_sign;

                                var row = '<div class="row"><div class="col-md-6 col-md-offset-0">' + subitem_sign + child_task_item + '</div><div class="col-md-6">' + outcomeSign + '</div></div>';

                                $("#childjobs").append(row);
                            }
                            // All success or at least one failure: stop polling
                            if (allSuccess || atLeastOneFailure) {
                                progressbar.val(100);
                                if(allSuccess) {
                                    $('#confirmation').text(task_ready_msg);
                                    $('#progress').addClass("ready");
                                }
                                if(atLeastOneFailure) {
                                    $('#confirmation').text(task_error_msg);
                                    $('#progress').addClass("error");
                                }
                                ready = true;
                                $('#reviewbtn').removeClass('disabled');
                            } else if (atLeastOnePending) {
                                // check again if task still pending
                                setTimeout(function() {
                                    pollstate(task_id)
                                }, 1000);
                            } else {
                                window.console.log("Processing ...");
                            }
                        }
                    } else {
                        $("#errordiv").show();
                        $("#error").html('<b>Error</b>: '+resp_data.errmsg);
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