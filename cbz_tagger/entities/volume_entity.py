from typing import List
from typing import Set
from typing import Tuple

from cbz_tagger.entities.base_entity import BaseEntity


class VolumeEntity(BaseEntity):
    entity_url: str = f"{BaseEntity.base_url}/manga"
    paginated: bool = False

    @classmethod
    def from_server_url(cls, query_params=None, **kwargs):
        entity_id = query_params["ids[]"][0]

        response = cls.request_with_retry(f"{cls.entity_url}/{entity_id}/aggregate")
        response_json = response.json()
        return [cls(response_json)]

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
    def volume_map(self) -> List[Tuple[str, float, float]]:
        volume_list = []
        for volume_key, volume in self.volumes.items():
            if volume_key == "none":
                continue
            volume = [float(chapter) for chapter in volume]
            volume_list.append((volume_key, min(volume)))

        volume_list = sorted(volume_list, key=lambda x: float(x[0]))
        volume_ends = [item[1] for item in volume_list][1:] + [999999]

        volume_map = []
        for (volume_key, volume_start), volume_end in zip(volume_list, volume_ends):
            volume_map.append((volume_key, volume_start, volume_end))

        return volume_map

    @property
    def chapters(self) -> Set[str]:
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
        for volume_number, volume_start, volume_end in self.volume_map:
            if volume_start <= float(chapter_number) < volume_end:
                return volume_number

        return "-1"
