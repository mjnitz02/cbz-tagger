"""Backend parameterization for the repository conformance and persistence suites.

PR B adds "sqlite" to `REPOSITORY_BACKENDS` and a branch to `build_test_repository`;
nothing else in either suite should need to change.
"""

from cbz_tagger.database.repository import JsonRepository
from cbz_tagger.database.repository import Repository

REPOSITORY_BACKENDS = ["json"]


def build_test_repository(backend: str, config_path: str, storage_path: str) -> Repository:
    if backend == "json":
        # storage_path is unused by the JSON backend; the SQLite migration needs it to
        # recover download records by scanning the library, so it is in the signature now.
        _ = storage_path
        return JsonRepository(config_path)
    raise ValueError(f"Unknown repository backend: {backend}")
