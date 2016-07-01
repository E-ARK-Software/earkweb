"""Content specific solr document - DEACTIVATED, install 'dicom'  module to enable"""
import logging

logger = logging.getLogger(__name__)

# import dicom
# from dicom.errors import InvalidDicomError


class SolrDocParams(object):

    DICOM, NONE = range(2)

    file_path = None

    def __init__(self, file_path):
        """
        Constructor initialises solr specific parameters

        @type       file_path: string
        @param      file_path: file path
        """
        self.file_path = file_path

    def formattype(self):
        """
        Constructor takes

        @rtype:     SolrDocParams
        @return:    Format type
        """
        if not self.file_path:
            raise ValueError("File not initialized.")
        if self.file_path.endswith(".dcm"):
            return SolrDocParams.DICOM
        else:
            return SolrDocParams.NONE

    @staticmethod
    def str(alg):
        if alg is SolrDocParams.DICOM:
            return "DICOM"
        else:
            return "NONE"

    def get_params(self):
        if not self.file_path:
            raise ValueError("File not initialized.")
        if self.formattype() == SolrDocParams.DICOM:
            return self.get_solrdoc_params_dicom()
        else:
            return {}

    def get_solrdoc_params_dicom(self):
        return {}
    # def get_solrdoc_params_dicom(self):
    #     logger.info("Posting Dicom file")
    #     logger.info("")
    #     try:
    #         df = dicom.read_file(self.file_path)
    #         logger.info("afile: %s" % self.file_path)
    #         logger.info("Patient name: %s" % df.PatientName)
    #         PatientAge = df.PatientAge if hasattr(df, 'PatientAge') else ""
    #         PatientBirthDate = df.PatientBirthDate if hasattr(df, 'PatientBirthDate') else ""
    #         PatientID = df.PatientID if hasattr(df, 'PatientID') else ""
    #         PatientName = df.PatientName if hasattr(df, 'PatientName') else ""
    #         PatientSex = df.PatientSex if hasattr(df, 'PatientSex') else ""
    #         PatientWeight = df.PatientWeight if hasattr(df, 'PatientWeight') else ""
    #         PerformingPhysicianName = df.PerformingPhysicianName if hasattr(df, 'PerformingPhysicianName') else ""
    #         RequestingPhysician = df.RequestingPhysician if hasattr(df, 'RequestingPhysician') else ""
    #         InstitutionAddress = df.InstitutionAddress if hasattr(df, 'InstitutionAddress') else ""
    #         InstitutionName = df.InstitutionName if hasattr(df, 'InstitutionName') else ""
    #         params = {
    #             "literal.PatientAge": PatientAge,
    #             "literal.PatientBirthDate": PatientBirthDate,
    #             "literal.PatientID": PatientID,
    #             "literal.PatientName": PatientName,
    #             "literal.PatientSex": PatientSex,
    #             "literal.PatientWeight": PatientWeight,
    #             "literal.PerformingPhysicianName": PerformingPhysicianName,
    #             "literal.RequestingPhysician": RequestingPhysician,
    #             "literal.InstitutionAddress": InstitutionAddress,
    #             "literal.InstitutionName": InstitutionName,
    #             "literal.content_type": "application/dicom"
    #         }
    #         return params
    #     except InvalidDicomError as err:
    #         logger.error("Error reading dicom: %s" % err)
    #         return {}
