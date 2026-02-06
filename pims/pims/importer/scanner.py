import logging
import threading
import time
from redis import Redis
from pathlib import Path

from cytomine import Cytomine
from cytomine.models import ProjectCollection, StorageCollection, User

from pims.config import get_settings
from pims.importer.utils import iter_importable_files, FileImportCache, process_import_batch
from pims.schemas.auth import CytomineAuth

logger = logging.getLogger("pims.app")

class AutoImportScanner(threading.Thread):
    def __init__(self):
        super().__init__()
        self.settings = get_settings()
        self.interval = self.settings.auto_import_scan_interval
        # Force sync client for the thread
        self.redis = Redis.from_url(self.settings.cache_url, decode_responses=True)
        self.stop_event = threading.Event()
        
        self.lock_key = self.settings.import_lock_key
        self.dataset_root = Path(self.settings.dataset_path)
        
        # Initialize FileImportCache
        self.file_cache = FileImportCache(
            self.settings.cache_url, 
            self.settings.processed_files_cache_key
        )

    def run(self):
        logger.info(f"AutoImportScanner initialized. Enabled: {self.settings.enable_auto_import_scan}, Interval: {self.interval}s")
        while not self.stop_event.is_set():
            if self.settings.enable_auto_import_scan:
                try:
                    self.scan_cycle()
                except Exception as e:
                    logger.error(f"Error during auto scan cycle: {e}", exc_info=True)
            
            # Sleep with check for stop event
            if self.stop_event.wait(self.interval):
                break
        logger.info("AutoImportScanner stopped.")

    def stop(self):
        self.stop_event.set()

    def acquire_lock(self):
        # NX=True ensures we only set it if it doesn't exist, ex=1800 (30 min expiration)
        return self.redis.set(self.lock_key, "locked", ex=1800, nx=True)

    def release_lock(self):
        self.redis.delete(self.lock_key)

    def scan_cycle(self):
        start_time = time.time()
        logger.debug("Attempting to acquire import lock...")
        
        if not self.acquire_lock():
            logger.debug("Auto scan skipped: Import lock is held by another process.")
            return

        logger.debug("Import lock acquired. Starting scan...")
        try:
            self._do_scan()
        finally:
            self.release_lock()
            duration = time.time() - start_time
            logger.info(f"Scan cycle finished in {duration:.2f}s. Lock released.")

    def _do_scan(self):
        if not self.dataset_root.exists():
            logger.warning(f"Dataset root {self.dataset_root} does not exist. Skipping scan.")
            return

        # Prepare Cytomine connection
        cytomine_auth = CytomineAuth(
            host=self.settings.internal_url_core,
            public_key=self.settings.cytomine_public_key,
            private_key=self.settings.cytomine_private_key,
        )

        with Cytomine(**cytomine_auth.model_dump(), configure_logging=False) as c:
            if not c.current_user:
                c.set_credentials(self.settings.cytomine_public_key, self.settings.cytomine_private_key)
                if not c.current_user:
                     logger.error("Auto scan authentication failed.")
                     return

            # Find target storage
            storages = StorageCollection().fetch()
            if not storages:
                logger.error("No storage found for auto-import.")
                return
            
            target_username = self.settings.auto_import_target_storage_username
            storage_id = None
            
            # Try to find storage owned by target user
            for storage in storages:
                try:
                    storage_user = User().fetch(storage.user)
                    if storage_user and storage_user.username == target_username:
                        storage_id = storage.id
                        logger.info(f"Selected storage '{storage.name}' (ID: {storage_id}) owned by user '{target_username}'.")
                        break
                except Exception:
                    continue
            
            # Fallback
            if not storage_id:
                storage_id = storages[0].id
                logger.warning(f"Target storage for user '{target_username}' not found. Falling back to storage ID: {storage_id}")

            # Cache projects to avoid repeated API calls
            project_collection = ProjectCollection().fetch()
            projects = {project.name: project for project in project_collection}
            
            name_length = self.settings.easy_import_project_name_length
            name_offset = self.settings.easy_import_project_name_offset
            easy_import_enable_folder_based = self.settings.easy_import_enable_folder_based

            # Create iterator
            file_iterator = iter_importable_files(
                self.dataset_root, name_offset, name_length, easy_import_enable_folder_based
            )

            # Process batch
            summary = process_import_batch(
                file_iterator=file_iterator,
                file_cache=self.file_cache,
                projects=projects,
                cytomine_auth=cytomine_auth,
                current_user=c.current_user,
                storage_id=storage_id
            )
            
            if summary.total > 0:
                logger.info(f"Auto-scan cycle finished. Processed: {summary.successful}, Failed: {summary.failed}")