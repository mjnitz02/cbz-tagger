from cbz_tagger.entities.base_entity import BaseEntity


class AuthorEntity(BaseEntity):
    entity_url: str = f"{BaseEntity.base_url}/author"
    paginated: bool = False

    @property
    def name(self) -> str:
        return self.attributes["name"]
