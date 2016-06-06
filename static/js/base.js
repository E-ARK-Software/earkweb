/**
 * startswith and endsWith string methods
 */
if (typeof String.prototype.startsWith != 'function') {
  // see below for better implementation!
  String.prototype.startsWith = function (str){
    return this.indexOf(str) === 0;
  };
  String.prototype.endsWith = function(suffix) {
    return this.indexOf(suffix, this.length - suffix.length) !== -1;
  };
}


/**
 * JQuery extension to provide quick hide/show/remove stylesheet functions
 * Use:
 *     $('#idelement').visible
 *     $('#idelement').invisible
 */
(function($) {

    $.fn.invisible = function() {
        return this.each(function() {
            $(this).css("visibility", "hidden");
        });
    };
    $.fn.nodisplay = function() {
        return this.each(function() {
            $(this).css("display", "none");
        });
    };
    $.fn.visible = function() {
        return this.each(function() {
            $(this).css("visibility", "visible");
        });
    };
    $.fn.togglevisible = function() {
        if( $(this).css("display") == 'none' ) {
            $(this).css("display", "inline");
        } else {
            $(this).css("display", "none");
        }

    };


}(jQuery));


/**
 * Show element
 */
function show(id, value) {
    document.getElementById(id).style.display = value ? 'block' : 'none';
}


/**
 * Create id based on name by removing special and white space characters.
 * @param str String
 * @return Variable name string
 */
function name_to_id(str) { return  str.replace(/[|&;$%@"<>()+,./\- ]/g, "").toLowerCase(); }

