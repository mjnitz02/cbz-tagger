import math
from datetime import datetime
from typing import List, Optional, Union

from cbz_tagger.common.enums import Emoji, IgnoredTags, Status
from cbz_tagger.entities.base_entity import BaseEntity


class MetadataEntity(BaseEntity):
    entity_url: str = f"{BaseEntity.base_url}/manga"
    paginated: bool = True

    def __init__(self, content):
        super().__init__(content)
        # Descriptions are the largest metadata and can use a lot of unnecessary space
        # We only need the English description, so drop the rest
        if "description" in self.content.get("attributes", {}):
            self.content["attributes"]["description"] = {"en": self.content["attributes"]["description"].get("en", "")}

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
    def last_chapter(self) -> str:
        last_chapter_value = self.attributes.get("lastChapter")
        if last_chapter_value is None or len(last_chapter_value) == 0:
            return "-1"
        return str(int(math.floor(float(last_chapter_value))))

    @property
    def last_volume(self) -> str:
        return self.attributes.get("lastVolume")

    @property
    def completed(self) -> bool:
        return self.attributes["status"] == "completed"

    @property
    def status(self) -> str:
        return self.attributes["status"]

    @property
    def mylar_status(self) -> str:
        if self.completed:
            return "Ended"
        return "Continuing"

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
    def language(self) -> str:
        language_iso = self.attributes.get("originalLanguage", "en")
        if language_iso is None or len(language_iso) > 2:
            return "en"
        language_iso = language_iso.lower()
        return language_iso

    @property
    def genres(self) -> List[str]:
        tags = list(
            attr.get("attributes", {}).get("name", {}).get("en")
            for attr in self.attributes["tags"]
            if attr.get("id") not in IgnoredTags
        )
        genre_tags = sorted(set(tag for tag in tags if tag))
        if self.demographic and self.demographic not in genre_tags:
            genre_tags = [self.demographic] + genre_tags
        return genre_tags

    @property
    def demographic(self) -> Union[str, None]:
        demo = self.attributes.get("publicationDemographic")
        if demo:
            return demo.title()
        return None
