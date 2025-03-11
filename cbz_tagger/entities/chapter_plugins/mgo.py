import re
import datetime
from typing import Any
from typing import List

from bs4 import BeautifulSoup

from cbz_tagger.common.converter import convert_chapter_to_number
from cbz_tagger.common.enums import Plugins
from cbz_tagger.common.enums import Urls
from cbz_tagger.entities.chapter_plugins.plugin import ChapterPluginEntity


class ChapterPluginMGO(ChapterPluginEntity):
    entity_url = f"https://{Urls.MGO}/"

    @classmethod
    def parse_info_feed(cls, entity_id: str) -> List[Any]:
        url = f"{cls.entity_url}read-manga/{entity_id}"
        response = cls.request_with_retry(url)

        soup = BeautifulSoup(response.text, "html.parser")
        chapter_list = soup.find_all("table", class_="listing")
        chapter_list = chapter_list[0]
        items = chapter_list.find_all("tr")

        content = []
        # This constructs an api compatible response from the rss feed
        for item in items:
            item_content = item.find_all("a", class_="chico")[0]
            chapter_name_str = item_content.text
            chapter_number = convert_chapter_to_number(chapter_name_str)

            link = item_content.get("href")
            chapter_id = "-".join([part.lower() for part in link.split("/")[4:] if len(part) > 1])

            # Get the last updated date, these are not TZ aware
            updated_str = item.find_all("td")[-1].text
            updated_str = re.sub('[^A-Za-z0-9]+', ' ', updated_str).strip()
            updated_dt = datetime.datetime.strptime(updated_str, '%b %d %Y')
            updated = updated_dt.strftime("%Y-%m-%dT%H:%M:%S")

            content.append(
                {
                    "id": chapter_id,
                    "type": Plugins.MGO,
                    "attributes": {
                        "title": f"Chapter {chapter_number}",
                        "url": link,
                        "chapter": str(chapter_number),
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
