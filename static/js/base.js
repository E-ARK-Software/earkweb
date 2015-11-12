/**
 * Provides startswith string method
 */
if (typeof String.prototype.startsWith != 'function') {
  // see below for better implementation!
  String.prototype.startsWith = function (str){
    return this.indexOf(str) === 0;
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
    $.fn.isvisible = function() {
        window.console.log(($(this).css("display") != "none"))
        return ($(this).css("display") != "none");
    };



}(jQuery));

