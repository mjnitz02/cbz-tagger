import argparse

from manga_tag.services.container import Container
from manga_tag.services.manga_scanner import MangaScanner

parser = argparse.ArgumentParser(description="Manga Tagger")
parser.add_argument(
    "--entrymode", help="Container Entrymode Start", action="store_true"
)
parser.add_argument("--auto", help="Auto Mode", action="store_true")
parser.add_argument("--manual", help="Manual Mode", action="store_true")
parser.add_argument("--retag", help="Retag existing files", action="store_true")
parser.add_argument("--update", help="Update a database entry", action="store_true")
args = vars(parser.parse_args())

print("Fast Manga Tagger v1.0")
print("----------------------")
if args["entrymode"]:
    container = Container()
    container.run()
else:
    scanner = MangaScanner(args)
    scanner.run()
