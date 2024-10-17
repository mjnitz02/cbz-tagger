from datetime import datetime
from typing import List
from typing import Optional

from cbz_tagger.entities.base_entity import BaseEntity


class MetadataEntity(BaseEntity):
    entity_url: str = f"{BaseEntity.base_url}/manga"
    paginated: bool = True

    @property
    def title(self) -> Optional[str]:
        return next((item for item in self.attributes["title"].values()), None)

    @property
    def alt_title(self) -> Optional[str]:
        return next((item["en"] for item in self.attributes["altTitles"] if "en" in item), None)

    @property
    def all_titles(self) -> List[str]:
        return [self.title] + list(list(item.values())[0] for item in self.attributes["altTitles"])

    @property
    def description(self) -> Optional[str]:
        return next((item for item in self.attributes["description"].values()), None)

    @property
    def updated(self) -> str:
        return self.attributes.get("updatedAt")

    @property
    def latest_chapter(self) -> str:
        return self.attributes.get("latestUploadedChapter")

    @property
    def completed(self) -> bool:
        return self.attributes["status"] == "completed"

    @property
    def age_rating(self) -> str:
        if self.attributes["contentRating"] == "suggestive":
            return "Teen"
        if self.attributes["contentRating"] == "erotica":
            return "Mature 17+"
        return "Everyone"

    @property
    def author_entities(self) -> List[str]:
        return list(set(item for item in (self.author_id, self.artist_id, self.creator_id) if item))

    @property
    def author_id(self) -> Optional[str]:
        return next((item["id"] for item in self.relationships if item["type"] == "author"), None)

    @property
    def artist_id(self) -> Optional[str]:
        return next((item["id"] for item in self.relationships if item["type"] == "artist"), None)

    @property
    def creator_id(self) -> Optional[str]:
        return next((item["id"] for item in self.relationships if item["type"] == "creator"), None)

    @property
    def cover_art_id(self) -> Optional[str]:
        return next((item["id"] for item in self.relationships if item["type"] == "cover_art"), None)

    @property
    def created_at(self) -> datetime:
        return datetime.strptime(self.attributes["createdAt"].split("+")[0], "%Y-%m-%dT%H:%M:%S")

    @property
    def genres(self) -> List[str]:
        tags = list(attr.get("attributes", {}).get("name", {}).get("en") for attr in self.attributes["tags"])
        return sorted(set(tag for tag in tags if tag))
