# -*- coding: utf-8 -*-
"""
Helper: Create METS/PREMIS objects for a list of files
"""
import glob, os
import uuid
import hashlib
from subprocess import check_output
import config.params
import lxml.etree

def get_sha256_hash(file):
    blocksize = 65536
    hash = hashlib.sha256()
    print file
    with open(file, 'rb') as file:
        for block in iter(lambda: file.read(blocksize), ''):
            hash.update(block)
    return hash.hexdigest()

def get_puid(file):
    out = check_output(["python", "/usr/local/bin/fido", file])
    return out.split(",")[2]

def get_jhove(file):
    out = check_output(["/usr/bin/jhove", "-h", "XML", "-i", file])
    parsed = lxml.etree.fromstring(out)
    result = lxml.etree.tostring(parsed, xml_declaration=False)
    return result


os.chdir(config.params.root_dir + "/workers/resources/AIP-test/AIP-segmented/AIP-segmented/aip-metadata")

file = "../../AIP-segmented.tar.gz"


print """
<object xsi:type="file">
        <objectIdentifier>
            <objectIdentifierType>FILEPATH</objectIdentifierType>
            <objectIdentifierValue>%(file)s</objectIdentifierValue>
        </objectIdentifier>
        <objectCharacteristics>
            <compositionLevel>0</compositionLevel>
            <fixity>
                <messageDigestAlgorithm>SHA-256</messageDigestAlgorithm>
                <messageDigest>%(sha256)s</messageDigest>
                <messageDigestOriginator>/usr/bin/sha256sum</messageDigestOriginator>
            </fixity>
            <size>%(size)s</size>
            <format>
                <formatRegistry>
                    <formatRegistryName>PRONOM</formatRegistryName>
                    <formatRegistryKey>%(puid)s</formatRegistryKey>
                    <formatRegistryRole>specification</formatRegistryRole>
                </formatRegistry>
            </format>
            <objectCharacteristicsExtension>
                <mdSec ID="ID%(guid)s">
                    <mdWrap MDTYPE="OTHER" OTHERMDTYPE="JHOVE">
                        <xmlData>
                            %(jhove)s
                        </xmlData>
                    </mdWrap>
                </mdSec>
            </objectCharacteristicsExtension>
        </objectCharacteristics>
        <originalName>%(file)s</originalName>
        <storage>
            <contentLocation>
                <contentLocationType>FILEPATH</contentLocationType>
                <contentLocationValue>%(file)s</contentLocationValue>
            </contentLocation>
        </storage>
        <relationship>
            <relationshipType>structural</relationshipType>
            <relationshipSubType>is included in</relationshipSubType>
            <relatedObjectIdentification>
                <relatedObjectIdentifierType>PACKAGE_NAME</relatedObjectIdentifierType>
                <relatedObjectIdentifierValue>AIP-compound</relatedObjectIdentifierValue>
            </relatedObjectIdentification>
        </relationship>
    </object>

""" % {'sha256': get_sha256_hash(file), 'file': file, 'puid': get_puid(file), 'guid': uuid.uuid1(), 'size': os.path.getsize(file), 'jhove': get_jhove(file) }




#for file in glob.glob("*.xml"):
#    print(
#    "<mets:file ID=\"ID%s\" MIMETYPE=\"application/xml\" CREATED=\"2014-05-01T01:00:00+01:00\" ADMID=\"ID03a431cb-7801-4356-bcd9-861708eba1a1\" CHECKSUMTYPE=\"SHA-256\" CHECKSUM=\"%s\" SIZE=\"%d\"><mets:FLocat xlink:href=\"file://./aip-aip-metadata/%s\" xlink:type=\"simple\" LOCTYPE=\"URL\"/></mets:file>" % (
#    uuid.uuid1(), get_sha256_hash(file), os.path.getsize(file),file))

