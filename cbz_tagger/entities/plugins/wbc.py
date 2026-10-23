import base64
import re
from typing import Any

from cbz_tagger.common.plugins import Plugins
from cbz_tagger.entities.plugins.plugin_entity import ChapterPluginEntity


@Plugins.register("wbc")
class ChapterPluginWBC(ChapterPluginEntity):
    BASE_URL = base64.b64decode("d2VlYmNlbnRyYWwuY29t").decode("utf-8")
    TITLE_URL = f"https://{BASE_URL}/series/"
    HARU_SOURCE = base64.b64decode("V2VlYkNlbnRyYWwudHM=").decode("utf-8")
    entity_url = f"https://{BASE_URL}/"

    @classmethod
    def parse_info_feed(cls, entity_id: str) -> list[Any]:
        # haruneko FetchChapters: 'a[href*="/chapters/"]' on {series}/full-chapter-list, title from 'span.grow span'
        url = f"{cls.entity_url}series/{entity_id}/full-chapter-list"
        scraper = cls.fetch_and_parse(url)

        content = []
        for item in scraper.select_safe('a[href*="/chapters/"]', "Could not find chapter links"):
            link = cls.absolute_url(str(item["href"]))
            chapter_id = link.split("/chapters/")[-1]

            title_element = item.select_one("span.grow span")
            if title_element is None:
                raise EnvironmentError("Could not find chapter title")
            item_title = title_element.get_text(strip=True)

            time_element = item.select_one("time")
            updated = time_element.get_text(strip=True) if time_element is not None else None

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
        # haruneko FetchPages runs 'main section img[alt*="Page"]:not([x-show])' in a browser after the chapter
        # page has loaded its images. Those images come from an htmx fragment, so request that directly instead.
        scraper = self.fetch_and_parse(
            f"{url}/images", params={"is_prev": "False", "current_page": 1, "reading_style": "long_strip"}
        )
        pages = scraper.select_safe('section img[alt*="Page"]:not([x-show])', "Could not find chapter images")
        return [self.absolute_url(str(page["src"])) for page in pages]
