from cytomine.models.collection import Collection
from cytomine.models.model import Model


class ImageFilter(Model):
    def __init__(self, **attributes):
        super(ImageFilter, self).__init__()
        self.id = None
        self.name = None
        self.method = None
        self.baseUrl = None
        self.available = None
        self.populate(attributes)

    def save(self, *args, **kwargs):
        raise NotImplementedError("Cannot save a imagefilter by client.")


class ImageFilterCollection(Collection):
    def __init__(self, filters=None, max=0, offset=0, **parameters):
        super(ImageFilterCollection, self).__init__(ImageFilter, filters, max, offset)
        parameters["onlyRootsWithDetails"] = True
        self._allowed_filters = [None]
        self.set_parameters(parameters)

    def save(self, *args, **kwargs):
        raise NotImplementedError("Cannot save a imagefilter collection by client.")


class ImageFilterProject(Model):
    def __init__(self, **attributes):
        super(ImageFilterProject, self).__init__()
        self.imageFilter = None
        self.project = None
        self.populate(attributes)


class ImageFilterProjectCollection(Collection):
    def __init__(self, filters=None, max=0, offset=0, **parameters):
        super(ImageFilterProjectCollection, self).__init__(ImageFilterProject, filters, max, offset)
        parameters["onlyRootsWithDetails"] = True
        self._allowed_filters = [None, "project"]
        self.set_parameters(parameters)

    def save(self, *args, **kwargs):
        raise NotImplementedError("Cannot save a imagefilterproject collection by client.")
