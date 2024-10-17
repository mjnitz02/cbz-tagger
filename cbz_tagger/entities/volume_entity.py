from typing import List

import requests

from cbz_tagger.entities.base_entity import BaseEntity


class VolumeEntity(BaseEntity):
    entity_url: str = f"{BaseEntity.base_url}/manga"
    paginated: bool = False

    @classmethod
    def from_server_url(cls, query_params=None, **kwargs):
        entity_id = query_params["ids[]"][0]

        response = requests.get(f"{cls.entity_url}/{entity_id}/aggregate", timeout=60).json()
        return [cls(response)]

    @property
    def aggregate(self):
        return self.content.get("volumes", {})

    @property
    def volumes(self):
        volumes = {}
        for volume_key, volume in self.aggregate.items():
            volume_chapters = volume["chapters"]
            if isinstance(volume_chapters, dict):
                chapters = list(volume_chapters.keys())
                # If a chapter appears in an incorrect volume remove it
                chapters = [chapter for chapter in chapters if self.chapter_is_valid(volume_key, chapter)]
                volumes[volume_key] = chapters
        return volumes

    @property
    def chapters(self) -> List[str]:
        chapters = set()
        for volume_chapters in self.volumes.values():
            chapters.update(set(volume_chapters))
        return chapters

    @staticmethod
    def chapter_is_valid(volume_number, chapter_number):
        try:
            if volume_number == "none" and chapter_number != "none":
                return True
            if chapter_number != "none" and float(chapter_number) >= float(volume_number):
                return True
        except ValueError:
            pass
        return False

    @property
    def chapter_count(self):
        return len(self.chapters)

    def get_volume(self, chapter_number: str) -> str:
        for volume, volume_contents in self.volumes.items():
            for chapter in volume_contents:
                if str(chapter_number) == chapter:
                    return volume
        return "none"
