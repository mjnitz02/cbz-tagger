import math
from typing import Optional

from cbz_tagger.entities.base_entity import BaseEntity


class VolumeEntity(BaseEntity):
    entity_url: str = f"{BaseEntity.base_url}/manga"
    paginated: bool = False

    @classmethod
    def from_server_url(cls, query_params: Optional[dict] = None, **kwargs):
        if query_params is None:
            query_params = {}
        entity_id = query_params["ids[]"][0]

        response = cls.request_with_retry(f"{cls.entity_url}/{entity_id}/aggregate")
        response_json = response.json()
        return [cls(response_json)]

    @property
    def aggregate(self):
        volumes = self.content.get("volumes", {})
        if isinstance(volumes, list):
            return {}
        return volumes

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
    def volume_map(self) -> list[tuple[str, float, float]]:
        volume_list = []
        for volume_key, volume in self.volumes.items():
            # Volume may be defined with no keys
            if volume_key == "none":
                continue
            volume = [float(chapter) for chapter in volume]
            # Volume may be defined with no chapters
            if len(volume) == 0:
                continue
            volume_list.append((volume_key, min(volume), max(volume)))

        volume_list = sorted(volume_list, key=lambda x: float(x[0]))
        if len(volume_list) == 0:
            return [("-1", 0.0, 0.0)]

        final_volume_chapter = volume_list[-1][2] + 1.0
        volume_ends = [item[1] for item in volume_list][1:] + [final_volume_chapter]

        volume_map = []
        for idx, ((volume_key, volume_start, _), volume_end) in enumerate(zip(volume_list, volume_ends, strict=False)):
            if idx == 0:
                volume_start = 0.0
            volume_map.append((volume_key, volume_start, volume_end))

        return volume_map

    @property
    def last_volume(self):
        if len(self.volumes) == 0:
            return -1
        max_volume = max(float(key) for key in self.volumes if key != "none")
        return int(math.floor(max_volume))

    @property
    def chapters(self) -> set[str]:
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

    def get_volume(
        self, chapter_number: str, max_chapter_number: Optional[int] = None, cover_volumes: Optional[list[float]] = None
    ) -> str:
        volume_map = self.volume_map
        if len(volume_map) == 0:
            return "-1"

        if len(volume_map) == 1 and volume_map[0][0] == "-1":
            if max_chapter_number is not None and cover_volumes is not None and len(cover_volumes) > 1:
                # Create a synthetic volume map
                volume_map = []
                chapters_per_volume = max_chapter_number / len(cover_volumes)
                for idx, volume in enumerate(cover_volumes):
                    volume_start = idx * chapters_per_volume
                    volume_end = (idx + 1) * chapters_per_volume
                    volume_map.append((str(int(volume)), math.ceil(volume_start), math.ceil(volume_end)))
            else:
                return "-1"

        for volume_number, volume_start, volume_end in volume_map:
            if volume_start <= math.floor(float(chapter_number)) < volume_end:
                return volume_number

        # Attempt to allocate a synthetic volume
        chapter_num = float(chapter_number)
        if chapter_num > self.last_volume:
            # Determine the maximum chapters in a known volume
            max_volume_step = float(max(end - start for _, start, end in volume_map))
            last_volume = int(volume_map[-1][0])
            last_volume_chapter = float(volume_map[-1][2])
            # Determine the number of synthetic volumes
            synthetic_volumes = math.ceil((chapter_num - last_volume_chapter) / max_volume_step)
            if synthetic_volumes == 0:
                synthetic_volumes += 1
            return str(int(last_volume + synthetic_volumes))

        return "-1"
