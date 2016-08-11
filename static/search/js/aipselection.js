/**
 * Update aip selection dropdown list
 */
function updateAipSelectionDropdown(filterword) {
    $.ajax({
        url: "/earkweb/search/aipselectiondropdown",
        type: "POST",
        data: "filterword=" + filterword,
    }).success(function(aipselectiondropdownlist){
    window.console.log(aipselectiondropdownlist);
        $('#aipsel-dropdown-menu').html(aipselectiondropdownlist);
        $('#aipsel-dropdown-menu').togglevisible();
    });
}
$( document ).ready(function() {
    $( "#aipidfilter" ).keyup(function() {
       updateAipSelectionDropdown($('#aipidfilter').val());
       window.console.log($('#aipidfilter').val());
       checkValidParentIdentifier();
    });
    $( "#aipidfilter" ).focusin(function() {
       updateAipSelectionDropdown($('#aipidfilter').val());
       window.console.log($('#aipidfilter').val());
    });
});

function selectAip(aip_identifier) {
    $('#aipidfilter').val(aip_identifier);
    $('#aipsel-dropdown-menu').togglevisible();
    checkValidParentIdentifier();
}

function addaip(identifier, dip_name) {
    toggle_select_package(identifier, dip_name, 'add')
}

function removeaip(identifier, dip_name) {
    toggle_select_package(identifier, dip_name, 'remove')
}

/**
 * Add representation (ajax POST request)
 */
function toggle_select_package(identifier, dip, action) {
    $('#reperr').html("");
    window.console.log("identifier: "+identifier);
    window.console.log("dip:"+dip);
    window.console.log("action:"+action);

    $.ajax({
        url: "/earkweb/search/toggle_select_package",
        type: "POST",
        data: "identifier="+identifier+"&dip="+dip+"&action="+action,
    }).success(function(){
        $.ajax({
            url: "/earkweb/search/selectedaipstable",
            type: "POST",
            data: "dip_name=" + dip_name,
        }).success(function(selaipstab){
            window.console.log(selaipstab);
            $('#selaipstab').html(selaipstab);
        });
    });

}

 /**
 * Check if a package with the identifier exists.
 */
function checkValidParentIdentifier() {
    var idelm = $( "#aipidfilter" );
    var check_identifier_url = "/earkweb/earkcore/check_identifier_exists/" + idelm.val()
    if (idelm.val().length > 5) {
        $.ajax({
            url: check_identifier_url,
            type: "GET",
        }).success(function(identifier_exists){
            if(identifier_exists == 'true') {
                $('#aipidfilter').css({color:'green'});
                $('#addaipbutton').removeAttr("disabled");
            } else {
                $('#aipidfilter').css({color:'red'});
                $('#addaipbutton').attr("disabled","disabled");
            }
        });
    }
}