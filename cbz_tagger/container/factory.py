from cbz_tagger.common.enums import ContainerMode
from cbz_tagger.container.manual import ManualContainer
from cbz_tagger.container.timer import TimerContainer

container_factory = {
    ContainerMode.MANUAL: ManualContainer,
    ContainerMode.TIMER: TimerContainer,
}
