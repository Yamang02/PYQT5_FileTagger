from PyQt5.QtCore import QObject, pyqtSignal
from typing import List

from core.services.tag_service import TagService
from core.events import EventBus, TagAddedEvent, TagRemovedEvent

class FileDetailViewModel(QObject):
    # UI 업데이트를 위한 시그널
    file_details_updated = pyqtSignal(str, list) # file_path, tags
    show_message = pyqtSignal(str, int) # message, duration

    def __init__(self, tag_service: TagService, event_bus: EventBus):
        super().__init__()
        self._tag_service = tag_service
        self._event_bus = event_bus
        self._current_file_path: str = None

        # EventBus 구독
        self._event_bus.tag_removed.connect(self._on_tag_removed)
        self._event_bus.tag_added.connect(self._on_tag_added)

    def _on_tag_added(self, event: TagAddedEvent):
        # 현재 파일과 관련된 태그 변경 시 UI 업데이트
        if event.file_path == self._current_file_path:
            self.update_for_file(self._current_file_path)

    def _on_tag_removed(self, event: TagRemovedEvent):
        # 현재 파일과 관련된 태그 변경 시 UI 업데이트
        if event.file_path == self._current_file_path:
            self.update_for_file(self._current_file_path)

    def update_for_file(self, file_path: str):
        self._current_file_path = file_path
        if file_path:
            tags = self._tag_service.get_tags_for_file(file_path)
            self.file_details_updated.emit(file_path, tags)
        else:
            self.file_details_updated.emit(None, [])

    def remove_tag_from_file(self, tag_text: str):
        if self._current_file_path:
            if self._tag_service.remove_tag_from_file(self._current_file_path, tag_text):
                self.show_message.emit(f"'{tag_text}' 태그 제거됨", 2000)
            else:
                self.show_message.emit(f"'{tag_text}' 태그 제거 실패", 2000)
        else:
            self.show_message.emit("파일을 선택해주세요.", 2000)
