import logging
import os
import shutil
import time
from datetime import datetime
from typing import Dict
from zipfile import BadZipFile

from cbz_tagger.database.entity_db import EntityDB
from cbz_tagger.entities.cbz_entity import CbzEntity

logger = logging.getLogger()


class FileScanner:
    def __init__(
        self, config_path, scan_path, storage_path, add_missing=True, environment: Dict[str, str] = None
    ) -> None:
        self.config_path = config_path
        self.scan_path = scan_path
        self.storage_path = storage_path
        self.environment = environment

        self.add_missing = add_missing
        self.entity_database = EntityDB.load(root_path=self.config_path)
        self.recently_updated = []

    def reload_scanner(self):
        self.entity_database = EntityDB.load(root_path=self.config_path)

    def to_state(self):
        return self.entity_database.to_state()

    def run(self):
        logger.info("File scanner started. %s", datetime.now())
        # Reload the entity database at the start of a run to make sure it is up to date
        self.entity_database = EntityDB.load(root_path=self.config_path)
        self.run_scan()

        # If we have tracked entities, refresh the database to scan for new downloads and manga updates
        if self.entity_database.has_tracked_entities:
            self.entity_database.refresh(self.storage_path)

    def run_scan(self):
        self.entity_database = EntityDB.load(root_path=self.config_path)
        self.recently_updated = []
        while True:
            completed = self.scan()
            if not completed:
                logger.info("Scan not completed. Sleeping 120s")
                time.sleep(120)
                logger.info("Initiating rescan...")
            else:
                logger.info("Scan completed.")
                return

    def scan(self):
        logger.info("Starting scan....")
        for filepath in self.get_cbz_files():
            try:
                self.process(filepath)
            except BadZipFile:
                logger.error("Unable to read file... files are either in use or corrupted.")
                return False

        # Remove empty directories
        folders = [f[0] for f in list(os.walk(self.scan_path))[1:]]
        for folder in folders:
            if len(os.listdir(folder)) == 0:
                shutil.rmtree(folder)
        return True

    def get_files(self):
        return [(root, filenames) for (root, _, filenames) in os.walk(self.scan_path)]

    def get_cbz_files(self):
        files = self.get_files()

        filepaths = [
            list(os.path.join(root, f) for f in filenames if os.path.splitext(f)[-1] == ".cbz")
            for (root, filenames) in files
        ]
        filepaths = sorted([os.path.relpath(item, self.scan_path) for items in filepaths for item in items])
        return filepaths

    def process(self, filepath):
        cbz_entity = CbzEntity(filepath, self.config_path, self.scan_path, self.storage_path)
        entity_name, entity_xml, entity_image_path = self.get_cbz_comicinfo_and_image(cbz_entity)
        if entity_name:
            cbz_entity.build(entity_name, entity_xml, entity_image_path, environment=self.environment)

    def get_cbz_comicinfo_and_image(self, cbz_entity: CbzEntity):
        manga_name, chapter_number = cbz_entity.get_name_and_chapter()
        logger.info("%s, %s, %s", cbz_entity.filepath, manga_name, chapter_number)

        try:
            # If we haven't updated the metadata on this scan, update the metadata records
            if self.entity_database.check_manga_missing(manga_name):
                if not self.add_missing:
                    raise RuntimeError("Manual mode must be enabled for adding missing manga to the database.")
                self.entity_database.add(manga_name)

            if manga_name not in self.recently_updated:
                self.entity_database.update_manga_entity_name(manga_name)
                self.recently_updated.append(manga_name)

            entity_name, entity_xml, entity_image_path = self.entity_database.get_comicinfo_and_image(
                manga_name, chapter_number
            )
            if entity_name is None:
                raise RuntimeError(f"ERROR >> {manga_name} not in database. Run manual mode to add new series.")
            return entity_name, entity_xml, entity_image_path

        except (RuntimeError, EnvironmentError) as err:
            logger.error("ERROR >> %s not in database. Run manual mode to add new series. %s", manga_name, err)
            return None, None, None

    def add_tracked_entity(self):
        self.entity_database.add(None, track=True)

    def remove_tracked_entity(self):
        self.entity_database.remove()

    def delete_entity(self):
        self.entity_database.delete()

    def refresh(self):
        logger.info("Refreshing database...")
        self.entity_database.refresh(self.storage_path)

    def download_chapters(self, storage_path):
        self.entity_database.download_missing_chapters(storage_path)
