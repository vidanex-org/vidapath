import json
import os
from os.path import join, basename
import shutil
from difflib import SequenceMatcher
import tempfile
from typing import Any, List, Optional
from pathlib import Path
from math import sqrt
from shapely import wkt
import numpy as np
import cv2
from tifffile import TiffWriter
from sqlmodel import delete
from randomcolor import RandomColor

from cytomine.models import (
    UserCollection,
    CurrentUser,
    ProjectCollection,
    Project,
    StorageCollection,
    ImageInstanceCollection,
    ImageInstance,
    AnnotationCollection,
    Annotation,
    AnnotationTerm,
    Term,
    TermCollection,
    OntologyCollection,
)

from settings import settings
from extended.uploadedfile import (
    UploadedFileStatus,
    UploadedFile,
    UploadedFileCollection,
)
from extended.client import Client
from extended.imagefilter import (
    ImageFilter,
    ImageFilterCollection,
    ImageFilterProject,
    ImageFilterProjectCollection,
)
from storage import storage
from algorithm import algorithm
import models

import logging

logger = logging.getLogger("gunicorn.error")

MAX_PIXELS = 20000 * 20000

def make_archive(source, destination):
    base = os.path.basename(destination)
    name = base.split(".")[0]
    format = base.split(".")[1]
    archive_from = os.path.dirname(source)
    archive_to = os.path.basename(source.strip(os.sep))
    shutil.make_archive(name, format, archive_from, archive_to)
    shutil.move("%s.%s" % (name, format), destination)


class Viewer:
    ROOT_PROJECT_NAME = settings.project_name

    def startup(self):
        if not self.project:
            raise ValueError("Project not created!")

        # Enable all image filters
        project_id = self.project.id
        project_filter_ids = [
            filter.imageFilter
            for filter in ImageFilterProjectCollection().fetch_with_filter(
                "project", project_id
            )
        ]

        not_avilable_filters: list[ImageFilter] = [
            filter
            for filter in ImageFilterCollection().fetch()
            if filter.id not in project_filter_ids
        ]

        for filter in not_avilable_filters:
            ImageFilterProject(imageFilter=filter.id, project=project_id).save()

    def __getattribute__(self, name: str) -> Any:
        if name in [
            "upload_image",
        ]:
            return object.__getattribute__(self, name)
        else:
            logger.info(f"Connecting to Cytomine core at {settings.credential['host']}")
            with Client(**settings.credential):
                return object.__getattribute__(self, name)

    @property
    def current_user(self):
        return CurrentUser().fetch()

    @property
    def project(self):
        project = None

        for proj in ProjectCollection().fetch():
            if proj.name == self.ROOT_PROJECT_NAME:
                project = proj

        if not project:
            project = Project(self.ROOT_PROJECT_NAME, isRestricted=False)
            project.save()
            project.add_user(self.user.id)
            project.add_user(self.user.id, True)

        return project

    @property
    def ontology(self):
        return OntologyCollection().fetch_with_filter("project", 164)[0]

    @property
    def user(self):
        filtered = [
            user for user in UserCollection().fetch() if user.username == "admin"
        ]
        return filtered[0] if len(filtered) else None

    @property
    def images(self) -> list[ImageInstance]:
        return ImageInstanceCollection().fetch_with_filter("project", self.project.id)

    def find_image_by_id(self, id: int) -> ImageInstance:
        images = list(
            filter(
                lambda image: image.id == id,
                self.images,
            )
        )
        if not len(images):
            raise ValueError("Image not found")

        return images[0]

    def find_images_like(
        self, filepath: str, confidence: float = 0.8
    ) -> list[ImageInstance]:
        images = []
        for image in self.images:
            filename = image.path
            basename = os.path.basename(filename)
            if (
                SequenceMatcher(None, filename, filepath).ratio() >= confidence
                or SequenceMatcher(None, basename, filepath).ratio() >= confidence
                or SequenceMatcher(None, image.originalFilename, filepath).ratio()
                >= confidence
                or SequenceMatcher(None, image.instanceFilename, filepath).ratio()
                >= confidence
                or SequenceMatcher(None, image.filename, filepath).ratio() >= confidence
            ):
                images.append(image)

        return images

    def find_annotations_of_image(self, image: ImageInstance) -> list[Annotation]:
        roi_annotations = AnnotationCollection()
        roi_annotations.image = image.id
        roi_annotations.showWKT = True
        roi_annotations.showMeta = True
        roi_annotations.showTerm = True
        roi_annotations.showGIS = True
        roi_annotations.fetch()
        return roi_annotations

    def import_annotations_of_image(self, image: ImageInstance, annotations: List[models.ImportAnnotation]):
        image_id = image.id
        for annotation in annotations:
            anno = Annotation(location=annotation.location, id_image=image_id).save()
            if not isinstance(annotation.term, type(None)):
                for term in annotation.term:
                    AnnotationTerm(anno.id, term).save()
        return "Success"

    def export_annotations_as_standalone_of_image(self, image: ImageInstance) -> bytes:
        output_name = Path(image.originalFilename).stem + ".vid"

        pixels = image.width * image.height
        ratio = 1.0 if pixels < MAX_PIXELS else sqrt(MAX_PIXELS / pixels)
        resolution = (int(image.width * ratio), int(image.height * ratio))
        default_mask = np.zeros((resolution[1], resolution[0], 4), dtype=np.uint8)

        roi_annotations = self.find_annotations_of_image(image)

        terms = TermCollection().fetch_with_filter("image", image.id)
        as_tag = lambda id, o: (
            id,
            1,
            len(o.encode("utf-16-le")),
            o.encode("utf-16-le"),
            True,
        )
        terms = {
            term["id"]: {
                "count": 0,
                "mask": default_mask.copy(),
                "extratags": [
                    as_tag(40091, term["name"]),
                    as_tag(40093, ""),
                    as_tag(40094, "RotateAngle:0"),
                    as_tag(40095, "#64" + term["color"][1:]),
                ],
            }
            for term in [t.__dict__ for t in terms]
            + [{"id": -1, "name": "No term", "color": "#1A8560"}]
        }

        for anno in roi_annotations:
            geometry = wkt.loads(anno.location)
            contour = np.array(geometry.exterior.coords)
            contour[:, 1] = -contour[:, 1] + image.height
            contour = (contour * ratio).astype(int)

            if not len(anno.term):
                anno.term = [-1]

            for tid in anno.term:
                term = terms[tid]
                term["count"] += 1
                mask = term["mask"]
                cv2.drawContours(mask, [contour], -1, (0, 0, 0, 255), -1)

        zip_file_raw = b""
        with tempfile.TemporaryDirectory() as tmpDir:
            anno_dir = Path(tmpDir) / output_name
            anno_dir.mkdir(parents=True, exist_ok=True)
            with TiffWriter(anno_dir / output_name) as tif:
                for term in terms.values():
                    if term["count"]:
                        tif.write(
                            data=term["mask"],
                            photometric="rgb",
                            metadata=None,
                            software="VIDANEX web viewer",
                            compression="zlib",
                            extratags=term["extratags"],
                            resolution=(96, 96),
                            resolutionunit=2,
                        )
            zip_file = Path(tmpDir) / "annotations.zip"
            make_archive(str(anno_dir), str(zip_file))

            with open(zip_file, "rb") as f:
                zip_file_raw = f.read()

        return zip_file_raw

    def delete_image(self, image: ImageInstance) -> ImageInstance:
        uploadedfile = self.find_uploadedfiles_by_base_image(image.baseImage)
        self.delete_uploadedfile(uploadedfile)
        return image

    def find_image(self, full_filepath: str) -> bool:
        filepath = basename(full_filepath)
        images = list(
            filter(
                lambda image: image.instanceFilename.lower() == filepath.lower(),
                self.images,
            )
        )
        return len(images) > 0

    def import_image(self, full_filepath: str) -> ImageInstance:
        filepath = basename(full_filepath)
        images = list(
            filter(
                lambda image: image.instanceFilename.lower() == filepath.lower(),
                self.images,
            )
        )
        if not len(images):
            try:
                full_filepath = storage.find_file(full_filepath)
                print(f"Uploading file {filepath} ...")
                images = self.upload_image(filepath, full_filepath)
            except ValueError:
                raise ValueError("File not found")
            except FileNotFoundError as e:
                error_file = str(e).split(os.sep)[0]
                uploadedfile = self.find_uploadedfiles_like(error_file, 0.5)
                if not len(uploadedfile):
                    raise BufferError("Upload failed")

                raise BufferError(
                    f"Upload failed with status [{UploadedFileStatus(uploadedfile[0].status).name}]"
                )

        return images

    @property
    def storage(self):
        storages = list(
            filter(
                lambda storage: storage.user == self.current_user.id,
                StorageCollection().fetch(),
            )
        )
        if not len(storages):
            raise ValueError("Storage not found")

        return storages[0]

    @property
    def algorithm(self):
        return algorithm

    def find_annotations_of_image_with_term(self, image_id: int, term_id: int):
        roi_annotations = AnnotationCollection()
        roi_annotations.image = image_id
        roi_annotations.term = term_id
        roi_annotations.showWKT = True
        roi_annotations.fetch()
        return roi_annotations

    def find_annotation_with_id(self, id: int):
        anno = Annotation()
        anno.id = id
        anno.fetch()
        return anno

    def run_ai(
        self,
        image_id: int,
        roi_term_ids: Optional[List[int]],
        roi_ids: Optional[List[int]],
        ai_id: str,
        session: models.SessionDep,
    ) -> str:
        task = models.AITask.from_data(image_id, roi_term_ids, roi_ids, ai_id)

        payload = task.payload  # Raise error if AI not found

        session.add(task)
        session.commit()
        session.refresh(task)

        # Upsert terms for AI
        terms = TermCollection().fetch_with_filter("project", self.project.id)
        terms = {term["name"]: term["id"] for term in [t.__dict__ for t in terms]}
        for term in payload.terms:
            if term.name in terms:
                term.id = terms[term.name]
            else:
                ontology_term = Term()
                ontology_term.ontology = self.ontology.id
                ontology_term.name = term.name
                ontology_term.color = RandomColor().generate()[0].upper()
                ontology_term.save()

                term.id = ontology_term.id

        res = algorithm.run_ai(payload)

        task.status = models.AIUtils.Status.STARTED
        session.add(task)
        session.commit()
        session.refresh(task)

        return res

    def save_ai_result(self, data: dict, session: models.SessionDep):
        task: models.AITask | None = None
        try:
            result = models.AITaskResult.parse_obj(data)

            task = session.get(models.AITask, result.run_id)
            if not task:
                raise RuntimeError("AI task not found")

            result.save(task)

            session.exec(
                delete(models.AITask).where(models.AITask.run_id == task.run_id)
            )
            session.commit()

            return "Success"
        except Exception as e:
            if task:
                task.status = models.AIUtils.Status.ERROR
                task.status_message = json.dumps(data)
                session.add(task)
                session.commit()
                session.refresh(task)
            else:
                payload = json.dumps(data)

                task = models.AITask(
                    status=models.AIUtils.Status.ERROR,
                    status_message=payload,
                    ai_id="",
                    slide_id=-1,
                    slide_name="",
                    slide_path="",
                )
                session.add(task)
                session.commit()
                session.refresh(task)

                logger.error(
                    f"AI Webhook failed catastrophically! JSON Body: {payload}"
                )

            raise e

    def upload_image(self, filepath: str, full_filepath: str):
        with Client(
            **settings.credential,
        ) as cytomine:
            uploaded_file = cytomine.upload_image(
                filename=full_filepath,
                id_storage=self.storage.id,
                id_project=self.project.id,
                sync=True,
            )
            if type(uploaded_file) == FileNotFoundError:
                raise uploaded_file

            images = uploaded_file.images

            def _rename_image(image, name: str):
                for instance in image["imageInstances"]:
                    instance.instanceFilename = name
                    instance.save()

            if len(images) == 1:
                image = images[0]
                _rename_image(images[0], filepath)
            else:
                for i, image in enumerate(images):
                    _rename_image(image, f"{filepath} - {i+1}")

            return [
                instance for image in images for instance in image["imageInstances"]
            ]

    @property
    def uploaded_files(self) -> list[UploadedFile]:
        return UploadedFileCollection().fetch()

    def find_uploadedfiles_like(
        self, filepath: str, confidence: float = 0.8
    ) -> list[UploadedFile]:
        files = []
        for file in self.uploaded_files:
            filename = file.filename
            basename = os.path.basename(filename)
            if (
                SequenceMatcher(None, filename, filepath).ratio() >= confidence
                or SequenceMatcher(None, basename, filepath).ratio() >= confidence
            ):
                files.append(file)

        return files

    def find_uploadedfiles_by_base_image(self, base_image: int) -> UploadedFile:
        files = list(
            filter(
                lambda file: file.image == base_image,
                self.uploaded_files,
            )
        )
        if not len(files):
            raise ValueError("Uploadedfile not found")

        return files[0]

    def find_uploadedfile_by_id(self, id: int) -> UploadedFile:
        files = list(
            filter(
                lambda file: file.id == id,
                self.uploaded_files,
            )
        )
        if not len(files):
            raise ValueError("Uploadedfile not found")

        return files[0]

    def delete_uploadedfile(self, uploadedfile: UploadedFile) -> UploadedFile:
        images = list(
            filter(lambda image: image.baseImage == uploadedfile.image, self.images)
        )
        for image in images:
            for anno in self.find_annotations_of_image(image):
                anno.delete()
            image.delete()

        shutil.rmtree(join(settings.root_path, uploadedfile.filename.split(os.sep)[0]))

        uploadedfile.delete()

        return uploadedfile

    def clear_failed_uplaodfiles(self):
        cleared = []
        for uploadfile in self.uploaded_files:
            if uploadfile.status in [
                stat.value
                for stat in [
                    UploadedFileStatus.ERROR_CONVERSION,
                    UploadedFileStatus.ERROR_DEPLOYMENT,
                    UploadedFileStatus.ERROR_EXTRACTION,
                    UploadedFileStatus.ERROR_FORMAT,
                    UploadedFileStatus.ERROR_INTEGRITY,
                    UploadedFileStatus.ERROR_UNPACKING,
                ]
            ]:
                uploadfile.delete()
                cleared.append(uploadfile)

        return cleared

    def delete_all_annotations_of_image(self, image: ImageInstance) -> str:
        """Delete all annotations for a given image"""
        roi_annotations = self.find_annotations_of_image(image)
        
        # Delete each annotation
        for annotation in roi_annotations:
            annotation.delete()
        
        return f"Successfully deleted {len(roi_annotations)} annotations from image {image.id}"
    
    def delete_all_annotations_of_image_by_term(self, image: ImageInstance, term_id: int) -> str:
        """Delete all annotations for a given image that have a specific term"""
        # Find annotations for the image with the specific term
        roi_annotations = self.find_annotations_of_image_with_term(image.id, term_id)
        
        # Delete each annotation
        for annotation in roi_annotations:
            annotation.delete()
        
        return f"Successfully deleted {len(roi_annotations)} annotations with term {term_id} from image {image.id}"


viewer = Viewer()
