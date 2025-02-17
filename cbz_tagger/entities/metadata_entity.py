from datetime import datetime
from typing import List, Union
from typing import Optional

from cbz_tagger.common.enums import Emoji
from cbz_tagger.common.enums import Status
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
        return self.attributes["description"].get("en")

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
    def status(self) -> str:
        return self.attributes["status"]

    @property
    def status_indicator(self) -> str:
        if self.status == Status.ONGOING:
            return Emoji.CIRCLE_GREEN
        if self.status == Status.COMPLETED:
            return Emoji.CHECK_GREEN
        if self.status == Status.HIATUS:
            return Emoji.CIRCLE_YELLOW
        if self.status == Status.CANCELLED:
            return Emoji.CIRCLE_RED
        return Emoji.QUESTION_MARK

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
        genre_tags = sorted(set(tag for tag in tags if tag))
        if self.demographic and self.demographic not in genre_tags:
            genre_tags = [self.demographic] + genre_tags
        return genre_tags

    @property
    def demographic(self) -> Union[str, None]:
        return self.attributes.get("publicationDemographic").title()
