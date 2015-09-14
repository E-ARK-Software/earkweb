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
mets_attributes = {'OBJID': '',
                    'TYPE': 'AIP',
                    'LABEL': '',
                    'ID': ''}
