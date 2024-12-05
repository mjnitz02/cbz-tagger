import logging
import os
from io import BytesIO
from os import path
from typing import Dict
from typing import List
from typing import Set
from typing import Tuple

from PIL import Image

from cbz_tagger.database.base_db import BaseEntityDB
from cbz_tagger.entities.cover_entity import CoverEntity

logger = logging.getLogger()


class CoverEntityDB(BaseEntityDB):
    entity_class = CoverEntity
    database: Dict[str, List[CoverEntity]]
    query_param_field: str = "manga[]"

    def get_indexed_covers(self) -> List[Tuple[str, str]]:
        covers = []
        for entity_id, cover_list in self.database.items():
            for cover_entity in cover_list:
                covers.append((entity_id, cover_entity.local_filename))
        return covers

    @staticmethod
    def get_local_covers(image_db_path) -> List[str]:
        return sorted(os.listdir(image_db_path))

    def get_orphaned_covers(self, image_db_path) -> List[str]:
        indexed_covers = self.get_indexed_covers()
        indexed_cover_ids = [cover[1] for cover in indexed_covers]
        local_covers = self.get_local_covers(image_db_path)
        return [cover for cover in local_covers if cover not in indexed_cover_ids]

    def remove_orphaned_covers(self, image_db_path):
        orphaned_covers = self.get_orphaned_covers(image_db_path)
        for cover in orphaned_covers:
            os.remove(path.join(image_db_path, cover))

    def get_missing_covers(self, image_db_path) -> Set[str]:
        indexed_covers = self.get_indexed_covers()
        local_covers = self.get_local_covers(image_db_path)
        missing_covers = [item for item in indexed_covers if item[1] not in local_covers]
        missing_entities = set(item[0] for item in missing_covers)
        return missing_entities

    def download_missing_covers(self, image_db_path):
        missing_entities = self.get_missing_covers(image_db_path)
        for entity_id in missing_entities:
            self.download(entity_id, image_db_path)

    def get_latest_cover_for_entity(self, entity_id: str) -> CoverEntity:
        return sorted(self[entity_id], key=lambda x: x.attributes["createdAt"], reverse=True)[0]

    def format_content_for_entity(self, content, entity_id=None):
        _ = entity_id

        def _filter_content(original_content, locale):
            return [c for c in original_content if c.attributes["locale"] == locale]

        # Filter only english and japanese covers
        if len(_filter_content(content, "ja")) > 0:
            return _filter_content(content, "ja")
        if len(_filter_content(content, "en")) > 0:
            return _filter_content(content, "en")
        if len(_filter_content(content, "ko")) > 0:
            return _filter_content(content, "ko")
        if len(_filter_content(content, "zh")) > 0:
            return _filter_content(content, "zh")
        return content

    def download(self, entity_id: str, filepath: str):
        os.makedirs(filepath, exist_ok=True)
        for cover in self[entity_id]:
            image_path = path.join(filepath, cover.local_filename)
            if not path.exists(image_path):
                logger.info("Downloading: %s", cover.cover_url)
                image = cover.download_file(cover.cover_url)
                in_memory_image = Image.open(BytesIO(image))
                if in_memory_image.format != "JPEG":
                    in_memory_image = in_memory_image.convert("RGB")
                in_memory_image.save(image_path, quality=95, optimize=True)

    def get_cover_for_volume(self, entity_id, volume, default_cover_art_id):
        covers = self[entity_id]
        cover_entity = None
        if volume != "-1":
            cover_entity = next((cover for cover in covers if cover.volume == volume), None)
        if cover_entity is None:
            cover_entity = next((cover for cover in covers if cover.entity_id == default_cover_art_id), None)
            # If the art id was associated as a bad language in the databases, try to find the latest cover
            if cover_entity is None:
                cover_entity = self.get_latest_cover_for_entity(entity_id)

        return cover_entity
