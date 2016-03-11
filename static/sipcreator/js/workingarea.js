/**
 * Populate tree using json representation of the directory hierarchy
 * (variable 'uuid' is provided as global variable)
 */

// container: dirtree-content
function loadDir(containerelm, uuid, rep) {
    window.console.log("loadDir(uuid:"+uuid+", rep:"+rep+")")
    var containerelm = containerelm;
    $.ajax({
        url: "/earkweb/earkcore/get_directory_json",
        type: "POST",
        data: "uuid="+uuid+"/"+rep,
        context: document.body,
        global: true,
    }).success(function(dir_as_json){

        containerelm
        .on('changed.jstree', function (e, data) {
            window.console.log(e);
            window.console.log(data);
         }).on('open_node.jstree', function (e, data) {
            //$('#directorytree').jstree(true).set_icon(data.node.id, 'glyphicon glyphicon-folder-open');
         }).on('close_node.jstree', function (e, data) {
            //$('#directorytree').jstree(true).set_icon(data.node.id, 'glyphicon glyphicon-folder-close');
         }).on('loaded.jstree', function() {
            containerelm.jstree('open_all');
         }).jstree({'open_all': true, 'core' : dir_as_json }).jstree("open_node", $('#j1_1'));

    });

}
if(rep != "") {
    loadDir($('#dirtree-content'), uuid, 'representations/'+rep+'/data');
    loadDir($('#dirtree-documentation'), uuid, 'representations/'+rep+'/documentation');
    loadDir($('#dirtree-schemas'), uuid, 'representations/'+rep+'/schemas');

    loadDir($('#dirtree-metadata'), uuid, 'metadata');

    loadDir($('#dirtree-rootschemas'), uuid, 'schemas');

}
//(function(){
//    $.ajax({
//        url: "/earkweb/earkcore/get_directory_json",
//        type: "POST",
//        data: "uuid="+uuid,
//    }).success(function(dir_as_json){
//        $('#dirtree-content')
//        .on('changed.jstree', function (e, data) {
//            window.console.log(e);
//            window.console.log(data);
//         }).on('open_node.jstree', function (e, data) {
//            //$('#directorytree').jstree(true).set_icon(data.node.id, 'glyphicon glyphicon-folder-open');
//         }).on('close_node.jstree', function (e, data) {
//            //$('#directorytree').jstree(true).set_icon(data.node.id, 'glyphicon glyphicon-folder-close');
//         }).on('loaded.jstree', function() {
//            $('#dirtree-content').jstree('open_all');
//         }).jstree({'open_all': true, 'core' : dir_as_json }).jstree("open_node", $('#j1_1'));
//
//    });
//
//})();

$('#dirtree-content').bind("dblclick.jstree", function (event) {
   var node = $(event.target).closest("li");
   var data = node.data("jstree");
   window.console.log(data);
});


/**
 * Populate tree using json representation of the directory hierarchy
 * (variable 'uuid' is provided as global variable)
 */
//(function(){
//    $.ajax({
//        url: "/earkweb/earkcore/get_directory_json",
//        type: "POST",
//        data: "uuid="+uuiddocumentation,
//    }).success(function(dir_as_json){
//        $('#dirtree-documentation')
//        .on('changed.jstree', function (e, data) {
//            window.console.log(e);
//            window.console.log(data);
//         }).on('open_node.jstree', function (e, data) {
//            //$('#directorytree').jstree(true).set_icon(data.node.id, 'glyphicon glyphicon-folder-open');
//         }).on('close_node.jstree', function (e, data) {
//            $('#directorytree').jstree(true).set_icon(data.node.id, 'glyphicon glyphicon-folder-close');
//         }).on('loaded.jstree', function() {
//            $('#dirtree-documentation').jstree('open_all');
//         }).jstree({ 'core' : dir_as_json });
//    });
//})();

/**
 * Populate tree using json representation of the directory hierarchy
 * (variable 'uuid' is provided as global variable)
 */
//(function(){
//    $.ajax({
//        url: "/earkweb/earkcore/get_directory_json",
//        type: "POST",
//        data: "uuid="+uuiddescriptivemetadata,
//    }).success(function(dir_as_json){
//        $('#dirtree-metadata')
//        .on('changed.jstree', function (e, data) {
//            window.console.log(e);
//            window.console.log(data);
//         }).on('open_node.jstree', function (e, data) {
//            //$('#directorytree').jstree(true).set_icon(data.node.id, 'glyphicon glyphicon-folder-open');
//         }).on('close_node.jstree', function (e, data) {
//            //$('#directorytree').jstree(true).set_icon(data.node.id, 'glyphicon glyphicon-folder-close');
//         }).on('loaded.jstree', function() {
//            $('#dirtree-metadata').jstree('open_all');
//         }).jstree({ 'core' : dir_as_json });
//
//
//    });
//})();


/**
 * Populate tree using json representation of the directory hierarchy
 * (variable 'uuid' is provided as global variable)
 */
//(function(){
//    $.ajax({
//        url: "/earkweb/earkcore/get_directory_json",
//        type: "POST",
//        data: "uuid="+uuidmschemas,
//    }).success(function(dir_as_json){
//        $('#dirtree-schemas')
//        .on('changed.jstree', function (e, data) {
//            window.console.log(e);
//            window.console.log(data);
//         }).on('open_node.jstree', function (e, data) {
//            //$('#directorytree').jstree(true).set_icon(data.node.id, 'glyphicon glyphicon-folder-open');
//         }).on('close_node.jstree', function (e, data) {
//            //$('#directorytree').jstree(true).set_icon(data.node.id, 'glyphicon glyphicon-folder-close');
//         }).on('loaded.jstree', function() {
//            $('#dirtree-schemas').jstree('open_all');
//         }).jstree({ 'core' : dir_as_json });
//
//
//    });
//})();