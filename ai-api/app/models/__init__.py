from models.image import ImageInstance
from models.uploadedfile import UploadedFile
from models.annotation import Annotation, ImportAnnotation
from models.storage import PendingFile
from models.ai_task import AI, AITaskResult, AITask

import models.ai_task as AIUtils


from typing import Annotated
from pathlib import Path

from fastapi import Depends
from sqlmodel import Session, SQLModel, create_engine

# The working directory in the container is /dist
data_dir = Path("/dist/data")
data_dir.mkdir(exist_ok=True)

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{data_dir / sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
