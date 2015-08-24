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
