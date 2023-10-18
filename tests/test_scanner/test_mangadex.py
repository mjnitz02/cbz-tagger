from cbz_tagger.database.cbz_database import CbzDatabase
from cbz_tagger.database.cbz_scanner import CbzScanner

# title = "Tonikaku Kawaii"
#
# db = CbzDatabase()
# xml_1 = db.get_metadata(title, 1)
# xml_2 = db.get_metadata(title, 2)
# db.update_metadata(title)
# image_str = db.get_image_data(title, 1)
# assert True

scanner = CbzScanner()
scanner.scan()
