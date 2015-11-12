/**
 * Check package exists
 */
$( document ).ready(function() {

        function checkValidParentIdentifier(successCallback) {
            var idelm = $( "#parent" );
            var check_identifier_url = "/earkweb/earkcore/check_identifier_exists/" + idelm.val()
            if (idelm.val().length < 3) {
                $('#parent').css({color:'red'});

                $('#proceedbtn').attr("disabled","disabled");
                return false;
            } else {
                var regex = new RegExp('^[a-zA-Z0-9_\.\-]*$');
                if(!regex.test(idelm.val())) {
                    $('#parent').css({color:'red'});
                    $('#proceedbtn').attr("disabled","disabled");
                    return false;
                } else {
                    $.ajax({
                        url: check_identifier_url,
                        type: "GET",
                    }).success(function(identifier_exists){
                        if(identifier_exists == 'true') {
                            $('#parent').css({color:'green'});
                            $('#proceedbtn').removeAttr("disabled");
                            successCallback();
                        } else {
                            $('#parent').css({color:'red'});
                            $('#proceedbtn').attr("disabled","disabled");
                        }
                    });
                }
            }
        }
        /**
         * Continously check if folder for package name exists
         */
        function validIdentifierEntered() {
            var idelm = $( "#parent" );
            var url = "/earkweb/earkcore/save_parent_identifier/" + uuid + "/"
            $.ajax({
                url: url,
                type: "POST",
                data: "parent_identifier="+idelm.val(),
            }).success(function(identifier_exists){

            });
        }
        $( "#parent" ).keyup(function() {
           checkValidParentIdentifier(validIdentifierEntered);
        });
});

