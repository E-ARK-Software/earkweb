/**
 * Preview file
 */
function previewfile(node) {
    if(node.data) {
        var ip_work_dir_sub_path = node.data.path;
        if(typeof encoded_identifier !== 'undefined' && encoded_identifier != '') {
            ip_work_dir_sub_path = ip_work_dir_sub_path.replace("../", "");
            ip_work_dir_sub_path = encoded_identifier + "/" + ip_work_dir_sub_path;
        }
        var mimetype = node.data.mimetype;
    
        var url = "/earkweb/read-file/" + ip_work_dir_sub_path + "/";
        window.open(url,'file view','directories=no,titlebar=no,toolbar=no,location=no,status=no,menubar=no,scrollbars=yes,resizable=yes,width=1000,height=800');
    }
 }

function isEAD(name) {
    return !!(name.toLowerCase().match(/ead[A-Za-z0-9-_]{0,20}.xml/));
}

function isStateFile(name) {
    return !!(name.toLowerCase().match(/state.json/));
}

function previewSupported(name) {
    return !!(name.toLowerCase().match(/(.pdf$|.png$|.xml$|.png$|.log$|.xsd|.txt$|.gif$|.tiff$|.tar|.odt$)/));
}
$(document).ready(function(){

    function getCookie(c_name) {
        if(document.cookie.length > 0) {
            c_start = document.cookie.indexOf(c_name + "=");
            if(c_start != -1) {
                c_start = c_start + c_name.length + 1;
                c_end = document.cookie.indexOf(";", c_start);
                if(c_end == -1) c_end = document.cookie.length;
                return unescape(document.cookie.substring(c_start,c_end));
            }
        }
        return "";
    }

    $(function () {
        $.ajaxSetup({
            headers: {
                "X-CSRFToken": getCookie("csrftoken")
            }
        });
    });

});

/**
 * Context menu
 */
function customMenu(node) {

    var items = {
        viewItem: {
            label: "View",
            action: function () { previewfile(node); }
        },
        deleteItem: {
            label: "Delete",
            action: function () {
                // console.log("node.data.path: "+node.data.path);
                //$('#directorytree').delete_node(node);
                $.ajax({
                    url: '/earkweb/api/ips/'+uid+'/file-resource/'+node.data.path.replace(uid+'/','')+'/',
                    type: 'DELETE',
                    success: function() { console.log("success") },
                    error: function() { console.log("error") },
                });

                $('#directorytree').jstree(true).delete_node(node);

            }
        }
    };
    var n = $(node)[0];
    if (!previewSupported(n.text)) { delete items.viewItem; }
    return items;
}

var loadThis = $.parseJSON(dirasjson);

/**
 * Populate tree using json representation of the directory hierarchy
 * (variable 'dirasjson' is provided as global variable)
 */
(function(){
    $('#directorytree')
        .on('open_node.jstree', function (e, data) {

            $('#directorytree').jstree(true).set_icon(data.node.id, 'fas fa-folder-open');
            // console.log("data.node.id: "+data.node.id)
            // console.log(data.node);
         }).on('close_node.jstree', function (e, data) {
            $('#directorytree').jstree(true).set_icon(data.node.id, 'fas fa-folder');
         }).on('move_node.jstree', function (e, data) {
            origin_path = data.node.data.path;
            target_path = $('#directorytree').jstree().get_node(data.parent).data.path;
            // console.log("Original path: "+origin_path);
            // console.log("Target path: "+target_path);
         }).on('dblclick.jstree', function (e) {
            var node = $('#directorytree').jstree(true).get_node(e.target);
            // preview/download enabled for all types
            if(true || previewSupported(node.data.path)) {
                previewfile(node);
            } else {
                alert("View/download of this file type is not allowed!");
            }
         }).on('loaded.jstree', function() {
            $('#directorytree').jstree('open_all');
         }).jstree({ 'core' : loadThis, "plugins" : [
            //"checkbox",
            "contextmenu",
            "dnd",
            //"massload",
            //"search",
            //"sort",
            //"state",
            "types",
            //"unique",
            //"wholerow",
            "changed",
            //"conditionalselect"
        ], contextmenu: {items: customMenu} }).bind('loaded.jstree',function(e,data){
            $('.jstree-leaf').each(function(){
                var id   = ($(this).attr('id').split("_"))[0];
                var text = $(this).children('a').text();
                // console.log("id + text: "+ id + " - " + text + "\n");
                var icon = "fas fa-file";
                if(text.endsWith("json"))
                    icon = "fas fa-file-code"
                else if(text.endsWith("doc") || text.endsWith("docx"))
                    icon = "fas fa-file-word";
                else if(text.endsWith("pdf"))
                    icon = "fas fa-file-pdf";
                else if(text.endsWith("csv"))
                    icon = "fas fa-file-csv";
                else if(text.endsWith("log"))
                    icon = "fas fa-file-alt";
                else if(text.endsWith("xml") || text.endsWith("xsd"))
                    icon = "fas fa-file-code";
                else if(text.endsWith("tar") || text.endsWith("tar.gz") || text.endsWith("zip"))
                    icon = "fas fa-file-archive";
                else
                    icon = "fas fa-file";

                $('#directorytree').jstree(true).set_icon($(this).attr('id'), icon);
            });
        });
        $(document).on('dnd_start.vakata', function (e, data) {
            // console.log("data: "+data);
        });
        //$("#directorytree").jstree(true).get_node("j1_2").set_icon(, "/earkwebstatic/earkweb/fontawesome-5.12.1/svgs/regular/angry.svg");
        //console.log($("#directorytree").jstree(true))

})();
