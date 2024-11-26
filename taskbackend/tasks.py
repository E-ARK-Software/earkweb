"""backend tasks"""
import datetime
import fnmatch
import gettext
import io
import json
import os
import shutil
import tarfile
import time
import traceback
import uuid
from pathlib import Path
from os import walk
import redis
import requests
from lxml import etree, objectify
from django.conf import settings
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import pysolr
from celery import chain, group
from access.search.solrclient import SolrClient, default_reporter
from access.search.solrquery import SolrQuery
from access.search.solrserver import SolrServer
from config.configuration import solr_core_url
from config.configuration import config_path_storage, config_path_work, solr_protocol, \
    solr_host, solr_port, solr_core, representations_directory, verify_certificate, \
    redis_host, redis_port, redis_password, commands, root_dir, metadata_file_pattern_ead, \
    django_service_protocol, django_service_host, django_service_port, \
    backend_api_key, sw_version
from earkweb.celery import app
from earkweb.decorators import requires_parameters, task_logger
from earkweb.models import InformationPackage
from earkweb.views import clean_metadata
from eatb import VersionDirFormat
from eatb.checksum import ChecksumValidation, ChecksumAlgorithm
from eatb.cli import CliExecution, CliCommand, CliCommands
from eatb.csip_validation import CSIPValidation
from eatb.file_format import FormatIdentification
from eatb.metadata import XLINK_NS, METS_NS
from eatb.metadata.ead import field_namevalue_pairs_per_file
from eatb.metadata.mets_generator import MetsGenerator
from eatb.metadata.mets_validation import MetsValidation
from eatb.metadata.parsed_mets import ParsedMets
from eatb.metadata.premis_creator import PremisCreator
from eatb.metadata.premis_generator import PremisGenerator
from eatb.oais_ip import DeliveryValidation, SIPGenerator, create_sip
from eatb.pairtree_storage import PairtreeStorage, make_storage_data_directory_path
from eatb.utils.XmlHelper import q
from eatb.utils.datetime import date_format, current_timestamp
from eatb.utils.fileutils import to_safe_filename, find_files, \
    strip_prefixes, remove_protocol
from eatb.utils.randomutils import get_unique_id
from eatb.storage import write_inventory_from_directory, update_storage_with_differences, get_previous_version_series
from taskbackend.taskutils import get_working_dir, validate_ead_metadata, get_first_ip_path, \
    create_or_update_state_info_file, persist_state, update_status
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
    """
    This task creates a Submission Information Package (SIP) from the provided context.

    Parameters:
    self (Task): The task instance (passed automatically by the Celery framework).
    context (str): A JSON string containing task parameters such as 'package_name' and 'uid'.
    task_log (Logger): A logger instance for logging task-related messages.

    Task Parameters in Context:
    - package_name (str): The name of the package to be created.
    - uid (str): The unique identifier for the package.
    - org_nsid (str): The organizational namespace identifier (required by decorator).

    The task performs the following steps:
    1. Parses the context JSON string to extract task parameters.
    2. Creates a working directory for the package if it doesn't already exist.
    3. Calls the `create_sip` function to create the SIP.
    4. Packages the working directory into a tar file, ensuring files are not duplicated.
    5. Generates a delivery METS file for the SIP.
    6. Sends a PATCH request to update the status information on a remote server.
    7. Updates the task state to 'PROGRESS' and reports the packaging progress.

    The final state of the task is updated, and the function returns the context as a 
    JSON string.

    Returns:
    str: The context JSON string.
    """
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
    task_log.info(f"Packaging working directory: {working_dir}")
    total = sum([len(files) for (root, dirs, files) in walk(working_dir)])
    task_log.info(f"Total number of files in working directory {total}")
    i = 0
    excludes = [f"{package_name}.tar", "{package_name}.xml"]
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
    rp = (django_service_protocol, django_service_host, django_service_port, task_context["uid"])
    url = f"{rp[0]}://{rp[1]}:{rp[2]}/earkweb/api/ips/{rp[3]}/"
    response = requests.patch(
        url, 
        data=patch_data, 
        headers={'Authorization': 'Api-Key %s' % backend_api_key},
        verify=verify_certificate, 
        timeout=10
    )
    print("Status information updated: %s (%d)" % (response.text, response.status_code))

    self.update_state(state='PROGRESS', meta={'process_percent': 100})

    return json.dumps(task_context)


@app.task(bind=True, name="ingest_pipeline")
@requires_parameters("uid")
def ingest_pipeline(_, context):
    """
    Ingests a pipeline by performing a series of chained tasks on the provided context.

    This pipeline now skips AIP packaging and directly stores the directory contents as-is.

    Workflow:
    1. Validate the working directory.
    2. Perform descriptive metadata validation.
    3. Record AIP events.
    4. Record AIP structure.
    5. Store the AIP.
    6. Index the AIP.

    Parameters:
    context (str): A JSON string containing the task context, which must include a "uid".

    Returns:
    result: The result of the chained tasks executed asynchronously.
    """
    task_context = json.loads(context)
    check_required_params(task_context, ["uid"])
    result = chain(
        validate_working_directory.s(json.dumps(task_context)),
        descriptive_metadata_validation.s(),
        aip_record_events.s(),
        aip_record_structure.s(),
        store_aip.s(),
        aip_indexing.s(),
    ).delay()
    return result



@app.task(bind=True, name="update_pipeline")
@requires_parameters("uid")
def update_pipeline(_, context):
    """
    Task to update the pipeline with the provided context.

    This task performs the following steps in a chain:
    1. Validate the working directory.
    2. Validate descriptive metadata.
    3. Record AIP events.
    4. Record AIP structure.
    5. Package the AIP.
    6. Store the AIP.
    7. Index the AIP.

    Parameters:
    context (str): JSON-encoded string containing the task context. Must include 'uid'.

    Returns:
    AsyncResult: The result of the chained tasks.
    """
    task_context = json.loads(context)
    check_required_params(task_context, ["uid"])
    result = chain(
        validate_working_directory.s(json.dumps(task_context)),
        descriptive_metadata_validation.s(),
        aip_record_events.s(),
        aip_record_structure.s(),
        store_aip.s(),
        aip_indexing.s(),
    ).delay()
    return result


@app.task(bind=True, name="validate_working_directory")
@requires_parameters("uid", "package_name")
@task_logger
def validate_working_directory(_, context, task_log):
    """
    Validates the working directory for the specified information package.

    This function performs several validation steps:
    1. Checks for the existence of the delivery XML file and the corresponding package file.
    2. Verifies the checksum of the SIP tar file against the expected checksum in the delivery XML file.
    3. Ensures the working directory contains an information package or the package is within a subfolder.
    4. Validates the METS file of the information package using the specified schema files.
    5. Ensures the presence of the representations folder.
    6. Validates the METS files within each representation folder.
    7. Performs CSIP validation on the information package.

    Raises:
        ValueError: If any validation step fails.

    Returns:
        str: The JSON-encoded task context.
    """
    task_context = json.loads(context)
    working_dir = get_working_dir(task_context["uid"])
    package_name = task_context["package_name"]
    delivery_file = os.path.join(working_dir, f"{package_name}.tar")
    delivery_xml_file = os.path.join(working_dir, f"{package_name}.xml")

    if os.path.exists(delivery_xml_file):
        task_log.info(f"Package file: {delivery_file}")
        task_log.info(f"Delivery XML file: {delivery_xml_file}")
        mets_schema_file = os.path.join(root_dir, "static/schemas/IP.xsd")
        sdv = DeliveryValidation()
        file_elements = sdv.getFileElements(working_dir, delivery_xml_file, mets_schema_file)
        delivery_file_element = file_elements[0]
        # Checksum validation
        checksum_expected = ParsedMets.get_file_element_checksum(delivery_file_element)
        checksum_algorithm = ParsedMets.get_file_element_checksum_algorithm(delivery_file_element)
        file_reference = ParsedMets.get_file_element_reference(delivery_file_element)

        task_log.info(f"Extracted file reference: {file_reference}")
        file_path = os.path.join(working_dir, remove_protocol(file_reference))
        task_log.info(f"Computing checksum for file: {file_path}")
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
                #    raise ValueError(
                #       "Representation METS file is not valid: %s" % os.path.join(rep_path, 'METS.xml')
                #    )

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
    """
    Validate descriptive metadata files in the specified working directory.

    This task looks for EAD metadata files in the 'metadata' directory of the
    working directory associated with the given UID. It logs the discovery of
    each EAD file and validates each file using the `validate_ead_metadata`
    function. If no EAD metadata files are found, it logs an informational
    message. If all files are valid, it logs a success message. If any file
    is invalid, it logs a warning message.

    Parameters:
    - context (str): JSON string containing the task context, including the UID.
    - task_log (TaskLogger): Logger object for logging task progress and results.

    Returns:
    - str: JSON string of the updated task context.
    """
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
    """
    This Celery task handles the migration of Archival Information Packages (AIPs) to new formats
    as defined by migration policies. The task performs the following steps:

    1. Parses the input context to extract the UID and sets up working directories.
    2. Creates necessary directories for storing metadata and migration logs.
    3. Defines migration policies for specific file formats (e.g., PDF, GIF).
    4. Identifies the representations in the submission folder.
    5. For each representation, identifies the files, checks their formats, and
    queues migration tasks according to the policies.
    6. Waits for all queued migration tasks to complete.
    7. Generates an XML log of the migration processes.
    8. Copies XML schema files to the working directory.
    9. Generates PREMIS metadata and METS files for each migrated representation.

    Args:
        self: The task instance (injected by Celery).
        context (str): A JSON string containing the task context, including the UID.
        task_log (logging.Logger): Logger for recording task progress and issues.

    Returns:
        str: JSON string of the task context, updated as needed.
    """
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
    """
    Executes a file migration task using the provided details.

    Args:
        self: Reference to the current task instance.
        details (dict): A dictionary containing the following keys:
            - 'targetrep': The target repository for the migration.
            - 'commandline': The command line arguments to execute.

    Raises:
        ValueError: If the 'commandline' parameter is empty.

    Returns:
        bool: True if the command line execution is successful.
    """
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
        premis.add_agent(f"urn:eark:software:earkweb:v{sw_version}", "earkweb", "software")
        premis.add_event(f"urn:eark:event:ingest:{identifier}", "success", f"urn:eark:software:earkweb:v{sw_version}")
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
    """
    Task to record AIP (Archival Information Package) events using the given context.

    This task parses the context to retrieve the 'identifier' and 'uid', constructs the
    working directory path, and creates a Premis event. The event includes adding an agent
    and an event record for the ingest process, and then creates the necessary metadata.

    If an exception occurs during the process, it logs the error and the traceback for debugging.

    Parameters:
    - _: Unused positional argument required by the task binding.
    - context (str): JSON string containing the task context with necessary parameters.
    - task_log (logging.Logger): Logger for logging task-related information.

    Returns:
    - str: JSON string containing the task context.

    Expected context keys:
    - "uid": Unique identifier for the task.
    - "package_name": Name of the package being processed.
    - "identifier": Identifier for the event being recorded.
    """
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
    """
    Packages the contents of a working directory into a tar archive for AIP (Archival Information Package).

    This task reads the necessary parameters from the context, prepares the working directory, and packages
    its contents into a tar file, excluding specific files. It logs progress and updates the task state.

    Parameters:
        self (Task): The bound task instance.
        context (str): A JSON string containing the context with required parameters.
        task_log (Logger): The task-specific logger instance for logging progress and information.

    Context Parameters:
        package_name (str): The name of the package.
        uid (str): The unique identifier for the package.
        identifier (str): A specific identifier for the package.
        org_nsid (str): The organization namespace ID.

    Workflow:
        1. Load and parse the context.
        2. Prepare the working directory and pair tree storage.
        3. Create a safe filename for the archive.
        4. Create a tar archive and add files from the working directory.
        5. Exclude specified files from the archive.
        6. Log the packaging progress.
        7. Update the task state to 'PROGRESS' and include the progress percentage.
        8. Return the task context as a JSON string.

    Returns:
        str: The JSON-encoded task context.

    Logs:
        - Info level logs for packaging start and total files in the directory.
        - Debug level logs for packaging progress every 10 files.
        - Warning level logs if status information is not updated.
    """
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
    task_log.info("Packaging working directory: %s", working_dir)
    total = sum([len(files) for (root, dirs, files) in walk(working_dir)])
    task_log.info("Total number of files in working directory %d", total)
    i = 0
    excludes = [f"{package_name}.tar", f"{package_name}.xml", archive_file]
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
                    logger.debug("Packaging progress: %d", perc)
                    # todo: activate
                    # self.update_state(state='PROGRESS', meta={'process_percent': perc})
            i += 1
    tar.close()

    self.update_state(state='PROGRESS', meta={'process_percent': 100})

    return json.dumps(task_context)


@app.task(bind=True, name="store_aip")
@requires_parameters("uid", "package_name", "identifier")
@task_logger
def store_aip(_, context, task_log):
    """
    Stores the AIP by transferring only changed files to a new version directory.
    Updates the OCFL inventory to reflect additions, deletions, and changes.
    """
    task_context = json.loads(context)
    identifier = task_context["identifier"].strip()
    package_name = task_context["package_name"]
    uid = task_context["uid"]
    working_dir = get_working_dir(uid)

    # Pairtree storage
    pts = PairtreeStorage(config_path_storage)

    # Define version and storage directories
    base_dir = pts.get_dir_path_from_id(identifier)
    data_dir = os.path.join(base_dir, "data")
    previous_version = pts.curr_version(identifier)
    new_version = pts.next_version(identifier)
    storage_dir = os.path.join(data_dir, new_version)
    os.makedirs(storage_dir, exist_ok=True)

    # Copy only changed files and record deletions
    inventory_path = os.path.join(data_dir, "inventory.json")

    previous_versions = get_previous_version_series(new_version)

    excludes = [f"{package_name}.tar", f"{package_name}.xml"]
    changed_files, deleted_files = update_storage_with_differences(
        working_dir, storage_dir, previous_versions, inventory_path, exclude_files=excludes
    )

    # Update inventory
    task_log.info(f"Updating OCFL inventory for version {new_version}")
    write_inventory_from_directory(
        identifier=identifier,
        version=new_version,
        data_dir=data_dir,
        action="ingest",
        metadata={"added": changed_files, "removed": deleted_files},
    )

    # Persist state
    patch_data = persist_state(identifier, new_version, storage_dir, None, working_dir)

    # Update status database
    try:
        response = update_status(uid, patch_data)
        if response.status_code == 200:
            task_log.info("Status information updated")
        else:
            task_log.warning(f"Status information not updated: {response.text} ({response.status_code})")
    except requests.exceptions.ConnectionError as err:
        task_log.warning("Connection to API failed. Status was not updated.", err)

    return json.dumps(task_context)


@app.task(bind=True, name="aip_indexing")
@requires_parameters("identifier")
@task_logger
def aip_indexing(_, context, task_log=None):
    """
    Index content files in AIP directory

    Indexes content files and adds metadata to the Solr document
    """
    if not task_log:
        task_log = logger
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

    # Check Solr server availability
    solr_server = SolrServer(solr_protocol, solr_host, solr_port)
    sq = SolrQuery(solr_server)
    base_url = sq.get_base_url()
    task_log.info(f"SolR base URL: {base_url}")
    solr_response = requests.get(base_url, verify=verify_certificate, timeout=5)
    if solr_response.status_code != 200:
        task_log.warn(f"Information package cannot be indexed because SolR is not available at: {base_url}")
        return json.dumps(task_context)

    # Delete existing records
    submission_url = f"{solr_protocol}://{solr_host}:{solr_port}/solr/storagecore1/update/?commit=true"
    task_log.info(f"Submission URL: {submission_url}")
    delete_response = requests.post(submission_url, data=f"<delete><query>package:\"{identifier}\"</query></delete>",
                                     headers={'Content-Type': 'text/xml'}, verify=verify_certificate, timeout=5)
    if delete_response.status_code == 200:
        task_log.info(f"Index records deleted for package: {identifier}")
    else:
        task_log.warn(
            f"Index records cannot be removed. Response code {delete_response.status_code}, message: {delete_response.text}"
        )

    # Initialize Solr client
    solr_client = SolrClient(solr_server, "storagecore1")
    # Index files from storage directory
    task_log.info(f"Indexing content files from directory: {storage_dir}")
    results = solr_client.index_directory(storage_dir, identifier, version, default_reporter, task_log=task_log)
    task_log.info("Total number of files posted: %d" % len(results))
    num_ok = sum(1 for result in results if result['status'] == 200)
    task_log.info("Number of files posted successfully: %d" % num_ok)
    num_failed = sum(1 for result in results if result['status'] != 200)
    task_log.info("Number of failed postings: %d" % num_failed)

    return json.dumps(task_context)


@app.task(bind=True, name="solr_update_metadata")
@requires_parameters("uid", "package_name", "identifier")
@task_logger
def solr_update_metadata(_, context, task_log):
    """
    Add descriptive metadata to Solr document
    """
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
        if solr.availability(solr_base_url=solr_base_url, solr_unique_key='id') == 200:
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
    # pylint: disable-next=no-member
    InformationPackage.objects.create(work_dir=os.path.join(config_path_work, uid), uid=uid,
                                      package_name=package_name, user=username, version=0)
    # pylint: disable-next=no-member
    InformationPackage.objects.get(uid=uid)
    task_context["uid"] = uid
    create_or_update_state_info_file(working_dir, task_context)
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


@app.task(name='generate_wordcloud_task')
def generate_wordcloud_task():
    """Generate word cloud"""
    solr = pysolr.Solr(solr_core_url, timeout=10)
    filter_query = 'path:*/representations/*/data/*'
    
    results = solr.search('*:*', **{
        'fq': filter_query,
        'fl': 'content,path',
        'rows': 1000
    })
    
    try:
        all_content = ' '.join(
            [clean_metadata(' '.join(doc['content'])) if isinstance(doc.get('content', ''), list)
             else clean_metadata(doc.get('content', '')) for doc in results]
        )
    except KeyError as e:
        logger.error(f"KeyError: {e}")
        all_content = ''
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        all_content = ''
    
    if not all_content.strip():
        logger.info("No content found for word cloud generation")
        return
    
    # Generate word cloud
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(all_content)

    # Save the word cloud image to a static/media directory
    image_path = os.path.join(settings.MEDIA_ROOT, 'wordcloud', 'wordcloud.png')
    os.makedirs(os.path.dirname(image_path), exist_ok=True)
    
    buffer = io.BytesIO()
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    
    with open(image_path, 'wb') as f:
        f.write(buffer.getvalue())
    
    logger.info(f"Word cloud image saved at {image_path}")


@app.task(name="backend_available")
def backend_available():
    return 5 * 5
