/**
 * Update data table
 * current_ip variable must be provided (global scope)
 */
function updateTable() {
    window.console.log("Update table ...")
    $.ajax({
        url: "/earkweb/management/ip_detail_table",
        type: "POST",
        data: "pkg_id="+current_ip,
    }).success(function(table_html){
        $('#ip-detail-table').html(table_html);
    });
}