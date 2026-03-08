import os
import requests
from cytomine import Cytomine
from cytomine.cytomine import CytomineAuth
from requests_toolbelt import MultipartEncoder


class Client(Cytomine):
    def upload_image(
        self, filename, id_storage, id_project=None, properties=None, sync=False
    ):
        upload_host = self._base_url(with_base_path=False)

        query_parameters = {
            "idStorage": id_storage,  # backwards compatibility
            "storage": id_storage,
            "sync": sync,
        }

        if id_project:
            query_parameters["idProject"] = id_project  # backwards compatibility
            query_parameters["projects"] = id_project

        if properties:
            query_parameters["keys"] = ",".join(list(properties.keys()))
            query_parameters["values"] = ",".join(list(properties.values()))

        basename = os.path.basename(filename)
        m = MultipartEncoder(fields={"files[]": (basename, open(filename, "rb"))})
        response: requests.Response = self._session.post(
            f"{upload_host}/upload",
            auth=CytomineAuth(self._public_key, self._private_key, upload_host, ""),
            headers=self._headers(content_type=m.content_type),
            params=query_parameters,
            data=m,
        )

        if response.status_code == requests.codes.ok:
            uf = self._process_upload_response(response.json()[0])
            self._logger.info("Image uploaded successfully")
            return uf
        else:
            self._logger.error("Error during image upload.")
            return FileNotFoundError(
                "upload-" + response.json()[0]["error"].split("/upload-")[1]
            )
