
class PackageFormat:
    TARGZ, TAR, ZIP = range(3)

    @staticmethod
    def get(filename):
        """
        Constructor takes

        @type       filename: string
        @param      filename: File name
        @rtype:     PackageFormat
        @return:    Package type
        """
        if filename.endswith("tar.gz"):
            return PackageFormat.TARGZ
        elif filename.endswith("tar"):
            return PackageFormat.TAR
        elif filename.endswith("zip"):
            return PackageFormat.ZIP
        else:
            return PackageFormat.NONE

    @staticmethod
    def str(alg):
        if alg is PackageFormat.TARGZ:
            return "TARGZ"
        elif alg is PackageFormat.TAR:
            return "TAR"
        elif alg is PackageFormat.ZIP:
            return "ZIP"
        else:
            return "NONE"
