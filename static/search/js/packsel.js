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