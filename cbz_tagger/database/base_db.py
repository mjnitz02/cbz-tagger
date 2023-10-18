import json
from typing import Union, List, Dict

from cbz_tagger.database.entities.base_entity import BaseEntityObject


class BaseEntityDB(BaseEntityObject):
    entity_class = None
    db: Dict[str, entity_class]
    query_param_field = "ids[]"

    def __init__(self, db=None):
        self.version = 2
        self.db = {} if db is None else db

    def __getitem__(self, entity_id) -> entity_class:
        return self.db.get(entity_id)

    def __len__(self):
        return len(self.db)

    def to_json(self):
        content = {}
        for key, value in self.db.items():
            if isinstance(value, list):
                content[key] = [v.to_json() for v in value]
            else:
                content[key] = value.to_json()
        return json.dumps(content)

    @classmethod
    def from_json(cls, json_str):
        db_contents = json.loads(json_str)
        db = {}
        for key, value in db_contents.items():
            db[key] = cls.entity_class.from_json(value)
        return cls(db=db)

    def update(self, entity_ids: Union[List[str], str], skip_on_exist=False):
        if not isinstance(entity_ids, list):
            entity_ids = [entity_ids]

        for entity_id in entity_ids:
            if skip_on_exist and entity_id in self.db:
                return

            content = self.entity_class.from_server_url(query_params={self.query_param_field: [entity_id]})
            self.db[entity_id] = content[0] if len(content) == 1 else content



