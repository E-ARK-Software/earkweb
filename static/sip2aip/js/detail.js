/**
 * Update data table
 * current_ip variable must be provided (global scope)
 */
function updateTable() {
    $.ajax({
        url: "/earkweb/sip2aip/ip_detail_table",
        type: "POST",
        data: "pkg_id="+current_ip,
    }).success(function(table_html){
        $('#ip-detail-table').html(table_html);
    });
}