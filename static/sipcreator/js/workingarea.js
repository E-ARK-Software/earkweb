/**
 * Start creating SIP
 */
(function(){
    $( "#initialize" ).on( "click", function() {
        var pn = $( "#packagename" );
        var initialize_url = "/earkweb/sipcreator/initialize/" + pn.val()
        $.ajax({
            url: initialize_url,
            type: "GET",
        }).success(function(response){
            window.location.href = "/earkweb/sipcreator/index";
        });
    });
    function checkPackageName(successCallback) {
        var pn = $( "#packagename" );
        var check_folder_url = "/earkweb/earkcore/check_submission_exists/" + pn.val()
        if (pn.val().length < 3) {
            $( "#msgpackagename" ).html("Package name must have at least 3 characters!");
            $("#createsip").attr("disabled", "disabled");
            return false;
        } else {
            $( "#msgpackagename" ).html("");
            var regex = new RegExp('^[a-zA-Z0-9_\.\-]*$');
            if(!regex.test(pn.val())) {
                $( "#msgpackagename" ).html("Invalid characters in package name!");
                $("#createsip").attr("disabled", "disabled");
                return false;
            } else {
                $.ajax({
                    url: check_folder_url,
                    type: "GET",
                }).success(function(folder_exists){
                    if(folder_exists == 'true') {
                        $( "#msgpackagename" ).html("A package with this name already exists, please choose another name!");
                        $("#createsip").attr("disabled", "disabled");
                    } else {
                        $( "#msgpackagename" ).html("");
                        $("#createsip").removeAttr("disabled");
                        successCallback();
                    }
                });
            }
        }
    }
    /**
     * Continously check if folder for package name exists
     */
    $( "#packagename" ).keyup(function() {
       checkPackageName(function() {});
    });
})();

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
        $('#dirtree-content')
        .on('changed.jstree', function (e, data) {
            window.console.log(e);
            window.console.log(data);
         }).on('open_node.jstree', function (e, data) {
            //$('#directorytree').jstree(true).set_icon(data.node.id, 'glyphicon glyphicon-folder-open');
         }).on('close_node.jstree', function (e, data) {
            //$('#directorytree').jstree(true).set_icon(data.node.id, 'glyphicon glyphicon-folder-close');
         }).on('loaded.jstree', function() {
            $('#dirtree-content').jstree('open_all');
         }).jstree({'open_all': true, 'core' : dir_as_json }).jstree("open_node", $('#j1_1'));

    });

})();

$('#dirtree-content').bind("dblclick.jstree", function (event) {
   var node = $(event.target).closest("li");
   var data = node.data("jstree");
   window.console.log(data);
});


/**
 * Populate tree using json representation of the directory hierarchy
 * (variable 'uuid' is provided as global variable)
 */
(function(){
    $.ajax({
        url: "/earkweb/sip2aip/get_directory_json",
        type: "POST",
        data: "uuid="+uuidcontent,
    }).success(function(dir_as_json){
        $('#dirtree-documentation')
        .on('changed.jstree', function (e, data) {
            window.console.log(e);
            window.console.log(data);
         }).on('open_node.jstree', function (e, data) {
            //$('#directorytree').jstree(true).set_icon(data.node.id, 'glyphicon glyphicon-folder-open');
         }).on('close_node.jstree', function (e, data) {
            $('#directorytree').jstree(true).set_icon(data.node.id, 'glyphicon glyphicon-folder-close');
         }).on('loaded.jstree', function() {
            $('#dirtree-documentation').jstree('open_all');
         }).jstree({ 'core' : dir_as_json });
    });
})();

/**
 * Populate tree using json representation of the directory hierarchy
 * (variable 'uuid' is provided as global variable)
 */
(function(){
    $.ajax({
        url: "/earkweb/sip2aip/get_directory_json",
        type: "POST",
        data: "uuid="+uuidmetadata,
    }).success(function(dir_as_json){
        $('#dirtree-metadata')
        .on('changed.jstree', function (e, data) {
            window.console.log(e);
            window.console.log(data);
         }).on('open_node.jstree', function (e, data) {
            //$('#directorytree').jstree(true).set_icon(data.node.id, 'glyphicon glyphicon-folder-open');
         }).on('close_node.jstree', function (e, data) {
            //$('#directorytree').jstree(true).set_icon(data.node.id, 'glyphicon glyphicon-folder-close');
         }).on('loaded.jstree', function() {
            $('#dirtree-metadata').jstree('open_all');
         }).jstree({ 'core' : dir_as_json });


    });
})();