/**
 * Populate tree using json representation of the directory hierarchy
 * (variable 'uuid' is provided as global variable)
 */
(function(){
    $.ajax({
        url: "/earkweb/sip2aip/get_directory_json",
        type: "POST",
        data: "uuid="+uuid,
    }).success(function(dir_as_json){
        $('#directorytree')
        .on('changed.jstree', function (e, data) {
            window.console.log(e);
            window.console.log(data);
         }).on('open_node.jstree', function (e, data) {
            $('#directorytree').jstree(true).set_icon(data.node.id, 'glyphicon glyphicon-folder-open');
         }).on('close_node.jstree', function (e, data) {
            $('#directorytree').jstree(true).set_icon(data.node.id, 'glyphicon glyphicon-folder-close');
         }).jstree({ 'core' : dir_as_json });
    });
})();