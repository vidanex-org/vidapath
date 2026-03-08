from enum import Enum
import json
from typing import List, Optional
from uuid import uuid4
from pydantic import BaseModel
from shapely import from_geojson, to_geojson, Geometry, wkt
from sqlmodel import Field, SQLModel

from cytomine.models import Annotation, AnnotationTerm

from models.image import ImageInstance

import logging

logger = logging.getLogger("gunicorn.error")


class GeoJSONShape(BaseModel, extra="allow"):
    type: str
    coordinates: list

    @property
    def shape(self):
        return from_geojson(json.dumps(self.model_dump()))

    @classmethod
    def from_shapely(cls, shape: Geometry):
        return cls(**json.loads(to_geojson(shape)))


class AI(BaseModel, extra="allow"):
    ai_id: str
    ai_name: str
    ai_description: str
    ai_terms: List[str]


class RunAIPayloadTerm(BaseModel, extra="allow"):
    id: int
    name: str


class RunAIPayload(BaseModel, extra="allow"):
    run_id: str
    ai_id: str
    slide_name: str
    slide_path: str
    full_wsi: str
    full_ontology: str
    terms: List[RunAIPayloadTerm]
    roi: Optional[List[GeoJSONShape]] = None


class Status(str, Enum):
    CREATED = "CREATED"
    STARTED = "STARTED"
    ERROR = "ERROR"


class AITask(SQLModel, table=True):
    run_id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    status: Status = Field(default=Status.CREATED)
    status_message: str = Field(default="")
    ai_id: str
    slide_id: int
    slide_name: str
    slide_path: str
    roi_term_ids: str = Field(default="null")
    roi_ids: str = Field(default="null")

    @classmethod
    def find_image(cls, image_id: int):
        from viewer import viewer

        image = ImageInstance.parse_obj(viewer.find_image_by_id(image_id).__dict__) # Raise error if Image not found
        return image

    @classmethod
    def from_data(cls, image_id: int, roi_term_ids: Optional[List[int]], roi_ids: Optional[List[int]], ai_id: str):
        from storage import storage

        image = cls.find_image(image_id)
        file = None
        for _file in storage.files:
            if _file['name'] == image.filename:
                file = _file
                break
        if isinstance(file, type(None)):
            raise RuntimeError(f'Image {image.filename} not found in pending files')

        return cls(
            ai_id=ai_id,
            slide_id=image.id,
            slide_name=image.filename,
            slide_path=file["dir"],
            roi_term_ids=json.dumps(roi_term_ids),
            roi_ids=json.dumps(roi_ids),
        )

    @property
    def image(self):
        return self.__class__.find_image(self.slide_id)

    @property
    def ai(self):
        from algorithm import algorithm

        # Find AI
        ais = list(filter(lambda _ai: _ai.ai_id == self.ai_id, algorithm.ais))
        if not len(ais):
            raise RuntimeError("AI not found")
        return ais[0]

    @property
    def roi_terms(self) -> Optional[List[int]]:
        return json.loads(self.roi_term_ids)

    @property
    def rois(self) -> Optional[List[int]]:
        return json.loads(self.roi_ids)

    @property
    def ROIs(self) -> Optional[List[int]]:
        from viewer import viewer

        ROIs: List[int] = []
        image_id = self.image.id

        if not isinstance(self.roi_terms, type(None)):
            for term_id in self.roi_terms:
                for anno in viewer.find_annotations_of_image_with_term(image_id, term_id):
                    ROIs.append(anno.id)
        
        if not isinstance(self.rois, type(None)):
            for roi in self.rois:
                ROIs.append(roi)
        
        return ROIs if len(ROIs) else None
            

    @property
    def roi(self):
        from viewer import viewer

        ROIs = self.ROIs
        if isinstance(ROIs, type(None)):
            return None
        else:
            roi: List[GeoJSONShape] = []
            for roi_id in ROIs:
                try:
                    anno = viewer.find_annotation_with_id(roi_id)
                    geometry = wkt.loads(anno.location)
                    shape = GeoJSONShape.from_shapely(geometry)
                    roi.append(shape)
                except Exception as e:
                    logger.error(f"Annotation [{roi_id}] read failed with error {e}")

            return roi

    @property
    def payload(self):
        terms = [
            RunAIPayloadTerm(id=str(i + 1), name=term_name)
            for i, term_name in enumerate(self.ai.ai_terms)
        ]
        _bool_to_str = lambda b: '1' if b else '0'
        roi = self.roi
        full_ontology = len(self.roi_terms) > 0 if not isinstance(self.roi_terms, type(None)) else False
        full_wsi = not full_ontology and isinstance(roi, type(None))
        return RunAIPayload(
            run_id=self.run_id,
            ai_id=self.ai_id,
            slide_name=self.slide_name,
            slide_path=self.slide_path,
            full_wsi=_bool_to_str(full_wsi),
            full_ontology=_bool_to_str(full_ontology),
            terms=terms,
            roi=roi,
        )


class AITaskResultGeoJSONShape(GeoJSONShape, extra="allow"):
    term_id: int

    @property
    def shape(self):
        return from_geojson(json.dumps(self.model_dump()))


class AITaskResult(BaseModel, extra="allow"):
    run_id: str
    inference_time: int
    results: List[AITaskResultGeoJSONShape]

    def save(self, task: AITask):
        image_id = task.image.id
        for result in self.results:
            anno = Annotation(location=result.shape.wkt, id_image=image_id).save()
            AnnotationTerm(anno.id, result.term_id).save()
