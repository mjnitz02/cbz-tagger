import json
import logging
import os
import re
import shutil
import tempfile
from contextlib import suppress
from xml.dom import minidom
from xml.etree import ElementTree
from zipfile import ZIP_DEFLATED
from zipfile import ZipFile

from cbz_tagger.common.enums import Urls
from cbz_tagger.common.input import InputEntity
from cbz_tagger.common.input import console_selector
from cbz_tagger.common.permissions import make_directory_with_ownership
from cbz_tagger.common.permissions import set_file_ownership
from cbz_tagger.common.plugins import Plugins
from cbz_tagger.database.author_entity_db import AuthorEntityDB
from cbz_tagger.database.chapter_entity_db import ChapterEntityDB
from cbz_tagger.database.cover_entity_db import CoverEntityDB
from cbz_tagger.database.downloads import DownloadLedger
from cbz_tagger.database.metadata_entity_db import MetadataEntityDB
from cbz_tagger.database.series import ChapterSource
from cbz_tagger.database.series import Series
from cbz_tagger.database.series import SeriesIndex
from cbz_tagger.database.volume_entity_db import VolumeEntityDB

logger = logging.getLogger()


class EntityDB:
    def __init__(
        self,
        root_path: str,
        series=None,
        downloads=None,
        metadata=None,
        covers=None,
        authors=None,
        volumes=None,
        chapters=None,
    ):
        self.root_path = root_path
        self.series: SeriesIndex = SeriesIndex() if series is None else series
        self.downloads: DownloadLedger = DownloadLedger() if downloads is None else downloads

        self.metadata: MetadataEntityDB = MetadataEntityDB() if metadata is None else metadata
        self.covers: CoverEntityDB = CoverEntityDB() if covers is None else covers
        self.authors: AuthorEntityDB = AuthorEntityDB() if authors is None else authors
        self.volumes: VolumeEntityDB = VolumeEntityDB() if volumes is None else volumes
        self.chapters: ChapterEntityDB = ChapterEntityDB() if chapters is None else chapters

    def __getitem__(self, manga_name) -> str | None:
        series = self.series.by_alias(manga_name)
        return series.entity_id if series is not None else None

    def __len__(self):
        return len(self.series)

    def keys(self):
        return self.series.aliases()

    @property
    def image_db_path(self) -> str:
        return os.path.join(self.root_path, "images")

    @property
    def has_tracked_entities(self) -> bool:
        return self.series.has_tracked()

    def save(self) -> None:
        entity_db_path = os.path.join(self.root_path, "entity_db.json")
        entity_database_json = self.to_json()

        os.makedirs(self.root_path, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=self.root_path, prefix=".entity_db.", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="UTF-8") as write_file:
                write_file.write(entity_database_json)
                write_file.flush()
                os.fsync(write_file.fileno())
            os.replace(tmp_path, entity_db_path)
        except BaseException:
            with suppress(OSError):
                os.unlink(tmp_path)
            raise

    def to_json(self):
        entity_map = {}
        entity_names = {}
        entity_tracked = []
        entity_chapter_plugin = {}
        for series in self.series:
            entity_names[series.entity_id] = series.canonical_name
            for alias in series.aliases:
                entity_map[alias] = series.entity_id
            if series.tracked:
                entity_tracked.append(series.entity_id)
            # Only non-default sources are written, so the file stays legacy-compatible.
            if not series.source.is_default:
                entity_chapter_plugin[series.entity_id] = {
                    "plugin_type": series.source.plugin_type,
                    "plugin_id": series.source.plugin_id,
                }

        content = {
            "entity_map": entity_map,
            "entity_names": entity_names,
            "entity_downloads": self.downloads.as_tuples(),
            "entity_tracked": entity_tracked,
            "entity_chapter_plugin": entity_chapter_plugin,
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
        entity_map = content["entity_map"]
        entity_names = content["entity_names"]
        entity_tracked = set(content.get("entity_tracked", []))
        entity_chapter_plugin = content.get("entity_chapter_plugin", {})

        # Preserve insertion order of entity_map so `storage_name` keeps picking the same alias
        # that the old `next(iter(...))` scan in download_chapter picked.
        aliases_by_id: dict[str, list[str]] = {}
        for alias, entity_id in entity_map.items():
            aliases_by_id.setdefault(entity_id, []).append(alias)

        series_records = {}
        for entity_id in list(entity_map.values()) + list(entity_names.keys()):
            if entity_id in series_records:
                continue
            aliases = aliases_by_id.get(entity_id, [])
            canonical_name = entity_names.get(entity_id)
            if canonical_name is None:
                # Orphan: present in entity_map but never given a canonical name.
                logger.warning("Series %s has no canonical name; using its alias.", entity_id)
                canonical_name = aliases[0] if aliases else entity_id
            if not aliases:
                # Orphan: named but unreachable by any local name. Keep it so it is not silently
                # dropped, and give it an alias so storage_name stays valid.
                logger.warning("Series %s (%s) has no local name mapping.", canonical_name, entity_id)
                aliases = [canonical_name]
            plugin = entity_chapter_plugin.get(entity_id, {})
            series_records[entity_id] = Series(
                entity_id=entity_id,
                canonical_name=canonical_name,
                aliases=aliases,
                tracked=entity_id in entity_tracked,
                source=ChapterSource(
                    plugin_type=plugin.get("plugin_type", Plugins.DEFAULT),
                    plugin_id=plugin.get("plugin_id", entity_id),
                ),
            )

        return cls(
            root_path=root_path,
            series=SeriesIndex(series_records),
            downloads=DownloadLedger(set(tuple(item) for item in content.get("entity_downloads", []))),
            metadata=MetadataEntityDB.from_json(content["metadata"]),
            covers=CoverEntityDB.from_json(content["covers"]),
            authors=AuthorEntityDB.from_json(content["authors"]),
            volumes=VolumeEntityDB.from_json(content["volumes"]),
            chapters=ChapterEntityDB.from_json(content.get("chapters", "{}")),
        )

    def to_state(self):
        state = []
        for series in self.series:
            entity_id = series.entity_id
            entity_metadata = self.metadata[entity_id]
            if entity_metadata is None:
                continue  # Skip entities without metadata
            latest_chapter = self.chapters.get_latest_chapter(entity_id)
            plugin_type = series.source.plugin_type
            plugin_id = series.source.plugin_id
            state.append(
                {
                    "entity_id": entity_id,
                    "name": series.storage_name,
                    "name_link": f"{Plugins.TITLE_URLS[Plugins.DEFAULT]}{entity_id}",
                    "status": entity_metadata.status,
                    "tracked": series.tracked,
                    "latest_chapter": latest_chapter.chapter_string if latest_chapter else None,
                    "latest_chapter_date": latest_chapter.updated_date if latest_chapter else None,
                    "metadata_updated": entity_metadata.updated,
                    "plugin": plugin_type,
                    "plugin_link": f"{Plugins.TITLE_URLS[plugin_type]}{plugin_id}",
                }
            )
        state = sorted(state, key=lambda d: d["name"].lower())
        return state

    def check_manga_missing(self, manga_name):
        return self.series.by_alias(manga_name) is None

    @staticmethod
    def search(manga_name: str | None = None):
        """This is a temporary abstraction to the new class"""
        return InputEntity.search(manga_name)

    def add(self, manga_name: str | None, update=True, track=False):
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

        if self.series.by_alias(manga_name) is None:
            canonical_name = self.clean_entity_name(entity_name)
            self.series.add(
                Series(
                    entity_id=entity_id,
                    canonical_name=canonical_name,
                    aliases=[manga_name],
                    source=ChapterSource(plugin_id=entity_id),
                )
            )
        else:
            logger.warning("Entity %s (%s) already exists in the database.", manga_name, entity_id)
            return

        if track:
            if backend is not None:
                self.series[entity_id].source = ChapterSource(**backend)

        if update:
            self.update_manga_entity_id(entity_id)

        if track:
            logger.info("Tracking: %s (%s)", entity_name, entity_id)
            self.series[entity_id].tracked = True
            if mark_as_tracked:
                logger.info("Marking all chapters as downloaded. %s (%s)", entity_name, entity_id)
                chapters = self.chapters[entity_id]
                if chapters is not None:
                    self.downloads.mark_all(entity_id, chapters)
            else:
                logger.info("No chapters marked as downloaded. %s (%s)", entity_name, entity_id)

        self.save()

    def remove(self):
        tracked = list(self.series.tracked())
        choices = list(f"{s.canonical_name} ({s.entity_id})" for s in tracked)
        choice = console_selector(
            choices, "Select a manga to remove tracking for", "Please select the local and storage name number"
        )

        # Remove the entity from tracking
        entity_id_to_remove = tracked[choice - 1].entity_id
        self.remove_entity_id_from_tracking(entity_id_to_remove)

    def delete(self):
        all_series = list(self.series)
        choices = list(f"{s.storage_name} ({s.entity_id})" for s in all_series)
        choice = console_selector(
            choices, "Select a manga to delete", "Please select the local and storage name number"
        )

        # Remove the entity from tracking
        series = all_series[choice - 1]
        self.delete_entity_id(series.entity_id, series.storage_name)

    def remove_entity_id_from_tracking(self, entity_id):
        series = self.series.get(entity_id)
        if series is not None:
            series.tracked = False
            series.source = ChapterSource(plugin_id=entity_id)
        logger.warning("Removed %s from tracking.", entity_id)

        # Remove the downloaded chapters
        self.downloads.clear_series(entity_id)
        logger.warning("Removed downloaded chapters for %s from tracking.", entity_id)
        self.save()

    def delete_entity_id(self, entity_id_to_remove, entity_name_to_remove):
        self.remove_entity_id_from_tracking(entity_id_to_remove)
        self.series.remove(entity_id_to_remove)
        self.metadata.database.pop(entity_id_to_remove, None)
        self.covers.database.pop(entity_id_to_remove, None)
        self.volumes.database.pop(entity_id_to_remove, None)
        self.chapters.database.pop(entity_id_to_remove, None)
        logger.warning("Deleted entity from database %s (%s).", entity_name_to_remove, entity_id_to_remove)
        self.save()

    def set_downloaded_chapters(self, entity_id, downloaded_chapter_ids):
        """Reconcile the downloaded chapters for an entity to match the given set in a single save()."""
        self.downloads.reconcile(entity_id, self.chapters[entity_id] or [], downloaded_chapter_ids)
        self.save()

    def update_manga_entity_name(self, manga_name):
        series = self.series.by_alias(manga_name)
        entity_id = series.entity_id if series is not None else None
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
            # Check if the series uses a non-default source, always update in that case
            series = self.series.get(entity_id)
            if (series is not None and not series.source.is_default) or metadata_changed:
                self.chapters.update(entity_id, **(series.source.to_update_kwargs() if series else {}))

        # There are extra verbose checks here, but this makes debugging easier if breakpoints are set
        updated_entity_ids = []
        for entity_id in entity_ids:
            updated_metadata = self.metadata.to_hash(entity_id)
            updated_chapters = self.chapters.to_hash(entity_id)
            if (updated_metadata != previous_metadata.get(entity_id, "0")) or (
                updated_chapters != previous_chapters.get(entity_id, "0")
            ):
                updated_entity_ids.append(entity_id)
                series = self.series.get(entity_id)
                logger.debug(
                    "Updated metadata for %s: %s",
                    series.canonical_name if series else "Unknown",
                    entity_id,
                )

        return updated_entity_ids

    def update_manga_entity_id(self, entity_id, update_metadata=True):
        series = self.series.get(entity_id)
        manga_name = series.canonical_name if series is not None else None
        if entity_id is not None:
            try:
                chapter_plugin = series.source.to_update_kwargs() if series is not None else {}
                logger.debug("Checking for updates %s: %s", manga_name, entity_id)

                if update_metadata:
                    self.metadata.update(entity_id)
                    self.chapters.update(entity_id, **chapter_plugin)

                # Update the collections
                logger.info("Updating %s: %s", manga_name, entity_id)
                self.volumes.update(entity_id)
                self.covers.update(entity_id)

                metadata = self.metadata[entity_id]
                if metadata is not None:
                    self.authors.update(metadata.author_entities)

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
        if self.downloads.has(entity_id, chapter_item):
            return

        manga_name = self.series[entity_id].storage_name
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
            self.downloads.mark(entity_id, chapter_item)
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
            if self.downloads.has(entity_id, chapter_item):
                logger.error("Removing download record: %s, %s", entity_id, chapter_item.entity_id)
                self.downloads.unmark(entity_id, chapter_item)
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
        entity_image_path = os.path.join(str(self.image_db_path), str(cover_path))
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

    def to_entity_name(self, manga_name) -> str | None:
        series = self.series.by_alias(manga_name)
        if series is None:
            return None
        return series.canonical_name

    def to_local_image_file(self, manga_name, chapter_number, chapter_is_volume=False) -> str | None:
        series = self.series.by_alias(manga_name)
        if series is None:
            return None
        entity_id = series.entity_id

        metadata = self.metadata[entity_id]
        if metadata is None:
            return None

        max_chapter_number = self.chapters.get_max_chapter_number(entity_id)
        cover_volumes = self.covers.get_sorted_cover_volumes(entity_id)

        if chapter_is_volume:
            volume = str(int(chapter_number))
        else:
            volume_entity = self.volumes[entity_id]
            if volume_entity is None:
                return None
            volume = volume_entity.get_volume(chapter_number, max_chapter_number, cover_volumes)

        cover_entity = self.covers.get_cover_for_volume(entity_id, volume, metadata.cover_art_id)
        return cover_entity.local_filename if cover_entity else None

    def to_xml_tree(self, manga_name, chapter_number, chapter_is_volume=False) -> ElementTree.Element:
        series = self.series.by_alias(manga_name)
        if series is None:
            raise ValueError(f"Could not find an entity for {manga_name}")
        entity_id = series.entity_id

        metadata = self.metadata[entity_id]
        if metadata is None:
            raise ValueError(f"Could not find metadata for entity {entity_id}")

        # build a tree structure
        root = ElementTree.Element("ComicInfo")
        root.attrib["xmlns:xsi"] = "http://www.w3.org/2001/XMLSchema-instance"
        root.attrib["xmlns:xsd"] = "http://www.w3.org/2001/XMLSchema"

        # Lookup the authors
        author = self.authors[metadata.author_id]
        artist = self.authors[metadata.artist_id]

        author_name = author.name if author else None
        artist_name = artist.name if artist else author_name

        # Lookup volumes
        volume_entity = self.volumes[entity_id]
        if volume_entity is None:
            raise ValueError(f"Could not find volume data for entity {entity_id}")

        def assign(cix_entry, md_entry):
            if md_entry is not None:
                ElementTree.SubElement(root, cix_entry).text = f"{md_entry}"

        if chapter_is_volume:
            volume = str(int(chapter_number))
            count = volume_entity.last_volume
        else:
            volume = volume_entity.get_volume(chapter_number)
            count = -1
            if metadata.completed:
                count = metadata.last_chapter

        assign("Series", metadata.title)
        assign("LocalizedSeries", metadata.alt_title)
        assign("Number", chapter_number)
        assign("Count", count)
        assign("Volume", volume)
        assign("Summary", metadata.description)
        assign("Year", metadata.created_at.year)
        assign("Month", metadata.created_at.month)
        assign("Day", metadata.created_at.day)
        assign("Writer", author_name)
        assign("Penciller", artist_name)
        assign("Inker", artist_name)
        assign("Colorist", artist_name)
        assign("Letterer", artist_name)
        assign("CoverArtist", artist_name)
        assign("LanguageISO", metadata.language)
        assign("Manga", "Yes")
        assign("Genre", ",".join(metadata.genres))
        assign("AgeRating", metadata.age_rating)
        assign("Web", f"https://{Urls.MDX}/title/{entity_id}")
        return root

    def to_xml_string(self, manga_name, chapter_number, chapter_is_volume=False) -> str:
        root = self.to_xml_tree(manga_name, chapter_number, chapter_is_volume)
        xmlstr = minidom.parseString(ElementTree.tostring(root)).toprettyxml()
        return xmlstr

    def to_mylar_series_json(self, manga_name) -> str:
        """Construct a Komga compatible series.json file"""
        series = self.series.by_alias(manga_name)
        if series is None:
            raise ValueError(f"Could not find an entity for {manga_name}")
        entity_id = series.entity_id

        metadata = self.metadata[entity_id]
        if metadata is None:
            raise ValueError(f"Could not find metadata for entity {entity_id}")

        total_issues = "-1"
        if metadata.completed and metadata.last_chapter is not None:
            total_issues = str(metadata.last_chapter)

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
            series = self.series.get(entity_id)
            if series is None or not series.tracked:
                continue
            for chapter_item in chapter_items:
                if not self.downloads.has(entity_id, chapter_item):
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
