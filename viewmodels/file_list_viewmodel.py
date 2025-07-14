from PyQt5.QtCore import QObject, pyqtSignal
from typing import List
import os

from core.services.tag_service import TagService
from core.events import EventBus, TagAddedEvent, TagRemovedEvent
from core.path_utils import normalize_path

class FileListViewModel(QObject):
    # UI 업데이트를 위한 시그널
    files_updated = pyqtSignal(list) # file_paths
    show_message = pyqtSignal(str, int) # message, duration

    def __init__(self, tag_service: TagService, event_bus: EventBus):
        super().__init__()
        self._tag_service = tag_service
        self._event_bus = event_bus

        self._all_files: List[str] = [] # 필터링되지 않은 모든 파일 목록 (디렉토리 모드)
        self._filtered_files: List[str] = [] # 필터링된 파일 목록 (디렉토리 모드)
        self._search_results: List[str] = [] # 검색 결과 파일 목록 (검색 모드)
        self._current_directory: str = ""
        self._tag_filter: str = "" # 현재 적용된 태그 필터
        self._is_search_mode: bool = False # 검색 모드 여부

        # EventBus 구독
        self._event_bus.tag_added.connect(self._on_tag_changed)
        self._event_bus.tag_removed.connect(self._on_tag_changed)

    def _on_tag_changed(self, event):
        # 태그 변경 시 파일 목록 새로고침
        if self._is_search_mode:
            # 검색 모드에서는 검색 결과를 다시 로드
            # TODO: SearchManager와 연동하여 검색 조건 유지하며 새로고침 필요
            pass
        else:
            # 디렉토리 모드에서는 현재 디렉토리 기준으로 새로고침
            self.set_directory(self._current_directory, self._recursive, self._file_extensions)

    def set_directory(self, directory_path: str, recursive: bool = False, file_extensions: List[str] = None):
        self._current_directory = directory_path
        self._recursive = recursive
        self._file_extensions = file_extensions
        self._is_search_mode = False
        self._tag_filter = ""

        self._all_files = self._tag_service.get_files_in_directory(directory_path, recursive, file_extensions)
        self._all_files.sort(key=lambda x: os.path.basename(x).lower())
        self._apply_filter()
        self.files_updated.emit(self._filtered_files)

    def set_tag_filter(self, tag_text: str):
        self._tag_filter = tag_text.strip()
        self._apply_filter()
        self.files_updated.emit(self._filtered_files)

    def set_search_results(self, file_paths: List[str]):
        self._search_results = sorted(file_paths, key=lambda x: os.path.basename(x).lower())
        self._is_search_mode = True
        self.files_updated.emit(self._search_results)

    def _apply_filter(self):
        if not self._tag_filter:
            self._filtered_files = list(self._all_files)
        else:
            self._filtered_files = []
            for file_path in self._all_files:
                tags = self._tag_service.get_tags_for_file(file_path)
                if self._tag_filter.lower() in [tag.lower() for tag in tags]:
                    self._filtered_files.append(file_path)

    def get_file_path_at_index(self, index: int) -> str:
        if self._is_search_mode:
            if index < len(self._search_results):
                return self._search_results[index]
        else:
            if index < len(self._filtered_files):
                return self._filtered_files[index]
        return ""

    def get_tags_for_file(self, file_path: str) -> List[str]:
        return self._tag_service.get_tags_for_file(file_path)

    def get_current_display_files(self) -> List[str]:
        return self._search_results if self._is_search_mode else self._filtered_files

    def get_current_directory(self) -> str:
        return self._current_directory

    def is_search_mode(self) -> bool:
        return self._is_search_mode
