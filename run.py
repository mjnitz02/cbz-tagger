from cbz_tagger.common.enums import ContainerMode
from cbz_tagger.common.env import AppEnv
from cbz_tagger.common.get_arg_parser import get_arg_parser
from cbz_tagger.container import Container

kwargs = get_arg_parser()
container = Container()
if kwargs.get("entrymode"):
    if AppEnv.CONTAINER_MODE == ContainerMode.TIMER:
        container.run_timer()
    else:
        container.run_gui()
else:
    container.run_manual(**kwargs)
