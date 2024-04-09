/**
 * Update data table
 * current_ip variable must be provided (global scope)
 */
function updateTable(filterword) {
    $.ajax({
        url: "/earkweb/submission/ips_table",
        type: "POST",
        data: "filterword=" + filterword,
        success: function(table_html){
            console.log("Table updated!")
            $('#ips-table').html(table_html);
        },
        error: function(err){
            console.log(err);
        }
    });
}
$( document ).ready(function() {
    $( "#filterchars" ).keyup(function() {
       updateTable($('#filterchars').val());
       window.console.log($('#filterchars').val());
    });
});
$(document).ready(function () {
        $(".nav li").removeClass("active");
        $('#submission').addClass('active');
});

