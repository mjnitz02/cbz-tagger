import json
import re
from typing import Dict
from typing import Optional
from xml.dom import minidom
from xml.etree import ElementTree

from cbz_tagger.common.helpers import get_input
from cbz_tagger.database.base_db import BaseEntityDB
from cbz_tagger.database.chapter_entity_db import ChapterEntityDB
from cbz_tagger.database.cover_entity_db import CoverEntityDB
from cbz_tagger.database.entities.author_entity import AuthorEntity
from cbz_tagger.database.entities.metadata_entity import MetadataEntity
from cbz_tagger.database.entities.volume_entity import VolumeEntity


class AuthorEntityDB(BaseEntityDB):
    entity_class = AuthorEntity


class MetadataEntityDB(BaseEntityDB):
    entity_class = MetadataEntity


class VolumeEntityDB(BaseEntityDB):
    entity_class = VolumeEntity


class EntityDB:
    def __init__(
        self,
        entity_map=None,
        entity_names=None,
        entity_downloads=None,
        metadata=None,
        covers=None,
        authors=None,
        volumes=None,
        chapters=None,
    ):
        self.entity_map: Dict[str, str] = {} if entity_map is None else entity_map
        self.entity_names: Dict[str, str] = {} if entity_names is None else entity_names
        self.entity_downloads = [] if entity_downloads is None else entity_downloads

        self.metadata: MetadataEntityDB = MetadataEntityDB() if metadata is None else metadata
        self.covers: CoverEntityDB = CoverEntityDB() if covers is None else covers
        self.authors: AuthorEntityDB = AuthorEntityDB() if authors is None else authors
        self.volumes: VolumeEntityDB = VolumeEntityDB() if volumes is None else volumes
        self.chapters: ChapterEntityDB = ChapterEntityDB() if volumes is None else chapters

    def __getitem__(self, manga_name) -> str:
        return self.entity_map.get(manga_name)

    def __len__(self):
        return len(self.entity_map)

    def keys(self):
        return self.entity_map.keys()

    def to_json(self):
        content = {
            "entity_map": self.entity_map,
            "entity_names": self.entity_names,
            "entity_downloads": self.entity_downloads,
            "metadata": self.metadata.to_json(),
            "covers": self.covers.to_json(),
            "authors": self.authors.to_json(),
            "volumes": self.volumes.to_json(),
            "chapters": self.chapters.to_json(),
        }
        return json.dumps(content)

    @classmethod
    def from_json(cls, json_data):
        content = json.loads(json_data)
        return cls(
            entity_map=content["entity_map"],
            entity_names=content["entity_names"],
            entity_downloads=content["entity_downloads"],
            metadata=MetadataEntityDB.from_json(content["metadata"]),
            covers=CoverEntityDB.from_json(content["covers"]),
            authors=AuthorEntityDB.from_json(content["authors"]),
            volumes=VolumeEntityDB.from_json(content["volumes"]),
            chapters=ChapterEntityDB.from_json(content["chapters"]),
        )

    def search(self, search_term: Optional[str] = None):
        if search_term is None:
            search_term = input("Enter a new name to search for: ")

        entity = None
        while entity is None:
            entity = self.find_mangadex_entry(search_term)
            if entity is None:
                search_term = input("Enter a new name to search for: ")
        entity_id = entity.entity_id

        print("Select a storage name for the series:")
        counter = 0
        for title in entity.all_titles:
            print(f"{counter+1}. {title}")
            counter += 1
        choice = get_input("Please select the manga that you are searching for in number: ", counter + 1)
        entity_name = entity.all_titles[choice - 1]

        return entity_id, entity_name

    def add(self, manga_name):
        entity_id, entity_name = self.search(manga_name)
        self.entity_map[manga_name] = entity_id
        self.entity_names[manga_name] = entity_name

    def add_without_search(self, manga_name, entity_name, entity_id):
        if manga_name in self.entity_map:
            print(f"Entity {manga_name} already exists in the database.")
            return
        self.entity_map[manga_name] = entity_id
        self.entity_names[manga_name] = entity_name

    def find_mangadex_entry(self, search_term):
        print(f">>> SEARCHING MANGADEX FOR NEW SERIES [{search_term}]")
        meta_entries = MetadataEntity.from_server_url(query_params={"title": search_term})

        counter = 0
        for manga in meta_entries:
            print(f"{counter+1}. {manga.title} ({manga.alt_title}) - {manga.created_at.year} - {manga.age_rating}")
            counter += 1
        print(" ")
        print("!!! INPUT -1 TO ENTER A NEW NAME TO SEARCH FOR IF THESE RESULTS ARE BAD !!!")
        choice = get_input(
            "Please select the manga that you are searching for in number: ", counter + 1, allow_negative_exit=True
        )
        if choice < 0:
            return None

        entity = meta_entries[choice - 1]
        return entity

    def update_manga_entity(self, manga_name, filepath=None):
        entity_id = self.entity_map.get(manga_name)
        if entity_id is not None:
            # Update the standard collections
            self.chapters.update(entity_id)
            self.metadata.update(entity_id)
            self.volumes.update(entity_id)
            self.covers.update(entity_id)

            # Get authors from the metadata
            metadata = self.metadata[entity_id]
            self.authors.update(metadata.author_entities)

            # Update missing covers
            if filepath is not None:
                self.covers.download(entity_id, filepath)

    def clean(self, image_db_path):
        print("Cleaning orphaned covers...")
        self.covers.remove_orphaned_covers(image_db_path)

    def clean_entity_name(self, entity_name):
        entity_name = re.sub(r"[^A-Za-z0-9 ]+", " ", entity_name)
        entity_name = " ".join(entity_name.split())
        return entity_name

    def to_entity_name(self, manga_name) -> Optional[str]:
        entity_name = self.entity_names.get(manga_name)
        if entity_name is None:
            return None
        return self.clean_entity_name(entity_name)

    def to_local_image_file(self, manga_name, chapter_number) -> Optional[str]:
        entity_id = self.entity_map.get(manga_name)

        volume = self.volumes[entity_id].get_volume(chapter_number)
        cover_entity = None
        if volume != "none":
            cover_entity = next((cover for cover in self.covers[entity_id] if cover.volume == volume), None)
        if cover_entity is None:
            cover_art_entity_id = self.metadata[entity_id].cover_art_id
            cover_entity = next(cover for cover in self.covers[entity_id] if cover.entity_id == cover_art_entity_id)

        return cover_entity.local_filename if cover_entity else None

    def to_xml_tree(self, manga_name, chapter_number) -> ElementTree:
        entity_id = self.entity_map.get(manga_name)
        if entity_id is None:
            raise ValueError(f"Could not find an entity for {manga_name}")

        # build a tree structure
        root = ElementTree.Element("ComicInfo")
        root.attrib["xmlns:xsi"] = "http://www.w3.org/2001/XMLSchema-instance"
        root.attrib["xmlns:xsd"] = "http://www.w3.org/2001/XMLSchema"

        # Lookup the authors
        author = self.authors[self.metadata[entity_id].author_id]
        artist = self.authors[self.metadata[entity_id].artist_id]

        author_name = author.name if author else None
        artist_name = artist.name if artist else author_name

        def assign(cix_entry, md_entry):
            if md_entry is not None:
                ElementTree.SubElement(root, cix_entry).text = f"{md_entry}"

        assign("Series", self.metadata[entity_id].title)
        assign("LocalizedSeries", self.metadata[entity_id].alt_title)
        assign("Number", chapter_number)
        assign("Count", self.volumes[entity_id].chapter_count if self.metadata[entity_id].completed else -1)
        assign("Volume", self.volumes[entity_id].get_volume(chapter_number))
        assign("Summary", self.metadata[entity_id].description)
        assign("Year", self.metadata[entity_id].created_at.year)
        assign("Month", self.metadata[entity_id].created_at.month)
        assign("Day", self.metadata[entity_id].created_at.day)
        assign("Writer", author_name)
        assign("Penciller", artist_name)
        assign("Inker", artist_name)
        assign("Colorist", artist_name)
        assign("Letterer", artist_name)
        assign("CoverArtist", artist_name)
        assign("LanguageISO", "en")
        assign("Manga", "Yes")
        assign("Genre", ",".join(self.metadata[entity_id].genres))
        assign("AgeRating", self.metadata[entity_id].age_rating)
        assign("Web", f"https://mangadex.org/title/{entity_id}")
        return root

    def to_xml_string(self, manga_name, chapter_number) -> str:
        root = self.to_xml_tree(manga_name, chapter_number)
        xmlstr = minidom.parseString(ElementTree.tostring(root)).toprettyxml()
        return xmlstr
