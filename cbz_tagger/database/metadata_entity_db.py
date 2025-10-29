from cbz_tagger.database.base_db import BaseEntityDB
from cbz_tagger.entities.metadata_entity import MetadataEntity


class MetadataEntityDB(BaseEntityDB[MetadataEntity]):
    entity_class = MetadataEntity
