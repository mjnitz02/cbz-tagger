from nicegui import app

from cbz_tagger.common.enums import ContainerMode
from cbz_tagger.common.env import AppEnv
from cbz_tagger.common.get_arg_parser import get_arg_parser
from cbz_tagger.container import Container

# Store Container instance as an attribute on the app object to maintain a single instance
# across all client connections and page reloads. This ensures all clients see the same
# server state rather than isolated instances.
if not hasattr(app, "container_instance"):
    app.container_instance = Container()

kwargs = get_arg_parser()
container = app.container_instance

if kwargs.get("entrymode"):
    if AppEnv.CONTAINER_MODE == ContainerMode.TIMER:
        container.run_timer()
    else:
        container.run_gui()
else:
    container.run_manual(**kwargs)
