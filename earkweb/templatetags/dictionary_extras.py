from django import template
from eatb.utils.fileutils import from_safe_filename, to_safe_filename
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
                return 'Error'
            else:
                return key_value


@register.filter(name='decode_id')
def decode_id(encoded_identifier):
    """
    Decodes the encoded identifier.

    Args:
        encoded_identifier (str): The encoded identifier to decode.

    Returns:
        str: The decoded identifier.
    """
    return from_safe_filename(encoded_identifier)


@register.filter(name='encode_id')
def encode_id(identifier):
    """
    Encodes the identifier.

    Args:
        identifier (str): The identifier to encode.

    Returns:
        str: The encoded identifier.
    """
    encoded_id = to_safe_filename(identifier)
    return encoded_id
