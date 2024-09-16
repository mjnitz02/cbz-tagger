from os import path

from cbz_tagger.entities.base_entity import BaseEntity


class CoverEntity(BaseEntity):
    entity_url: str = f"{BaseEntity.base_url}/cover"
    paginated: bool = True

    @property
    def manga_id(self) -> str:
        return next(rel["id"] for rel in self.relationships if rel.get("type") == "manga")

    @property
    def volume(self) -> str:
        return self.attributes["volume"]

    @property
    def filename(self) -> str:
        return self.attributes["fileName"]

    @property
    def local_filename(self) -> str:
        filename = self.filename
        if path.splitext(filename)[-1] == ".png":
            filename = f"{path.splitext(filename)[0]}.jpg"

        return filename

    @property
    def cover_url(self) -> str:
        return f"https://uploads.mangadex.org/covers/{self.manga_id}/{self.filename}"
