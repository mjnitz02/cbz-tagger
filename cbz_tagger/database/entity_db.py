import json
import logging
import os
import re
import shutil
from typing import Any
from typing import Optional
from xml.dom import minidom
from xml.etree import ElementTree
from zipfile import ZIP_DEFLATED
from zipfile import ZipFile

from cbz_tagger.common.enums import Emoji
from cbz_tagger.common.enums import Plugins
from cbz_tagger.common.enums import Urls
from cbz_tagger.common.helpers import make_directory_with_ownership
from cbz_tagger.common.helpers import set_file_ownership
from cbz_tagger.common.input import InputEntity
from cbz_tagger.common.input import console_selector
from cbz_tagger.database.author_entity_db import AuthorEntityDB
from cbz_tagger.database.chapter_entity_db import ChapterEntityDB
from cbz_tagger.database.cover_entity_db import CoverEntityDB
from cbz_tagger.database.metadata_entity_db import MetadataEntityDB
from cbz_tagger.database.volume_entity_db import VolumeEntityDB

logger = logging.getLogger()


class EntityDB:
    def __init__(
        self,
        root_path: str,
        entity_map=None,
        entity_names=None,
        entity_downloads=None,
        entity_tracked=None,
        entity_chapter_plugin=None,
        metadata=None,
        covers=None,
        authors=None,
        volumes=None,
        chapters=None,
    ):
        self.root_path = root_path

        self.entity_map: dict[str, str] = {} if entity_map is None else entity_map
        self.entity_names: dict[str, str] = {} if entity_names is None else entity_names
        self.entity_downloads = set() if entity_downloads is None else entity_downloads
        self.entity_tracked = set() if entity_tracked is None else entity_tracked
        self.entity_chapter_plugin: dict[str, Any] = {} if entity_chapter_plugin is None else entity_chapter_plugin

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
            "entity_chapter_plugin": self.entity_chapter_plugin,
            "metadata": self.metadata.to_json(),
            "covers": self.covers.to_json(),
            "authors": self.authors.to_json(),
            "volumes": self.volumes.to_json(),
            "chapters": self.chapters.to_json(),
        }
        return json.dumps(content)

    @classmethod
    def load(cls, root_path) -> "EntityDB":
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
            entity_chapter_plugin=content.get("entity_chapter_plugin", {}),
            metadata=MetadataEntityDB.from_json(content["metadata"]),
            covers=CoverEntityDB.from_json(content["covers"]),
            authors=AuthorEntityDB.from_json(content["authors"]),
            volumes=VolumeEntityDB.from_json(content["volumes"]),
            chapters=ChapterEntityDB.from_json(content.get("chapters", "{}")),
        )

    def to_state(self):
        state = []
        for entity_name, entity_id in self.entity_map.items():
            entity_metadata = self.metadata[entity_id]
            latest_chapter = self.chapters.get_latest_chapter(entity_id)
            plugin_type = self.entity_chapter_plugin.get(entity_id, {}).get("plugin_type", Plugins.MDX)
            plugin_id = self.entity_chapter_plugin.get(entity_id, {}).get("plugin_id", entity_id)
            state.append(
                {
                    "entity_name": {
                        "name": entity_name if len(entity_name) < 51 else f"{entity_name[:50]}...",
                        "link": f"{Plugins.TITLE_URLS[Plugins.MDX]}{entity_id}",
                    },
                    "entity_id": entity_id,
                    "updated": entity_metadata.updated,
                    "latest_chapter": latest_chapter.chapter_number if latest_chapter else None,
                    "latest_chapter_date": latest_chapter.updated_date if latest_chapter else None,
                    "status": entity_metadata.status_indicator,
                    "plugin": {"name": plugin_type, "link": f"{Plugins.TITLE_URLS[plugin_type]}{plugin_id}"},
                    "tracked": Emoji.CIRCLE_GREEN if entity_id in self.entity_tracked else Emoji.CIRCLE_BROWN,
                }
            )
        state = sorted(state, key=lambda d: d["entity_name"]["name"].lower())
        return state

    def check_manga_missing(self, manga_name):
        return manga_name not in self.keys()

    @staticmethod
    def search(manga_name: Optional[str] = None):
        """This is a temporary abstraction to the new class"""
        return InputEntity.search(manga_name)

    def add(self, manga_name: Optional[str], update=True, track=False):
        entity_id, entity_name = self.search(manga_name)

        if track:
            backend = InputEntity.select_a_chapter_backend()
            mark_as_tracked = InputEntity.should_mark_all_tracked(manga_name)
        else:
            backend = None
            mark_as_tracked = False

        self.add_entity(
            entity_name,
            entity_id,
            manga_name=manga_name,
            backend=backend,
            update=update,
            track=track,
            mark_as_tracked=mark_as_tracked,
        )

    def add_entity(
        self, entity_name, entity_id, manga_name=None, backend=None, update=True, track=False, mark_as_tracked=False
    ):
        if manga_name is None:
            manga_name = self.clean_entity_name(entity_name)

        if manga_name not in self.entity_map:
            self.entity_map[manga_name] = entity_id
            self.entity_names[entity_id] = self.clean_entity_name(entity_name)
        else:
            logger.warning("Entity %s (%s) already exists in the database.", manga_name, entity_id)
            return

        if track:
            if backend is not None:
                self.entity_chapter_plugin[entity_id] = backend

        if update:
            self.update_manga_entity_id(entity_id)

        if track:
            logger.info("Tracking: %s (%s)", entity_name, entity_id)
            self.entity_tracked.add(entity_id)
            if mark_as_tracked:
                logger.info("Marking all chapters as downloaded. %s (%s)", entity_name, entity_id)
                self.entity_downloads.update((entity_id, chapter.entity_id) for chapter in self.chapters[entity_id])
            else:
                logger.info("No chapters marked as downloaded. %s (%s)", entity_name, entity_id)

        self.save()

    def remove(self):
        tracked_ids = list(self.entity_tracked)
        choices = list(f"{self.entity_names[entity_id]} ({entity_id})" for entity_id in tracked_ids)
        choice = console_selector(
            choices, "Select a manga to remove tracking for", "Please select the local and storage name number"
        )

        # Remove the entity from tracking
        entity_id_to_remove = tracked_ids[choice - 1]
        self.remove_entity_id_from_tracking(entity_id_to_remove)

    def delete(self):
        all_ids = list(self.entity_map.items())
        choices = list(f"{name} ({entity_id})" for name, entity_id in all_ids)
        choice = console_selector(
            choices, "Select a manga to delete", "Please select the local and storage name number"
        )

        # Remove the entity from tracking
        entity_name_to_remove, entity_id_to_remove = all_ids[choice - 1]
        self.delete_entity_id(entity_id_to_remove, entity_name_to_remove)

    def remove_entity_id_from_tracking(self, entity_id):
        self.entity_tracked.discard(entity_id)
        self.entity_chapter_plugin.pop(entity_id, None)
        logger.warning("Removed %s from tracking.", entity_id)

        # Remove the downloaded chapters
        downloaded_chapters = []
        for chapter in self.entity_downloads:
            if chapter[0] == entity_id:
                downloaded_chapters.append(chapter)
        for chapter in downloaded_chapters:
            self.entity_downloads.discard(chapter)
        logger.warning("Removed downloaded chapters for %s from tracking.", entity_id)
        self.save()

    def delete_entity_id(self, entity_id_to_remove, entity_name_to_remove):
        self.remove_entity_id_from_tracking(entity_id_to_remove)
        self.entity_map.pop(entity_name_to_remove, None)
        self.entity_names.pop(entity_id_to_remove, None)
        self.metadata.database.pop(entity_id_to_remove, None)
        self.covers.database.pop(entity_id_to_remove, None)
        self.volumes.database.pop(entity_id_to_remove, None)
        self.chapters.database.pop(entity_id_to_remove, None)
        logger.warning("Deleted entity from database %s (%s).", entity_name_to_remove, entity_id_to_remove)
        self.save()

    def delete_chapter_entity_id_from_downloaded_chapters(self, entity_id, chapter_id):
        """Remove a chapter entity ID from the downloaded chapters."""
        if (entity_id, chapter_id) in self.entity_downloads:
            self.entity_downloads.discard((entity_id, chapter_id))
            logger.info("Removed chapter %s from downloaded chapters for %s.", chapter_id, entity_id)
            self.save()
        else:
            logger.warning("Chapter %s not found in downloaded chapters for %s.", chapter_id, entity_id)

    def update_manga_entity_name(self, manga_name):
        entity_id = self.entity_map.get(manga_name)
        self.update_manga_entity_id(entity_id)

    def update_manga_entity_id_metadata_and_find_updated_ids(
        self, entity_ids: list[str], batch_size: int = 50
    ) -> list[str]:
        """Find the first entity ID that has metadata and chapters."""
        previous_metadata = {}
        previous_chapters = {}
        for entity_id in entity_ids:
            previous_metadata[entity_id] = self.metadata.to_hash(entity_id)
            previous_chapters[entity_id] = self.chapters.to_hash(entity_id)

        logger.info("Checking for metadata updates...")
        for i in range(0, len(entity_ids), batch_size):
            batch = entity_ids[i : i + batch_size]
            self.metadata.update(batch, batch_response=True)

        for idx, entity_id in enumerate(entity_ids):
            if idx % 10 == 0:
                logger.info("Checking for chapter updates... [Remaining: %d]", len(entity_ids) - (idx + 1))
            # Check if non-plugin chapter updates are available, update if metadata changed
            updated_metadata = self.metadata.to_hash(entity_id)
            metadata_changed = updated_metadata != previous_metadata.get(entity_id, "0")
            # Check if chapter uses plugin, always update when plugin present
            chapter_plugin = self.entity_chapter_plugin.get(entity_id, {})
            if chapter_plugin or metadata_changed:
                self.chapters.update(entity_id, **chapter_plugin)

        # There are extra verbose checks here, but this makes debugging easier if breakpoints are set
        updated_entity_ids = []
        for entity_id in entity_ids:
            updated_metadata = self.metadata.to_hash(entity_id)
            updated_chapters = self.chapters.to_hash(entity_id)
            if (updated_metadata != previous_metadata.get(entity_id, "0")) or (
                updated_chapters != previous_chapters.get(entity_id, "0")
            ):
                updated_entity_ids.append(entity_id)
                logger.debug("Updated metadata for %s: %s", self.entity_names.get(entity_id, "Unknown"), entity_id)

        return updated_entity_ids

    def update_manga_entity_id(self, entity_id, update_metadata=True):
        manga_name = self.entity_names.get(entity_id)
        if entity_id is not None:
            try:
                chapter_plugin = self.entity_chapter_plugin.get(entity_id, {})
                logger.debug("Checking for updates %s: %s", manga_name, entity_id)

                if update_metadata:
                    self.metadata.update(entity_id)
                    self.chapters.update(entity_id, **chapter_plugin)

                # Update the collections
                logger.info("Updating %s: %s", manga_name, entity_id)
                self.volumes.update(entity_id)
                self.covers.update(entity_id)
                self.authors.update(self.metadata[entity_id].author_entities)

                # Update missing covers
                self.covers.download(entity_id, self.image_db_path)

                # Save database on successful update, this makes each call slightly slower, but more reliable
                # since the APIs are prone to crashing
                self.save()

            except EnvironmentError as err:
                logger.info("API Down >> Unable to update %s metadata. %s", manga_name, err)

    def refresh(self, storage_path):
        logger.info("Refreshing database...")
        entity_ids = sorted(self.metadata.keys())
        updated_entity_ids = self.update_manga_entity_id_metadata_and_find_updated_ids(entity_ids)
        for entity_id in updated_entity_ids:
            self.update_manga_entity_id(entity_id, update_metadata=False)
        self.download_missing_covers()
        self.remove_orphaned_covers()
        logger.debug("Downloading missing chapters...")
        self.download_missing_chapters(storage_path)
        logger.info("Refresh complete.")

    def remove_orphaned_covers(self):
        logger.debug("Cleaning orphaned covers...")
        self.covers.remove_orphaned_covers(self.image_db_path)

    def download_missing_covers(self):
        logger.debug("Downloading missing covers...")
        self.covers.download_missing_covers(self.image_db_path)

    def download_chapter(self, entity_id, chapter_item, storage_path):
        if (entity_id, chapter_item.entity_id) in self.entity_downloads:
            return

        manga_name = next(iter(name for name, id in self.entity_map.items() if id == entity_id))
        chapter_name = f"{manga_name} - Chapter {chapter_item.padded_chapter_string}"

        chapter_filepath = os.path.join(storage_path, manga_name, chapter_name)
        logger.info("Downloading %s...", chapter_name)
        try:
            make_directory_with_ownership(chapter_filepath)
            # Build the chapter metadata files
            self.build_chapter_metadata(manga_name, chapter_item, chapter_filepath)

            # Download the chapter images and write them to the folder
            self.chapters.download(entity_id, chapter_item.entity_id, chapter_filepath)

            # Build the chapter CBZ file
            self.build_chapter_cbz(chapter_filepath)

            # Mark cbz creation as successful and save the database
            self.entity_downloads.add((entity_id, chapter_item.entity_id))
            self.save()

            # Set the ownership of the file
            set_file_ownership(f"{chapter_filepath}.cbz")

            # Update the mylar series.json file
            mylar_series_json = self.to_mylar_series_json(manga_name)
            mylar_series_json_path = os.path.join(storage_path, manga_name, "series.json")
            with open(mylar_series_json_path, "w", encoding="utf-8") as json_file:
                json_file.write(mylar_series_json)
            set_file_ownership(mylar_series_json_path)

        except EnvironmentError as err:
            logger.error("Could not download chapter: %s, %s, %s", entity_id, chapter_item.entity_id, err)
            if os.path.exists(f"{chapter_filepath}.cbz"):
                logger.error("Removing CBZ: %s, %s", entity_id, chapter_item.entity_id)
                os.remove(f"{chapter_filepath}.cbz")
            if (entity_id, chapter_item.entity_id) in self.entity_downloads:
                logger.error("Removing download record: %s, %s", entity_id, chapter_item.entity_id)
                self.entity_downloads.discard((entity_id, chapter_item.entity_id))
                self.save()
        finally:
            # Cleanup excess
            shutil.rmtree(chapter_filepath)

    def build_chapter_metadata(self, manga_name, chapter_item, chapter_filepath):
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

    def build_chapter_cbz(self, chapter_filepath):
        cbz_files = sorted(f for f in os.listdir(chapter_filepath) if os.path.splitext(f)[-1] in (".jpg", ".xml"))
        with ZipFile(f"{chapter_filepath}.cbz", "w", ZIP_DEFLATED) as zip_write:
            for cbz_file in cbz_files:
                if not os.path.exists(os.path.join(chapter_filepath, cbz_file)):
                    raise EnvironmentError(f"Could not find file to add to CBZ: {cbz_file}")
                zip_write.write(os.path.join(chapter_filepath, cbz_file), cbz_file)

    @staticmethod
    def clean_entity_name(entity_name):
        entity_name = entity_name.replace("é", "e")
        entity_name = re.sub(r"[^A-Za-z0-9 ']+", " ", entity_name)
        entity_name = " ".join(entity_name.split())
        return entity_name

    def to_entity_name(self, manga_name) -> Optional[str]:
        entity_id = self.entity_map.get(manga_name)
        if entity_id is None:
            return None
        return self.entity_names.get(entity_id)

    def to_local_image_file(self, manga_name, chapter_number, chapter_is_volume=False) -> Optional[str]:
        entity_id = self.entity_map.get(manga_name)
        max_chapter_number = self.chapters.get_max_chapter_number(entity_id)
        cover_volumes = self.covers.get_sorted_cover_volumes(entity_id)

        if chapter_is_volume:
            volume = str(int(chapter_number))
        else:
            volume = self.volumes[entity_id].get_volume(chapter_number, max_chapter_number, cover_volumes)

        cover_entity = self.covers.get_cover_for_volume(entity_id, volume, self.metadata[entity_id].cover_art_id)
        return cover_entity.local_filename if cover_entity else None

    def to_xml_tree(self, manga_name, chapter_number, chapter_is_volume=False) -> ElementTree.Element:
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

        if chapter_is_volume:
            volume = str(int(chapter_number))
            count = self.volumes[entity_id].last_volume
        else:
            volume = self.volumes[entity_id].get_volume(chapter_number)
            count = -1
            if self.metadata[entity_id].completed:
                count = self.metadata[entity_id].last_chapter

        assign("Series", self.metadata[entity_id].title)
        assign("LocalizedSeries", self.metadata[entity_id].alt_title)
        assign("Number", chapter_number)
        assign("Count", count)
        assign("Volume", volume)
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
        assign("LanguageISO", self.metadata[entity_id].language)
        assign("Manga", "Yes")
        assign("Genre", ",".join(self.metadata[entity_id].genres))
        assign("AgeRating", self.metadata[entity_id].age_rating)
        assign("Web", f"https://{Urls.MDX}/title/{entity_id}")
        return root

    def to_xml_string(self, manga_name, chapter_number, chapter_is_volume=False) -> str:
        root = self.to_xml_tree(manga_name, chapter_number, chapter_is_volume)
        xmlstr = minidom.parseString(ElementTree.tostring(root)).toprettyxml()
        return xmlstr

    def to_mylar_series_json(self, manga_name) -> str:
        """Construct a Komga compatible series.json file"""
        entity_id = self.entity_map.get(manga_name)
        if entity_id is None:
            raise ValueError(f"Could not find an entity for {manga_name}")

        metadata = self.metadata[entity_id]
        if metadata is None:
            raise ValueError(f"Could not find metadata for entity {entity_id}")

        total_issues = "-1"
        if metadata.completed:
            total_issues = metadata.last_chapter

        mylar_metadata = {
            "version": "1.0.2",
            "metadata": {
                "type": "comicSeries",
                "publisher": "",
                "imprint": None,
                "name": metadata.title,
                "comicid": 0,
                "year": metadata.created_at.year,
                "description_text": metadata.description,
                "description_formatted": None,
                "volume": None,
                "booktype": "Print",
                "collects": None,
                "comic_image": "",
                "total_issues": int(total_issues),
                "publication_run": "",
                "status": metadata.mylar_status,
            },
        }

        mylar_json = json.dumps(mylar_metadata, indent=4)
        return mylar_json

    def get_comicinfo_and_image(self, manga_name, chapter_number, chapter_is_volume=False):
        entity_name = self.to_entity_name(manga_name)
        if entity_name is None:
            return None, None, None
        entity_xml = self.to_xml_string(manga_name, chapter_number, chapter_is_volume)
        entity_image_path = self.to_local_image_file(manga_name, chapter_number, chapter_is_volume)
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
                logger.error("Error occurred in chapter: %s, %s, %s", entity_id, chapter_item.entity_id, err)
        return missing_chapters
