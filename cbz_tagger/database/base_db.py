import hashlib
import json
from typing import Generic
from typing import TypeVar
from typing import Union

from cbz_tagger.entities.base_entity import BaseEntity
from cbz_tagger.entities.base_entity import BaseEntityObject

T = TypeVar("T")


class BaseEntityDB(BaseEntityObject, Generic[T]):
    entity_class: type[BaseEntity]
    database: dict[str, T]
    query_param_field = "ids[]"

    def __init__(self, database=None):
        self.version = 2
        self.database = {} if database is None else database

    def __getitem__(self, entity_id) -> T | None:
        return self.database.get(entity_id)

    def __len__(self):
        return len(self.database)

    def keys(self):
        return self.database.keys()

    def to_json(self):
        content = {}
        for key, value in self.database.items():
            if isinstance(value, list):
                content[key] = [v.to_json() for v in value]  # type: ignore
            else:
                content[key] = value.to_json()  # type: ignore
        return json.dumps(content)

    @classmethod
    def from_json(cls, json_str):
        database_contents = json.loads(json_str)
        database = {}
        for key, value in database_contents.items():
            database[key] = cls.entity_class.from_json(value)
        return cls(database=database)

    def to_hash(self, entity_id: str) -> str:
        """
        Returns a hash of the entity content.
        This is useful for comparing entities or checking if they have changed.
        """
        entity_content = self.database.get(entity_id)
        if entity_content is None:
            return "0"

        if isinstance(entity_content, list):
            sha_1 = hashlib.sha1()
            for item in entity_content:
                sha_1.update(item.to_hash().encode("utf-8"))
            return sha_1.hexdigest()
        else:
            return entity_content.to_hash()  # type: ignore

    def update(self, entity_ids: Union[list[str], str], skip_on_exist=False, batch_response=False, **kwargs):
        if not isinstance(entity_ids, list):
            entity_ids = [entity_ids]

        if batch_response:
            contents = self.entity_class.from_server_url(query_params={self.query_param_field: [entity_ids]}, **kwargs)
            for content in contents:
                entity_id = content.entity_id
                if skip_on_exist and entity_id in self.database:
                    continue

                self.database[entity_id] = self.format_content_for_entity([content], entity_id)
        else:
            for entity_id in entity_ids:
                if skip_on_exist and entity_id in self.database:
                    return

                content = self.entity_class.from_server_url(
                    query_params={self.query_param_field: [entity_id]}, **kwargs
                )
                self.database[entity_id] = self.format_content_for_entity(content, entity_id)

    def format_content_for_entity(self, content, entity_id=None):
        _ = entity_id
        return content[0] if len(content) == 1 else content
