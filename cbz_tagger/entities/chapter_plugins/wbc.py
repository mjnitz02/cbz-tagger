import re
from typing import Any, List

from bs4 import BeautifulSoup

from cbz_tagger.common.enums import Plugins, Urls
from cbz_tagger.entities.chapter_plugins.plugin import ChapterPluginEntity


class ChapterPluginWBC(ChapterPluginEntity):
    entity_url = f"https://{Urls.WBC}/"

    @classmethod
    def parse_info_feed(cls, entity_id: str) -> List[Any]:
        url = f"{cls.entity_url}series/{entity_id}/full-chapter-list"
        response = cls.request_with_retry(url)

        soup = BeautifulSoup(response.text, "html.parser")
        items = soup.find_all("div", class_="flex")

        content = []
        # This constructs an api compatible response from the rss feed
        for item in items:
            item_content = item.find_all("a", href=True, class_="flex-1")[0]
            chapter_id = str(item_content.get("href").split("chapters/")[-1])
            link = str(item_content.get("href"))

            item_x_data = item.get("x-data")
            updated = str(item_x_data[item_x_data.index("('") + 2 : item_x_data.index("')")])

            item_chapter_spans = item_content.find_all("span", class_="")
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

    def parse_chapter_download_links(self, url: str) -> List[str]:
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
