import datetime
import fnmatch
import gettext
import json
import os
import shutil
import tarfile
import time
import traceback
import uuid
from functools import partial
from os import walk

import redis
import requests
from celery import chain, group
# from celery.task import Task

from lxml import etree, objectify

import eatb.pairtree_storage
from access.search.solrclient import SolrClient, default_reporter
from access.search.solrquery import SolrQuery
from access.search.solrserver import SolrServer
from config.configuration import config_path_storage, config_path_work, solr_protocol, solr_host, solr_port, \
    solr_core, representations_directory, verify_certificate, redis_host, redis_port, redis_password, commands, \
    root_dir, metadata_file_pattern_ead, django_service_protocol, django_service_host, django_service_port, \
    backend_api_key
from earkweb.celery import app
from earkweb.decorators import requires_parameters, task_logger
from earkweb.models import InformationPackage
from eatb import VersionDirFormat
from eatb.checksum import check_transfer, ChecksumValidation, ChecksumAlgorithm, ChecksumFile
from eatb.cli import CliExecution, CliCommand, CliCommands
from eatb.csip_validation import CSIPValidation
from eatb.file_format import FormatIdentification
from eatb.metadata import XLINK_NS, METS_NS
from eatb.metadata.dip_parsed_premis import DIPPremis
from eatb.metadata.ead import field_namevalue_pairs_per_file
from eatb.metadata.mets import get_mets_objids_from_basedir
from eatb.metadata.mets_generator import MetsGenerator
from eatb.metadata.mets_validation import MetsValidation
from eatb.metadata.parsed_mets import ParsedMets
from eatb.metadata.premis_creator import PremisCreator
from eatb.metadata.premis_generator import PremisGenerator
from eatb.oais_ip import DeliveryValidation, SIPGenerator, create_sip, create_aip
from eatb.packaging import ManifestCreation
from eatb.pairtree_storage import PairtreeStorage, make_storage_data_directory_path
from eatb.utils.XmlHelper import q
from eatb.utils.datetime import date_format, current_timestamp
from eatb.utils.fileutils import to_safe_filename, list_files_in_dir, find_files, \
    strip_prefixes, remove_protocol, fsize, FileBinaryDataChunks
from eatb.utils.randomutils import get_unique_id, randomword
from taskbackend.taskutils import get_working_dir, extract_and_remove, validate_ead_metadata, get_first_ip_path, \
    get_children_from_storage, get_package_from_storage, get_aip_parent, \
    create_or_update_state_info_file, store_bag, persist_state, write_inventory, update_status, \
    update_inventory
from util.djangoutils import check_required_params
from util.solrutils import SolrUtility

gettext.bindtextdomain('earkweb', os.path.join(root_dir, "locale"))
gettext.textdomain('earkweb')
_ = gettext.gettext

logger = app.log.get_default_logger()

r = redis.StrictRedis(host=redis_host, port=redis_port, password=redis_password, decode_responses=True)

cli_commands = CliCommands(os.path.join(root_dir, "settings/commands.cfg"))


@app.task(bind=True, name="sip_package")
@requires_parameters("package_name", "uid", "org_nsid")
@task_logger
def sip_package(self, context, task_log):
    task_context = json.loads(context)
    package_name = task_context["package_name"]
    uid = task_context["uid"]
    working_dir = get_working_dir(task_context["uid"])

    if not os.path.exists(working_dir):
        os.makedirs(working_dir, exist_ok=True)

    create_sip(working_dir, package_name, uid, True, False, task_log)

    # append generation number to tar file; if tar file exists, the generation number is incremented
    sip_tar_file = os.path.join(working_dir, task_context['package_name'] + '.tar')
    tar = tarfile.open(sip_tar_file, "w:")
    task_log.info("Packaging working directory: %s" % working_dir)
    total = sum([len(files) for (root, dirs, files) in walk(working_dir)])
    task_log.info("Total number of files in working directory %d" % total)
    i = 0
    excludes = ["%s.tar" % package_name, "%s.xml" % package_name]
    for subdir, dirs, files in os.walk(working_dir):

        for directory in dirs:
            entry = os.path.join(subdir, directory)

            if not os.listdir(entry):
                tar.add(entry, arcname=os.path.join(package_name, os.path.relpath(entry, working_dir)))

        for file in files:
            if not file in excludes and not file.startswith("urn+uuid"):
                entry = os.path.join(subdir, file)
                tar.add(entry, arcname=os.path.join(package_name, os.path.relpath(entry, working_dir)))
                if i % 10 == 0:
                    perc = (i * 100) / total
                    logger.debug("Packaging progress: %d" % perc)
                    self.update_state(state='PROGRESS', meta={'process_percent': perc})
            i += 1
    tar.close()

    sipgen = SIPGenerator(working_dir)
    delivery_mets_file = os.path.join(working_dir, "%s.xml" % package_name)
    sipgen.createDeliveryMets(sip_tar_file, delivery_mets_file)

    patch_data = {
        "last_change": date_format(datetime.datetime.utcnow())
    }
    url = "%s://%s:%s/earkweb/api/ips/%s/" % (
        django_service_protocol, django_service_host, django_service_port, task_context["uid"])
    response = requests.patch(url, data=patch_data, headers={'Authorization': 'Api-Key %s' % backend_api_key},
                              verify=verify_certificate)
    print("Status information updated: %s (%d)" % (response.text, response.status_code))

    self.update_state(state='PROGRESS', meta={'process_percent': 100})

    return json.dumps(task_context)


@app.task(bind=True, name="ingest_pipeline")
@requires_parameters("uid")
def ingest_pipeline(_, context):
    task_context = json.loads(context)
    check_required_params(task_context, ["uid"])
    result = chain(
        validate_working_directory.s(json.dumps(task_context)),
        descriptive_metadata_validation.s(),
        store_original_sip.s(),
        # aip_migrations.s(),
        aip_record_events.s(),
        aip_record_structure.s(),
        aip_packaging.s(),
        store_aip.s(),
        aip_indexing.s(),
    ).delay()
    return result


@app.task(bind=True, name="update_pipeline")
@requires_parameters("uid")
def update_pipeline(_, context):
    task_context = json.loads(context)
    check_required_params(task_context, ["uid"])
    result = chain(
        validate_working_directory.s(json.dumps(task_context)),
        descriptive_metadata_validation.s(),
        aip_record_events.s(),
        aip_record_structure.s(),
        aip_packaging.s(),
        store_aip.s(),
        aip_indexing.s(),
    ).delay()
    return result


@app.task(bind=True, name="validate_working_directory")
@requires_parameters("uid", "package_name")
@task_logger
def validate_working_directory(_, context, task_log):
    task_context = json.loads(context)
    working_dir = get_working_dir(task_context["uid"])
    package_name = task_context["package_name"]
    delivery_file = os.path.join(working_dir, "%s.tar" % package_name)
    delivery_xml_file = os.path.join(working_dir, "%s.xml" % package_name)

    if os.path.exists(delivery_xml_file):
        task_log.info("Package file: %s" % delivery_file)
        task_log.info("Delivery XML file: %s" % delivery_xml_file)
        mets_schema_file = os.path.join(root_dir, "static/schemas/IP.xsd")
        sdv = DeliveryValidation()
        file_elements = sdv.getFileElements(working_dir, delivery_xml_file, mets_schema_file)
        delivery_file_element = file_elements[0]
        # Checksum validation
        checksum_expected = ParsedMets.get_file_element_checksum(delivery_file_element)
        checksum_algorithm = ParsedMets.get_file_element_checksum_algorithm(delivery_file_element)
        file_reference = ParsedMets.get_file_element_reference(delivery_file_element)

        task_log.info("Extracted file reference: %s" % file_reference)
        file_path = os.path.join(working_dir, remove_protocol(file_reference))
        task_log.info("Computing checksum for file: %s" % file_path)
        csval = ChecksumValidation()
        valid_checksum = csval.validate_checksum(file_path, checksum_expected,
                                                 ChecksumAlgorithm.get(checksum_algorithm))
        if not valid_checksum:
            raise ValueError("Checksum of the SIP tar file is invalid.")
        else:
            task_log.info("SIP tar file delivery checksum verified.")
    else:
        task_log.warn("Delivery file does not exist. SIP checksum is not verified.")

    def item_exists(descr, item):
        if os.path.exists(item):
            task_log.info("%s found: %s" % (descr, os.path.abspath(item)))
            return True
        else:
            task_log.error(("%s missing: %s" % (descr, os.path.abspath(item))))
            return False

    # working directory must contain an IP or the IP must be in a subfolder
    ip_path = get_first_ip_path(working_dir)
    if not ip_path:
        raise ValueError("No information package found")
    else:
        task_log.info("Information package folder: %s" % ip_path)

    # package METS file validation
    root_mets_path = os.path.join(ip_path, "METS.xml")
    mets_schema_file = os.path.join(root_dir, "static/schemas/IP.xsd")
    premis_schema_file = os.path.join(root_dir, "static/schemas/premis-v3-0.xsd")
    root_mets_validator = MetsValidation(ip_path, mets_schema_file=mets_schema_file,
                                         premis_schema_file=premis_schema_file)
    if root_mets_validator.validate_mets(root_mets_path):
        task_log.info("Information package METS file validated successfully: %s" % root_mets_path)
    else:
        task_log.info("Information package METS file validated successfully: %s" % root_mets_path)
        # task_log.error("Error validating package METS file: %s" % root_mets_path)
        # for err in root_mets_validator.validation_errors:
        #    task_log.error(str(err))
        # raise ValueError("Error validating package METS file. See processing log for details.")

    # representations folder is mandatory
    representations_path = os.path.join(ip_path, "representations")
    if not item_exists("Representations folder", representations_path):
        raise ValueError("No representation folder found")

    valid = True
    # representation METS file validation
    mets_validator = None
    if os.path.exists(os.path.join(ip_path, "representations")):
        for name in os.listdir(representations_path):
            rep_path = os.path.join(representations_path, name)
            if os.path.isdir(rep_path):
                mets_validator = MetsValidation(rep_path)
                v = mets_validator.validate_mets(os.path.join(rep_path, 'METS.xml'))
                # if not v:
                #    raise ValueError("Representation METS file is not valid: %s" % os.path.join(rep_path, 'METS.xml'))

    csip_validation = CSIPValidation()
    csip_validation.validate(ip_path)
    for log_line in csip_validation.get_log_lines():
        if log_line["type"] == "ERROR":
            task_log.error(log_line["message"])
        else:
            task_log.info(log_line["message"])

    # IP is valid if all METS files are valid
    if mets_validator and not valid:
        for error in mets_validator.validation_errors:
            task_log.error(error)
    if not valid:
        raise ValueError("Not valid!")

    return json.dumps(task_context)


@app.task(bind=True, name="descriptive_metadata_validation")
@requires_parameters("uid")
@task_logger
def descriptive_metadata_validation(_, context, task_log):
    task_context = json.loads(context)
    working_dir = get_working_dir(task_context["uid"])
    metadata_dir = os.path.join(working_dir, 'metadata/')
    task_log.info("Looking for EAD metadata files in metadata directory: %s" % metadata_dir)

    # "warning" state for validation errors
    try:
        md_files_valid = []
        for filename in find_files(metadata_dir, metadata_file_pattern_ead):
            path, md_file = os.path.split(filename)
            task_log.info("Found EAD file '%s'" % md_file)
            md_files_valid.append(validate_ead_metadata(path, md_file, None, task_log))
        if len(md_files_valid) == 0:
            task_log.info("No EAD metadata files found.")
        valid = False not in md_files_valid
        if valid:
            task_log.info("Descriptive metadata validated successfully.")
    except Exception as err:
        logger.error(err)
    return json.dumps(task_context)


@app.task(bind=True, name="aip_migrations")
@requires_parameters("uid")
@task_logger
def aip_migrations(self, context, task_log):
    software = "earkweb"
    task_context = json.loads(context)
    working_dir = get_working_dir(task_context["uid"])
    # make metadata/earkweb dir for temporary files
    if not os.path.exists(os.path.join(working_dir, 'metadata/earkweb')):
        os.makedirs(os.path.join(working_dir, 'metadata/earkweb'))
    if not os.path.exists(os.path.join(working_dir, 'metadata/earkweb/migrations')):
        os.makedirs(os.path.join(working_dir, 'metadata/earkweb/migrations'))

    # create xml file for migration logging
    migration_root = objectify.Element('migrations', attrib={'source': 'source representation',
                                                             'target': 'target representation',
                                                             'total': ''})

    # migration policy
    pdf = ['fmt/14', 'fmt/15', 'fmt/16', 'fmt/17', 'fmt/18', 'fmt/19', 'fmt/20', 'fmt/276']
    cli_execution = CliExecution(['ghostscript', '-version'])
    pdf_software = cli_execution.execute()  # Ghostscript version
    gif = ['fmt/3', 'fmt/4']

    cli_execution = CliExecution(['convert', '-version'])
    image_software = cli_execution.execute()  # ImageMagick version

    # list of all representations in submission folder
    rep_path = os.path.join(working_dir, 'representations/')
    replist = []
    for repdir in os.listdir(rep_path):
        replist.append(repdir)

    # begin migrations
    total = 0

    jobs_queue = []

    # start migrations from every representation
    for rep in replist:
        source_rep_data = '%s/data' % rep
        migration_source = os.path.join(rep_path, source_rep_data)
        # migration_target = ''
        # target_rep = ''
        outputfile = ''

        # Unix-style pattern matching: if representation directory is in format of <name>_mig-<number>,
        # the new representation will be <number> + 1. Else, it is just <name>_mig-1.
        if fnmatch.fnmatch(rep, '*_mig-*'):
            rep, iteration = rep.rsplit('_mig-', 1)
            target_rep = '%s_mig-%s' % (rep, (int(iteration) + 1).__str__())
            target_rep_data = 'representations/%s/data' % target_rep
            migration_target = os.path.join(working_dir, target_rep_data)
        else:
            target_rep = '%s_mig-%s' % (rep, '1')
            target_rep_data = 'representations/%s/data' % target_rep
            migration_target = os.path.join(working_dir, target_rep_data)

        # needs to walk from top-level dir of representation data
        for directory, subdirectories, filenames in os.walk(migration_source):
            for filename in filenames:
                # fido, file format identification
                identification = FormatIdentification()
                fido_result = identification.identify_file(os.path.join(directory, filename))
                self.args = ''
                if fido_result in pdf:
                    software = pdf_software
                    task_log.info('File %s is queued for migration to PDF/A.' % filename)
                    outputfile = "%s.pdf" % filename.rsplit('.', 1)[0]
                    cliparams = {'output_file': '-sOutputFile=' + os.path.join(migration_target, filename),
                                 'input_file': os.path.join(directory, filename)}
                    cli_command = CliCommand("pdftopdfa", commands["pdftopdfa"])
                    self.args = cli_command.get_command(cliparams)
                elif fido_result in gif:
                    software = image_software
                    task_log.info('File %s is queued for migration to TIFF.' % filename)
                    outputfile = "%s.tiff" % filename.rsplit('.', 1)[0]
                    cliparams = {'input_file': os.path.join(directory, filename),
                                 'output_file': os.path.join(migration_target, outputfile)}

                    self.args = CliCommand('totiff', cliparams)
                else:
                    task_log.info('No policy rule applies to file %s, fido result: %s. No file format migration.'
                                  % (filename, fido_result))

                if self.args != '':
                    task_id = uuid.uuid4().__str__()

                    # create folder for new representation (if it doesnt exist already)
                    if not os.path.exists(migration_target):
                        os.makedirs(migration_target)

                    # create folder for migration process task "feedback" (if it doesnt exist)
                    if not os.path.exists(
                            os.path.join(working_dir, 'metadata/earkweb/migrations/%s') % target_rep):
                        os.makedirs(os.path.join(working_dir, 'metadata/earkweb/migrations/%s') % target_rep)

                    # queue the MigrationProcess task
                    try:
                        details = {'filename': filename,
                                   'source': migration_source,
                                   'target': migration_target,
                                   'targetrep': target_rep,
                                   'taskid': task_id,
                                   'commandline': self.args}

                        # use kwargs, those can be seen in Celery Flower
                        jobs_queue.append(file_migration.s(details))

                        task_log.info('Migration queued for %s.' % filename)
                    except Exception as e:
                        task_log.error('Migration task %s for file %s could not be queued: %s' % (task_id, filename, e))

                    # migration.xml entry - need this for Premis creation. Can put additional stuff here if desired.
                    objectify.SubElement(migration_root, 'migration', attrib={'file': filename,
                                                                              'output': outputfile,
                                                                              'sourcedir': migration_source,
                                                                              'targetdir': migration_target,
                                                                              'targetrep': target_rep,
                                                                              'taskid': task_id,
                                                                              'status': 'queued',
                                                                              'starttime': current_timestamp(),
                                                                              'agent': software})
                    total += 1
                else:
                    pass

    jobs = group(jobs_queue)
    async_res = jobs.apply_async()

    # wait for all migrations to finish
    while not all(res.status == "SUCCESS" for res in async_res.results):
        num_success = sum(res.status == "SUCCESS" for res in async_res.results)
        logger.info("Migration running [%d/%d] ..." % (num_success, len(async_res.results)))
        time.sleep(5)

    # create migrations result xml file
    migration_root.set('total', total.__str__())
    migrations_xml_content = etree.tostring(migration_root, encoding='UTF-8', pretty_print=True, xml_declaration=True)
    xml_path = os.path.join(working_dir, 'metadata/earkweb/migrations.xml')
    with open(xml_path, 'wb') as output_file:
        output_file.write(migrations_xml_content)

    # copy xml schemas
    try:
        # copy schema files
        schemalist = os.listdir(os.path.join(root_dir, 'static/schemas'))
        if not os.path.exists(os.path.join(working_dir, 'schemas')):
            os.mkdir(os.path.join(working_dir, 'schemas'))
        for schemafile in schemalist:
            if os.path.isfile(os.path.join(root_dir, 'static/schemas/%s' % schemafile)):
                shutil.copy2(os.path.join(root_dir, 'static/schemas/%s' % schemafile),
                             os.path.join(working_dir, 'schemas'))
    except OSError:
        task_log.error('Error when copying schema files.')

    # schema file location for Mets generation
    schemas = os.path.join(working_dir, 'schemas')

    aip_representations_dir = os.path.join(working_dir, 'representations')
    if os.path.exists(aip_representations_dir):
        for repdir in os.listdir(aip_representations_dir):
            try:
                rep_path = os.path.join(working_dir, 'representations/%s' % repdir)
                premis_info = {'info': os.path.join(working_dir, 'metadata/earkweb/migrations.xml')}
                premisgen = PremisGenerator(rep_path)
                premisgen.createMigrationPremis(premis_info)
                task_log.info('Generated a Premis file for the representation %s.' % repdir)
            except IOError:
                task_log.error('Premis generation for representation %s failed.' % repdir)

            # for every REPRESENTATION without METS file:
            task_log.info("reps: %s" % os.listdir(os.path.join(working_dir, 'representations')))
            for rdir in os.listdir(os.path.join(working_dir, 'representations')):
                try:
                    rep_path = os.path.join(working_dir, 'representations/%s' % rdir)
                    mets_data = {'packageid': rdir,
                                 'type': 'AIP',
                                 'schemas': schemas,
                                 'parent': ''}
                    metsgen = MetsGenerator(rep_path)
                    metsgen.createMets(mets_data)

                    task_log.info('Generated a Mets file for representation %s.' % rdir)
                except IOError:
                    task_log.error('Mets generation for representation %s failed.' % rdir)

    return json.dumps(task_context)


@app.task(bind=True, name="file_migration")
def file_migration(self, details):
    # filename = details['filename']
    # taskid = details['taskid']
    self.targetrep = details['targetrep']
    self.args = details['commandline']

    if self.args != '':
        cli_execution = CliExecution(self.args)
        cli_execution.execute()
    else:
        raise ValueError("Missing parameters")
    return True


@app.task(bind=True, name="aip_record_events")
@requires_parameters("uid", "package_name", "identifier")
@task_logger
def aip_record_events(_, context, task_log):
    task_context = json.loads(context)
    identifier = task_context["identifier"]
    working_dir = get_working_dir(task_context["uid"])
    try:
        premis = PremisCreator(working_dir)
        premis.add_agent("urn:eark:software:earkweb:v1.3", "earkweb", "software")
        premis.add_event("urn:eark:event:ingest:{0}", "success", "urn:eark:software:earkweb:v1.3", identifier)
        premis.create("metadata/preservation/", "event", "ingest")
    except Exception as err:
        task_log.debug(err)
        tb = traceback.format_exc()
        task_log.debug(tb)
    return json.dumps(task_context)


@app.task(bind=True, name="aip_record_structure")
@requires_parameters("uid", "package_name", "identifier")
@task_logger
def aip_record_structure(_, context, task_log):
    task_context = json.loads(context)
    working_dir = get_working_dir(task_context["uid"])
    try:
        # copy schema files
        schemalist = os.listdir(os.path.join(root_dir, 'static/schemas'))
        if not os.path.exists(os.path.join(working_dir, 'schemas')):
            os.mkdir(os.path.join(working_dir, 'schemas'))
        for schemafile in schemalist:
            if os.path.isfile(os.path.join(root_dir, 'static/schemas/%s' % schemafile)):
                shutil.copy2(os.path.join(root_dir, 'static/schemas/%s' % schemafile),
                             os.path.join(working_dir, 'schemas'))
    except IOError:
        task_log.error('Error when copying schema files.')

    try:
        # schema file location for Mets generation
        schemas = os.path.join(working_dir, 'schemas')

        identifier = task_context['identifier']

        parent = task_context['parent_id'] if 'parent_id' in task_context else ""

        mets_data = {'packageid': identifier,
                     'type': 'AIP',
                     'schemas': schemas,
                     'parent': parent}

        metsgen = MetsGenerator(working_dir)
        metsgen.createMets(mets_data)

        # get identifier_map from context
        identifier_map = task_context['identifier_map'] if 'identifier_map' in task_context else None
        if identifier_map:
            # check if packagename is in the identifier map
            packagename = task_context['package_name']
            if packagename in identifier_map:
                identifier = identifier_map[packagename]
                task_log.info("Provided identifier assigned: %s" % identifier)
            else:
                raise ValueError("Cannot find uuid for package name %s in provided identifier_map" % packagename)

            # parse submission SIP mets
            parser = etree.XMLParser(resolve_entities=False, remove_blank_text=True, strip_cdata=False)
            sip_mets_path = os.path.join(working_dir, 'submission', 'METS.xml')
            # print sip_mets_path
            sip_parse = etree.parse(sip_mets_path, parser)
            sip_root = sip_parse.getroot()

            # parse package AIP METS and append children and parent structMaps
            aip_mets_path = os.path.join(working_dir, 'METS.xml')
            aip_parse = etree.parse(aip_mets_path, parser)
            aip_root = aip_parse.getroot()

            # get children structMap and replace the urn:uuid:packagename with corresponding urn:uuid:uuid
            children_map = sip_root.find("%s[@LABEL='child %s']" % (q(METS_NS, 'structMap'), 'SIP'))
            if children_map is not None:
                children_map.set('LABEL', 'child AIP')
                children_div = children_map.find("%s[@LABEL='child %s identifiers']" % (q(METS_NS, 'div'), 'SIP'))
                children_div.set('LABEL', 'child AIP identifiers')
                children = children_div.findall("%s[@LABEL='child %s']" % (q(METS_NS, 'div'), 'SIP'))
                for child in children:
                    child.set('LABEL', 'child AIP')
                    mptr = child.find("%s" % q(METS_NS, 'mptr'))
                    urn = mptr.get(q(XLINK_NS, 'href'))
                    urn = urn.split('urn:uuid:', 1)[1]
                    unique_id = identifier_map[urn]
                    mptr.set(q(XLINK_NS, 'href'), 'urn:uuid:' + unique_id)
                    mptr.set(q(XLINK_NS, 'title'), 'Referencing a child AIP.')
                aip_root.append(children_map)
            # get parents structMap and replace the urn:uuid:packagename with corresponding urn:uuid:uuid
            parents_map = sip_root.find("%s[@LABEL='parent %s']" % (q(METS_NS, 'structMap'), 'SIP'))
            if parents_map is not None:
                parents_map.set('LABEL', 'parent AIP')
                parents_div = parents_map.find("%s[@LABEL='parent %s identifiers']" % (q(METS_NS, 'div'), 'SIP'))
                parents_div.set('LABEL', 'parent AIP identifiers')
                parents = parents_div.findall("%s[@LABEL='parent %s']" % (q(METS_NS, 'div'), 'SIP'))
                for parent in parents:
                    parent.set('LABEL', 'parent AIP')
                    mptr = parent.find("%s" % q(METS_NS, 'mptr'))
                    urn = mptr.get(q(XLINK_NS, 'href'))
                    urn = urn.split('urn:uuid:', 1)[1]
                    unique_id = identifier_map[urn]
                    mptr.set(q(XLINK_NS, 'href'), 'urn:uuid:' + unique_id)
                    mptr.set(q(XLINK_NS, 'title'), 'Referencing a parent AIP.')
                aip_root.append(parents_map)
            output_xml = etree.tostring(aip_root, encoding='UTF-8', pretty_print=True, xml_declaration=True)
            with open(aip_mets_path, 'w') as output_file:
                output_file.write(output_xml)
        task_log.info('METS updated with AIP content.')
    except Exception as err:
        task_log.debug(err)
        tb = traceback.format_exc()
        task_log.debug(tb)
    return json.dumps(task_context)


@app.task(bind=True, name="aip_packaging")
@requires_parameters("package_name", "uid", "identifier", "org_nsid")
@task_logger
def aip_packaging(self, context, task_log):
    task_context = json.loads(context)
    package_name = task_context["package_name"]
    identifier = task_context["identifier"].strip()
    uid = task_context["uid"]
    working_dir = get_working_dir(uid)

    # pair tree storage
    pts = PairtreeStorage(config_path_storage)
    # archive file name
    safe_identifier_name = to_safe_filename(identifier)
    archive_file = "%s.tar" % safe_identifier_name

    aip_package_path = os.path.join(working_dir, archive_file)

    tar = tarfile.open(aip_package_path, "w:")
    task_log.info("Packaging working directory: %s" % working_dir)
    total = sum([len(files) for (root, dirs, files) in walk(working_dir)])
    task_log.info("Total number of files in working directory %d" % total)
    i = 0
    excludes = ["%s.tar" % package_name, "%s.xml" % package_name, archive_file]
    for subdir, dirs, files in os.walk(working_dir):

        for directory in dirs:
            entry = os.path.join(subdir, directory)

            if not os.listdir(entry):
                tar.add(entry, arcname=os.path.join(safe_identifier_name, os.path.relpath(entry, working_dir)))

        for file in files:
            if not file in excludes:
                entry = os.path.join(subdir, file)
                tar.add(entry, arcname=os.path.join(safe_identifier_name, os.path.relpath(entry, working_dir)))
                if i % 10 == 0:
                    perc = (i * 100) / total
                    logger.debug("Packaging progress: %d" % perc)
                    # todo: activate
                    # self.update_state(state='PROGRESS', meta={'process_percent': perc})
            i += 1
    tar.close()

    self.update_state(state='PROGRESS', meta={'process_percent': 100})

    return json.dumps(task_context)


@app.task(bind=True, name="create_manifest")
@requires_parameters("uid")
@task_logger
def create_manifest(_, context, task_log):
    time.sleep(2)
    task_context = json.loads(context)
    working_dir = get_working_dir(task_context["uid"])
    manifest_creation = ManifestCreation(working_dir)
    manifest_file = os.path.join(working_dir, "manifest.txt")
    manifest_creation.create_manifest(working_dir, manifest_file)
    if os.path.exists(manifest_file):
        task_log.info("Manifest file created at: %s" % manifest_file)
    else:
        task_log.warn("Error creating manifest file")
    return json.dumps(task_context)


@app.task(bind=True, name="store_original_sip")
@requires_parameters("uid", "package_name", "identifier")
@task_logger
def store_original_sip(_, context, task_log):
    task_context = json.loads(context)
    identifier = task_context["identifier"].strip()
    package_name = task_context["package_name"]
    uid = task_context["uid"]
    working_dir = get_working_dir(uid)

    sip = "%s.tar" % package_name
    sip_path = os.path.join(working_dir, sip)
    if not os.path.exists(sip_path):
        raise ValueError("SIP not found: %s" % sip_path)

    # store original sip
    pts = PairtreeStorage(config_path_storage)
    version_0 = VersionDirFormat % 0
    task_context["version"] = version_0
    data_dir = os.path.join(pts.get_dir_path_from_id(identifier), "data")
    storage_dir = os.path.join(data_dir, version_0)
    task_context["storage_dir"] = storage_dir
    archive_file = sip
    aip_path = os.path.join(storage_dir, archive_file)
    os.makedirs(storage_dir, exist_ok=True)
    shutil.copy2(sip_path, aip_path)

    write_inventory(identifier, version_0, data_dir, aip_path, archive_file)

    # check successful creation of original sip
    if not os.path.exists(aip_path):
        raise ValueError("AIP not created: %s" % aip_path)

    # persist state
    persist_state(identifier, version_0, storage_dir, archive_file, working_dir)

    return json.dumps(task_context)


@app.task(bind=True, name="store_aip")
@requires_parameters("uid", "package_name", "identifier")
@task_logger
def store_aip(_, context, task_log):
    task_context = json.loads(context)
    identifier = task_context["identifier"].strip()
    uid = task_context["uid"]
    working_dir = get_working_dir(uid)
    action = "update" if "is_update_task" in task_context and task_context["is_update_task"] else "ingest"

    # pairtree storage
    pts = PairtreeStorage(config_path_storage)

    # store aip file
    aip_file_name = "%s.tar" % to_safe_filename(identifier)
    source_aip_file = os.path.join(working_dir, aip_file_name)
    if not os.path.exists(source_aip_file):
        raise ValueError("Source AIP not found: %s" % source_aip_file)
    version = pts.store(identifier, source_aip_file)
    data_dir = os.path.join(pts.get_dir_path_from_id(identifier), "data")
    storage_dir = os.path.join(data_dir, version)
    aip_path = os.path.join(storage_dir, aip_file_name)
    task_context["version"] = version
    task_context["storage_dir"] = storage_dir

    # persist state
    patch_data = persist_state(identifier, version, storage_dir, aip_file_name, working_dir)

    # update status db
    try:
        response = update_status(uid, patch_data)
        if response.status_code == 200:
            task_log.info("Status information updated")
        else:
            task_log.warning("Status information not updated: %s (%d)" % (response.text, response.status_code))
    except requests.exceptions.ConnectionError as err:
        task_log.warning("Connection to API failed. Status was not updated.")

    # update ocfl inventory
    if action == "update":
        update_inventory(identifier, version, aip_path, aip_file_name, action)
    else:
        write_inventory(identifier, version, aip_path, aip_file_name)

    return json.dumps(task_context)


@app.task(bind=True, name="aip_indexing")
@requires_parameters("identifier")
@task_logger
def aip_indexing(_, context, task_log):
    task_context = json.loads(context)

    pts = PairtreeStorage(config_path_storage)
    identifier = task_context['identifier']
    version = pts.curr_version(task_context["identifier"])
    storage_dir = os.path.join(
        make_storage_data_directory_path(task_context["identifier"], config_path_storage),
        version
    )

    if not pts.identifier_object_exists(identifier):
        task_log.warn("Unable to index data set because it is not available in storage.")
        return json.dumps(task_context)

    # check solr server availability
    solr_server = SolrServer(solr_protocol, solr_host, solr_port)
    sq = SolrQuery(solr_server)
    solr_response = requests.get(sq.get_base_url(), verify=verify_certificate)
    if not solr_response.status_code == 200:
        task_log.warn("Information package cannot be indexed because SolR is not available at: %s" % sq.get_base_url())
        return json.dumps(task_context)

    # delete existing records
    submission_url = "%s://%s:%d/solr/storagecore1/update/?commit=true" % (solr_protocol, solr_host, solr_port)
    delete_response = requests.post(submission_url, data="<delete><query>package:\"%s\"</query></delete>" % identifier,
                                    headers={'Content-Type': 'text/xml'}, verify=verify_certificate)
    if delete_response.status_code == 200:
        task_log.info("Index records deleted for package: %s" % identifier)
    else:
        task_log.warn("Index records cannot be removed. Response code %s, message: %s" % (
        delete_response.status_code, delete_response.text))

    # initialize solr client
    solr_client = SolrClient(solr_server, "storagecore1")
    # store_dir = os.path.join(storage_dir)
    package_files = list_files_in_dir(storage_dir)
    for package_file in package_files:
        if package_file.endswith(".tar"):
            task_log.info("Indexing %s" % package_file)
            results = solr_client.post_tar_file(os.path.join(storage_dir, package_file),
                                                identifier, version, default_reporter)
            task_log.info("Total number of files posted: %d" % len(results))
            num_ok = sum(1 for result in results if result['status'] == 200)
            task_log.info("Number of files posted successfully: %d" % num_ok)
            num_failed = sum(1 for result in results if result['status'] != 200)
            task_log.info("Number of plain documents: %d" % num_failed)

    return json.dumps(task_context)


@app.task(bind=True, name="solr_update_metadata")
@requires_parameters("uid", "package_name", "identifier")
@task_logger
def solr_update_metadata(_, context, task_log):
    task_context = json.loads(context)
    working_dir = get_working_dir(task_context["uid"])
    task_log.info("Updating SolR records with metadata.")

    submiss_dir = 'submission'
    md_dir = 'metadata'
    md_subdir_descr = 'descriptive'

    descriptive_md_dir = os.path.join(md_dir, md_subdir_descr)
    submiss_descr_md_dir = os.path.join(working_dir, submiss_dir, descriptive_md_dir)
    overruling_metadata_dir = os.path.join(working_dir, md_dir, submiss_dir, descriptive_md_dir)

    task_log.info("Looking for EAD metadata files in metadata directory: %s"
                  % strip_prefixes(submiss_descr_md_dir, working_dir))

    # "warning" state for validation errors

    md_files_valid = []
    for filename in find_files(submiss_descr_md_dir, metadata_file_pattern_ead):
        md_path, md_file = os.path.split(filename)
        task_log.info("Found descriptive metadata file in submission folder: '%s'" % md_file)
        task_log.info(
            "Looking for overruling version in AIP metadata folder: '%s'"
            % strip_prefixes(overruling_metadata_dir, working_dir))
        overruling_md_file = os.path.join(overruling_metadata_dir, md_file)
        validation_md_path = md_path
        if os.path.exists(overruling_md_file):
            task_log.info(
                "Overruling version of descriptive metadata file found: %s" %
                strip_prefixes(overruling_md_file, working_dir))
            validation_md_path = overruling_metadata_dir
        else:
            task_log.info("No overruling version of descriptive metadata file in AIP metadata folder found.")
        task_log.info("Using EAD metadata file: %s" % filename)

        extract_defs = [
            {'ead_element': 'unittitle', 'solr_field': 'eadtitle_s'},
            {'ead_element': 'unitdate', 'solr_field': 'eaddate_s'},
            {'ead_element': 'unitid', 'solr_field': 'eadid_s'},
            {'ead_element': 'unitdatestructured', 'solr_field': 'eaddatestructuredfrom_dt',
             'text_access_path': 'ead:datesingle'},
            {'ead_element': 'unitdatestructured', 'solr_field': 'eaddatestructuredto_dt',
             'text_access_path': 'ead:datesingle'},
            {'ead_element': 'unitdatestructured', 'solr_field': 'eaddatestructuredfrom_dt',
             'text_access_path': 'ead:daterange/ead:fromdate'},
            {'ead_element': 'unitdatestructured', 'solr_field': 'eaddatestructuredto_dt',
             'text_access_path': 'ead:daterange/ead:todate'},
            {'ead_element': 'origination', 'solr_field': 'eadorigination_s', 'text_access_path': '*/ead:part'},
            {'ead_element': 'abstract', 'solr_field': 'eadabstract_t', 'text_access_path': None},
            {'ead_element': 'accessrestrict', 'solr_field': 'eadaccessrestrict_s', 'text_access_path': 'ead:head'},
            {'ead_element': '[Cc][0,1][0-9]', 'solr_field': 'eadclevel_s', 'text_access_path': 'level',
             'is_attribute': True},
        ]
        result = field_namevalue_pairs_per_file(extract_defs, validation_md_path, filename)

        # solr interface configuration
        solr_base_url = '%s://%s:%s/solr/%s/' % (solr_protocol, solr_host, solr_port, solr_core)
        solr = SolrUtility()
        if solr.availability(solr_base_url=solr_base_url, solr_unique_key='id') is 200:
            for k in result.keys():
                safe_urn_identifier = (task_context['identifier']).replace(":", "\\:")
                entry_path = k.replace(working_dir, '')
                identifier = solr.get_doc_id_from_path(safe_urn_identifier, entry_path)
                status_code = solr.update_document(identifier, result[k])
                task_log.info("Solr document %s updated for file item: %s (return code: %s)"
                              % (identifier, entry_path, status_code))
            md_files_valid.append(validate_ead_metadata(validation_md_path, md_file, None))
        else:
            task_log.error('Solr %s is not reachable, file was not updated!' % solr_base_url)
    if len(md_files_valid) == 0:
        task_log.info("No descriptive metadata files found.")
    valid = False not in md_files_valid
    if valid:
        task_log.info("Descriptive metadata validated successfully.")

    # reload the Solr core, because the index was changed by adding new fields
    requests.get('%s://%s:%s/solr/admin/cores?action=RELOAD&core=%s' % (solr_protocol, solr_host, solr_port, solr_core))


@app.task(bind=True, name="dip_acquire_aips")
@requires_parameters("selected_aips")
@task_logger
def dip_acquire_aips(self, context, task_log):
    task_context = json.loads(context)
    working_dir = get_working_dir(task_context["uid"])

    # create dip working directory
    if not os.path.exists(working_dir):
        os.mkdir(working_dir)

    total_bytes_read = 0
    aip_total_size = 0

    selected_aips = task_context["selected_aips"]
    print("selected AIPs: %s" % selected_aips)
    for aip_source in selected_aips.values():
        if not os.path.exists(aip_source):
            raise ValueError("Missing AIP source %s" % aip_source)
        else:
            aip_total_size += fsize(aip_source)

    # task_context["selected_aips"] = selected_aips.keys()

    task_log.info("DIP total size: %d" % aip_total_size)
    # for aip in dip.aips.all():
    for aip_identifier, aip_source in selected_aips.iteritems():
        aip_source_size = fsize(aip_source)
        partial_progress_reporter = partial(default_reporter, self)
        package_extension = aip_source.rpartition('.')[2]
        aip_in_dip_work_dir = os.path.join(working_dir, ("%s.%s" % (aip_identifier, package_extension)))
        task_log.info("Source: %s (%d)" % (aip_source, aip_source_size))
        task_log.info("Target: %s" % aip_in_dip_work_dir)
        with open(aip_in_dip_work_dir, 'wb') as target_file:
            for chunk in FileBinaryDataChunks(
                    aip_source, 65536, partial_progress_reporter
            ).chunks(total_bytes_read, aip_total_size):
                target_file.write(chunk)
            total_bytes_read += aip_source_size
            target_file.close()
        check_transfer(aip_source, aip_in_dip_work_dir)
    # self.update_state(state='PROGRESS', meta={'process_percent': 100})

    return json.dumps(task_context)


@app.task(bind=True, name="dip_acquire_dependant_aips")
@requires_parameters("storage_dest")
@task_logger
def dip_acquire_dependant_aips(_, context, task_log):
    task_context = json.loads(context)
    working_dir = get_working_dir(task_context["uid"])

    # create dip working directory
    if not os.path.exists(working_dir):
        os.mkdir(working_dir)

    if not task_context['storage_dest']:
        raise ValueError("Storage root must be defined to execute this task.")

    selected_aips = task_context["selected_aips"]
    task_log.info("selected AIPs: %s" % selected_aips)
    package_extension = "tar"
    aip_parents = []
    for aip_identifier, aip_source in selected_aips.iteritems():
        package_extension = aip_source.rpartition('.')[2]
        head_parent = None
        while True:
            parent_uuid = get_aip_parent(working_dir, aip_identifier, package_extension)
            if parent_uuid:
                # get the parent from storage
                get_package_from_storage(working_dir, parent_uuid, package_extension)
                aip_identifier = parent_uuid
                head_parent = parent_uuid
            else:
                aip_parents.append(head_parent)
                break
    for aip_parent in aip_parents:
        get_children_from_storage(working_dir, aip_parent, package_extension)
    # self.update_state(state='PROGRESS', meta={'process_percent': 100})
    return json.dumps(task_context)


@app.task(bind=True, name="dip_extract_aips")
@requires_parameters("selected_aips")
@task_logger
def dip_extract_aips(_, context, task_log):
    task_context = json.loads(context)
    working_dir = get_working_dir(task_context["uid"])
    selected_aips = task_context["selected_aips"]
    for selected_aip in selected_aips:
        task_log.info(str(selected_aip))

    # create dip working directory
    if not os.path.exists(working_dir):
        os.mkdir(working_dir)

    # packagename is identifier of the DIP creation process
    selected_aips = task_context["selected_aips"]

    total_members = 0
    for aip_identifier, aip_source in selected_aips.iteritems():
        if not os.path.exists(aip_source):
            raise ValueError("Missing AIP source %s" % aip_source)
        else:
            package_extension = aip_source.rpartition('.')[2]
            aip_in_dip_work_dir = os.path.join(working_dir, ("%s.%s" % (aip_identifier, package_extension)))
            tar_obj = tarfile.open(name=aip_in_dip_work_dir, mode='r', encoding='utf-8')
            members = tar_obj.getmembers()
            total_members += len(members)
            tar_obj.close()

    task_log.info("Total number of entries: %d" % total_members)
    total_processed_members = 0
    for aip_identifier, aip_source in selected_aips.iteritems():
        package_extension = aip_source.rpartition('.')[2]
        aip_in_dip_work_dir = os.path.join(working_dir, ("%s.%s" % (aip_identifier, package_extension)))
        task_log.info("Extracting: %s" % aip_in_dip_work_dir)
        tar_obj = tarfile.open(name=aip_in_dip_work_dir, mode='r', encoding='utf-8')
        members = tar_obj.getmembers()
        current_package_total_members = 0
        for member in members:
            if total_processed_members % 10 == 0:
                perc = (total_processed_members * 100) / total_members
                logger.debug("Progress: %d" % perc)
                # self.update_state(state='PROGRESS', meta={'process_percent': perc})
            tar_obj.extract(member, working_dir)
            task_log.info(("File extracted: %s" % member.name), display=False)
            total_processed_members += 1
            current_package_total_members += 1

        task_log.info("Untar of %d items from package %s finished" % (current_package_total_members, aip_identifier))
    task_log.info(("Untar of %d items in total finished" % total_processed_members))
    # self.update_state(state='PROGRESS', meta={'process_percent': 100})

    # Add related AIPs to PREMIS based on the extracted AIP directories available in the working directory
    premis_path = os.path.join(working_dir, 'metadata/preservation/premis.xml')
    extracted_aips = get_mets_objids_from_basedir(working_dir)
    if os.path.isfile(premis_path):
        dip_premis = DIPPremis(premis_path)
        dip_premis.add_related_aips(extracted_aips, 'DIPAcquireAIPs')
        with open(premis_path, 'w') as output_file:
            output_file.write(str(dip_premis))
    task_log.info("Related AIPs added to PREMIS: %s" % ", ".join(extracted_aips))

    return json.dumps(task_context)


@app.task(bind=True, name="dip_package_metadata_creation")
@requires_parameters("selected_aips")
@task_logger
def dip_package_metadata_creation(_, context, task_log):
    task_context = json.loads(context)
    working_dir = get_working_dir(task_context["uid"])
    reps_path = os.path.join(working_dir, 'representations')
    if os.path.isdir(reps_path):
        for name in os.listdir(reps_path):
            rep_path = os.path.join(reps_path, name)
            if os.path.isdir(rep_path):
                # Premis
                premisgen = PremisGenerator(rep_path)
                premisgen.createPremis()
                # Mets
                mets_data = {'packageid': task_context["uid"],
                             'type': 'DIP',
                             'schemas': os.path.join(working_dir, 'schemas'),
                             'parent': ''}
                metsgen = MetsGenerator(rep_path)
                metsgen.createMets(mets_data)
    else:
        task_log.info("No DIP representations found.")

    # Premis not needed as already existing
    # premisgen = PremisGenerator(working_dir)
    # premisgen.createPremis()

    # create DIP parent Mets
    mets_data = {'packageid': task_context["uid"],
                 'type': 'DIP',
                 'schemas': os.path.join(working_dir, 'schemas'),
                 'parent': ''}
    metsgen = MetsGenerator(working_dir)
    metsgen.createMets(mets_data)

    # copy schemas folder from extracted tar to root
    selected_aips = task_context["selected_aips"]
    src_schemas_folder = os.path.join(working_dir, selected_aips.keys()[0], 'schemas')
    dst_schemas_folder = os.path.join(working_dir, 'schemas')
    shutil.copytree(src_schemas_folder, dst_schemas_folder)

    return json.dumps(task_context)


@app.task(bind=True, name="dip_packaging")
@requires_parameters("identifier")
@task_logger
def dip_packaging(_, context, task_log):
    task_context = json.loads(context)
    working_dir = get_working_dir(task_context["uid"])

    # identifier (not uuid of the working directory) is used as first part of the tar file

    task_log.info("Packaging working directory: %s" % working_dir)

    dip_identifier = task_context['identifier']

    storage_file = os.path.join(working_dir, "%s.tar" % dip_identifier)
    tar = tarfile.open(storage_file, "w:")
    task_log.info("Creating archive: %s" % storage_file)

    item_list = ['metadata', 'representations', 'schemas', 'METS.xml']
    total = 0
    for item in item_list:
        pack_item = os.path.join(working_dir, item)
        if os.path.exists(pack_item):
            if os.path.isdir(pack_item):
                total += sum([len(files) for (root, dirs, files) in walk(pack_item)])
            else:
                total += 1
    task_log.info("Total number of files in working directory %d" % total)
    # log file is closed at this point because it will be included in the package,
    # subsequent log messages can only be shown in the gui
    # tl.log.close()
    i = 0
    for item in item_list:
        pack_item = os.path.join(working_dir, item)
        if os.path.exists(pack_item):
            if os.path.isdir(pack_item):
                for subdir, dirs, files in os.walk(pack_item):
                    for file in files:
                        if os.path.join(subdir, file):
                            entry = os.path.join(subdir, file)
                            arcname = dip_identifier + "/" + os.path.relpath(entry, working_dir)
                            tar.add(entry, arcname=arcname)
                            if i % 10 == 0:
                                perc = (i * 100) / total
                                logger.debug("Progress: %d" % perc)
                                # self.update_state(state='PROGRESS', meta={'process_percent': perc})
                        i += 1
            else:
                arcname = dip_identifier + "/" + os.path.relpath(pack_item, working_dir)
                tar.add(pack_item, arcname=arcname)
                if i % 10 == 0:
                    perc = (i * 100) / total
                    logger.debug("Progress: %d" % perc)
                    # self.update_state(state='PROGRESS', meta={'process_percent': perc})
                i += 1
    tar.close()
    task_log.info("Package created: %s" % storage_file)

    # self.update_state(state='PROGRESS', meta={'process_percent': 100})

    return json.dumps(task_context)


@app.task(bind=True, name="dip_store")
@requires_parameters("identifier")
@task_logger
def dip_store(_, context, task_log):
    task_context = json.loads(context)
    working_dir = get_working_dir(task_context["uid"])
    from config.configuration import config_path_storage
    if not os.path.exists(os.path.join(config_path_storage, "pairtree_version0_1")):
        raise ValueError("Storage path is not a pairtree storage directory.")
    if "identifier" not in task_context:
        raise ValueError("DIP identifier is not defined.")
    package_identifier = task_context["identifier"].strip()
    package_file_name = "%s.tar" % task_context["identifier"]
    package_file_path = os.path.join(working_dir, package_file_name)
    if not os.path.exists(package_file_path):
        raise ValueError("DIP TAR package does not exist: %s" % package_file_path)

    pts = PairtreeStorage(config_path_storage)
    pts.store(package_identifier, package_file_path)

    package_object_path = pts.get_object_path(package_identifier)
    if os.path.exists(package_object_path):
        task_log.info('Storage path: %s' % package_object_path)
        if ChecksumFile(package_file_path).get(ChecksumAlgorithm.SHA256) == ChecksumFile(package_object_path).get(
                ChecksumAlgorithm.SHA256):
            task_log.info("Checksum verification completed, the package was transmitted successfully.")
            task_context["storage_loc"] = package_object_path
        else:
            task_log.error("Checksum verification failed, an error occurred while trying to transmit the package.")

    return json.dumps(task_context)


@app.task(bind=True, name="dip_create_access_copy")
@requires_parameters("identifier")
@task_logger
def dip_create_access_copy(self, context, task_log):
    task_context = json.loads(context)
    working_dir = get_working_dir(task_context["uid"])
    from config.configuration import config_path_storage
    from config.configuration import dip_download_base_url
    from config.configuration import dip_download_path

    if not os.path.exists(os.path.join(config_path_storage, "pairtree_version0_1")):
        raise ValueError("Storage path is not a pairtree storage directory.")
    if not ("identifier" in task_context.keys() and task_context["identifier"] != ""):
        raise ValueError("DIP identifier is not defined.")
    package_identifier = task_context["identifier"].strip()
    package_file_name = "%s.tar" % task_context["identifier"]
    package_file_path = os.path.join(working_dir, package_file_name)
    if not os.path.exists(package_file_path):
        raise ValueError("DIP TAR package does not exist: %s" % package_file_path)
    try:
        pts = PairtreeStorage(config_path_storage)
        package_object_path = pts.get_object_path(package_identifier)
        if os.path.exists(package_object_path):
            task_log.info('Storage path: %s' % package_object_path)
            random_token = randomword(8)
            access_dir = os.path.join(dip_download_path, random_token)
            os.makedirs(access_dir, exist_ok=True)
            access_file = os.path.join(access_dir, package_file_name)

            total_bytes_read = 0

            dip_total_size = fsize(package_object_path)

            task_log.info("DIP total size: %d" % dip_total_size)

            aip_source_size = fsize(package_object_path)
            partial_progress_reporter = partial(default_reporter, self)
            task_log.info("Source: %s (%d)" % (package_object_path, aip_source_size))
            task_log.info("Target: %s" % access_file)
            with open(access_file, 'wb') as target_file:
                for chunk in FileBinaryDataChunks(package_object_path, 65536, partial_progress_reporter).chunks(
                        total_bytes_read, dip_total_size):
                    target_file.write(chunk)
                total_bytes_read += aip_source_size
                target_file.close()
            check_transfer(package_object_path, access_file)

            # self.update_state(state='PROGRESS', meta={'process_percent': 100})

            random_url_part = os.path.join(random_token, package_file_name)
            if not dip_download_base_url.endswith('/'):
                dip_download_base_url += '/'
            download_url = "%s%s" % (dip_download_base_url, random_url_part)
            task_context["download_url"] = download_url

    except Exception as e:
        raise e
    return json.dumps(task_context)


@app.task(name="initialize_working_directory")
def initialize_working_directory(context):
    task_context = json.loads(context)
    check_required_params(task_context, ["package_name", "username"])
    package_name = task_context['package_name']
    username = task_context['username']
    uid = get_unique_id()
    working_dir = os.path.join(config_path_work, uid)
    os.makedirs(os.path.join(working_dir, 'distributions'), exist_ok=True)
    os.makedirs(os.path.join(working_dir, 'metadata'), exist_ok=True)
    InformationPackage.objects.create(work_dir=os.path.join(config_path_work, uid), uid=uid,
                                      package_name=package_name, user=username, version=0)
    InformationPackage.objects.get(uid=uid)
    task_context["uid"] = uid
    create_or_update_state_info_file(working_dir, task_context)
    return json.dumps(task_context)


@app.task(bind=True, name="checkout_working_copy_from_storage")
@requires_parameters("identifier", "uid")
@task_logger
def checkout_working_copy_from_storage(_, context, task_log):
    task_context = json.loads(context) if isinstance(context, str) else context
    uid = task_context['uid']
    identifier = task_context['identifier']

    task_log.info('Checking out archival information package: %s' % identifier)
    metadata_only = 'metadataonly' in task_context and task_context['metadataonly'] == "true"
    task_log.info('Check out metadata only: %s' % metadata_only)

    dpts = PairtreeStorage(config_path_storage)
    version = dpts.curr_version(identifier)
    archival_package_file = os.path.join(make_storage_data_directory_path(identifier, config_path_storage),
                                         version, to_safe_filename(identifier),
                                         "%s.tar" % to_safe_filename(identifier))

    work_dir = os.path.join(config_path_work, uid)

    shutil.copy2(archival_package_file, work_dir)
    for f in os.listdir(work_dir):
        if f.endswith(".tar"):
            extract_and_remove(os.path.join(work_dir, f), work_dir)

    extract_dir = os.path.join(work_dir, to_safe_filename(identifier))
    if not os.path.exists(extract_dir):
        raise ValueError("Directory with extracted content does not exist: %s" % extract_dir)

    # move extracted content one level higher to working directory
    for directory_item in os.listdir(extract_dir):
        if directory_item.endswith("processing.log"):
            target = os.path.join(work_dir, "processing_%s.log" % to_safe_filename(identifier))
        else:
            target = work_dir
        shutil.move(os.path.join(extract_dir, directory_item), target)

    if len(os.listdir(extract_dir)) == 0:
        shutil.rmtree(extract_dir)
    else:
        raise ValueError("Extraction directory cannot be removed because it is not empty")

    reset = 'reset' in task_context and task_context['reset']
    task_log.info('Reset AIP to SIP: %s' % reset)
    if reset:
        for f in os.listdir(work_dir):
            if not f == "submission":
                file_path = os.path.join(work_dir, f)
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                else:
                    os.unlink(file_path)
        submission_dir = os.path.join(work_dir, "submission")
        submission_representations = os.path.join(submission_dir, "representations")
        if not os.path.exists(submission_representations):
            raise ValueError("No representations found in submission folder.")
        shutil.move(submission_representations, work_dir)
        shutil.rmtree(submission_dir)

    create_or_update_state_info_file(work_dir, {"version": version, "identifier": identifier})
    return json.dumps(task_context)


@app.task(name="delete_representation_data_from_workdir")
def delete_representation_data_from_workdir(context):
    task_context = json.loads(context)
    check_required_params(task_context, ["uid", "representation_id"])

    uid = task_context['uid']
    representation_id = task_context['representation_id']

    work_dir = os.path.join(config_path_work, uid)
    distribution_dir = os.path.join(work_dir, representations_directory, representation_id)

    if os.path.exists(distribution_dir):
        shutil.rmtree(distribution_dir)

    return json.dumps(task_context)


@app.task(name="rename_representation_directory")
def rename_representation_directory(context):
    task_context = json.loads(context)
    check_required_params(task_context, ["uid", "current_representation_dir", "new_representation_dir"])

    uid = task_context['uid']
    current_representation_dirname = task_context['current_representation_dir']
    new_representation_dirname = task_context['new_representation_dir']

    work_dir = os.path.join(config_path_work, uid)
    current_representation_directory = os.path.join(work_dir, representations_directory, current_representation_dirname)
    new_representation_directory = os.path.join(work_dir, representations_directory, new_representation_dirname)

    if os.path.exists(current_representation_directory):
        shutil.move(current_representation_directory, new_representation_directory)
    else:
        os.makedirs(new_representation_directory)
    if not os.path.exists(new_representation_directory):
        raise ValueError("Process id: %s, renaming directory failed. The new directory does not exist: %s"
                         % (uid, new_representation_directory))
    return json.dumps(task_context)


@app.task(name="backend_available")
def backend_available():
    return 5 * 5
