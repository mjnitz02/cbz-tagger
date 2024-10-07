import json
import os
import re
import shutil
from typing import Dict
from typing import Optional
from typing import Self
from xml.dom import minidom
from xml.etree import ElementTree
from zipfile import ZIP_DEFLATED
from zipfile import ZipFile

from cbz_tagger.common.helpers import get_input
from cbz_tagger.common.helpers import get_raw_input
from cbz_tagger.database.author_entity_db import AuthorEntityDB
from cbz_tagger.database.chapter_entity_db import ChapterEntityDB
from cbz_tagger.database.cover_entity_db import CoverEntityDB
from cbz_tagger.database.metadata_entity_db import MetadataEntityDB
from cbz_tagger.database.volume_entity_db import VolumeEntityDB
from cbz_tagger.entities.metadata_entity import MetadataEntity


class EntityDB:
    def __init__(
        self,
        root_path: str,
        entity_map=None,
        entity_names=None,
        entity_downloads=None,
        entity_tracked=None,
        metadata=None,
        covers=None,
        authors=None,
        volumes=None,
        chapters=None,
    ):
        self.root_path = root_path

        self.entity_map: Dict[str, str] = {} if entity_map is None else entity_map
        self.entity_names: Dict[str, str] = {} if entity_names is None else entity_names
        self.entity_downloads = set() if entity_downloads is None else entity_downloads
        self.entity_tracked = set() if entity_tracked is None else entity_tracked

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

    def entity_keys(self):
        return self.metadata.keys()

    @property
    def image_db_path(self) -> str:
        return os.path.join(self.root_path, "images")

    @property
    def has_tracked_entities(self) -> bool:
        return len(self.entity_tracked) > 0

    def save(self) -> None:
        entity_db_path = os.path.join(self.root_path, "entity_db.json")
        entity_database_json = self.to_json()

        os.makedirs(self.root_path, exist_ok=True)
        with open(entity_db_path, "w", encoding="UTF-8") as write_file:
            write_file.write(entity_database_json)

    def to_json(self):
        content = {
            "entity_map": self.entity_map,
            "entity_names": self.entity_names,
            "entity_downloads": list(self.entity_downloads),
            "entity_tracked": list(self.entity_tracked),
            "metadata": self.metadata.to_json(),
            "covers": self.covers.to_json(),
            "authors": self.authors.to_json(),
            "volumes": self.volumes.to_json(),
            "chapters": self.chapters.to_json(),
        }
        return json.dumps(content)

    @classmethod
    def load(cls, root_path) -> Self:
        entity_db_path = os.path.join(root_path, "entity_db.json")
        if os.path.exists(entity_db_path):
            with open(entity_db_path, "r", encoding="UTF-8") as read_file:
                json_data = read_file.read()
            return EntityDB.from_json(root_path, json_data)
        return EntityDB(root_path)

    @classmethod
    def from_json(cls, root_path, json_data):
        content = json.loads(json_data)
        return cls(
            root_path=root_path,
            entity_map=content["entity_map"],
            entity_names=content["entity_names"],
            entity_downloads=set(tuple(item) for item in content.get("entity_downloads", [])),
            entity_tracked=set(content.get("entity_tracked", [])),
            metadata=MetadataEntityDB.from_json(content["metadata"]),
            covers=CoverEntityDB.from_json(content["covers"]),
            authors=AuthorEntityDB.from_json(content["authors"]),
            volumes=VolumeEntityDB.from_json(content["volumes"]),
            chapters=ChapterEntityDB.from_json(content.get("chapters", "{}")),
        )

    def check_manga_missing(self, manga_name):
        return manga_name not in self.keys()

    def search(self, search_term: Optional[str] = None):
        if search_term is None:
            search_term = get_raw_input("Enter a new name to search for: ")

        entity = None
        while entity is None:
            entity = self.find_mangadex_entry(search_term)
            if entity is None:
                search_term = get_raw_input("Enter a new name to search for: ")
        entity_id = entity.entity_id

        print("Select a storage name for the series:")
        counter = 0
        for title in entity.all_titles:
            print(f"{counter+1}. {title}")
            counter += 1
        choice = get_input("Please select the manga that you are searching for in number: ", counter + 1)
        entity_name = entity.all_titles[choice - 1]

        return entity_id, entity_name

    def add(self, manga_name: Optional[str], update=True, track=False):
        entity_id, entity_name = self.search(manga_name)
        if manga_name is None:
            manga_name = self.clean_entity_name(entity_name)

        if manga_name not in self.entity_map:
            self.entity_map[manga_name] = entity_id
            self.entity_names[entity_id] = self.clean_entity_name(entity_name)
        else:
            print(f"Entity {manga_name} already exists in the database.")

        if update:
            self.update_manga_entity_id(entity_id)

        if track:
            self.entity_tracked.add(entity_id)
            if self.should_mark_all_tracked(manga_name):
                self.entity_downloads.update((entity_id, chapter.entity_id) for chapter in self.chapters[entity_id])

        self.save()

    @staticmethod
    def should_mark_all_tracked(manga_name):
        return get_input(f"Mark all chapters for {manga_name} as tracked? (y/n): ", 2) == 1

    @staticmethod
    def find_mangadex_entry(search_term):
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

    def update_manga_entity_name(self, manga_name):
        entity_id = self.entity_map.get(manga_name)
        self.update_manga_entity_id(entity_id)

    def update_manga_entity_id(self, entity_id):
        manga_name = self.entity_names.get(entity_id)
        if entity_id is not None:
            try:
                print(f"Checking for updates {manga_name}: {entity_id}")
                last_updated = None
                if self.metadata[entity_id] is not None:
                    last_updated = self.metadata[entity_id].updated

                self.metadata.update(entity_id)
                if last_updated == self.metadata[entity_id].updated:
                    return

                # Update the collections
                print(f"Updating {manga_name}: {entity_id}")
                self.chapters.update(entity_id)
                self.volumes.update(entity_id)
                self.covers.update(entity_id)
                self.authors.update(self.metadata[entity_id].author_entities)

                # Update missing covers
                self.covers.download(entity_id, self.image_db_path)

                # Save database on successful update, this makes each call slightly slower, but more reliable
                # since the APIs are prone to crashing
                self.save()

            except EnvironmentError:
                print(f"Mangadex API Down >> Unable to update {manga_name} metadata.")

    def refresh(self, storage_path):
        print("Refreshing database...")
        for entity_id in self.metadata.keys():
            self.update_manga_entity_id(entity_id)
        print("Cleaning orphaned covers...")
        self.covers.remove_orphaned_covers(self.image_db_path)
        print("Downloading missing chapters...")
        self.download_missing_chapters(storage_path)

    def download_chapter(self, entity_id, chapter_item, storage_path):
        if (entity_id, chapter_item.entity_id) in self.entity_downloads:
            return

        manga_name = next(iter(name for name, id in self.entity_map.items() if id == entity_id))
        chapter_name = f"{manga_name} - Chapter {chapter_item.chapter_string}"

        chapter_filepath = os.path.join(storage_path, manga_name, chapter_name)
        print(f"Downloading {chapter_name}...")
        try:
            os.makedirs(chapter_filepath, exist_ok=True)
            # Write the comicinfo.xml file
            entity_xml = self.to_xml_string(manga_name, chapter_item.chapter_string)
            with open(os.path.join(chapter_filepath, "ComicInfo.xml"), "w", encoding="UTF-8") as write_file:
                write_file.write(entity_xml)

            # Write the cover image
            cover_path = self.to_local_image_file(manga_name, chapter_item.chapter_string)
            entity_image_path = os.path.join(self.image_db_path, cover_path)
            with open(os.path.join(chapter_filepath, "000_cover.jpg"), "wb") as write_file:
                with open(entity_image_path, "rb") as read_file:
                    write_file.write(read_file.read())

            # Download the chapter images and write them to the folder
            self.chapters.download(entity_id, chapter_item.entity_id, chapter_filepath)

            cbz_files = sorted(f for f in os.listdir(chapter_filepath) if os.path.splitext(f)[-1] in (".jpg", ".xml"))
            with ZipFile(f"{chapter_filepath}.cbz", "w", ZIP_DEFLATED) as zip_write:
                for cbz_file in cbz_files:
                    zip_write.write(os.path.join(chapter_filepath, cbz_file), cbz_file)
            # Mark cbz creation as successful
            self.entity_downloads.add((entity_id, chapter_item.entity_id))
            # Save that the chapter was downloaded
            self.save()
            # Cleanup excess
            shutil.rmtree(chapter_filepath)
        except EnvironmentError as err:
            print(f"Could not download chapter: {entity_id}, {chapter_item.entity_id}", err)

    @staticmethod
    def clean_entity_name(entity_name):
        entity_name = re.sub(r"[^A-Za-z0-9 ]+", " ", entity_name)
        entity_name = " ".join(entity_name.split())
        return entity_name

    def to_entity_name(self, manga_name) -> Optional[str]:
        entity_id = self.entity_map.get(manga_name)
        if entity_id is None:
            return None
        return self.entity_names.get(entity_id)

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

    def get_comicinfo_and_image(self, manga_name, chapter_number):
        entity_name = self.to_entity_name(manga_name)
        if entity_name is None:
            return None, None, None
        entity_xml = self.to_xml_string(manga_name, chapter_number)
        entity_image_path = self.to_local_image_file(manga_name, chapter_number)
        return entity_name, entity_xml, entity_image_path

    def get_missing_chapters(self):
        missing_chapters = []
        for entity_id, chapter_items in self.chapters.database.items():
            if entity_id not in self.entity_tracked:
                continue
            for chapter_item in chapter_items:
                key = (entity_id, chapter_item.entity_id)
                if key not in self.entity_downloads:
                    missing_chapters.append((entity_id, chapter_item))
        return missing_chapters

    def download_missing_chapters(self, storage_path):
        missing_chapters = self.get_missing_chapters()
        for entity_id, chapter_item in missing_chapters:
            try:
                self.download_chapter(entity_id, chapter_item, storage_path)
            except EnvironmentError as err:
                print(f"Could not download chapter: {entity_id}, {chapter_item.entity_id}", err)
        return missing_chapters
