from typing import List, Optional
from pydantic import BaseModel, Field, AnyHttpUrl


class Point(BaseModel, extra="allow"):
    x: float
    y: float


class Annotation(BaseModel, extra="allow"):
    id: int
    created: int
    updated: int

    name: Optional[str]
    image: Optional[int]
    slice: Optional[int]
    project: Optional[int]
    term: Optional[List[int]]

    url: Optional[AnyHttpUrl]
    imageURL: Optional[AnyHttpUrl]
    cropURL: Optional[AnyHttpUrl]
    smallCropURL: Optional[AnyHttpUrl]

    location: Optional[str] = Field(description="WKT Location (geometry)")
    geometryCompression: Optional[float]
    area: Optional[float]
    areaUnit: Optional[str]
    perimeter: Optional[float]
    perimeterUnit: Optional[str]
    centroid: Optional[Point]

    countReviewedAnnotations: Optional[int]
    reviewed: Optional[bool]

class ImportAnnotation(BaseModel):
    location: str = Field(description="WKT Location (geometry)")
    term: List[int] = Field(default_factory=[])
