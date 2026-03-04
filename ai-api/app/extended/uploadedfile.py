from enum import Enum
from cytomine.models.collection import Collection
from cytomine.models.model import Model


class UploadedFileStatus(Enum):
    UPLOADED = 0
    DETECTING_FORMAT = 10
    ERROR_FORMAT = 11
    EXTRACTING_DATA = 20
    ERROR_EXTRACTION = 21
    CONVERTING = 30
    ERROR_CONVERSION = 31
    DEPLOYING = 40
    ERROR_DEPLOYMENT = 41
    DEPLOYED = 100
    EXTRACTED = 102
    CONVERTED = 104
    UNPACKING = 50
    ERROR_UNPACKING = 51
    CHECKING_INTEGRITY = 60
    ERROR_INTEGRITY = 61
    UNPACKED = 106


class UploadedFile(Model):
    def __init__(self, **attributes):
        super(UploadedFile, self).__init__()
        self.image = None
        self.isArchive = None
        self.globalSize = None
        self.userId = None
        self.filename = None
        self.size = None
        self.nbChildren = None
        self.root = None
        self.thumbURL = None
        self.contentType = None
        self.originalFilename = None
        self.status = None
        self.storageId = None
        self.populate(attributes)

    def save(self, *args, **kwargs):
        raise NotImplementedError("Cannot save a uploadedfile by client.")


class UploadedFileCollection(Collection):
    def __init__(self, filters=None, max=0, offset=0, **parameters):
        super(UploadedFileCollection, self).__init__(UploadedFile, filters, max, offset)
        parameters["onlyRootsWithDetails"] = True
        self._allowed_filters = [None, "originalFilename"]
        self.set_parameters(parameters)

    def save(self, *args, **kwargs):
        raise NotImplementedError("Cannot save a uploadedfile collection by client.")
