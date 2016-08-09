/**
 * Update data table
 * current_ip variable must be provided (global scope)
 */
function updateTable(filterword) {
    $.ajax({
        url: "/earkweb/search/ips_table",
        type: "POST",
        data: "filterword=" + filterword,
    }).success(function(table_html){
        $('#ips-table').html(table_html);
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
        $('#aip2dip').addClass('active');
});
