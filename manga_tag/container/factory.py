from manga_tag.container.continuous import ContinuousContainer
from manga_tag.container.enums import ContainerMode
from manga_tag.container.manual import ManualContainer
from manga_tag.container.timer import TimerContainer

container_factory = {
    ContainerMode.MANUAL: ManualContainer(),
    ContainerMode.TIMER: TimerContainer(),
    ContainerMode.CONTINUOUS: ContinuousContainer(),
}