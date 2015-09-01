$('#apply-task').click( function() {
   $('#pg').css('width', '0%');
   $('#pg').removeClass('pgsuccess');
   window.console.log("Send task application request for ip " +
        $("#id_ips option:selected").text() + ", selected action: " + $("#id_wfs option:selected").text());
   $.ajax({
    url: "/earkweb/workflow/apply_task/",
    method: "POST",
    async: true,
    data: {'selected_ip': $( "#id_ips" ).val(),'selected_action': $( "#id_wfs" ).val()},
    success: function(resp_data){
     if(resp_data.success) {
         $("#error").invisible();
         window.console.log("Acceptance confirmation, task id: " + resp_data.id);
         $( "#taskheadline" ).html("Task: " + resp_data.id);
         pollstate(resp_data.id);
     } else {
        $("#error").visible();
        $("#errmsg").html(resp_data.errmsg)
        $("#err").html(resp_data.errdetail)
     }
    }
   });
   // only execute ajax request, do not submit form
   return false;
});

$('#apply-workflow').click( function() {
   $('#pg').css('width', '0%');
   $('#pg').removeClass('pgsuccess');
   window.console.log("Send task application request for ip " +
        $("#id_ips option:selected").text() + ", selected action: " + $("#id_wiref option:selected").text());
   $.ajax({
    url: "/earkweb/workflow/apply_workflow/",
    method: "POST",
    async: true,
    data: {'selected_ip': $( "#id_ips" ).val(),'selected_action': $( "#id_wiref" ).val()},
    success: function(resp_data){
     if(resp_data.success) {
         $("#error").invisible();
         window.console.log("Acceptance confirmation, task id: " + resp_data.id);
         $( "#taskheadline" ).html("Task: " + resp_data.id);
         pollstate(resp_data.id);
     } else {
        $("#error").visible();
        $("#errmsg").html(resp_data.errmsg)
        $("#err").html(resp_data.errdetail)
     }
    }
   });
   // only execute ajax request, do not submit form
   return false;
});