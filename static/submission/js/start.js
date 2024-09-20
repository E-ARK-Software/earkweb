/**
 * Start creating SIP
 */
(function(){

    function setValid(elmid) {
        $( "#"+elmid ).removeClass("error");
        $( "#"+elmid ).addClass("ok");
        $('#initialize').removeAttr("disabled");
    }

    function setInvalid(elmid) {
        $( "#"+elmid ).addClass("error");
        $( "#"+elmid ).removeClass("ok");
        $('#initialize').attr("disabled", "disabled");
    }

    $('#initialize').attr("disabled", "disabled");
//    $( "#initialize" ).on( "click", function() {
//        var pn = $( "#packagename" );
//        var extuid = $( "#extuid" );
//        var initialize_url = "/earkweb/submission/initialize/" + pn.val() + "/" + extuid.val() + "/";
//        $.ajax({
//            url: initialize_url,
//            type: "GET",
//        }).success(function(response){
////            window.location.href = "/earkweb/submission/detail/"+response;
//            window.location.href = "/earkweb/submission/upload_step1/"+response;
//        });
//    });
    function checkPackageName(successCallback) {
        var pn = $( "#packagename" );
        var check_folder_url = "/earkweb/check_submission_exists/" + pn.val()
        window.console.log(check_folder_url);
        if (pn.val().length < 3) {
            $( "#msgpackagename" ).html("The package name must consist of at least 3 characters!");
            setInvalid("packagename");
            return false;
        } else {
            $( "#msgpackagename" ).html("");
            var regex = new RegExp('^[a-zA-Z0-9\.\\-_]*$');
            if(!regex.test(pn.val())) {
                $( "#msgpackagename" ).html("Invalid characters in submission name!");
                setInvalid("packagename");
                return false;
            } else {


                $.ajax({
                    type: "GET",
                    url: check_folder_url,
                    success: function (folder_exists) {
                        if(folder_exists == 'true') {
                            $( "#msgpackagename" ).html("A submission with this name already exists, please choose another name!");
                            setInvalid("packagename");
                        } else {
                            $( "#msgpackagename" ).html("");
                            setValid("packagename");
                            successCallback();
                        }
                    }
                });

            }
        }
    }
    /**
     * Continously check if folder for data set exists
     */
    $( "#packagename" ).keyup(function() {
       checkPackageName(function() {});
    }).focus(function() {
       checkPackageName(function() {});
    });
    const uriPattern = /^(https?:\/\/[^\s/$.?#].[^\s]*|doi:\d{2}\.\d{4,9}\/[-._;()/:A-Z0-9]+|handle:[^\s]+|info:[^\s]+)$/i;
    function validateURI(uri) {
        return uriPattern.test(uri);
    }
    $( "#extuid" ).keyup(function() {
        var isValidURI = validateURI($(this).val());
        window.console.log(isValidURI);
        if($(this).val() == '' || isValidURI) {
            setValid("extuid");
        } else {
            setInvalid("extuid");
        }
    });
})();
