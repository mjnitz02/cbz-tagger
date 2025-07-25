from collections import defaultdict
from typing import Optional

from cbz_tagger.database.base_db import BaseEntityDB
from cbz_tagger.entities.chapter_entity import ChapterEntity


class ChapterEntityDB(BaseEntityDB):
    database: dict[str, list[ChapterEntity]]
    entity_class = ChapterEntity

    @staticmethod
    def group_chapters(list_of_chapters):
        scanlation_groups = []
        grouped_chapters = defaultdict(list)
        for chapter in list_of_chapters:
            if chapter.translated_language != "en":
                continue
            # Some chapters are not numbered, these are errors in the databases
            if chapter.chapter_number is None:
                continue
            grouped_chapters[chapter.chapter_number].append(chapter)
            scanlation_groups.append(chapter.scanlation_group)
        return grouped_chapters, scanlation_groups

    @staticmethod
    def get_priority_scanlation_groups(scanlation_groups):
        """For groups with same frequency they are sorted in descending alphabetic order"""
        scanlation_group_frequency = {group: scanlation_groups.count(group) for group in scanlation_groups}
        priority_groups = [
            group
            for _, group in sorted(
                [(value, group) for group, value in scanlation_group_frequency.items()], reverse=True
            )
        ]
        if "official" in priority_groups:
            priority_groups.insert(0, priority_groups.pop(priority_groups.index("official")))
        return priority_groups

    @staticmethod
    def filter_chapters_by_priority_scanlation_groups(grouped_chapters, priority_groups):
        filtered_chapters = []
        for key in sorted(grouped_chapters.keys()):
            entries = grouped_chapters[key]
            if len(entries) == 1:
                filtered_chapters.append(entries[0])
            else:
                for group in priority_groups:
                    entry = next((entry for entry in entries if entry.scanlation_group == group), None)
                    if entry is not None:
                        filtered_chapters.append(entry)
                        break

        if len(filtered_chapters) != len(grouped_chapters.keys()):
            raise ValueError("Chapter entries are not being filtered correctly")

        return filtered_chapters

    @staticmethod
    def remove_chapter_duplicate_entries(list_of_chapters) -> list[Optional[str]]:
        grouped_chapters, scanlation_groups = ChapterEntityDB.group_chapters(list_of_chapters)
        priority_groups = ChapterEntityDB.get_priority_scanlation_groups(scanlation_groups)
        filtered_chapters = ChapterEntityDB.filter_chapters_by_priority_scanlation_groups(
            grouped_chapters, priority_groups
        )

        return filtered_chapters

    def format_content_for_entity(self, content, entity_id: Optional[str] = None):
        content.extend(self.database.get(entity_id, []))
        filtered_content = self.remove_chapter_duplicate_entries(content)
        return filtered_content

    def download(self, entity_id: str, chapter_id: str, filepath: str):
        chapter = next(iter(c for c in self[entity_id] if c.entity_id == chapter_id), None)
        if chapter is not None:
            return chapter.download_chapter(filepath)

        raise EnvironmentError(f"Chapter {chapter_id} not found for {entity_id}")

    def get_latest_chapter(self, entity_id) -> Optional[ChapterEntity]:
        chapters = self.database[entity_id]
        latest_chapter = None
        for chapter in chapters:
            if latest_chapter is None or chapter.chapter_number > latest_chapter.chapter_number:
                latest_chapter = chapter
        return latest_chapter
