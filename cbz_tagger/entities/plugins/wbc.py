import base64
import re
from typing import Any

from bs4.element import Tag

from cbz_tagger.common.enums import Plugins
from cbz_tagger.entities.plugins.plugin_entity import ChapterPluginEntity


@Plugins.register("wbc")
class ChapterPluginWBC(ChapterPluginEntity):
    PLUGIN_TYPE = "wbc"
    BASE_URL = base64.b64decode("d2VlYmNlbnRyYWwuY29t").decode("utf-8")
    TITLE_URL = f"https://{BASE_URL}/series/"
    entity_url = f"https://{BASE_URL}/"

    @classmethod
    def parse_info_feed(cls, entity_id: str) -> list[Any]:
        url = f"{cls.entity_url}series/{entity_id}/full-chapter-list"
        scraper = cls.fetch_and_parse(url)

        items = scraper.find_all("div", {"class": "flex"})

        content = []
        for item in items:
            assert isinstance(item, Tag), f"Expected Tag, got {type(item)}"
            item_content_list = item.find_all("a", {"class": "flex-1"}, href=True)
            assert len(item_content_list) > 0, "No anchor tags found"
            item_content = item_content_list[0]
            assert isinstance(item_content, Tag), f"Expected Tag, got {type(item_content)}"

            href = item_content.get("href")
            assert isinstance(href, str), f"Expected str for href, got {type(href)}"
            chapter_id = href.split("chapters/")[-1]
            link = href

            item_x_data = item.get("x-data")
            assert isinstance(item_x_data, str), f"Expected str for x-data, got {type(item_x_data)}"
            updated = item_x_data[item_x_data.index("('") + 2 : item_x_data.index("')")]

            # Find spans with empty class attribute - compatible with BS4 4.13 where class="" is not
            # findable with find_all and is now represented as an empty list
            all_spans = item_content.find_all("span")
            item_chapter_spans = [span for span in all_spans if isinstance(span, Tag) and span.get("class") == []]

            if len(item_chapter_spans) == 0:
                raise EnvironmentError("Could not find chapter spans")
            first_span = item_chapter_spans[0]
            assert isinstance(first_span, Tag), f"Expected Tag, got {type(first_span)}"
            item_title = str(first_span.contents[0]) if first_span.contents else ""

            content.append(
                cls.ResponseBuilder.build(
                    cls.build_chapter_data(
                        chapter_id=f"{entity_id}-{chapter_id}".lower(),
                        entity_id=entity_id,
                        title=item_title,
                        url=link,
                        chapter=re.sub("[^\\d.]", "", item_title),
                        updated_at=updated,
                    )
                )
            )
        return content

    def parse_chapter_download_links(self, url: str) -> list[str]:
        scraper = self.fetch_and_parse(url)

        # Find the root url for the chapter
        root_element = scraper.find_one_safe("link", {"rel": "preload"}, "Could not find preload link")
        root_url = root_element.get("href")
        assert isinstance(root_url, str), "href attribute not found on preload link"
        base_url = "/".join(root_url.split("/")[:-1])
        base_chapter = root_url.split("/")[-1].split("-")[0]

        # Find the list of pages
        page_select_modal = scraper.find_one_safe(
            "dialog", {"id": "page_select_modal"}, "Could not find page_select_modal dialog"
        )
        page_tags = list(page_select_modal.find_all("button", {"class": "w-full btn"}))
        pages = [
            int(str(p.contents[0])) for p in page_tags if isinstance(p, Tag) and p.contents and len(p.contents) > 0
        ]

        return [f"{base_url}/{base_chapter}-{page:03}.png" for page in pages]
