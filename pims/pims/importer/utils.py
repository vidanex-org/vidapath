import logging
import os
import time
import re
from pathlib import Path
from typing import Generator, Tuple, Dict, Any, Optional
from redis import Redis
from cytomine.models import (
    Project, ImageGroup, ImageGroupCollection
)

from pims.importer.image import ImageImporter
from pims.schemas.operations import ImportSummary

logger = logging.getLogger("pims.app")


class FileImportCache:
    def __init__(self, redis_url: str, cache_key: str):
        self.redis = Redis.from_url(redis_url, decode_responses=True)
        self.cache_key = cache_key

    def should_process(self, file_path: Path) -> bool:
        """
        Check if the file needs processing based on its mtime and size.
        Returns True if the file is new or modified since last import.
        """
        if not file_path.exists():
            return False
            
        try:
            stat = file_path.stat()
            current_fingerprint = f"{stat.st_mtime}_{stat.st_size}"
            
            cached_fingerprint = self.redis.hget(self.cache_key, str(file_path))
            
            if cached_fingerprint == current_fingerprint:
                return False # Already processed and unchanged
            
            return True
        except OSError:
            return False

    def mark_processed(self, file_path: Path):
        """
        Mark the file as processed in Redis using its current mtime and size.
        """
        try:
            stat = file_path.stat()
            fingerprint = f"{stat.st_mtime}_{stat.st_size}"
            self.redis.hset(self.cache_key, str(file_path), fingerprint)
        except OSError:
            pass # File might have been moved/deleted


def iter_importable_files(
    dataset_root: Path, name_offset: int, name_length: int,
    project_name_strategy: str = "folder"
) -> Generator[Tuple[Path, Path, str, Optional[str]], None, None]:
    """
    Iterate over importable files in the dataset directory.
    This function now processes files in the root directory first, then iterates
    through subdirectories (buckets).

    Yields:
        Tuple[Path, Path, str, Optional[str]]: (bucket_path, file_path, project_name, imagegroup_name)
    """
    if not dataset_root.exists():
        logger.warning(f"Dataset root '{dataset_root}' does not exist!")
        return

    logger.info(f"Starting scan in root directory: {dataset_root}")

    min_required_len = name_offset + name_length

    # Blacklist of extensions and name patterns that should not be processed as images.
    INVALID_PATTERNS = ['.json', '.xml', '.txt', '.md', '.pdf', '.docx', '.xlsx', '.mip', 'dsmeta.zip', '.dsmeta']

    # Regex for pattern strategy, now capturing specimen type for image group.
    pattern_regex = re.compile(r"([A-Z]{1,2})(\d{4})([-_]?)(\d{4,5})-([A-Z0-9]{1})")

    def get_project_and_group_name(strategy: str, file_path: Path) -> Tuple[str, Optional[str]]:
        """Helper function to determine project and imagegroup name based on strategy."""
        stem = file_path.stem
        project_name, imagegroup_name = None, None

        if strategy == 'folder':
            project_name = file_path.parent.name
        elif strategy == 'substring':
            if len(stem) < min_required_len:
                logger.info(f"Skipping '{file_path}' - name too short for substring strategy (Required: {min_required_len}, Actual: {len(stem)}).")
            else:
                project_name = stem[name_offset : name_offset + name_length]
        elif strategy == 'pattern':
            match = pattern_regex.search(stem)
            if match:
                project_name = f"{match.group(1)}{match.group(2)}{match.group(3)}{match.group(4)}"
                imagegroup_name = match.group(5)
            else:
                logger.info(f"Skipping '{file_path}' - does not match pattern strategy.")
        else:
            logger.warning(f"Unknown project_name_strategy: {strategy}. Skipping file '{file_path}'")
        
        return project_name, imagegroup_name

    def is_invalid_file_type(file_path: Path) -> bool:
        """Helper to check if a file has a disallowed extension or name pattern."""
        lower_name = file_path.name.lower()
        if any(lower_name.endswith(pattern) for pattern in INVALID_PATTERNS):
            logger.info(f"Skipping '{file_path}' - file name/type is on the deny list.")
            return True
        return False

    # 1. Process files directly in the root directory
    logger.info(f"Scanning for files directly in root: {dataset_root}")
    for entry in os.scandir(dataset_root):
        if entry.is_file():
            file_path = Path(entry.path)
            if file_path.name.startswith('.') or is_invalid_file_type(file_path):
                continue
            
            project_name, imagegroup_name = get_project_and_group_name(project_name_strategy, file_path)
            if project_name:
                yield dataset_root, file_path, project_name, imagegroup_name

    # 2. Process files in subdirectories (buckets)
    for entry in os.scandir(dataset_root):
        if not entry.is_dir():
            continue

        bucket = Path(entry.path)
        logger.info(f"Entering bucket: {bucket}")

        # Recursively walk the bucket
        for root, dirs, files in os.walk(bucket):
            logger.info(f"Scanning directory: {root}")
            for file in files:
                file_path = Path(root) / file
                
                if file.startswith('.') or is_invalid_file_type(file_path):
                    continue

                project_name, imagegroup_name = get_project_and_group_name(project_name_strategy, file_path)
                if project_name:
                    yield bucket, file_path, project_name, imagegroup_name


def process_import_batch(
    file_iterator: Generator[Tuple[Path, Path, str, Optional[str]], None, None],
    file_cache: FileImportCache,
    projects: Dict[str, Project],
    cytomine_auth: Any,
    current_user: Any,
    storage_id: int
) -> ImportSummary:
    """
    Process a batch of files for import.
    Common logic used by both manual import and auto-scanner.
    """
    start_time = time.time()
    summary = ImportSummary()
    count_skipped = 0
    count_total_seen = 0
    # Cache for image groups to avoid repeated API calls within the batch
    image_groups_cache = {}

    logger.info("Starting batch import processing...")

    for bucket, file_path, project_name, imagegroup_name in file_iterator:
        count_total_seen += 1
        
        # Check if file has already been processed and unchanged
        if not file_cache.should_process(file_path):
            count_skipped += 1
            logger.info(f"Skipping '{file_path.name}' (cached, unchanged).")
            continue

        logger.info(f"Processing file: {file_path.name} (Project: {project_name}, Group: {imagegroup_name})")
        
        try:
            # Get or create project
            project = get_project(project_name, projects)
            
            imagegroup_id = None
            if imagegroup_name:
                cache_key = f"{project.id}-{imagegroup_name}"
                if cache_key in image_groups_cache:
                    imagegroup_id = image_groups_cache[cache_key]
                else:
                    groups = ImageGroupCollection(filters={'project': project.id}).fetch()
                    found_group = next((g for g in groups if g.name == imagegroup_name), None)
                    
                    if found_group:
                        imagegroup_id = found_group.id
                    else:
                        logger.info(f"Creating new ImageGroup '{imagegroup_name}' in project '{project_name}'.")
                        new_group = ImageGroup(name=imagegroup_name, id_project=project.id).save()
                        imagegroup_id = new_group.id
                    
                    image_groups_cache[cache_key] = imagegroup_id
            
            importer = ImageImporter(
                base_path=bucket,
                cytomine_auth=cytomine_auth,
                user=current_user,
                storage_id=storage_id,
            )
            
            result = importer.run_easy(file_path, projects=[project], imagegroup_id=imagegroup_id)
            
            summary.total += 1
            if result.success:
                file_cache.mark_processed(file_path)
                summary.successful += 1
                logger.info(f"[SUCCESS] Imported: {file_path.name}")
            else:
                summary.failed += 1
                logger.error(f"[FAILED] Import {file_path.name}: {result.message}")
            
            summary.results.append(result)

        except Exception as e:
            summary.failed += 1
            logger.error(f"[ERROR] Unexpected exception processing {file_path.name}: {e}", exc_info=True)

    duration = time.time() - start_time
    logger.info(f"Batch processing completed in {duration:.2f}s.")
    logger.info(f"Stats - Scanned: {count_total_seen}, Skipped (Cached): {count_skipped}, Processed: {summary.total}, Success: {summary.successful}, Failed: {summary.failed}")

    return summary


def get_project(key: str, projects: dict[str, Project]) -> Project:
    return projects.setdefault(key, Project(name=key).save())