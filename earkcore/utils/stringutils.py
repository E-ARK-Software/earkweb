def lstrip_substring(str, substr):
    """
    Remove substring from string at the beginning
    @type       str: string
    @param      str: String
    @type       substr: string
    @param      substr: Sub-string
    @rtype:     bool
    @return:    Result string
    """
    if str.startswith(substr):
        len_substr = len(substr)
        return str[len_substr:]
    else:
        return str

def safe_path_string(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to underscore.
    """
    import unicodedata
    import re
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s-]', '', value).strip().lower())
    return re.sub('[-\s]+', '_', value)