#!/usr/bin/env python
# coding=UTF-8
"""OAI-PMH module"""
from venv import logger
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from earkweb.models import InformationPackage
from config.configuration import django_service_url
from config.configuration import solr_core_url
from eatb.utils.datetime import date_format
import xml.etree.ElementTree as ET

from eatb.utils.datetime import DT_ISO_FORMAT, current_timestamp

import pysolr
from django.utils.safestring import mark_safe
import xml.etree.ElementTree as ET
import logging

# Initialisiere das pysolr-Objekt (passe die Solr-URL an)
solr = pysolr.Solr(solr_core_url, always_commit=True)

logger = logging.getLogger(__name__)


ET.register_namespace('oai_dc', 'http://www.openarchives.org/OAI/2.0/oai_dc/')
ET.register_namespace('dc', 'http://purl.org/dc/elements/1.1/')


# Dummy data for the repository
RECORDS = {
    'oai:example.org:1': {
        'identifier': 'oai:example.org:1',
        'datestamp': '2023-01-01',
        'metadata': '<oai_dc:title xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/">Example Record 1</oai_dc:title>',
    },
    'oai:example.org:2': {
        'identifier': 'oai:example.org:2',
        'datestamp': '2023-02-01',
        'metadata': '<oai_dc:title xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/">Example Record 2</oai_dc:title>',
    },
}

def oai_pmh(request):
    """
    Main entry point for OAI-PMH requests.

    Parameters:
    request (HttpRequest): The incoming HTTP request.

    Returns:
    HttpResponse: The response based on the OAI-PMH verb.
    """
    verb = request.GET.get('verb')

    if verb == 'Identify':
        return identify()
    elif verb == 'ListMetadataFormats':
        return list_metadata_formats(request)
    elif verb == 'ListIdentifiers':
        return list_identifiers()
    elif verb == 'GetRecord':
        return get_record(request)
    else:
        return bad_verb()

def identify():
    """
    Handle the OAI-PMH Identify request.

    Returns:
    HttpResponse: The Identify response containing repository information.
    """
    root = ET.Element('OAI-PMH', xmlns='http://www.openarchives.org/OAI/2.0/')
    response_date = ET.SubElement(root, 'responseDate')
    response_date.text = current_timestamp(fmt=DT_ISO_FORMAT)

    identify = ET.SubElement(root, 'Identify')
    repository_name = ET.SubElement(identify, 'repositoryName')
    repository_name.text = 'Example Repository'
    base_url = ET.SubElement(identify, 'baseURL')
    base_url.text = "%s/oai" % django_service_url
    protocol_version = ET.SubElement(identify, 'protocolVersion')
    protocol_version.text = '2.0'
    admin_email = ET.SubElement(identify, 'adminEmail')
    admin_email.text = 'support@e-ark-foundation.eu'
    earliest_datestamp = ET.SubElement(identify, 'earliestDatestamp')
    earliest_datestamp.text = '2023-01-01'
    deleted_record = ET.SubElement(identify, 'deletedRecord')
    deleted_record.text = 'no'
    granularity = ET.SubElement(identify, 'granularity')
    granularity.text = 'YYYY-MM-DD'

    return xml_response(root)

def list_metadata_formats(request):
    """
    Handle the OAI-PMH ListMetadataFormats request.

    Returns:
    HttpResponse: The ListMetadataFormats response containing supported metadata formats.
    """
    identifier = request.GET.get('identifier')
    if identifier and identifier not in RECORDS:
        return error_response('idDoesNotExist', 'The value of the identifier argument is unknown or illegal in this repository.')

    root = ET.Element('OAI-PMH', xmlns='http://www.openarchives.org/OAI/2.0/')
    response_date = ET.SubElement(root, 'responseDate')
    response_date.text = current_timestamp(fmt=DT_ISO_FORMAT)

    list_metadata_formats = ET.SubElement(root, 'ListMetadataFormats')
    metadata_format = ET.SubElement(list_metadata_formats, 'metadataFormat')
    metadata_prefix = ET.SubElement(metadata_format, 'metadataPrefix')
    metadata_prefix.text = 'oai_dc'
    schema = ET.SubElement(metadata_format, 'schema')
    schema.text = 'http://www.openarchives.org/OAI/2.0/oai_dc.xsd'
    metadata_namespace = ET.SubElement(metadata_format, 'metadataNamespace')
    metadata_namespace.text = 'http://www.openarchives.org/OAI/2.0/oai_dc/'

    return xml_response(root)


def list_identifiers(request):
    """
    Handle the OAI-PMH ListIdentifiers request with pagination support using resumption tokens.

    Parameters:
    request (HttpRequest): The incoming HTTP request.

    Returns:
    HttpResponse: The ListIdentifiers response containing headers for records with a resumption token for pagination.
    """
    root = ET.Element('OAI-PMH', xmlns='http://www.openarchives.org/OAI/2.0/')
    response_date = ET.SubElement(root, 'responseDate')
    response_date.text = current_timestamp(fmt=DT_ISO_FORMAT)

    list_identifiers = ET.SubElement(root, 'ListIdentifiers')

    # Retrieve the resumption token from the request, if present
    resumption_token = request.GET.get('resumptionToken')
    page_size = 10  # Define how many records to return per page
    start_index = int(resumption_token) if resumption_token else 0

    # Query InformationPackage objects for identifiers
    # pylint: disable-next=no-member
    packages = InformationPackage.objects.exclude(identifier='').exclude(storage_dir='')[start_index:start_index + page_size]

    for ip in packages:
        header = ET.SubElement(list_identifiers, 'header')
        identifier = ET.SubElement(header, 'identifier')
        identifier.text = ip.identifier
        datestamp = ET.SubElement(header, 'datestamp')
        datestamp.text = date_format(ip.last_change)

    # If there are more records to fetch, create a resumption token
    next_index = start_index + page_size
    total_records = InformationPackage.objects.exclude(identifier='').exclude(storage_dir='').count()
    if next_index < total_records:
        resumption_token_elem = ET.SubElement(list_identifiers, 'resumptionToken')
        resumption_token_elem.text = str(next_index)
        resumption_token_elem.set('cursor', str(start_index))
        resumption_token_elem.set('completeListSize', str(total_records))
    else:
        # If there are no more records, resumptionToken should be empty
        resumption_token_elem = ET.SubElement(list_identifiers, 'resumptionToken')
        resumption_token_elem.text = ''

    return xml_response(root)


def get_record(request):
    """
    Handle the OAI-PMH GetRecord request using Solr.

    Parameters:
    request (HttpRequest): The incoming HTTP request.

    Returns:
    HttpResponse: The GetRecord response containing the requested record.
    """
    identifier = request.GET.get('identifier')
    metadata_prefix = request.GET.get('metadataPrefix')

    if not identifier or not metadata_prefix:
        return error_response('badArgument', 'The request is missing required arguments.')

    if metadata_prefix != 'oai_dc':
        return error_response('cannotDisseminateFormat', 'The metadata format identified by the value given for the metadataPrefix argument is not supported by the item or by the repository.')

    # Solr query to find the document based on identifier
    solr_query = f'package:"{identifier}"'
    results = solr.search(solr_query)

    # Check if any documents were found
    if not results.docs:
        return error_response('idDoesNotExist', 'The value of the identifier argument is unknown or illegal in this repository.')

    # Use the first document as the main record
    doc = results.docs[0]

    # OAI-PMH XML structure
    root = ET.Element('OAI-PMH', xmlns='http://www.openarchives.org/OAI/2.0/')
    response_date = ET.SubElement(root, 'responseDate')
    response_date.text = current_timestamp(fmt=DT_ISO_FORMAT)

    get_record = ET.SubElement(root, 'GetRecord')
    record_elem = ET.SubElement(get_record, 'record')
    header = ET.SubElement(record_elem, 'header')
    identifier_elem = ET.SubElement(header, 'identifier')
    identifier_elem.text = doc.get('id', 'Unknown ID')
    datestamp = ET.SubElement(header, 'datestamp')
    datestamp.text = doc.get('indexdate', 'Unknown Date')

    # Metadata section
    metadata = ET.SubElement(record_elem, 'metadata')
    oai_dc = ET.SubElement(metadata, 'oai_dc:dc', xmlns="http://www.openarchives.org/OAI/2.0/oai_dc/")
    ns = "http://purl.org/dc/elements/1.1/"

    # Title or file description (depending on availability)
    title_text = doc.get('filedescription', doc.get('title', ['No title'])[0])
    title = ET.SubElement(oai_dc, f'{{{ns}}}title')
    title.text = title_text

    # Populate other Dublin Core fields
    fields = {
        'creator': 'publisher',
        'date': 'archivedate',
        'identifier': 'uid',
        'format': 'content_type',
        'description': 'description',
    }

    for dc_field, solr_field in fields.items():
        value = doc.get(solr_field, [''])[0]
        if value:
            elem = ET.SubElement(oai_dc, f'{{{ns}}}{dc_field}')
            elem.text = value

    # Optional additional fields
    publisher = ET.SubElement(oai_dc, f'{{{ns}}}publisher')
    publisher.text = doc.get('publisher', ['Unknown Publisher'])[0]
    
    # Prepare response
    xml_data = ET.tostring(root, encoding='utf-8')
    return HttpResponse(xml_data, content_type='text/xml')

def error_response(code, message):
    """
    Generate an OAI-PMH error response.

    Parameters:
    code (str): The OAI-PMH error code.
    message (str): The error message.

    Returns:
    HttpResponse: The error response as XML.
    """
    root = ET.Element('OAI-PMH', xmlns='http://www.openarchives.org/OAI/2.0/')
    error_elem = ET.SubElement(root, 'error', code=code)
    error_elem.text = message
    return HttpResponse(ET.tostring(root, encoding='utf-8'), content_type='text/xml')

def current_timestamp(fmt):
    # Implement timestamp formatting here (or use Django's utilities)
    pass

def bad_verb():
    """
    Handle invalid or missing OAI-PMH verbs.

    Returns:
    HttpResponse: The error response for an invalid verb.
    """
    return error_response('badVerb', 'The verb argument provided is illegal.')

def xml_response(root):
    """
    Generate an HttpResponse with XML content.

    Parameters:
    root (Element): The root element of the XML tree.

    Returns:
    HttpResponse: The response with XML content.
    """
    xml_str = ET.tostring(root, encoding='utf-8')
    return HttpResponse(xml_str, content_type='text/xml')
