/**
 * Create variable name by removing special and white space characters.
 * @param str String 
 * @return Variable name string
 */
function toVarName(str) { return  str.replace(/[|&;$%@"<>()+,. ]/g, "").toLowerCase(); }

/**
 * Append new element
 * @param id ID of the parent element where the new element is appended 
 * @param elmName New element name
 * @param newElmAttrs New element attributes
 * @return New element
 */
function appendNewElementById(id, newElmName, newElmAttrs) {
  var parentElm = document.getElementById(id);
  return appendNewElement(parentElm, newElmName, newElmAttrs);
}

/**
 * Append new element
 * @param parentElm Parent element where the new element is appended
 * @param elmName New element name
 * @param newElmAttrs New element attributes
 * @return New element
 */
function appendNewElement(parentElm, newElmName, newElmAttrs) {
  var newElm = document.createElement(newElmName); 
  for(var newAttrName in newElmAttrs) {
    newElm.setAttribute(newAttrName,newElmAttrs[newAttrName]);   
  }
  parentElm.appendChild(newElm);
  return newElm;
}

/**
 * Append new text node
 * @param parentElm Parent element where the new element is appended
 * @param elmName New element name
 * @param newElmAttrs New element attributes
 */
function appendNewTextNode(parentElm, textContent) {
  var textElm = document.createTextNode(textContent);
  parentElm.appendChild(textElm);
  return textElm;
}

/**
 * Ajax serch request processing
 * After sending the search request, the JSON response is processed and the
 * hierarchical result list is sorted and created.  
 */ 
$(document).ready(function() {

    $('[data-toggle="tooltip"]').tooltip();

    function block_form() {
        $("#loading").show();
        $('input').attr('disabled', 'disabled');
    }
    function unblock_form() {
        $('#loading').hide();
        $('input').removeAttr('disabled');
        $('.errorlist').remove();
    }
    var searchOptions = {
        
        beforeSubmit: function() {
            // return false to cancel submit
            block_form();
            $("#articles-1").show();
        },
        success: function(resp) {
            unblock_form();
            $('.top-left').notify({
                message: { text: 'search request finished' },
                type: 'success'
            }).show(); 
            var jsonRes = (JSON.parse(resp));
            var documents = jsonRes.documents;
            
            var packArtListElm = document.getElementById("packgroupresults");
            while (packArtListElm.firstChild) {
                packArtListElm.removeChild(packArtListElm.firstChild);
            }
            var to = ((jsonRes.numFound-jsonRes.start > jsonRes.rows) ? (jsonRes.start+jsonRes.rows) : jsonRes.numFound-jsonRes.start);
            $('#foundlabel').text(jsonRes.numFound+" documents found (displaying "+(jsonRes.start+1)+" to "+to+")");
            // sort by package
            var grouped = _.chain(documents).sortBy("pack").groupBy("pack").value(); 
            for (var key in grouped) {
                var isSelected = grouped[key][0].is_selected_pack;
                var packArtListItemElm = appendNewElement(packArtListElm, "li", {});
                var packSpanProps = {id:'result-'+toVarName(key)};
                if(isSelected) packSpanProps.style = "background-color: green; color: white";
                var packArtListItemSpanElm = appendNewElement(packArtListItemElm, "span", packSpanProps);
                
                appendNewElement(packArtListItemSpanElm, "i", {class:'glyphicon glyphicon-folder-open'});
                
                appendNewElement(packArtListItemSpanElm, "input", {type:'hidden', id: toVarName(key),  value: key});
                
                appendNewTextNode(packArtListItemSpanElm, " "+key);
                var addBtnProps = {id:'add-'+toVarName(key), class:'glyphicon glyphicon-plus', name: 'add-'+toVarName(key), type: 'submit'};
                if(isSelected) addBtnProps.style = 'display:none'; 
                appendNewElement(packArtListItemElm, "button", addBtnProps);
                var remBtnProps = {id:'rem-'+toVarName(key), class:'glyphicon glyphicon-minus', name: 'rem-'+toVarName(key), type: 'submit' };
                if(!isSelected) remBtnProps.style = 'display:none'; 
                appendNewElement(packArtListItemElm, "button", remBtnProps);
                var packArtListItemUlElm = appendNewElement(packArtListItemElm, "ul", {id:'package-'+toVarName(key)});
                
                // package file item list elements
                for(var k=0;k<grouped[key].length;k++){    
                    var lilyId = grouped[key][k].lily_id;
                    var title = (grouped[key][k].title);
                    var size = (grouped[key][k].size);
                    var contentType = (grouped[key][k].contentType);
                    title = title.substring(key.length+1, title.length);
                    var articleListItemElm = appendNewElement(packArtListItemUlElm, "li", {});
                    var articleListItemSpanElm = appendNewElement(articleListItemElm, "span", {});
                    var linkprops = {id: 'fileItem', name: encodeURIComponent(lilyId), 'data-mime': contentType, 'data-size': size };
                    if(contentType != 'application/xml') linkprops.style = 'color:gray;text-decoration:none'; 
                    var articleListItemAhrefElm = appendNewElement(articleListItemSpanElm, "a", linkprops);
                    appendNewTextNode(articleListItemAhrefElm, title);
                }
            }
        },
        error:  function(resp) {
            unblock_form();
            window.console.log(resp.responseText);
            var errors = JSON.parse(resp.responseText);
            
            $('.top-left').notify({
                message: { text: errors.error },
                type: 'danger'
            }).show(); 
            setTimeout(function() {
            }, 5000);
        }
    };
    
    var options = {
       
        beforeSubmit: function(arr, form, options) {
            var btn = $(document.activeElement).context.id;
            if(btn.startsWith("sendbutton")) {
                searchOptions.beforeSubmit();
                return;
            }
            // append additional post variables
            var cleanIdFormObj = $.grep(arr, function(v) {
                return v.name.startsWith("add") || v.name.startsWith("rem");
            });
            var actionIdArr = cleanIdFormObj[0].name.split('-'); 
            var cleanId = actionIdArr.pop();
            var action = actionIdArr.pop();
            var identifier = $("#"+cleanId).attr('value');
            arr.push({name: "action", value: action });
            arr.push({name: "identifier", value: identifier });
            arr.push({name: "cleanid", value: cleanId });
        },
        success: function(resp) {
            var btn = $(document.activeElement).context.id;
            if(btn.startsWith("sendbutton")) {
                searchOptions.success(resp);
                return;
            }
            var sfx = btn.split('-').pop();
            if(btn.startsWith("add")) {
                $('#result-'+sfx).css("background-color", "green");
                $('#result-'+sfx).css("color", "white");
                $('#add-'+sfx).hide();
                $('#rem-'+sfx).show();
            } else if(btn.startsWith("rem")) {
                $('#result-'+sfx).css("background-color", "transparent");
                $('#result-'+sfx).css("color", "gray");
                $('#add-'+sfx).show();
                $('#rem-'+sfx).hide();
            }
            var action = 'remove';
            if(btn.startsWith('add')) action = "add";
            window.console.log(action + ' package request for package '+ sfx + ' completed.');
            $('.top-left').notify({
                message: { text: 'Package '+action },
                type: 'success'
            }).show(); 
        },
        error: function(resp) {
            var btn = $(document.activeElement).context.id;
            if(btn.startsWith("sendbutton"))
                searchOptions.error(resp);
        }
    };
    $('#select-aip-form').ajaxForm(options);

});

/**
 * Setup expandable tree
 */
$(function () {
    $('.tree li:has(ul)').addClass('parent_li').find(' > span').attr('title', 'Collapse this branch');
    $('.tree li.parent_li > span').on('click', function (e) {
        var children = $(this).parent('li.parent_li').find(' > ul > li');
        if (children.is(":visible")) {
            children.hide('fast');
            $(this).attr('title', 'Expand this branch').find(' > i').addClass('icon-plus-sign').removeClass('icon-minus-sign');
        } else {
            children.show('fast');
            $(this).attr('title', 'Collapse this branch').find(' > i').addClass('icon-minus-sign').removeClass('icon-plus-sign');
        }
        e.stopPropagation();
    });
});

/**
 * Toggle package nodes in the tree
 *
 * Adds an event handler to the package container element so that the 
 * children can be hidden or shown.
 */
$(document).on("click", "[id^=result]", function() {
    var whats = $(this);
    var packageNode = $($(this).parent());
    var folderNode = $($(this).children("i"));
    window.console.log(packageNode.context);
        window.console.log(folderNode);

    if(packageNode.children("ul").is(":visible")) {
        packageNode.children("ul").hide();
        folderNode.removeClass("glyphicon-folder-open").addClass("glyphicon-folder-close");
    } else {
        packageNode.children("ul").show();
        folderNode.removeClass("glyphicon-folder-close").addClass("glyphicon-folder-open");
     }
 });
 
 /**
  * Get file content ajax request (file item links onclick event)
  */
$(document).on("click", "[id^=fileItem]", function() {
show('loadingpreview', true);
    var fileContentPath = "/earkweb/search/filecontent/";
    var selectedItem = ($(this)[0]);
    var identifier = selectedItem.getAttribute("name");
    var encodedIdentifier = encodeURIComponent(identifier);
    window.console.log("File content path: " + fileContentPath+identifier);
    
    var mime = selectedItem.dataset.mime;
    window.console.log("MIME-Type: " + mime);
    var size = parseInt(selectedItem.dataset.size);
    window.console.log("Size: " + size);
    $.ajax({
        url : fileContentPath+identifier,
        success : function(result){                
            bootbox.dialog({
                message: "<div id='XmlPreview' class='xmlview'></div>",
                title: "File preview",
                className: "modal70"
            }); 
            switch (mime) {
                case "application/xml":
                    

                    LoadXMLString('XmlPreview',result);
                    show('loadingpreview', false);
                    break;
                case "image/jpeg":
                    window.console.log("load image");
                    appendNewElement(document.getElementById("XmlPreview"), "img", {src: fileContentPath+identifier });
                    
                    break;
            }
        } 
    });
 }); 
 function show(id, value) {
    document.getElementById(id).style.display = value ? 'block' : 'none';
}
/*
function onReady(callback) {
    var intervalID = window.setInterval(checkReady, 1000);

    function checkReady() {
        if (document.getElementsByTagName('body')[0] !== undefined) {
            window.clearInterval(intervalID);
            callback.call(this);
        }
    }
}



onReady(function () {
    show('page', true);
    show('loading', false);
});
*/
