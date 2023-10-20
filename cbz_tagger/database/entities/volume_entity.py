from typing import List

import requests

from cbz_tagger.database.entities.base_entity import BaseEntity


class VolumeEntity(BaseEntity):
    entity_url: str = f"{BaseEntity.base_url}/manga"
    paginated: bool = False

    @classmethod
    def from_server_url(cls, query_params=None):
        entity_id = query_params["ids[]"][0]

        response = requests.get(f"{cls.entity_url}/{entity_id}/aggregate", timeout=60).json()
        return [cls(response)]

    @property
    def aggregate(self):
        return self.content.get("volumes", {})

    @property
    def volumes(self):
        volumes = {}
        for key, value in self.aggregate.items():
            chapters = list(value["chapters"].keys())
            # If a chapter appears in an incorrect volume remove it
            if key != "none":
                chapters = [c for c in chapters if float(c) >= float(key)]
            volumes[key] = chapters
        return volumes

    @property
    def chapters(self) -> List[str]:
        chapters = set()
        for value in self.aggregate.values():
            chapters.update(value["chapters"].keys())
        return [chapter for chapter in chapters if chapter != "none"]

    @property
    def chapter_count(self):
        return len(self.chapters)

    def get_volume(self, chapter_number: str) -> str:
        for volume, volume_contents in self.volumes.items():
            for chapter in volume_contents:
                if str(chapter_number) == chapter:
                    return volume
        return "none"
