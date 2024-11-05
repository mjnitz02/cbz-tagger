from typing import Optional

from cbz_tagger.database.chapter_entity_db import ChapterEntityDB
from cbz_tagger.entities.metadata_entity import MetadataEntity


class InputEntity:
    @classmethod
    def search(cls, search_term: Optional[str] = None):
        if search_term is None:
            search_term = get_raw_input("Enter a new name to search for: ")

        entity = None
        while entity is None:
            entity = cls.find_manga_entry(search_term)
            if entity is None:
                search_term = get_raw_input("Enter a new name to search for: ")
        entity_id = entity.entity_id

        choice = console_selector(
            entity.all_titles, "Select a storage name for the series", "Please select the local and storage name number"
        )
        entity_name = entity.all_titles[choice - 1]

        return entity_id, entity_name

    @staticmethod
    def find_manga_entry(search_term):
        print(f">>> SEARCHING FOR NEW SERIES [{search_term}]")
        meta_entries = MetadataEntity.from_server_url(query_params={"title": search_term})
        choices = list(
            f"{manga.title} ({manga.alt_title}) - {manga.created_at.year} - {manga.age_rating}"
            for manga in meta_entries
        )
        choice = console_selector(
            choices,
            f">>> SEARCHING FOR NEW SERIES [{search_term}]",
            "Please select the manga that you are searching for in number",
            allow_negative_exit=True,
            show_help=True,
        )
        if choice < 0:
            return None

        entity = meta_entries[choice - 1]
        return entity

    @staticmethod
    def select_a_chapter_backend():
        plugins_types = list(ChapterEntityDB.entity_class.plugins.keys())
        choice = console_selector(
            plugins_types,
            "Select a chapter backend for the series (Default: mdx)",
            "Please select the chapter backend to use for the series",
            allow_negative_exit=True,
        )
        if choice <= 1:
            return None

        backend = plugins_types[choice - 1]
        plugin_id = get_raw_input(f"Please enter the {backend} plugin manga ID: ")
        return {
            "plugin_type": backend,
            "plugin_id": plugin_id,
        }

    @staticmethod
    def should_mark_all_tracked(manga_name):
        response = get_raw_input(f"Mark all chapters for {manga_name} as tracked? (y/n): ")
        return response == "y"


def console_selector(choices, title, prompt, allow_negative_exit=False, show_help=False):
    print(f"{title}:")
    counter = 0
    for choice in list(choices):
        print(f"{counter + 1}. {choice}")
        counter += 1
    if show_help:
        print(" ")
        print("!!! INPUT -1 TO ENTER A NEW NAME TO SEARCH FOR IF THESE RESULTS ARE BAD !!!")
    selection = get_input(f"{prompt}: ", counter + 1, allow_negative_exit=allow_negative_exit)
    return selection


def get_raw_input(desc):
    """Allow input to be simply mapped in unit testing"""
    return input(desc)


def get_input(desc, max_val, allow_negative_exit=False):
    """Allow selection from a list of inputs"""
    while True:
        user_input = input(desc)
        try:
            user_input = int(user_input)
            if user_input > max_val:
                print("Your input is incorrect! Please try again!")
            elif not allow_negative_exit and user_input <= 0:
                print("Your input is incorrect! Please try again!")
            else:
                return user_input

        except (TypeError, ValueError):
            print("Your input is incorrect! Please try again!")
