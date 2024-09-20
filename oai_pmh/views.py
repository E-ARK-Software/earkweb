#!/usr/bin/env python
# coding=UTF-8
"""OAI-PMH module"""
from venv import logger
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from earkweb.models import InformationPackage
from config.configuration import django_service_url
from eatb.utils.datetime import date_format
import xml.etree.ElementTree as ET

from eatb.utils.datetime import DT_ISO_FORMAT, current_timestamp


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

def list_identifiers():
    """
    Handle the OAI-PMH ListIdentifiers request.

    Returns:
    HttpResponse: The ListIdentifiers response containing headers for records.
    """
    root = ET.Element('OAI-PMH', xmlns='http://www.openarchives.org/OAI/2.0/')
    response_date = ET.SubElement(root, 'responseDate')
    response_date.text = current_timestamp(fmt=DT_ISO_FORMAT)

    list_identifiers = ET.SubElement(root, 'ListIdentifiers')
    # pylint: disable-next=no-member
    for ip in InformationPackage.objects.exclude(identifier='').exclude(storage_dir=''):
        header = ET.SubElement(list_identifiers, 'header')
        identifier = ET.SubElement(header, 'identifier')
        identifier.text = ip.identifier
        datestamp = ET.SubElement(header, 'datestamp')
        datestamp.text = date_format(ip.last_change)

    return xml_response(root)

def get_record(request):
    """
    Handle the OAI-PMH GetRecord request.

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
    # pylint: disable-next=no-member
    ips = InformationPackage.objects.filter(identifier=identifier).order_by('-id')
    if len(ips) == 0:
        return error_response('idDoesNotExist', 'The value of the identifier argument is unknown or illegal in this repository.')
    if len(ips) > 1:
        logger.warning("More than one record exists for identifier: %s" % identifier)
    ip = ips[0]

    root = ET.Element('OAI-PMH', xmlns='http://www.openarchives.org/OAI/2.0/')
    response_date = ET.SubElement(root, 'responseDate')
    response_date.text = current_timestamp(fmt=DT_ISO_FORMAT)

    get_record = ET.SubElement(root, 'GetRecord')
    record_elem = ET.SubElement(get_record, 'record')
    header = ET.SubElement(record_elem, 'header')
    identifier_elem = ET.SubElement(header, 'identifier')
    identifier_elem.text = ip.identifier
    datestamp = ET.SubElement(header, 'datestamp')
    datestamp.text = date_format(ip.last_change)

    metadata = ET.SubElement(record_elem, 'metadata')

    record_json = {
        "title": "Example Record 1",
        "creator": "John Doe",
        "subject": "Example Subject",
        "description": "This is an example description for the metadata record.",
        "publisher": "Example Publisher",
        "contributor": "Jane Smith",
        "date": "2024-05-14",
        "type": "Text",
        "format": "application/pdf",
        "identifier": "urn:uuid:53e8aeb7-034b-499b-a965-30df02f06970",
        "source": "Example Source",
        "language": "en",
        "relation": "http://example.org/related-resource",
        "coverage": "World",
        "rights": "Example Rights Statement"
    }

    metadata.append(ET.fromstring("""<oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/">
                    <dc:title xmlns:dc="http://purl.org/dc/elements/1.1/">Example Record 1</dc:title>
                    <dc:creator xmlns:dc="http://purl.org/dc/elements/1.1/">John Doe</dc:creator>
                    <dc:subject xmlns:dc="http://purl.org/dc/elements/1.1/">Example Subject</dc:subject>
                    <dc:description xmlns:dc="http://purl.org/dc/elements/1.1/">This is an example description for the metadata record.</dc:description>
                    <dc:publisher xmlns:dc="http://purl.org/dc/elements/1.1/">Example Publisher</dc:publisher>
                    <dc:contributor xmlns:dc="http://purl.org/dc/elements/1.1/">Jane Smith</dc:contributor>
                    <dc:date xmlns:dc="http://purl.org/dc/elements/1.1/">2024-05-14</dc:date>
                    <dc:type xmlns:dc="http://purl.org/dc/elements/1.1/">Text</dc:type>
                    <dc:format xmlns:dc="http://purl.org/dc/elements/1.1/">application/pdf</dc:format>
                    <dc:identifier xmlns:dc="http://purl.org/dc/elements/1.1/">urn:uuid:53e8aeb7-034b-499b-a965-30df02f06970</dc:identifier>
                    <dc:source xmlns:dc="http://purl.org/dc/elements/1.1/">Example Source</dc:source>
                    <dc:language xmlns:dc="http://purl.org/dc/elements/1.1/">en</dc:language>
                    <dc:relation xmlns:dc="http://purl.org/dc/elements/1.1/">http://example.org/related-resource</dc:relation>
                    <dc:coverage xmlns:dc="http://purl.org/dc/elements/1.1/">World</dc:coverage>
                    <dc:rights xmlns:dc="http://purl.org/dc/elements/1.1/">Example Rights Statement</dc:rights>
                </oai_dc:dc>"""''))

    return xml_response(root)

def error_response(code, message):
    """
    Generate an error response.

    Parameters:
    code (str): The OAI-PMH error code.
    message (str): The error message.

    Returns:
    HttpResponse: The error response.
    """
    root = ET.Element('OAI-PMH', xmlns='http://www.openarchives.org/OAI/2.0/')
    response_date = ET.SubElement(root, 'responseDate')
    response_date.text = current_timestamp(fmt=DT_ISO_FORMAT)
    
    error = ET.SubElement(root, 'error', code=code)
    error.text = message

    return xml_response(root)

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
