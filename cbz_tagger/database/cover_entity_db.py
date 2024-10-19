import logging
import os
from io import BytesIO
from os import path
from typing import Dict
from typing import List

from PIL import Image

from cbz_tagger.database.base_db import BaseEntityDB
from cbz_tagger.entities.cover_entity import CoverEntity

logger = logging.getLogger()


class CoverEntityDB(BaseEntityDB):
    entity_class = CoverEntity
    database: Dict[str, List[CoverEntity]]
    query_param_field: str = "manga[]"

    def get_indexed_covers(self) -> List[str]:
        covers = []
        for _, cover_list in self.database.items():
            for cover_entity in cover_list:
                covers.append(cover_entity.local_filename)
        return sorted(covers)

    def get_local_covers(self, image_db_path) -> List[str]:
        return sorted(os.listdir(image_db_path))

    def get_orphaned_covers(self, image_db_path) -> List[str]:
        indexed_covers = self.get_indexed_covers()
        local_covers = self.get_local_covers(image_db_path)
        return [cover for cover in local_covers if cover not in indexed_covers]

    def remove_orphaned_covers(self, image_db_path):
        orphaned_covers = self.get_orphaned_covers(image_db_path)
        for cover in orphaned_covers:
            os.remove(path.join(image_db_path, cover))

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
