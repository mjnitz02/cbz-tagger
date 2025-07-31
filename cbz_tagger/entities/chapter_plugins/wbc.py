import re
from typing import Any

from bs4 import BeautifulSoup

from cbz_tagger.common.enums import Plugins
from cbz_tagger.common.enums import Urls
from cbz_tagger.entities.chapter_plugins.plugin import ChapterPluginEntity


class ChapterPluginWBC(ChapterPluginEntity):
    entity_url = f"https://{Urls.WBC}/"

    @classmethod
    def parse_info_feed(cls, entity_id: str) -> list[Any]:
        url = f"{cls.entity_url}series/{entity_id}/full-chapter-list"
        response = cls.request_with_retry(url)

        soup = BeautifulSoup(response.text, "html.parser")
        items = soup.find_all("div", {"class": "flex"})

        content = []
        # This constructs an api compatible response from the rss feed
        for item in items:
            item_content = item.find_all(
                "a",
                {"class": "flex-1"},
                href=True,
            )[0]
            chapter_id = str(item_content.get("href").split("chapters/")[-1])
            link = str(item_content.get("href"))

            item_x_data = item.get("x-data")
            updated = str(item_x_data[item_x_data.index("('") + 2 : item_x_data.index("')")])

            # Find spans with empty class attribute - compatible with BS4 4.13 where class="" is not
            # findable with find_all and is now represented as an empty list
            all_spans = item_content.find_all("span")
            item_chapter_spans = [span for span in all_spans if span.get("class") == []]

            if len(item_chapter_spans) == 0:
                raise EnvironmentError("Could not find page_select_modal dialog")
            item_title = str(item_chapter_spans[0].contents[0])
            content.append(
                {
                    "id": f"{entity_id}-{chapter_id}".lower(),
                    "type": Plugins.WBC,
                    "attributes": {
                        "title": item_title,
                        "url": link,
                        "chapter": re.sub("[^\\d.]", "", item_title),
                        "translatedLanguage": "en",
                        "pages": -1,
                        "volume": -1,
                        "updatedAt": updated,
                    },
                }
            )
        return content

    def parse_chapter_download_links(self, url: str) -> list[str]:
        response = self.request_with_retry(url)
        soup = BeautifulSoup(response.text, "html.parser")

        # Find the root url for the chapter
        root_element = soup.find_all("link", {"rel": "preload"})[0]
        root_url = root_element.get("href")
        base_url = "/".join(root_url.split("/")[:-1])
        base_chapter = root_url.split("/")[-1].split("-")[0]

        # Find the list of pages
        page_select_element = list(soup.find_all("dialog", {"id": "page_select_modal"}))
        if len(page_select_element) == 0:
            raise EnvironmentError("Could not find page_select_modal dialog")
        page_select_modal = page_select_element[0]
        page_tags = list(x for x in page_select_modal.find_all("button", {"class": "w-full btn"}))
        pages = [int(str(p.contents[0])) for p in page_tags]

        links = []
        for page in pages:
            links.append(f"{base_url}/{base_chapter}-{page:03}.png")
        return links
