import re
from datetime import datetime
from datetime import timedelta
from typing import Any

from bs4.element import Tag

from cbz_tagger.common.enums import Plugins
from cbz_tagger.common.enums import Urls
from cbz_tagger.entities.chapter_plugins.html_plugin import HtmlChapterPluginEntity


@Plugins.register(Plugins.KAL)
class ChapterPluginKAL(HtmlChapterPluginEntity):
    PLUGIN_TYPE = Plugins.KAL
    entity_url = f"https://{Urls.KAL}"

    @staticmethod
    def get_approximate_date(date_str) -> str | None:
        pattern = r"(\d+)\s+(minute|minutes|day|days|month|months|year|years) ago"
        match = re.match(pattern, date_str.strip())
        if not match:
            return None
        value, unit = int(match.group(1)), match.group(2)
        now = datetime.now().astimezone()
        if unit.startswith("minute"):
            delta = timedelta(minutes=value)
        elif unit.startswith("day"):
            delta = timedelta(days=value)
        elif unit.startswith("month"):
            # Approximate a month as 30 days
            delta = timedelta(days=30 * value)
        elif unit.startswith("year"):
            # Approximate a year as 365 days
            delta = timedelta(days=365 * value)
        else:
            return None
        approx_date = now - delta
        return approx_date.isoformat()

    @classmethod
    def parse_info_feed(cls, entity_id: str) -> list[Any]:
        url = f"{cls.entity_url}/manga/{entity_id}"
        scraper = cls.fetch_and_parse(url)

        chapter_entity = scraper.find_one_safe("ul", {"class": "chapter-list"}, "Could not find chapter list")
        items = chapter_entity.find_all("li")

        content = []
        for item in items:
            assert isinstance(item, Tag), f"Expected Tag, got {type(item)}"
            chapter_number_str = str(item.get("id", ""))[2:]
            item_content_list = item.find_all("a", href=True)
            assert len(item_content_list) > 0, "No anchor tags found"
            item_content = item_content_list[0]
            assert isinstance(item_content, Tag), f"Expected Tag, got {type(item_content)}"

            href = item_content.get("href")
            assert isinstance(href, str), f"Expected str for href, got {type(href)}"
            chapter_id = href.split("manga/")[-1].replace("/", "-")
            link = f"{cls.entity_url}{href}"

            chapter_title_list = item_content.find_all("strong", {"class": "chapter-title"})
            assert len(chapter_title_list) > 0, "No chapter title found"
            chapter_title_elem = chapter_title_list[0]
            assert isinstance(chapter_title_elem, Tag), f"Expected Tag, got {type(chapter_title_elem)}"
            chapter_title = chapter_title_elem.text

            item_time = item_content.find_all("time")
            if len(item_time) > 0:
                chapter_updated = None  # KAL may not provide chapter dates
            else:
                item_time_str = item_time[0].text.strip()
                chapter_updated = ChapterPluginKAL.get_approximate_date(item_time_str)

            content.append(
                cls.ResponseBuilder.build(
                    cls.build_chapter_data(
                        chapter_id=f"{entity_id}-{chapter_id}".lower(),
                        entity_id=entity_id,
                        title=chapter_title,
                        url=link,
                        chapter=chapter_number_str,
                        volume=None,
                        created_at=chapter_updated,
                        updated_at=chapter_updated,
                    )
                )
            )
        return content

    def parse_chapter_download_links(self, url: str) -> list[str]:
        scraper = self.fetch_and_parse(url)
        chapter_images = scraper.extract_script_variable("chapImages", "Could not find chapter images")

        pages = chapter_images.split(",")
        return [page.strip() for page in pages]
