from django import template
register = template.Library()
 
@register.filter(name='access')
def access(value, arg):
    if arg is None:
        return None
    else:
        try:
            arg = int(arg)
        except:
            return None
        else:
            try:
                key_value = value[arg]
            except KeyError:
                return '#KeyError#'
            else:
                return key_value