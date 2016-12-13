$( document ).ready(function() {

    /**
     * Check valid parent identifier. If a package with the parent identifier exists, it is
     * stored in the database (using callback function successCallback).
     */
    function checkValidParentIdentifier(successCallback) {
        var idelm = $( "#parent" );
        var check_identifier_url = "/earkweb/earkcore/check_identifier_exists/" + idelm.val()
        if (idelm.val().length < 3) {
            $('#parent').css({color:'red'});

            $('#proceedbtn').attr("disabled","disabled");
            return false;
        } else {
            var regex = new RegExp('^[a-zA-Z0-9_\.\:\-]*$');
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
     * Callback function used above to store the parent identifier value.
     * (ajax POST request)
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


    /**
     * Keup event to check parent identifier
     */
    $( "#parent" ).keyup(function() {
       checkValidParentIdentifier(validIdentifierEntered);
    });


    /**
     * Disable data upload areas if no representation exists.
     */
    if(rep == '') {
        $('#content-folder').invisible();
        $('#documentation-folder').invisible();
        $('#schemas-folder').invisible();
        $('#metadata-folder').invisible();
        $('#reprnote').notify({
            message: { text: 'Please add a representation first to enable the data upload areas.' },
            type: 'info'
        }).show();
    }


    /**
     * Delete confirmation modal dialog.
     */
    $('#confirm-delete').on('show.bs.modal', function(e) {
        $(this).find('.btn-ok').attr('href', $(e.relatedTarget).data('href'));
    });
});


/**
 * Change representation (redirect to representation url)
 */
function changeRep(rep, sip_detail_url) {
    var repr_value = rep;
    tourl = sip_detail_url+repr_value+"/"
    window.location.href = tourl
}


/**
 * Add representation (ajax POST request)
 */
function addRep(rep, url) {
    var rep_value = $('#repval').val();
    var re = new RegExp("^[A-Za-z]{1,1}[A-Za-z0-9_-]{3,200}$");
    if(re.test(rep_value)) {
        $.ajax({
            url: url,
            type: "POST",
            data: "representation="+$('#repval').val(),
        }).success(function(json_response){
            if(json_response.success == true)
                changeRep(json_response.representation, sip_detail_url);
            else
                $('#reperr').html(json_response.message);
        });
    } else
        $('#reperr').html("Only alphanumerical characters with minimum length 4 and maximum length 200 allowed!");
}

