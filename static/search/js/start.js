/**
 * Check package exists
 */
(function(){
    function checkPackageName(successCallback) {
        var pn = $( "#dip_creation_process_name" );
        var check_folder_url = "/earkweb/earkcore/check_submission_exists/" + pn.val()
        if (pn.val().length < 3) {
            $( "#msgpackagename" ).html("Package name must have at least 3 characters!");
            $("#startbtn").attr("disabled", "disabled");
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
                        $("#startbtn").removeAttr("disabled");
                        successCallback();
                    }
                });
            }
        }
    }
    /**
     * Continously check if folder for package name exists
     */
    $( "#dip_creation_process_name" ).keyup(function() {
       checkPackageName(function() {});
    });
})();
