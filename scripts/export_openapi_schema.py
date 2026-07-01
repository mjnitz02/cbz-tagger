import json
from pathlib import Path

from cbz_tagger.web.api import app

output_path = Path(__file__).resolve().parent.parent / "frontend" / "openapi.json"
output_path.write_text(json.dumps(app.openapi(), indent=2))
