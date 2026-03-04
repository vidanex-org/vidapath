import json
import sys
from contextlib import asynccontextmanager
from typing import List
from fastapi import FastAPI, HTTPException, Request
import io
from starlette.responses import StreamingResponse
from functools import wraps

from settings import settings
from storage import storage
from viewer import viewer
import models
from models import SessionDep

import logging

logger = logging.getLogger("gunicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Setting up DB...")
    models.create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan, root_path=settings.root_path)


def catch(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except RuntimeError as e:
            raise HTTPException(status_code=404, detail=str(e.args[0]))
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except BufferError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise e

    return wrapper


@app.get("/images", response_model=list[models.ImageInstance], tags=["images"])
@catch
async def find_images():
    return viewer.images


@app.get(
    "/images/like/{filepath:path}",
    response_model=list[models.ImageInstance],
    tags=["images"],
)
@catch
async def find_images_path_like(filepath: str, condifence: float = 0.8):
    return viewer.find_images_like(filepath, condifence)


@app.get("/images/{id}", response_model=models.ImageInstance, tags=["images"])
@catch
async def find_image_by_id(id: int):
    return viewer.find_image_by_id(id)


@app.get(
    "/images/{id}/annotations", response_model=list[models.Annotation], tags=["images"]
)
@catch
async def find_annotations_of_image_by_id(id: int):
    return viewer.find_annotations_of_image(viewer.find_image_by_id(id))


@app.post("/images/{id}/annotations", tags=["images"])
@catch
async def create_annotations_of_image_by_id(id: int, annotations: list[models.ImportAnnotation]):
    return viewer.import_annotations_of_image(viewer.find_image_by_id(id), annotations)


@app.get("/images/{id}/annotations.zip", tags=["images"])
@catch
async def export_annotations_as_standalone_of_image(id: int):
    return StreamingResponse(
        io.BytesIO(
            viewer.export_annotations_as_standalone_of_image(
                viewer.find_image_by_id(id)
            )
        ),
        media_type="application/x-zip",
    )

@app.delete("/images/{id}/annotations", tags=["images"])
@catch
async def delete_all_annotations_of_image_by_id(id: int):
    return viewer.delete_all_annotations_of_image(viewer.find_image_by_id(id))

@app.delete("/images/{image_id}/annotations/term/{term_id}", tags=["images"])
@catch
async def delete_all_annotations_of_image_by_term(image_id: int, term_id: int):
    image = viewer.find_image_by_id(image_id)
    return viewer.delete_all_annotations_of_image_by_term(image, term_id)


@app.delete("/images/{id}", response_model=models.ImageInstance, tags=["images"])
@catch
async def delete_image_with_uploadedfile_and_annotations(id: int):
    return viewer.delete_image(viewer.find_image_by_id(id))


@app.get("/files", response_model=list[models.UploadedFile], tags=["files"])
@catch
async def find_uploadedfiles():
    return viewer.uploaded_files


@app.get("/files/pending", response_model=list[models.PendingFile], tags=["files"])
@catch
async def find_pending_files():
    return storage.files


@app.get(
    "/files/like/{filepath:path}",
    response_model=list[models.UploadedFile],
    tags=["files"],
)
@catch
async def find_uploadedfile_path_like(filepath: str, confidence: float = 0.8):
    return viewer.find_uploadedfiles_like(filepath, confidence)


@app.get("/files/{id}", response_model=models.UploadedFile, tags=["files"])
@catch
async def find_uploadedfile_by_id(id: int):
    return viewer.find_uploadedfile_by_id(id)


@app.get(
    "/files/base_image/{base_image}", response_model=models.UploadedFile, tags=["files"]
)
@catch
async def find_uploadedfile_by_base_image_id(base_image: int):
    return viewer.find_uploadedfiles_by_base_image(base_image)


@app.delete("/files/{id}", response_model=models.UploadedFile, tags=["files"])
@catch
async def delete_uploadedfile_with_images_and_annotations(id: int):
    return viewer.delete_uploadedfile(viewer.find_uploadedfile_by_id(id))


@app.get("/ai", response_model=list[models.AI], tags=["ai_service"])
@catch
async def find_ais():
    return viewer.algorithm.ais


from sqlmodel import select, delete


@app.get("/ai/tasks", tags=["ai_service"])
async def read_ai_tasks(
    session: SessionDep,
) -> list[models.AITask]:
    return session.exec(select(models.AITask)).all()


@app.post("/ai/tasks", tags=["ai_service"])
@catch
async def run_ai(image_id: int, wsi: bool, ontology: bool, roi_term_ids: List[int], roi_ids: List[int], ai_id: str, session: SessionDep):
    roi_term_ids = roi_term_ids if len(roi_term_ids) else None
    roi_term_ids = None if not ontology else roi_term_ids
    roi_term_ids = None if wsi else roi_term_ids

    roi_ids = roi_ids if len(roi_ids) else None
    roi_ids = None if ontology else roi_ids
    roi_ids = None if wsi else roi_ids
    return viewer.run_ai(image_id, roi_term_ids, roi_ids, ai_id, session)


@app.post("/ai/tasks/webhook", tags=["ai_service"])
@catch
async def webhook_for_ai_task_results(request: Request, session: SessionDep):
    data: dict = await request.json()
    return viewer.save_ai_result(data, session)


@app.post("/ai/tasks/retry", tags=["ai_service"])
async def retry_all_failed_ai_tasks(session: SessionDep):
    tasks = session.exec(
        select(models.AITask).where(models.AITask.status == models.AIUtils.Status.ERROR)
    ).all()
    for task in tasks:
        try:
            data: dict = json.loads(task.status_message)
            viewer.save_ai_result(data, session)
        except Exception as e:
            logger.error(f"Retry task {task.run_id} error occured: {e}")
            continue
    return "Success"


@app.post("/ai/tasks/clear", tags=["ai_service"])
async def clear_all_ai_tasks(session: SessionDep):
    session.exec(delete(models.AITask))
    session.commit()
    return "Success"


@app.post(
    "/import/{filepath:path}",
    response_model=list[models.ImageInstance],
    summary=f"Import relative file from path {settings.pending_path}, and try to import medical images. (It may contained multiple valid medical images)",
    tags=["commands"],
)
@catch
async def import_image(filepath: str):
    return viewer.import_image(filepath)


@app.post("/clear", response_model=list[models.UploadedFile], tags=["commands"])
@catch
async def clear_failed_uploadfiles():
    return viewer.clear_failed_uplaodfiles()


if __name__ == "__main__":
    print("Viewer starting up...")
    try:
        viewer.startup()
    except Exception as e:
        print(e)
        sys.exit(1)
