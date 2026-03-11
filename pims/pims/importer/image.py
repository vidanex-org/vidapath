import logging
from lxml import etree
from pathlib import Path
from typing import List, Optional

from cytomine.models import UploadedFile, ImageGroupImageInstance

from pims.config import get_settings
from pims.importer.importer import run_import
from pims.importer.listeners import CytomineListener
from pims.schemas.operations import ImportResult, ImportSummary

logger = logging.getLogger("pims.app")


FILE_ROOT_PATH = Path(get_settings().root)
WRITING_PATH = Path(get_settings().writing_path)


class ImageImporter:
    def __init__(self, base_path: Path, cytomine_auth, user, storage_id) -> None:
        self.base_path = base_path
        self.cytomine_auth = cytomine_auth
        self.user = user
        self.storage_id = storage_id

    def get_images(self) -> None:
        dataset_xml_path = self.base_path / "METADATA" / "dataset.xml"
        tree = etree.parse(dataset_xml_path)
        root = tree.getroot()

        images = root.findall(".//IMAGE_REF")
        return [image.get("alias") for image in images]

    def import_image(self, alias: str, projects: List[str]) -> ImportResult:
        image_path = self.base_path / "IMAGES" / alias
        if not image_path.exists():
            logger.warning(f"'{image_path}' does not exist!")
            return ImportResult(
                name=image_path.name,
                success=False,
                message="Image does not exist",
            )

        if is_already_imported(image_path, Path(FILE_ROOT_PATH)):
            logger.warning(f"'{image_path}' already imported!")
            return ImportResult(
                name=image_path.name,
                success=True,
                message="Already imported",
            )

        tmp_path = Path(WRITING_PATH, image_path.name)
        tmp_path.symlink_to(image_path, target_is_directory=image_path.is_dir())

        uploadedFile = UploadedFile(
            original_filename=image_path.name,
            filename=str(tmp_path),
            size=image_path.size,
            ext="",
            content_type="",
            id_projects=[],
            id_storage=self.storage_id,
            id_user=self.user.id,
            status=UploadedFile.UPLOADED,
        )

        cytomine_listener = CytomineListener(
            self.cytomine_auth,
            uploadedFile,
            projects=projects,
            user_properties=iter([]),
        )

        try:
            run_import(
                tmp_path,
                image_path.name,
                extra_listeners=[cytomine_listener],
            )

            return ImportResult(name=image_path.name, success=True)
        except Exception as e:
            logger.error(f"Failed to import '{image_path.name}': {e}")
            return ImportResult(name=image_path.name, success=False, message=str(e))

    def run(self, projects=[]) -> ImportSummary:
        logger.info("[START] Import images...")
        results = [self.import_image(image, projects) for image in self.get_images()]
        successful = sum(1 for r in results if r.success)
        logger.info("[END] Import images...")

        return ImportSummary(
            total=len(results),
            successful=successful,
            failed=len(results) - successful,
            results=results,
        )

    def run_easy(self, file_path: Path, projects: List[str], imagegroup_id: Optional[int] = None) -> ImportResult:
        """
        简化版导入方法，用于导入单个文件
        :param file_path: 要导入的文件路径
        :param projects: 项目列表
        :param imagegroup_id: 图像组ID (可选)
        :return: 导入结果
        """
        logger.info(f"[START] Importing single image: {file_path.name}")

        if not file_path.exists():
            logger.warning(f"'{file_path}' does not exist!")
            return ImportResult(
                name=file_path.name,
                success=False,
                message="Image does not exist",
            )

        if is_already_imported(file_path, Path(FILE_ROOT_PATH)):
            logger.warning(f"'{file_path}' already imported!")
            return ImportResult(
                name=file_path.name,
                success=True,
                message="Already imported",
            )

        if not WRITING_PATH.exists():
            WRITING_PATH.mkdir(parents=True, exist_ok=True)

        tmp_path = Path(WRITING_PATH, file_path.name)
        # Remove existing symlink/file if it exists to avoid FileExistsError
        if tmp_path.exists() or tmp_path.is_symlink():
            tmp_path.unlink()

        tmp_path.symlink_to(file_path, target_is_directory=file_path.is_dir())

        uploadedFile = UploadedFile(
            original_filename=file_path.name,
            filename=str(tmp_path),
            size=file_path.stat().st_size,
            ext="",
            content_type="",
            id_projects=[],
            id_storage=self.storage_id,
            id_user=self.user.id,
            status=UploadedFile.UPLOADED,
        )

        cytomine_listener = CytomineListener(
            self.cytomine_auth,
            uploadedFile,
            projects=projects,
            user_properties=iter([]),
        )

        try:
            run_import(
                filepath=tmp_path,
                name=file_path.name,
                store_path=file_path,
                extra_listeners=[cytomine_listener],
            )

            # After successful import, associate with image group if needed
            if imagegroup_id:
                if cytomine_listener.images:
                    # cytomine_listener.images is a list of tuples (AbstractImage, List[ImageInstance])
                    # For a single file import, there's only one tuple.
                    # We associate the first instance with the group.
                    instances = cytomine_listener.images[0][1]
                    if instances:
                        image_instance_id = instances[0].id
                        logger.info(f"Associating image instance {image_instance_id} with group {imagegroup_id}")
                        try:
                            ImageGroupImageInstance(
                                id_image_group=imagegroup_id,
                                id_image_instance=image_instance_id
                            ).save()
                        except Exception as e:
                            logger.error(f"Failed to associate image instance {image_instance_id} with group {imagegroup_id}: {e}")
                            # Do not fail the whole import, just log the error
                else:
                    logger.warning(f"Import of {file_path.name} was successful but could not find created image instance to associate with group.")

            logger.info(f"[END] Importing single image: {file_path.name}")
            return ImportResult(name=file_path.name, success=True)
        except Exception as e:
            logger.error(f"Failed to import '{file_path.name}': {e}")
            return ImportResult(name=file_path.name, success=False, message=str(e))


def is_already_imported(image_path: Path, data_path: Path) -> bool:
    """Check if an image was already imported."""

    for upload_dir in data_path.iterdir():
        if not upload_dir.is_dir():
            continue

        for candidate in upload_dir.iterdir():
            if candidate.is_symlink() and candidate.resolve() == image_path.resolve():
                return True

    return False