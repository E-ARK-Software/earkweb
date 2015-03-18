/**
 * Create variable name by removing special and white space characters.
 * @param str String 
 * @return Variable name string
 */
function toVarName(str) { return  str.replace(/[|&;$%@"<>()+, ]/g, "").toLowerCase(); }

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
    function block_form() {
        $("#loading").show();
        $('input').attr('disabled', 'disabled');
    }
    function unblock_form() {
        $('#loading').hide();
        $('input').removeAttr('disabled');
        $('.errorlist').remove();
    }
    var options = {
        beforeSubmit: function(form, options) {
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
            var jsonResp = JSON.parse(resp);
            var packArtListElm = document.getElementById("packgroupresults");
            while (packArtListElm.firstChild) {
                packArtListElm.removeChild(packArtListElm.firstChild);
            }
            var grouped = _.chain(jsonResp).sortBy("pack").groupBy("pack").value(); 
            for (var key in grouped) {
                var packArtListItemElm = appendNewElement(packArtListElm, "li", {});
                var packArtListItemSpanElm = appendNewElement(packArtListItemElm, "span", {id:'result-'+toVarName(key)});
                //<i class="glyphicon glyphicon-folder-open"></i>
                appendNewElement(packArtListItemSpanElm, "i", {class:'glyphicon glyphicon-folder-open'});
                appendNewTextNode(packArtListItemSpanElm, " "+key);
                appendNewElement(packArtListItemElm, "button", {id:'addaip-'+toVarName(key), 
                    class:'glyphicon glyphicon-plus', name: 'addaip-'+toVarName(key), type: 'submit'});
                appendNewElement(packArtListItemElm, "button", {id:'removeaip-'+toVarName(key), 
                    class:'glyphicon glyphicon-minus', name: 'removeaip-'+toVarName(key), type: 'submit', style: 'display:none' });
                var packArtListItemUlElm = appendNewElement(packArtListItemElm, "ul", {id:'package-'+toVarName(key)});
                for(var k=0;k<grouped[key].length;k++){                    
                    var lilyId = grouped[key][k].lily_id;
                    var title = grouped[key][k].title;
                    var articleListItemElm = appendNewElement(packArtListItemUlElm, "li", {});
                    var articleListItemSpanElm = appendNewElement(articleListItemElm, "span", {});
                    var articleListItemAhrefElm = appendNewElement(articleListItemSpanElm, 
                        "a", {href: 'http://127.0.0.1:8000/search/article/'+lilyId });
                    appendNewTextNode(articleListItemAhrefElm, title);
                }
            }
        },
        error:  function(resp) {
            unblock_form();
            $("#form_ajax_error").show();
            window.console.log(resp.responseText)
            var errors = JSON.parse(resp.responseText);
            
            $('.top-left').notify({
                message: { text: errors.error },
                type: 'danger'
            }).show(); 
            setTimeout(function() {
                $("#form_ajax_error").hide();
            }, 5000);
        }
    };
    $('#ajaxform').ajaxForm(options);
    
});

/**
 * Ajax-form action to add or remove a package
 */
$(document).ready(function() {
    var options = {
        success: function(resp) {
            var btn = $(document.activeElement).context.id; 
            window.console.log(btn);
            var sfx = btn.split('-').pop();
            if(btn.startsWith("addaip")) {
                $('#result-'+sfx).css("background-color", "green");
                $('#result-'+sfx).css("color", "white");
                $('#addaip-'+sfx).hide();
                $('#removeaip-'+sfx).show();
            } else  if(btn.startsWith("removeaip")) {
                $('#result-'+sfx).css("background-color", "transparent");
                $('#result-'+sfx).css("color", "black");
                $('#addaip-'+sfx).show();
                $('#removeaip-'+sfx).hide();
            }
            var what = 'removed';
            if(btn.startsWith('addaip')) what = "added";
            window.console.log('Package '+what);
            $('.top-left').notify({
                message: { text: 'Package '+what },
                type: 'success'
            }).show(); 
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
 
