import json
from datetime import datetime
from xml.dom import minidom
from xml.etree import ElementTree

import requests

from cbz_tagger.common.enums import MetadataSource


class MangaObject:
    def __init__(
        self,
        manga_name,
        manga_id=None,
        manga_info=None,
    ):
        self.manga_name = manga_name
        self.manga_id = manga_id
        self.manga_info = manga_info

        if self.manga_id is None:
            self.manga_id = self.search_id()
        if self.manga_info is None:
            self.manga_info = self.extract_info()
            self.manga_info["age_rating"] = self.extract_age_rating()

    def to_dict(self):
        return {
            "manga_name": self.manga_name,
            "manga_id": self.manga_id,
            "manga_info": self.manga_info,
        }

    @classmethod
    def from_dict(cls, data):
        return MangaObject(
            manga_name=data["manga_name"],
            manga_id=data["manga_id"],
            manga_info=data["manga_info"],
        )

    @property
    def age_ratings(self):
        return {
            1: "Everyone",
            2: "Teen",
            3: "Mature 17+",
            4: "Adults Only 18+",
        }

    def extract_age_rating(self):
        print(">>> SET AGE RATING")
        for key, val in self.age_ratings.items():
            print(f"{key}: {val}")
        return self.get_input("Please select the age rating for the manga: ", len(self.age_ratings.keys()))

    def extract_id(self, term, page, perpage):
        preset = {"query": term, "page": page, "perpage": perpage}
        req = requests.post(
            MetadataSource.access["apiurl"],
            headers=MetadataSource.access["header"],
            json={"query": MetadataSource.query_id, "variables": preset},
            timeout=30,
        )

        if req.status_code != 200:
            raise Exception(f"Data post unsuccessful. ({req.status_code})")

        try:
            extracted_data = json.loads(req.text)
        except ValueError:
            return None
        except TypeError:
            return None
        else:
            return extracted_data

    def extract_info(self):
        id_val = {"id": self.manga_id}
        req = requests.post(
            MetadataSource.access["apiurl"],
            headers=MetadataSource.access["header"],
            json={"query": MetadataSource.query_info, "variables": id_val},
            timeout=30,
        )

        if req.status_code != 200:
            raise Exception(f"Data post unsuccessful. ({req.status_code})")

        try:
            extracted_data = json.loads(req.text)
        except ValueError:
            return None
        except TypeError:
            return None
        else:
            return extracted_data["data"]["Media"]

    def get_input(self, desc, max_val):
        while True:
            user_input = input(desc)
            try:
                user_input = int(user_input)
                if user_input <= 0 or user_input > max_val:
                    print("Your input is incorrect! Please try again!")
                else:
                    return user_input

            except (TypeError, ValueError):
                print("Your input is incorrect! Please try again!")

    def search_id_by_name(self, manga_name):
        data = self.extract_id(manga_name, 1, 5)
        counter = 0
        for i in range(len(data["data"]["Page"]["media"])):
            curr_manga = data["data"]["Page"]["media"][i]["title"]["romaji"]
            curr_eng = data["data"]["Page"]["media"][i]["title"]["english"]
            curr_format = data["data"]["Page"]["media"][i]["format"]
            curr_chapters = data["data"]["Page"]["media"][i]["chapters"]
            print(f"{counter + 1}. {curr_manga} ({curr_eng}) [{curr_format} - Ch. {curr_chapters}]")
            counter += 1
        return counter, data

    def search_id(self):
        print(f">>> SEARCHING FOR NEW SERIES [{self.manga_name}]")
        counter = 0
        manga_name = self.manga_name
        while counter <= 0:
            counter, data = self.search_id_by_name(manga_name)
            if counter == 0:
                print(f'No search result has been found for the manga "{manga_name}"!')
                manga_name = input("Enter an alternative name to search for: ")

        if counter == 1:
            user_input = 1
        else:
            user_input = self.get_input(
                "Please select the manga that you are searching for in number: ",
                counter + 1,
            )
        return data["data"]["Page"]["media"][user_input - 1]["id"]

    @property
    def series(self):
        if self.manga_info.get("title", {}).get("romaji") is None:
            return self.manga_info.get("title", {}).get("english")
        return self.manga_info.get("title", {}).get("romaji")

    @property
    def localized_series(self):
        return self.manga_info.get("title", {}).get("english")

    @property
    def chapters(self):
        if self.manga_info["status"] == "FINISHED":
            return self.manga_info["chapters"]
        return 0

    @property
    def summary(self):
        return self.manga_info["description"]

    @property
    def author(self):
        node = self.manga_info.get("staff", {}).get("edges", [{}])[0].get("node")
        if node:
            return node["name"]["full"]
        return "Unknown"

    @property
    def genre(self):
        if "genres" in self.manga_info:
            return ",".join(self.manga_info["genres"])
        return ""

    @property
    def year(self):
        return self.manga_info.get("startDate", {}).get("year")

    @property
    def month(self):
        return self.manga_info.get("startDate", {}).get("month")

    @property
    def day(self):
        return self.manga_info.get("startDate", {}).get("day")

    @property
    def age_rating(self):
        return self.manga_info["age_rating"]

    def to_xml_tree(self, chapter_number):
        # build a tree structure
        root = ElementTree.Element("ComicInfo")
        root.attrib["xmlns:xsi"] = "http://www.w3.org/2001/XMLSchema-instance"
        root.attrib["xmlns:xsd"] = "http://www.w3.org/2001/XMLSchema"

        def assign(cix_entry, md_entry):
            if md_entry is not None:
                ElementTree.SubElement(root, cix_entry).text = f"{md_entry}"

        assign("Series", self.series)
        assign("LocalizedSeries", self.localized_series)
        assign("Number", chapter_number)
        assign("Count", self.chapters)
        assign("Summary", self.summary)
        assign("Year", self.year)
        assign("Month", self.month)
        assign("Day", self.day)
        assign("Writer", self.author)
        assign("Penciller", self.author)
        assign("Inker", self.author)
        assign("Colorist", self.author)
        assign("Letterer", self.author)
        assign("CoverArtist", self.author)
        assign("LanguageISO", "en")
        assign("Manga", "Yes")
        assign("Genre", self.genre)
        assign("AgeRating", self.age_ratings[self.age_rating])
        assign("Web", MetadataSource.url.format(self.manga_id))
        assign(
            "Notes",
            f"Updated on {datetime.now().strftime('%m/%d/%Y, %H:%M:%S')}.",
        )
        # tree = ET.ElementTree(root)
        # ET.indent(tree, space="\t", level=0)
        return root

    def to_xml_file(self, chapter_number, filename):
        root = self.to_xml_tree(chapter_number)
        xmlstr = minidom.parseString(ElementTree.tostring(root)).toprettyxml()
        with open(filename, "w", encoding="UTF-8") as write_file:
            write_file.write(xmlstr)
