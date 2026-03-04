from enum import Enum
from typing import Optional
from pydantic import BaseModel, ByteSize, AnyHttpUrl, computed_field
from extended.uploadedfile import UploadedFileStatus

UploadedFileStatusChoices = Enum(
    "UploadedFileStatusChoices",
    ((value.name, value.name) for value in UploadedFileStatus),
    type=str,
)


class UploadedFile(BaseModel, extra='allow'):
    id: int
    created: int

    name: Optional[str]
    image: Optional[int]
    filename: Optional[str]
    originalFilename: Optional[str]
    globalSize: Optional[ByteSize]
    size: Optional[ByteSize]
    nbChildren: Optional[int]
    thumbURL: Optional[AnyHttpUrl]
    contentType: Optional[str]
    status: Optional[UploadedFileStatus]

    @computed_field
    @property
    def statusText(self) -> UploadedFileStatusChoices:
        return UploadedFileStatus(self.status).name
