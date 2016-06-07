/**
 * Preview file
 */
function previewfile(node) {
    if(node.data) {
        ip_work_dir_sub_path = node.data.path
        mimetype = node.data.mimetype
        show('loadingpreview', true);
        $.ajax({
          url: "/earkweb/earkcore/read_ipfc/" + ip_work_dir_sub_path,
          context: document.body
        }).success(function(data) {
            bootbox.dialog({
                message: "<div id='XmlPreview' class='xmlview'></div>",
                title: "File preview (" + mimetype + ")",
                className: "modal70"
            });
            switch (mimetype) {
                case 'application/xml':
                case 'text/xml':
                    LoadXMLString('XmlPreview',data);
                    break;
                case 'image/jpeg':
                     $('#XmlPreview').html("<p>JPEG viewer is not  implemented</p>")
                    break;
                case 'image/tiff':
                     $('#XmlPreview').html('<p><img src="" id="displayimage" style="max-width: 1000px;" /></p>')
                     document.getElementById("displayimage").src = data;
                    break;
                case 'image/png':
                     $('#XmlPreview').html('<p><img src="" id="displayimage" style="max-width: 1000px;" /></p>')
                     document.getElementById("displayimage").src = data;
                    break;
                case 'image/gif':
                     $('#XmlPreview').html('<p><img src="" id="displayimage" style="max-width: 1000px;" /></p>')
                     document.getElementById("displayimage").src = data;
                    break;
                case 'application/pdf':
//                             $('#XmlPreview').html('<p><img src="" id="displayimage" style="max-width: 1000px;" /></p>')
//                             document.getElementById("displayimage").src = data;
                     $('#XmlPreview').html(data)
                    break;
                case 'text/plain':
                     $('#XmlPreview').html("<pre>"+data+"</pre>")
                    break;
                default:
                    $('#XmlPreview').html("<pre>"+mimetype+"</pre>")
                    break;
            }
            show('loadingpreview', false);
        }).error(function(err, message, status_text) {
            bootbox.dialog({
              message: err.responseText,
              title: "Error "+err.status+ "(" + status_text + ")",
              buttons: {
                success: {
                  label: "OK!",
                  className: "btn-default"
                }
              }
            });
        });
    }
 }

function isEAD(name) {
    return !!(name.toLowerCase().match(/ead[A-Za-z0-9-_]{0,20}.xml/));
}

function isStateXML(name) {
    return !!(name.toLowerCase().match(/state.xml/));
}

function previewSupported(name) {
    return !!(name.toLowerCase().match(/(.pdf$|.png$|.xml$|.png$|.log$|.xsd$)/));
}

/**
 * Context menu
 */
function customMenu(node) {

    var items = {
        viewItem: {
            label: "View",
            action: function () { previewfile(node); }
        },
        editItem: {
            label: "Edit",
            action: function () { window.location.href = '/earkweb/earkcore/xmleditor/'+ node.data.path +'/'; }
        }
    };
    var n = $(node)[0];
    if (!isEAD(n.text) && !isStateXML(n.text)) { delete items.editItem; }
    if (!previewSupported(n.text)) { delete items.viewItem; }
    return items;
}


/**
 * Populate tree using json representation of the directory hierarchy
 * (variable 'uuid' is provided as global variable)
 */
(function(){
    $.ajax({
        url: "/earkweb/earkcore/get_directory_json",
        type: "POST",
        data: "uuid="+uuid,
    }).success(function(dir_as_json){
        $('#directorytree')
        .on('open_node.jstree', function (e, data) {
            $('#directorytree').jstree(true).set_icon(data.node.id, 'glyphicon glyphicon-folder-open');
         }).on('close_node.jstree', function (e, data) {
            $('#directorytree').jstree(true).set_icon(data.node.id, 'glyphicon glyphicon-folder-close');
         }).on('move_node.jstree', function (e, data) {
            origin_path = data.node.data.path;
            target_path = $('#directorytree').jstree().get_node(data.parent).data.path;
            console.log("Original path: "+origin_path);
            console.log("Target path: "+target_path);
         }).on('dblclick.jstree', function (e) {
            var node = $('#directorytree').jstree(true).get_node(e.target);
            if(previewSupported(node.data.path)) {
                previewfile(node);
            } else {
                alert("Preview of this file type is not supported!");
            }
         }).on('loaded.jstree', function() {
            $('#directorytree').jstree('open_all');
         }).jstree({ 'core' : dir_as_json, "plugins" : [
            //"checkbox",
            "contextmenu",
            "dnd",
            //"massload",
            //"search",
            //"sort",
            //"state",
            //"types",
            //"unique",
            //"wholerow",
            "changed",
            //"conditionalselect"
        ], contextmenu: {items: customMenu} });
        $(document).on('dnd_start.vakata', function (e, data) {
            console.log(data);
        });
    });
})();
