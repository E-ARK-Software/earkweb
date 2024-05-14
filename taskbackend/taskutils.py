import json
import os
import re
import shutil
import tarfile
from datetime import datetime
from json import JSONDecodeError
from typing import List

import bagit
from celery.result import AsyncResult

from api.util import get_representation_ids_by_label
from eatb.checksum import check_transfer, get_sha512_hash, get_hash_values
from eatb.csip_validation import XmlValidation
from eatb.packaging import TarContainer, create_package
from eatb.pairtree_storage import PairtreeStorage, make_storage_directory_path, make_storage_data_directory_path
from eatb.utils.XmlHelper import q

from eatb.utils.datetime import date_format, DT_ISO_FORMAT, ts_date, DT_ISO_FMT_SEC_PREC
from eatb.utils.fileutils import fsize, FileBinaryDataChunks, locate, strip_prefixes, remove_protocol, sub_dirs, \
    read_file_content, rec_find_files, to_safe_filename, read_and_load_json_file
from lxml import etree

from earkweb.models import InternalIdentifier, InformationPackage
from taskbackend.ip_state import IpState
from taskbackend.tasklogger import TaskLogger
from config.configuration import config_path_work, flower_service_url, \
    verify_certificate, representations_directory, flower_service_url, config_path_storage, \
    django_service_protocol, django_service_host, django_service_port, backend_api_key
from subprocess import Popen, PIPE
from config.configuration import django_backend_service_host, django_backend_service_port
import logging
import requests

from util.custom_exceptions import NotFoundError
from util.djangoutils import get_user_api_token
from util.flowerapiclient import get_task_info

logger = logging.getLogger(__name__)


def update_state_from_backend_api(request, uid):
    """updating frontend database table based on information persisted in the backend"""
    ip_state_url = "/earkweb/api/ips/%s/status/" % (uid)
    user_api_token = get_user_api_token(request.user)
    response = requests.get(ip_state_url, headers={'Authorization': 'Token %s' % user_api_token}, verify=verify_certificate)
    ip_state_json = json.loads(response.content)
    identifier = ip_state_json["identifier"]
    if identifier != "" and identifier != 'None':
        ip = InformationPackage.objects.get(uid=uid)
        ip.identifier = ip_state_json["identifier"]
        version = ip_state_json["version"]
        ip.version = int(version)
        ip.storage_dir = make_storage_directory_path(identifier, version)
        ip.save()


def update_states_from_backend_api(request):
    """updating frontend database table based on status information in the backend"""
    ip_states_url = "/earkweb/api/ips/status/"
    logger.info("Submissions update states request URL: %s" % ip_states_url)
    user_api_token = get_user_api_token(request.user)
    response = requests.get(ip_states_url, headers={'Authorization': 'Token %s' % user_api_token}, verify=verify_certificate)
    if response.status_code != 200:
        try:
            resp = json.loads(response.text)
            if "message" in resp:
                raise ValueError(resp["message"])
        except:
            raise ValueError("An error occurred")
    logger.info(response.text)
    ip_states_json = json.loads(response.text)
    if ip_states_json != "{}":
        for uid in ip_states_json.keys():
            states = ip_states_json[uid]
            identifier = states["identifier"]
            if identifier != "" and identifier != 'None':
                ip = InformationPackage.objects.get(uid=uid)
                ip.identifier = states["identifier"]
                version = states["version"]
                ip.version = int(version)
                ip.storage_dir = make_storage_directory_path(identifier, version)
                ip.save()


def get_working_dir(uid):
    """Get working directory for given process id"""
    working_dir = os.path.join(config_path_work, uid)
    if not os.path.exists(working_dir):
        raise RuntimeError("Working directory does not exist for the given process ID")
    return working_dir


def extract_and_remove_package(self, package_file_path, target_directory, proc_logfile):
    tl = TaskLogger(proc_logfile)

    tar_container = TarContainer(package_file_path)
    success = tar_container.extract(target_directory)

    if success:
        tl.addinfo("Package %s extracted to %s" % (package_file_path, target_directory))
    else:
        tl.adderr("An error occurred while trying to extract package %s to %s" % (package_file_path, target_directory))
    # delete file after extraction
    os.remove(package_file_path)
    return success


def extract_and_remove(package_file_path, target_directory):
    tar_container = TarContainer(package_file_path)
    success = tar_container.extract(target_directory)
    os.remove(package_file_path)
    return success


def run_command(args, stdin=PIPE, stdout=PIPE, stderr=PIPE):
    result, res_stdout, res_stderr = None, None, None
    try:
        # quote the executable otherwise we run into troubles
        # when the path contains spaces and additional arguments
        # are presented as well.
        # special: invoking bash as login shell here with
        # an unquoted command does not execute /etc/profile

        print('Launching: %s' % args)
        process = Popen(args, stdin=stdin, stdout=stdout, stderr=stderr, shell=False)

        res_stdout, res_stderr = process.communicate()
        result = process.returncode
        print('Finished: %s' % args)

    except Exception as ex:
        res_stderr = ''.join(str(ex.args))
        result = 1

    if result != 0:
        print('Command failed:' + ''.join(res_stderr))
        raise Exception('Command failed:' + ''.join(res_stderr))

    return result, res_stdout, res_stderr


def safe_copy_from_to(copy_from, copy_to, tl):
    package_source_size = fsize(copy_from)
    logger.info("Source: %s (%d)" % (copy_from, package_source_size))
    logger.info("Target: %s" % copy_to)
    total_bytes_read = 0
    with open(copy_to, 'wb') as target_file:
        for chunk in FileBinaryDataChunks(copy_from, 65536).chunks(total_bytes_read):
            target_file.write(chunk)
        total_bytes_read += package_source_size
        target_file.close()
    check_transfer(copy_from, copy_to, tl)


def get_identifier(org_nsid):
    """Get internal identifier"""
    intid_result_set = InternalIdentifier.objects.filter(used=False, org_nsid=org_nsid)[:1]
    if len(intid_result_set) == 0:
        raise ValueError("No identifier available for the namespace '%s'" % org_nsid)
    intid = intid_result_set[0]
    intid.used = True
    intid.save()
    return "%s:%s" % (org_nsid, intid.identifier)


def get_celery_worker_status():
    ERROR_KEY = "ERROR"
    try:
        from earkweb.celery import app

        insp = app.control.inspect()
        d = insp.stats()
        if not d:
            d = { ERROR_KEY: 'No Celery workers running.' }
    except IOError as e:
        from errno import errorcode
        msg = "Error connecting to the backend: " + str(e)
        if len(e.args) > 0 and errorcode.get(e.args[0]) == 'ECONNREFUSED':
            msg += ' Check that the RabbitMQ server is running.'
        d = { ERROR_KEY: msg }
    except ImportError as e:
        d = { ERROR_KEY: str(e)}

    return d


def flower_is_running():
    try:
        response = requests.get(flower_service_url, verify=verify_certificate)
        if response.status_code == 200:
            return True
        else:
            return False
    except:
        return False


def get_task_info_from_child_tasks(current_task_result):
    """Get child ids for a given task result"""
    child_task_ids = []
    task_status_from_result = {}

    def get_child_task_id(current_task_result):
        if current_task_result.children:
            c = current_task_result.children[0]
            curr_child_task = {"taskid": c.id, "status": c.status}
            curr_child_task.update(get_task_info(c.id))
            child_task_result = AsyncResult(c.id)
            result = child_task_result.result
            if result and isinstance(result, str):
                result_obj = json.loads(result)
                if "identifier" in result_obj:
                    task_status_from_result['identifier'] = result_obj['identifier']
                if "version" in result_obj:
                    task_status_from_result['version'] = result_obj['version']
                if "storage_dir" in result_obj:
                    task_status_from_result['storage_dir'] = result_obj['storage_dir']
            child_task_ids.append(curr_child_task)
            if child_task_result and child_task_result.children and len(child_task_result.children) > 0:
                return get_child_task_id(child_task_result)
    try:
        get_child_task_id(current_task_result)
    except Exception as e:
        logger.error(e)

    return child_task_ids, task_status_from_result


def validate_ead_metadata(root_path, pattern, schema_file, custom_logger=None):
    """
    This function validates the XML meta data file against the XML schema and performs additional consistency checks.
    If the schema_file is None, the EAD metadata file is validated against the XML schema files provided.
    @type       root_path: string
    @param      root_path: Root directory
    @type       pattern:  string
    @param      pattern:  pattern to search metadata
    @type       tl:  workers.TaskLogger
    @param      tl:  workers.TaskLogger
    @rtype:     bool
    @return:    Validity of EAD metadata
    """
    # ead 2002: ns = {'ead': 'http://ead3.archivists.org/schema/', 'xlink': 'http://www.w3.org/1999/xlink',
    #     'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}
    ns = {'ead': 'http://ead3.archivists.org/schema/', 'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}
    xmlval = XmlValidation()
    ead_md_files = [x for x in locate(pattern, root_path)]
    log = custom_logger if custom_logger else logger
    for ead in ead_md_files:
        log.debug("Validating EAD metadata file: %s" % strip_prefixes(ead, root_path))
        # validate against xml schema
        result = xmlval.validate_XML_by_path(ead, schema_file)
        if result.err and len(result.err) >  0:
            for e in result.err:
                log.error(e)
        if schema_file is None:
            schema_file = xmlval.get_schema_from_instance(ead)
            log.info("Using schema files specified by the 'schemaLocation' attribute")
        else:
            log.info("Using schema: " % schema_file)
        if result.valid:
            log.debug("Metadata file '%s' successfully validated." % ead)
        else:
            if schema_file is None:
                log.error("Error validating against schemas using schema files specified by the 'schemaLocation' attribute:")
            else:
                log.error("Error validating against schema '%s': %s" % (schema_file, result.err))

            for err in result.err:
                log.error("- %s" % str(err))
            return False
        ead_tree = etree.parse(ead)
        # check dao hrefs
        res = ead_tree.getroot().xpath('//ead:dao', namespaces=ns)
        if len(res) == 0:
            log.info("The EAD file does not contain any file references.")
        ead_dir, tail = os.path.split(ead)
        references_valid = True
        for dao in res:
            # ead 2002: dao_ref_file = os.path.join(ead_dir,
            #     remove_protocol(dao.attrib['{http://www.w3.org/1999/xlink}href']))
            dao_ref_file = os.path.join(ead_dir, remove_protocol(dao.attrib['href']))
            if not os.path.exists(dao_ref_file):
                references_valid = False
                log.error("DAO file reference error - File does not exist: %s" % dao_ref_file)
        if not references_valid:
            log.error( "DAO file reference errors. Please consult the log file for details.")
            return False
    return True


def validate_gml_data(root_path, pattern, schema_file):
    """
    This function validates the XML meta data file against the XML schema and performs additional consistency checks.
    If the schema_file is None, the GML data file is validated against the XML schema files provided.
    @type       root_path: string
    @param      root_path: Root directory
    @type       pattern:  string
    @param      pattern:  pattern to search metadata
    @type       tl:  workers.TaskLogger
    @param      tl:  workers.TaskLogger
    @rtype:     bool
    @return:    Validity of GML data
    """
    ns = {'ogr': 'http://ogr.maptools.org/', 'gml': 'http://www.opengis.net/gml', 'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}
    xmlval = XmlValidation()
    gml_data_files = [x for x in locate(pattern, root_path)]
    for ead in gml_data_files:
        logger.debug("Validating GML data file: %s" % strip_prefixes(ead, root_path))
        # validate against xml schema
        result = xmlval.validate_XML_by_path(ead, schema_file)
        if schema_file is None:
            logger.info("Using schema files specified by the 'schemaLocation' attribute")
        else:
            logger.info("Using schema: " % schema_file)
        if result.valid:
            logger.debug("GML data file '%s' successfully validated." % ead)
        else:
            if schema_file is None:
                logger.error("Error validating against schemas using schema files specified by the 'schemaLocation' attribute:")
            else:
                logger.error("Error validating against schema '%s': %s" % (schema_file, result.err))

            for err in result.err:
                logger.error("- %s" % str(err))
            return False
        ead_tree = etree.parse(ead)
    return True


def get_last_submission_path(ip_root_path):
    submiss_dir = 'submission'
    submiss_path = os.path.join(ip_root_path, submiss_dir)
    if os.path.exists(os.path.join(submiss_path, "METS.xml")):
        return submiss_path
    else:
        submiss_subdirs = sub_dirs(submiss_path)
        if submiss_subdirs and len(submiss_subdirs) > 0:
            # get last folder (possible submission update folders - sorted!)
            submiss_path = os.path.join(submiss_path, submiss_subdirs[-1])
            if os.path.exists(os.path.join(submiss_path, "METS.xml")):
                return submiss_path
    return None


def get_aip_children(task_context_path, aip_identifier, package_extension):
    aip_in_dip_work_dir = os.path.join(task_context_path, ("%s.%s" % (aip_identifier, package_extension)))

    children_uuids = []
    # get parent and children from existing AIP tar (aip_in_dip_work_dir)
    METS_NS = 'http://www.loc.gov/METS/'
    XLINK_NS = "http://www.w3.org/1999/xlink"
    print("reading METS of selected aip %s" % aip_in_dip_work_dir)
    with tarfile.open(aip_in_dip_work_dir) as tar:
        mets_file = aip_identifier+'/METS.xml'
        member = tar.getmember(mets_file)
        fp = tar.extractfile(member)
        mets_content = fp.read()

        # parse AIP mets
        parser = etree.XMLParser(resolve_entities=False, remove_blank_text=True, strip_cdata=False)
        aip_parse = etree.parse(mets_content.decode("utf-8"), parser)
        aip_root = aip_parse.getroot()

        # find AIP structmap and child identifiers
        children_map = aip_root.find("%s[@LABEL='child %s']" % (q(METS_NS, 'structMap'), 'AIP'))
        if children_map is not None:
            children_div = children_map.find("%s[@LABEL='child %s identifiers']" % (q(METS_NS, 'div'), 'AIP'))
            if children_div is not None:
                children = children_div.findall("%s[@LABEL='child %s']" % (q(METS_NS, 'div'), 'AIP'))
                for child in children:
                    mptr = child.find("%s" % q(METS_NS, 'mptr'))
                    urn = mptr.get(q(XLINK_NS, 'href'))
                    print("found child urn %s" % urn)
                    uuid = urn.split('urn:uuid:',1)[1]
                    print("found child uuid %s" % uuid)
                    children_uuids.append(uuid)
    return children_uuids


def get_first_ip_path(wd_root_path):
    if os.path.exists(os.path.join(wd_root_path, "METS.xml")):
        return wd_root_path
    else:
        wd_sub_dirs = sub_dirs(wd_root_path)
        if wd_sub_dirs and len(wd_sub_dirs) > 0:
            # get last folder (possible submission update folders - sorted!)
            for wd_sub_dir in wd_sub_dirs:
                mets_abs_path = os.path.join(wd_root_path, wd_sub_dir, "METS.xml")
                if os.path.exists(mets_abs_path):
                    return os.path.join(wd_root_path, wd_sub_dir)


def get_package_from_storage(task_context_path, package_uuid, package_extension):
    from config.configuration import config_path_storage
    pts = PairtreeStorage(config_path_storage)
    parent_object_path = pts.get_object_path(package_uuid)

    package_in_dip_work_dir = os.path.join(task_context_path, ("%s.%s" % (package_uuid, package_extension)))
    package_source_size = fsize(parent_object_path)
    total_bytes_read = 0
    with open(package_in_dip_work_dir, 'wb') as target_file:
         for chunk in FileBinaryDataChunks(parent_object_path, 65536).chunks(total_bytes_read):
             target_file.write(chunk)
         total_bytes_read += package_source_size
         target_file.close()
    check_transfer(parent_object_path, package_in_dip_work_dir)


def get_children_from_storage(task_context_path, package_uuid, package_extension):
    get_package_from_storage(task_context_path, package_uuid, package_extension)
    child_uuids = get_aip_children(task_context_path, package_uuid, package_extension)
    for child_uuid in child_uuids:
        get_children_from_storage(task_context_path, child_uuid, package_extension)


def get_aip_parent(task_context_path, aip_identifier, package_extension):
    aip_in_dip_work_dir = os.path.join(task_context_path, ("%s.%s" % (aip_identifier, package_extension)))

    # get parent and children from existing AIP tar (aip_in_dip_work_dir)
    METS_NS = 'http://www.loc.gov/METS/'
    XLINK_NS = "http://www.w3.org/1999/xlink"
    print("reading METS of selected aip %s" % aip_in_dip_work_dir)
    with tarfile.open(aip_in_dip_work_dir) as tar:
        mets_file = aip_identifier+'/METS.xml'
        member = tar.getmember(mets_file)
        fp = tar.extractfile(member)
        mets_content = fp.read()

        # parse AIP mets
        parser = etree.XMLParser(resolve_entities=False, remove_blank_text=True, strip_cdata=False)
        aip_parse = etree.parse(mets_content.decode("utf-8"), parser)
        aip_root = aip_parse.getroot()

        # find AIP structmap and parent identifiers
        parents_map = aip_root.find("%s[@LABEL='parent %s']" % (q(METS_NS, 'structMap'), 'AIP'))
        if parents_map is not None:
            parents_div = parents_map.find("%s[@LABEL='parent %s identifiers']" % (q(METS_NS, 'div'), 'AIP'))
            if parents_div is not None:
                parents = parents_div.findall("%s[@LABEL='parent %s']" % (q(METS_NS, 'div'), 'AIP'))
                for parent in parents:
                    mptr = parent.find("%s" % q(METS_NS, 'mptr'))
                    urn = mptr.get(q(XLINK_NS,'href'))
                    uuid = urn.split('urn:uuid:',1)[1]
                    print("found parent uuid %s" % uuid)
                    return uuid

    return None


def log_operation(task_log, response, success_condition, operation_name):
    try:
        parsed_response = json.loads(response.text)
        if success_condition:
            message = parsed_response['message'] if 'message' in parsed_response else response.text
            task_log.info("Operation successful: %s (%d): %s " % (operation_name, response.status_code, message))
        else:
            message = parsed_response['errdetail'] if 'errdetail' in parsed_response else \
                parsed_response['detail'] if 'detail' in parsed_response else parsed_response
            task_log.error("Operation failed: %s (%d): %s " % (operation_name, response.status_code, message))
    except JSONDecodeError as err:
        task_log.error("Operation failed: %s (%d): %s " % (operation_name, response.status_code, err))


def create_or_update_state_info_file(working_dir, info=None):
    if info is None:
        info = {}
    assert isinstance(info, dict)
    result_info = {}
    state_info_file = os.path.join(working_dir, "metadata/other/state.json")
    if os.path.exists(state_info_file):
        file_content = read_file_content(state_info_file)
        if file_content and file_content != "":
            existing_info = json.loads(file_content)
            if info:
                existing_info.update(info)
                result_info = existing_info
            else:
                result_info = existing_info
        else:
            result_info = info
    else:
        result_info = info
    current_date = date_format(datetime.utcnow(), fmt=DT_ISO_FORMAT)
    result_info["last_change"] = current_date
    with open(state_info_file, 'w') as status_file:
        status_file.write(json.dumps(result_info, indent=4))


def get_process_representation_ids_by_label(uid, representation_label) -> List[str]:
    working_directory = os.path.join(config_path_work, uid)
    return get_wd_representation_ids_by_label(working_directory, representation_label)


def get_wd_representation_ids_by_label(working_directory, representation_label) -> List[str]:
    if not os.path.exists(working_directory):
        raise NotFoundError("Working directory not found")
    metadata_file_path = os.path.join(working_directory, "metadata/metadata.json")
    if not os.path.exists(metadata_file_path):
        raise NotFoundError("Basic metadata not found")
    try:
        md_content = read_file_content(metadata_file_path)
        md = json.loads(md_content)
        if "representations" not in md:
            raise NotFoundError("Insufficient metadata")
        representation_ids = [k for k, v in md["representations"].items() if
                              "distribution_label" in v and v["distribution_label"] == representation_label]
        return representation_ids
    except JSONDecodeError:
        raise NotFoundError('Error parsing metadata')


def get_representation_data_dir_by_label(uid, representation_label):
    work_dir = os.path.join(config_path_work, uid)
    representation_ids = get_representation_ids_by_label(work_dir, representation_label)
    if len(representation_ids) < 1:
        raise ValueError("This dataset does not contain data with the label '%s'!" % representation_label)
    mldata_representation_id = representation_ids[0]
    representation_data_dir = os.path.join(work_dir, representations_directory, mldata_representation_id, "data")
    return representation_data_dir


def get_representation_data_files_by_pattern(uid, representation_label, pattern):
    representation_data_dir = get_representation_data_dir_by_label(uid, representation_label)
    representation_data_files = [
        data_file for data_file in
        rec_find_files(representation_data_dir, include_files_rgxs=[pattern])
    ]
    return representation_data_files


def get_ml_data_file(uid, subset_type):
    train_test_files = get_representation_data_files_by_pattern(uid, "mldata", r'%s_.*\.csv$' % subset_type)
    if len(train_test_files) < 1:
        raise ValueError("This dataset does not contain %s data!" % subset_type)
    # select first data file
    return train_test_files[0]


def create_file_backup(existing_file, move=False):
    existing_file_name = "bak_%s_%s" % (ts_date(fmt=DT_ISO_FMT_SEC_PREC),
                                       os.path.basename(existing_file))
    bak_file = os.path.join(os.path.dirname(existing_file), existing_file_name)
    if move:
        shutil.move(existing_file, bak_file)
    else:
        shutil.copy(existing_file, bak_file)
    return os.path.exists(bak_file)


def store_bag(version, identifier):
    aip_storage_root = make_storage_data_directory_path(identifier, config_path_storage)
    safe_identifier_name = to_safe_filename(identifier)

    bag_suffix = "b%05d" % int(1)
    bag_name = "%s_%s_%s" % (safe_identifier_name, version, bag_suffix)
    version_content_dir = os.path.join(
        aip_storage_root,
        version,
        "content"
    )
    bagit_storage_dir = os.path.join(
        version_content_dir,
        bag_name
    )
    if not os.path.exists(bagit_storage_dir):
        os.mkdir(bagit_storage_dir)
    # storage dir to bagit
    bag = bagit.make_bag(bagit_storage_dir, {'Contact-Name': 'E-ARK'})

    bagit_file_name = "%s.tar" % bag_name
    version_bag_package_file_path = os.path.join(version_content_dir, bagit_file_name)

    exclude_files = ["state.json", "processing.log"]
    checksum = create_package(bagit_storage_dir, bag_name, False, version_content_dir, True, exclude=exclude_files)
    shutil.rmtree(bagit_storage_dir)

    return bagit_storage_dir, version_bag_package_file_path, bagit_file_name, version


def persist_state(identifier, version, storage_dir, file_name, working_dir):
    patch_data = {
        "identifier": identifier,
        "version": int(re.sub("\D", "", version)),
        "storage_dir": storage_dir,
        "file_name": file_name,
        "last_change": date_format(datetime.utcnow()),
    }
    json_data = json.dumps(patch_data, indent=4)
    with open(os.path.join(working_dir, "metadata/other/state.json"), 'w') as inventory_file:
        inventory_file.write(json_data)
    return patch_data


def write_inventory(identifier, version, aip_path, archive_file):
    aip_storage_root = make_storage_data_directory_path(identifier, config_path_storage)
    hashval_md5, hashval_sha256, hashval_sha512 = get_hash_values(aip_path)
    ocfl_package_file_path = os.path.join(version, archive_file)
    ocfl = {
        "digestAlgorithm": "sha512",
        "fixity": {
            "md5": {
                hashval_md5: [ocfl_package_file_path]
            },
            "sha256": {
                hashval_sha256: [ocfl_package_file_path]
            }
        },
        "head": version,
        "id": identifier,
        "manifest": {
            hashval_sha512: [ocfl_package_file_path]
        },
        "type": "https://ocfl.io/1.0/spec/#inventory",
        "versions": {
            version: {
                "created": date_format(datetime.utcnow()),
                "message": "Original SIP",
                "state": {
                    hashval_sha512: [ocfl_package_file_path]
                }
            }
        }
    }
    ocfl_object_file_name = "0=ocfl_object_1.0"
    with open(os.path.join(aip_storage_root, ocfl_object_file_name), 'w') as ocfl_object_file:
        ocfl_object_file.write("ocfl_object_1.0")
    inventory_file_name = "inventory.json"
    inventory_file_path = os.path.join(aip_storage_root, inventory_file_name)
    with open(inventory_file_path, 'w') as inventory_file:
        inventory_file.write(json.dumps(ocfl, indent=4))
    inventory_file_sha512 = get_sha512_hash(inventory_file_path)
    with open(os.path.join(aip_storage_root, "inventory.json.sha512"), 'w') as checksum_inventory:
        checksum_inventory.write("%s %s" % (inventory_file_sha512, inventory_file_name))


def update_status(uid, patch_data):
    url = "%s://%s:%s/earkweb/api/ips/%s/" % (
        django_service_protocol, django_service_host, django_service_port, uid)
    return requests.patch(url, data=patch_data, headers={'Authorization': 'Api-Key %s' % backend_api_key},
                              verify=verify_certificate)


def update_inventory(identifier, version, aip_path, archive_file, action):
    aip_storage_root = make_storage_data_directory_path(identifier, config_path_storage)
    inventory_file_name = "inventory.json"
    inventory_file_path = os.path.join(aip_storage_root, inventory_file_name)
    hashval_md5, hashval_sha256, hashval_sha512 = get_hash_values(aip_path)
    ocfl_package_file_path = os.path.join(version, "data", archive_file)
    inventory_json = read_and_load_json_file(inventory_file_path)
    inventory_json["fixity"]["md5"][hashval_md5] = [ocfl_package_file_path]
    inventory_json["fixity"]["sha256"][hashval_sha256] = [ocfl_package_file_path]
    inventory_json["head"] = version
    inventory_json["manifest"][hashval_sha512] = [ocfl_package_file_path]
    inventory_json["versions"][version] = {
        "created": date_format(datetime.utcnow()),
        "message": "AIP (%s)" % action,
        "state": {
            hashval_sha512: [ocfl_package_file_path]
        }
    }
    with open(inventory_file_path, 'w') as inventory_file:
        inventory_file.write(json.dumps(inventory_json, indent=4))