/**
 * Update data table
 * current_ip variable must be provided (global scope)
 */
function updateTable() {
    $.ajax({
        url: "/earkweb/search/dip_detail_table",
        type: "POST",
        data: "pkg_id="+current_ip,
    }).success(function(table_html){
        $('#dip-detail-table').html(table_html);
    });
}