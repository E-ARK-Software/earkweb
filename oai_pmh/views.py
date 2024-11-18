#!/usr/bin/env python
# coding=UTF-8
"""OAI-PMH module"""
from venv import logger
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from earkweb.models import InformationPackage
from config.configuration import django_service_url
from config.configuration import solr_core_url
from eatb.utils.datetime import date_format, current_timestamp
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
        return list_identifiers(request)
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

    # Registriere die benötigten Namespaces
    ET.register_namespace('oai_dc', 'http://www.openarchives.org/OAI/2.0/oai_dc/')
    ET.register_namespace('dc', 'http://purl.org/dc/elements/1.1/')

    # OAI-PMH XML-Struktur
    root = ET.Element('OAI-PMH', xmlns='http://www.openarchives.org/OAI/2.0/')
    response_date = ET.SubElement(root, 'responseDate')
    response_date.text = current_timestamp(fmt=DT_ISO_FORMAT)

    # Request-Element hinzufügen
    request_elem = ET.SubElement(root, 'request', verb='GetRecord', identifier=identifier, metadataPrefix=metadata_prefix)
    request_elem.text = request.build_absolute_uri()

    get_record = ET.SubElement(root, 'GetRecord')
    record_elem = ET.SubElement(get_record, 'record')
    header = ET.SubElement(record_elem, 'header')
    identifier_elem = ET.SubElement(header, 'identifier')
    identifier_elem.text = str(doc.get('id', 'Unknown ID'))
    datestamp = ET.SubElement(header, 'datestamp')
    datestamp.text = str(doc.get('indexdate', 'Unknown Date'))

    # Metadata-Sektion
    metadata = ET.SubElement(record_elem, 'metadata')
    # Verwende ET.QName für korrektes Namespacing
    oai_dc = ET.SubElement(metadata, ET.QName('http://www.openarchives.org/OAI/2.0/oai_dc/', 'dc'))

    dc_namespace = "http://purl.org/dc/elements/1.1/"

    # Titel oder Dateibeschreibung (je nach Verfügbarkeit)
    title_field = doc.get('filedescription', doc.get('title', ['No title']))
    title_text = title_field[0] if isinstance(title_field, list) else str(title_field)
    title = ET.SubElement(oai_dc, ET.QName(dc_namespace, 'title'))
    title.text = title_text

    # Weitere Dublin Core Felder
    fields = {
        'creator': 'publisher',
        'date': 'archivedate',
        'identifier': 'uid',
        'format': 'content_type',
        'description': 'description',
    }

    for dc_field, solr_field in fields.items():
        value = doc.get(solr_field, [''])
        value = value[0] if isinstance(value, list) else str(value)
        if value:
            elem = ET.SubElement(oai_dc, ET.QName(dc_namespace, dc_field))
            elem.text = value

    # Optionales zusätzliches Feld
    publisher_field = doc.get('publisher', ['Unknown Publisher'])
    publisher_text = publisher_field[0] if isinstance(publisher_field, list) else str(publisher_field)
    publisher = ET.SubElement(oai_dc, ET.QName(dc_namespace, 'publisher'))
    publisher.text = publisher_text

    # XML-Daten serialisieren
    try:
        xml_data = ET.tostring(root, encoding='utf-8', xml_declaration=True)
    except Exception as e:
        return error_response('internalError', f'An error occurred while generating XML: {str(e)}')

    return HttpResponse(xml_data, content_type='text/xml')


def error_response(code, message):
    """
    Erzeugt eine OAI-PMH Fehlerantwort.
    """
    root = ET.Element('OAI-PMH', xmlns='http://www.openarchives.org/OAI/2.0/')
    response_date = ET.SubElement(root, 'responseDate')
    response_date.text = current_timestamp(fmt=DT_ISO_FORMAT)
    
    request_elem = ET.SubElement(root, 'request', verb='GetRecord')
    request_elem.text = 'http://example.com/oai'  # Ersetze dies durch die tatsächliche URL
    
    error = ET.SubElement(root, 'error', code=code)
    error.text = message
    
    xml_data = ET.tostring(root, encoding='utf-8', xml_declaration=True)
    return HttpResponse(xml_data, content_type='text/xml')


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
