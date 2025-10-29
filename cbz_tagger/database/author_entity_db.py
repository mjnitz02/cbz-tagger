from cbz_tagger.database.base_db import BaseEntityDB
from cbz_tagger.entities.author_entity import AuthorEntity


class AuthorEntityDB(BaseEntityDB[AuthorEntity]):
    entity_class = AuthorEntity
