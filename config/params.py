from config import root_dir

from models import Path

# list of root-level folders in the AIP
aip_folders = (
    'aip-metadata',
    'representations',
    'schemas',
)


def init_param(model_obj, name, default):
    """
    Get parameter from database with default configuration if no database value is available
    :param model_obj: Model class (database table)
    :param name: parameter name
    :param default: default value
    :return: parameter value
    """
    try:
        param = model_obj.objects.get(entity=name)
        return param.value
    except model_obj.DoesNotExist:
        return default


config_path_reception = init_param(Path, "path_reception", "/var/data/earkweb/reception")
config_path_ingest = init_param(Path, "path_ingest", "/var/data/earkweb/ingest")
config_path_work = init_param(Path, "path_work", "/var/data/earkweb/work")
config_path_storage = init_param(Path, "path_storage", "/var/data/earkweb/storage")


# location of METS Template
template_METS_path = root_dir + '/lib/metadata/mets/template_METS.xml'

# METS header params
# TODO: retrieve from db?
mets_header_attributes = {'OBJID': 'some identifier',
                          'TYPE': 'AIP',
                          'LABEL': 'label goes here',
                          'PROFILE': 'profile goes here',
                          'ID': ip.uui,
                          'xsi:schemaLocation': 'http://www.loc.gov/METS/ schemas/IP.xsd ExtensionMETS schemas/ExtensionMETS.xsd http://www.w3.org/1999/xlink schemas/xlink.xsd',
                          'xmlns:mets': 'http://www.loc.gov/METS/',
                          'xmlns:ext': 'ExtensionMETS',
                          'xmlns:xlink': 'http://www.w3.org/1999/xlink',
                          'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance'}
