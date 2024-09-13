from cbz_tagger.common.helpers import unpaginate_request
from cbz_tagger.database.entities.base_entity import BaseEntity


class ChapterEntity(BaseEntity):
    entity_url: str = f"{BaseEntity.base_url}/manga"
    paginated: bool = False

    @classmethod
    def from_server_url(cls, query_params=None):
        entity_id = query_params["ids[]"][0]

        response = unpaginate_request(f"{cls.entity_url}/{entity_id}/feed")
        return [cls(data) for data in response]

    @property
    def chapter_number(self):
        return float(self.attributes.get("chapter"))

    @property
    def volume_number(self):
        return float(self.attributes.get("volume"))

    @property
    def translated_language(self):
        return self.attributes.get("translatedLanguage")

    @property
    def scanlation_group(self):
        group = next(iter(rel for rel in self.relationships if rel["type"] == "scanlation_group"), {})
        return group.get("id", "none")
