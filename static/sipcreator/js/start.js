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
            window.location.href = "/earkweb/sipcreator/detail/"+response;
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
