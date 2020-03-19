import requests


def service_available(url):
    try:
        response = requests.get(url, verify=False)
        if response.status_code != 200:
            return False
    except Exception:
        return False
    return True


def build_url(protocol, host, port, app_label=None):
    url = "%s://%s%s" % (protocol, host, "" if port in [80, 443] else ":%s" % port)
    if app_label:
        url = "%s/%s" % (url, app_label)
    return url


def log_request_info(request, logger):
    if "REMOTE_ADDR" in request.META:
        logger.debug("Remote address: %s" % request.META["REMOTE_ADDR"])
    if "REQUEST_METHOD" in request.META:
        logger.debug("Request method: %s" % request.META["REQUEST_METHOD"])
    if "PATH_INFO" in request.META:
        logger.debug("Path info: %s" % request.META["PATH_INFO"])
    if "HTTP_USER_AGENT" in request.META:
        logger.debug("User agent: %s" % request.META["HTTP_USER_AGENT"])
    if "HTTP_REFERER" in request.META:
        logger.debug("HTTP Referer: %s" % request.META["HTTP_REFERER"])