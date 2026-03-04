from typing import Optional
from pydantic import BaseModel, AnyHttpUrl, computed_field

from settings import settings


class ImageInstance(BaseModel, extra='allow'):
    id: int
    created: int
    updated: int

    name: Optional[str]
    baseImage: Optional[int]
    project: Optional[int]
    originalFilename: Optional[str]
    instanceFilename: Optional[str]
    path: Optional[str]
    filename: Optional[str]
    contentType: Optional[str]

    tileSize: Optional[int]
    width: Optional[int]
    height: Optional[int]
    depth: Optional[int]
    duration: Optional[int]
    channels: Optional[int]
    physicalSizeX: Optional[float]
    physicalSizeY: Optional[float]
    physicalSizeZ: Optional[float]
    fps: Optional[int]
    bitPerSample: Optional[int]
    samplePerPixel: Optional[int]
    magnification: Optional[int]
    zoom: Optional[int]
    extrinsicChannels: Optional[int]

    thumb: Optional[AnyHttpUrl]
    preview: Optional[AnyHttpUrl]
    macroURL: Optional[AnyHttpUrl]

    numberOfAnnotations: Optional[int]
    numberOfJobAnnotations: Optional[int]
    numberOfReviewedAnnotations: Optional[int]
    reviewed: bool

    @computed_field
    @property
    def viewerURL(self) -> Optional[AnyHttpUrl]:
        return f"{settings.server_url}/#/project/{self.project}/image/{self.id}"
