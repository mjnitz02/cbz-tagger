import os

from cbz_tagger.container.container import get_environment_variables
from cbz_tagger.container.file_scanner import FileScanner

dir_path = os.path.dirname(os.path.realpath(__file__))
env_vars = get_environment_variables()

config_path = os.path.join(dir_path, "config")
scan_path = os.path.join(dir_path, "scan")
storage_path = os.path.join(dir_path, "storage")

os.makedirs(config_path, exist_ok=True)
os.makedirs(scan_path, exist_ok=True)
os.makedirs(storage_path, exist_ok=True)

# try:
scanner = FileScanner(
    config_path=config_path,
    scan_path=scan_path,
    storage_path=storage_path,
    environment=env_vars["environment"],
)
scanner.add()
scanner.download_chapters(config_path, storage_path)
# finally:
#     # shutil.rmtree(config_path)
#     shutil.rmtree(scan_path)
#     shutil.rmtree(storage_path)
