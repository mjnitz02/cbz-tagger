import json
from typing import Dict
from typing import List
from typing import Union

from cbz_tagger.database.entities.base_entity import BaseEntityObject


class BaseEntityDB(BaseEntityObject):
    entity_class = None
    database: Dict[str, entity_class]
    query_param_field = "ids[]"

    def __init__(self, database=None):
        self.version = 2
        self.database = {} if database is None else database

    def __getitem__(self, entity_id) -> entity_class:
        return self.database.get(entity_id)

    def __len__(self):
        return len(self.database)

    def to_json(self):
        content = {}
        for key, value in self.database.items():
            if isinstance(value, list):
                content[key] = [v.to_json() for v in value]
            else:
                content[key] = value.to_json()
        return json.dumps(content)

    @classmethod
    def from_json(cls, json_str):
        database_contents = json.loads(json_str)
        database = {}
        for key, value in database_contents.items():
            database[key] = cls.entity_class.from_json(value)
        return cls(database=database)

    def update(self, entity_ids: Union[List[str], str], skip_on_exist=False):
        if not isinstance(entity_ids, list):
            entity_ids = [entity_ids]

        for entity_id in entity_ids:
            if skip_on_exist and entity_id in self.database:
                return

            content = self.entity_class.from_server_url(query_params={self.query_param_field: [entity_id]})
            self.database[entity_id] = self.format_content_for_entity(content, entity_id)

    def format_content_for_entity(self, content, entity_id=None):
        _ = entity_id
        return content[0] if len(content) == 1 else content
