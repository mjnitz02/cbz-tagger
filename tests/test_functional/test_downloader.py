import os

from cbz_tagger.cbz_entity.cbz_scanner import CbzScanner
from cbz_tagger.container.container import get_environment_variables

dir_path = os.path.dirname(os.path.realpath(__file__))
env_vars = get_environment_variables()

config_path = os.path.join(dir_path, "config")
scan_path = os.path.join(dir_path, "scan")
storage_path = os.path.join(dir_path, "storage")

os.makedirs(config_path, exist_ok=True)
os.makedirs(scan_path, exist_ok=True)
os.makedirs(storage_path, exist_ok=True)

try:
    scanner = CbzScanner(
        config_path=config_path,
        scan_path=scan_path,
        storage_path=storage_path,
        environment=env_vars["environment"],
    )
    scanner.add()
finally:
    os.rmdir(config_path)
    os.rmdir(scan_path)
    os.rmdir(storage_path)
