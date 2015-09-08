$(document).on("click", "[id^=remproc]", function() {
    var whats = $(this);
    window.console.log(whats);
    window.console.log(whats.context.id);
    $.ajax({
      url: "remproc",
      context: $(this),
      data: { "remproc": whats.context.title },
      method: "POST"
    }).success(function(responsedata) {
        window.console.log(responsedata);
        var dip_p = $($(this)).context.id.replace('remproc','');
        $('#'+dip_p).remove();
    });
 });
 $(document).on("click", "[id^=remaip]", function() {
    var whats = $(this);
    window.console.log(whats);
    window.console.log(whats.context.id);
    $.ajax({
      url: "remaip",
      context: $(this),
      data: { "remaip": whats.context.title },
      method: "POST"
    }).success(function(responsedata) {
        var respJson = JSON.parse(responsedata);
        if(respJson.success) {
            var package_p_id = respJson.dip_name + respJson.aip_identifier;
            window.console.log(package_p_id);
            $('#'+package_p_id).remove();
        }
    });
 });