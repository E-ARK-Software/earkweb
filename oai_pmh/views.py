#!/usr/bin/env python
# coding=UTF-8
"""OAI-PMH module"""
from venv import logger
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from earkweb.models import InformationPackage
from config.configuration import django_service_url
from config.configuration import solr_core_url
from eatb.utils.datetime import date_format, current_timestamp
from config.configuration import django_backend_service_api_url, django_backend_service_url, verify_certificate, representations_directory
from util.djangoutils import get_user_api_token
import xml.etree.ElementTree as ET

from eatb.utils.datetime import DT_ISO_FORMAT, current_timestamp

import pysolr
from django.utils.safestring import mark_safe
import xml.etree.ElementTree as ET
import logging
import base64

import requests

# Initialisiere das pysolr-Objekt (passe die Solr-URL an)
solr = pysolr.Solr(solr_core_url, always_commit=True)

logger = logging.getLogger(__name__)

ET.register_namespace('oai_dc', 'http://www.openarchives.org/OAI/2.0/oai_dc/')
ET.register_namespace('dc', 'http://purl.org/dc/elements/1.1/')

lido_ns = 'http://www.lido-schema.org'


eark_ns = 'http://www.e-ark-foundation.eu'


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
    elif verb == 'ListRecords':
        return list_records(request)
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

import xml.etree.ElementTree as ET
from django.http import HttpResponse

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
    
    # OAI-DC Format
    metadata_format_dc = ET.SubElement(list_metadata_formats, 'metadataFormat')
    metadata_prefix_dc = ET.SubElement(metadata_format_dc, 'metadataPrefix')
    metadata_prefix_dc.text = 'oai_dc'
    schema_dc = ET.SubElement(metadata_format_dc, 'schema')
    schema_dc.text = 'http://www.openarchives.org/OAI/2.0/oai_dc.xsd'
    metadata_namespace_dc = ET.SubElement(metadata_format_dc, 'metadataNamespace')
    metadata_namespace_dc.text = 'http://www.openarchives.org/OAI/2.0/oai_dc/'
    
    # LIDO Format
    metadata_format_lido = ET.SubElement(list_metadata_formats, 'metadataFormat')
    metadata_prefix_lido = ET.SubElement(metadata_format_lido, 'metadataPrefix')
    metadata_prefix_lido.text = 'lido'
    schema_lido = ET.SubElement(metadata_format_lido, 'schema')
    schema_lido.text = 'http://www.lido-schema.org/schema/v1.0/lido-v1.0.xsd'
    metadata_namespace_lido = ET.SubElement(metadata_format_lido, 'metadataNamespace')
    metadata_namespace_lido.text = 'http://www.lido-schema.org'

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


def generate_metadata_element(metadata_prefix, identifier, metadata_json, record_elem):
    """
    Generate metadata XML element based on the specified metadataPrefix.

    Parameters:
    metadata_prefix (str): The requested metadata format (e.g., 'oai_dc' or 'lido').
    ip (InformationPackage): The record from which to extract metadata.

    Returns:
    Element: The metadata XML element.
    """
    metadata_elem = ET.Element('metadata')
    metadata = metadata_elem
    title = metadata_json.get('title', 'No Title')
    
    ET.register_namespace('eark', eark_ns)
    if metadata_prefix == 'lido':
        ET.register_namespace('lido', lido_ns)
        lido_wrap = ET.SubElement(metadata, ET.QName(lido_ns, 'lidoWrap'))
        lido_record = ET.SubElement(lido_wrap, ET.QName(lido_ns, 'lido'))

        administrative_metadata = ET.SubElement(lido_record, ET.QName(lido_ns, 'administrativeMetadata'))
        ET.SubElement(administrative_metadata, ET.QName(lido_ns, 'recordID')).text = metadata_json.get('uid', 'Unknown UID')
        ET.SubElement(administrative_metadata, ET.QName(lido_ns, 'recordSource')).text = metadata_json.get('contactPoint', 'Unknown Repository')

        descriptive_metadata = ET.SubElement(lido_record, ET.QName(lido_ns, 'descriptiveMetadata'))
        obj_ident = ET.SubElement(descriptive_metadata, ET.QName(lido_ns, 'objectIdentificationWrap'))
        title_elem = ET.SubElement(obj_ident, ET.QName(lido_ns, 'titleWrap'))
        ET.SubElement(title_elem, ET.QName(lido_ns, 'title')).text = title
        ET.SubElement(obj_ident, ET.QName(lido_ns, 'objectDescriptionWrap')).text = metadata_json.get('description', 'No Description')

        # Add rights information from the first representation
        rights_work_set = ET.SubElement(administrative_metadata, ET.QName(lido_ns, 'rightsWorkSet'))
        credit_line = ET.SubElement(rights_work_set, ET.QName(lido_ns, 'creditLine'))

        # Extract the first available access rights
        representations = metadata_json.get('representations', {})
        first_representation = next(iter(representations.values()), None)
        access_rights = first_representation.get('access_rights', 'No Rights Available') if first_representation else 'No Rights Available'

        credit_line.text = access_rights

        # linked data
        subject_wrap = ET.SubElement(descriptive_metadata, ET.QName(lido_ns, 'subjectWrap'))
        for linked_data in metadata_json.get('linkedData', []):
            concept_set = ET.SubElement(subject_wrap, ET.QName(lido_ns, 'subjectSet'))
            concept = ET.SubElement(concept_set, ET.QName(lido_ns, 'concept'))
            # Label
            concept_id = ET.SubElement(concept, ET.QName(lido_ns, 'conceptID'), type="URI")

            concept_id_text = linked_data.get('link', 'Unknown Link')
            # modify wikidata from https to http (Europeana requirement)
            if concept_id_text.startswith("https://www.wikidata.org/"):
                concept_id_text = concept_id_text.replace("https://", "http://", 1)
            concept_id.text = concept_id_text
            # Human-readable name
            concept_name = ET.SubElement(concept, ET.QName(lido_ns, 'term'))
            concept_name.text = linked_data.get('label', 'Unknown Label')

        # Add event and/or place data
        event_wrap = ET.SubElement(descriptive_metadata, ET.QName(lido_ns, 'eventWrap'))

        for location in metadata_json.get('locations', []):
            location_event = location.get('locationEvent', '').strip()
            location_date = location.get('locationDate', '').strip()

            # Convert event date to LIDO format if it exists
            formatted_event_date = location_date.replace('-', '.') if location_date else None

            if location_event or formatted_event_date:
                # Add event + place if event data exists
                event_set = ET.SubElement(event_wrap, ET.QName(lido_ns, 'eventSet'))
                event = ET.SubElement(event_set, ET.QName(lido_ns, 'event'))

                ET.SubElement(event, ET.QName(lido_ns, 'eventID')).text = location.get('eventIdentifier', 'Unknown event ID')
                ET.SubElement(event, ET.QName(lido_ns, 'eventName')).text = location_event if location_event else 'Unnamed Event'

                if formatted_event_date:
                    event_date_elem = ET.SubElement(event, ET.QName(lido_ns, 'eventDate'))
                    ET.SubElement(event_date_elem, ET.QName(lido_ns, 'date')).text = formatted_event_date

                # Place details within event
                event_place = ET.SubElement(event, ET.QName(lido_ns, 'eventPlace'))
            else:
                # If no event details, add only place information
                event_place = ET.SubElement(event_wrap, ET.QName(lido_ns, 'eventPlace'))

            # Place information
            place = ET.SubElement(event_place, ET.QName(lido_ns, 'place'))
            place_id = ET.SubElement(place, ET.QName(lido_ns, 'placeID'))
            place_id.text = location.get('identifier', 'Unknown ID')

            # Correctly store the location name
            place_name = ET.SubElement(place, ET.QName(lido_ns, 'placeName'))
            place_name.text = location.get('label', 'Unknown Place')

            place_coordinates = ET.SubElement(place, ET.QName(lido_ns, 'placeCoordinates'))
            ET.SubElement(place_coordinates, ET.QName(lido_ns, 'latitude')).text = str(location['coordinates'].get('lat', 'Unknown'))
            ET.SubElement(place_coordinates, ET.QName(lido_ns, 'longitude')).text = str(location['coordinates'].get('lng', 'Unknown'))
            place_coordinates.append(ET.Comment("""- Zoom 0   → Entire world view (fully zoomed out)
- Zoom 1-3 → Continents and large countries
- Zoom 4-6 → Countries and large regions
- Zoom 7-9 → Cities and smaller regions
- Zoom 10-12 → City details, major roads
- Zoom 13-15 → Streets, individual buildings
- Zoom 16-18+ → House-level details, very close-up views"""))
            ET.SubElement(place_coordinates, ET.QName(eark_ns, 'zoomLevel')).text = str(location.get('zoomLevel', 'Unknown'))
            place_coordinates.append(ET.Comment("""The locationUncertainty value represents confidence in the recorded location.
A lower value indicates higher confidence, while a higher value indicates greater uncertainty.
Possible range: 0 (high confidence) to 100 (low confidence).
"""))
            ET.SubElement(place_coordinates, ET.QName(eark_ns, 'locationUncertainty')).text = str(location.get('locationUncertainty', 'Unknown'))

            place_coordinates.append(ET.Comment("""The locationUncertaintyRadius is a visualization tool for uncertainty, not an absolute distance.
It is dynamically adjusted based on the zoom level to maintain a proportional representation on the map.
The radius is calculated as:
    radius = (200000 / 2^zoomLevel) * locationUncertainty
where:
    - Higher zoom levels result in smaller radius values.
    - A larger locationUncertainty value increases the radius.
    - The circle serves as an uncertainty visualization and scales dynamically with zoom."""))            
            ET.SubElement(place_coordinates, ET.QName(eark_ns, 'locationUncertaintyRadius')).text = str(location.get('locationUncertaintyRadius', 'Unknown'))

        # Add link to the landing page
        resource_wrap = ET.SubElement(descriptive_metadata, ET.QName(lido_ns, 'resourceWrap'))

        landing_page = f"{django_service_url}/access/{identifier}/"
        resource_set = ET.SubElement(resource_wrap, ET.QName(lido_ns, 'resourceSet'))
        ET.SubElement(resource_set, ET.QName(lido_ns, 'resourceID')).text = identifier

        # Extract the first available distribution_label from representations
        representations = metadata_json.get('representations', {})
        first_representation = next(iter(representations.values()), None)
        distribution_label = first_representation.get('distribution_label', 'Landing Page') if first_representation else 'Landing Page'

        ET.SubElement(resource_set, ET.QName(lido_ns, 'resourceType')).text = distribution_label  # Use distribution label

        resource = ET.SubElement(resource_set, ET.QName(lido_ns, 'resource'))
        ET.SubElement(resource, ET.QName(lido_ns, 'resourceName')).text = "Landing Page"
        ET.SubElement(resource, ET.QName(lido_ns, 'resourceDescription')).text = "Access the complete package."
        ET.SubElement(resource, ET.QName(lido_ns, 'resourceRepresentation')).text = landing_page

        for rep_id, rep_data in metadata_json.get('representations', {}).items():
            resource_set = ET.SubElement(resource_wrap, ET.QName(lido_ns, 'resourceSet'))
            ET.SubElement(resource_set, ET.QName(lido_ns, 'resourceID')).text = rep_id

            file_metadata = rep_data.get('file_metadata', {})
            file_items = rep_data.get('file_items', [])
            
            if not isinstance(file_items, list):
                print(f"Warning: file_items is not a list for rep_id {rep_id}: {file_items}")
                continue

            for file_path in file_items:
                file_data = file_metadata.get(file_path, {})

                # Only process files where 'isPublicAccess' is explicitly True
                if file_data.get('isPublicAccess') is True:
                    resource = ET.SubElement(resource_set, ET.QName(lido_ns, 'resource'))
                    ET.SubElement(resource, ET.QName(lido_ns, 'resourceName')).text = file_path
                    ET.SubElement(resource, ET.QName(lido_ns, 'resourceDescription')).text = file_data.get('description', 'No Description')
                    ET.SubElement(resource, ET.QName(eark_ns, 'isPreview')).text = str(file_data.get('isPreview', False))
                    ET.SubElement(resource, ET.QName(lido_ns, 'bytesSize')).text = str(file_data.get('bytesSize', 'Unknown'))
                    mime_type = file_data.get('mimeType', 'application/octet-stream')
                    ET.SubElement(resource, ET.QName(lido_ns, 'mimeType')).text = mime_type

                    # Add durationSeconds if applicable
                    if mime_type.startswith(('video/', 'audio/')):
                        ET.SubElement(resource, ET.QName(eark_ns, 'durationSeconds')).text = str(file_data.get('durationSeconds', 'Unknown'))

                    # Construct the full file URL
                    file_url = f"{django_service_url}/access/{identifier}/{representations_directory}/{rep_id}/data/{file_path}"
                    ET.SubElement(resource, ET.QName(lido_ns, 'resourceRepresentation')).text = file_url

    else:  # Default to OAI-DC
        ET.register_namespace('oai_dc', 'http://www.openarchives.org/OAI/2.0/oai_dc/')
        dc_elem = ET.SubElement(metadata_elem, ET.QName('http://www.openarchives.org/OAI/2.0/oai_dc/', 'dc'))
        ET.SubElement(dc_elem, ET.QName('http://purl.org/dc/elements/1.1/', 'title')).text = title or 'No Title'
        ET.SubElement(dc_elem, ET.QName('http://purl.org/dc/elements/1.1/', 'identifier')).text = identifier

    return metadata_elem

import base64

def encode_resumption_token(start_index, metadata_prefix):
    token_str = f"{start_index}|{metadata_prefix}"
    return base64.urlsafe_b64encode(token_str.encode()).decode()

def decode_resumption_token(token):
    try:
        decoded = base64.urlsafe_b64decode(token.encode()).decode()
        start_index_str, metadata_prefix = decoded.split('|')
        return int(start_index_str), metadata_prefix
    except Exception:
        return None, None

def list_records(request):
    """
    Handle the OAI-PMH ListRecords request.
    """
    resumption_token = request.GET.get('resumptionToken')
    
    if resumption_token:
        start_index, metadata_prefix = decode_resumption_token(resumption_token)
        if metadata_prefix not in ['oai_dc', 'lido']:
            return error_response('cannotDisseminateFormat', 'Unsupported metadataPrefix in resumptionToken.')
    else:
        metadata_prefix = request.GET.get('metadataPrefix')
        if metadata_prefix not in ['oai_dc', 'lido']:
            return error_response('cannotDisseminateFormat', 'The metadata format identified by the value given for the metadataPrefix argument is not supported.')
        start_index = 0

    root = ET.Element('OAI-PMH', xmlns='http://www.openarchives.org/OAI/2.0/')
    response_date = ET.SubElement(root, 'responseDate')
    response_date.text = current_timestamp(fmt=DT_ISO_FORMAT)

    list_records_elem = ET.SubElement(root, 'ListRecords')

    # Query InformationPackage objects
    page_size = 10
    packages = InformationPackage.objects.exclude(identifier='').exclude(storage_dir='')[start_index:start_index + page_size]

    for ip in packages:
        record_elem = ET.SubElement(list_records_elem, 'record')
        header = ET.SubElement(record_elem, 'header')
        identifier = ET.SubElement(header, 'identifier')
        identifier.text = ip.identifier
        datestamp = ET.SubElement(header, 'datestamp')
        datestamp.text = date_format(ip.last_change)

        # Fetch metadata
        metadata_url = f"{django_backend_service_api_url}/ips/{identifier.text}/file-resource/metadata/metadata.json/"
        response = requests.get(metadata_url)
        if response.status_code != 200:
            return error_response('idDoesNotExist', 'The value of the identifier argument is unknown or illegal in this repository.')
        metadata_json = response.json()

        metadata_elem = generate_metadata_element(metadata_prefix, identifier.text, metadata_json, record_elem)
        record_elem.append(metadata_elem)

    # Handle pagination
    total_records = InformationPackage.objects.exclude(identifier='').exclude(storage_dir='').count()
    next_index = start_index + page_size
    resumption_token_elem = ET.SubElement(list_records_elem, 'resumptionToken')
    if next_index < total_records:
        encoded_token = encode_resumption_token(next_index, metadata_prefix)
        resumption_token_elem.text = encoded_token
        resumption_token_elem.set('cursor', str(start_index))
        resumption_token_elem.set('completeListSize', str(total_records))
    else:
        resumption_token_elem.text = ''

    return xml_response(root)


def get_record(request):
    """
    Handle the OAI-PMH GetRecord request by fetching metadata from the API and formatting it in valid LIDO XML.
    """
    identifier = request.GET.get('identifier')
    metadata_prefix = request.GET.get('metadataPrefix')

    if not identifier or not metadata_prefix:
        return error_response('badArgument', 'The request is missing required arguments.')

    if metadata_prefix not in ['oai_dc', 'lido']:
        return error_response('cannotDisseminateFormat', 'The metadata format identified by the value given for the metadataPrefix argument is not supported by the item or by the repository.')

    # API call to fetch metadata
    metadata_url = f"{django_backend_service_api_url}/ips/{identifier}/file-resource/metadata/metadata.json/"
    response = requests.get(metadata_url)
    
    if response.status_code != 200:
        return error_response('idDoesNotExist', 'The value of the identifier argument is unknown or illegal in this repository.')
    
    metadata_json = response.json()

    root = ET.Element('OAI-PMH', xmlns='http://www.openarchives.org/OAI/2.0/')
    response_date = ET.SubElement(root, 'responseDate')
    response_date.text = current_timestamp(fmt=DT_ISO_FORMAT)

    request_elem = ET.SubElement(root, 'request', verb='GetRecord', identifier=identifier, metadataPrefix=metadata_prefix)
    request_elem.text = request.build_absolute_uri()

    get_record = ET.SubElement(root, 'GetRecord')
    record_elem = ET.SubElement(get_record, 'record')
    header = ET.SubElement(record_elem, 'header')
    identifier_elem = ET.SubElement(header, 'identifier')
    identifier_elem.text = identifier
    datestamp = ET.SubElement(header, 'datestamp')
    datestamp.text = metadata_json.get('lastChange', 'Unknown Date')

    # Use the modular metadata generator
    metadata_elem = generate_metadata_element(metadata_prefix, identifier, metadata_json, record_elem)
    record_elem.append(metadata_elem)
        
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
