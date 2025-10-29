from cbz_tagger.database.base_db import BaseEntityDB
from cbz_tagger.entities.volume_entity import VolumeEntity


class VolumeEntityDB(BaseEntityDB[VolumeEntity]):
    entity_class = VolumeEntity
