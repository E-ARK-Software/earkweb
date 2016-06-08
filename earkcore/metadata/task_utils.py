import logging
from earkcore.utils.pathutils import strip_prefixes

logger = logging.getLogger(__name__)
import os
from earkcore.utils.fileutils import locate
from earkcore.xml.xmlvalidation import XmlValidation
from earkcore.filesystem.fsinfo import remove_protocol
import lxml

def validate_ead_metadata(root_path, pattern, schema_file, tl):
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
    # ead 2002: ns = {'ead': 'http://ead3.archivists.org/schema/', 'xlink': 'http://www.w3.org/1999/xlink', 'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}
    ns = {'ead': 'http://ead3.archivists.org/schema/', 'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}
    xmlval = XmlValidation()
    ead_md_files = [x for x in locate(pattern, root_path)]
    for ead in ead_md_files:
        logger.debug("Validating EAD metadata file: %s" % strip_prefixes(ead, root_path))
        # validate against xml schema
        result = xmlval.validate_XML_by_path(ead, schema_file)
        if schema_file is None:
            tl.addinfo("Using schema files specified by the 'schemaLocation' attribute")
        else:
            tl.addinfo("Using schema: " % schema_file)
        if result.valid:
            logger.debug("Metadata file '%s' successfully validated." % ead)
        else:
            if schema_file is None:
                tl.adderr("Error validating against schemas using schema files specified by the 'schemaLocation' attribute:")
            else:
                tl.adderr("Error validating against schema '%s': %s" % (schema_file, result.err))

            for err in result.err:
                tl.adderr("- %s" % str(err))
            return False
        ead_tree = lxml.etree.parse(ead)
        # check dao hrefs
        res = ead_tree.getroot().xpath('//ead:dao', namespaces=ns)
        if len(res) == 0:
            tl.addinfo("The EAD file does not contain any file references.")
        ead_dir, tail = os.path.split(ead)
        references_valid = True
        for dao in res:
            # ead 2002: dao_ref_file = os.path.join(ead_dir, remove_protocol(dao.attrib['{http://www.w3.org/1999/xlink}href']))
            dao_ref_file = os.path.join(ead_dir, remove_protocol(dao.attrib['href']))
            if not os.path.exists(dao_ref_file):
                references_valid = False
                tl.adderr("DAO file reference error - File does not exist: %s" % dao_ref_file, False) # False
        if not references_valid:
            tl.adderr( "DAO file reference errors. Please consult the log file for details.")
            return False
    return True

