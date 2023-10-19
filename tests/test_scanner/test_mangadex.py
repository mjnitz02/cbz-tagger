from cbz_tagger.container.cbz_scanner import CbzScanner

# title = "Tonikaku Kawaii"
#
# database = CbzDatabase()
# xml_1 = database.get_metadata(title, 1)
# xml_2 = database.get_metadata(title, 2)
# database.update_metadata(title)
# image_str = database.get_image_data(title, 1)
# assert True

scanner = CbzScanner()
scanner.scan()
