import uuid

from django.contrib.auth.models import User
from django.http import HttpResponse
from django.template import loader
from eatb.utils import randomutils
from rest_framework.authtoken.models import Token

from earkweb.models import InternalIdentifier

from django.utils.translation import gettext_lazy as _

import logging

from util.custom_exceptions import ResourceNotAvailable

logger = logging.getLogger(__name__)


def get_user_api_token(user_pk):
    u = User.objects.get(username=user_pk)
    token = Token.objects.get(user=u)
    return token.key


def get_unused_identifier(user_id, get_blockchain_id=False):
    if get_blockchain_id:
        id_queryset = InternalIdentifier.objects.filter(used=False, is_blockchain_id=get_blockchain_id, user=user_id)[:1]
        if len(id_queryset) == 0:
            raise ResourceNotAvailable(_("No unused Blockchain identifier available"))
        identifier = id_queryset[0]
        identifier.used = True
        identifier.save()
        new_id = "%s" % identifier.identifier
    else:
        new_id = str(uuid.uuid4())
    return new_id


def error_resp(request, error_message, header=_("An error occurred"), redirect_url=None, redirect_msg=None):
    logger.error(error_message)
    template = loader.get_template("earkweb/error.html")
    context = {"header": header, "message": error_message,
               "redirectUrl": redirect_url, "redirectMsg": redirect_msg}
    return HttpResponse(template.render(context=context, request=request))


def check_required_params(input, required_params):
    missing_params = []
    for param in required_params:
        if param not in input:
            missing_params.append(param)
    if len(missing_params) > 0:
        raise RuntimeError("Missing parameters: %s" % ", ".join(missing_params))
