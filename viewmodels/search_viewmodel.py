from PyQt5.QtCore import QObject, pyqtSignal
from typing import List, Dict

from core.services.tag_service import TagService
from core.search_manager import SearchManager

class SearchViewModel(QObject):
    # UI 업데이트를 위한 시그널
    search_completed = pyqtSignal(int, str) # count, summary
    search_requested = pyqtSignal(dict) # search_conditions
    search_results_ready = pyqtSignal(list) # file_paths
    search_cleared = pyqtSignal() # no args

    def __init__(self, tag_service: TagService, search_manager: SearchManager):
        super().__init__()
        self._tag_service = tag_service
        self._search_manager = search_manager

    def perform_search(self, search_conditions: Dict):
        search_results = self._search_manager.search_files(search_conditions)
        summary = self._generate_summary(search_conditions)
        self.search_completed.emit(len(search_results), summary)
        self.search_results_ready.emit(search_results)

    def clear_search(self):
        self.search_cleared.emit()

    def update_search_results(self, count: int, summary: str):
        self.search_completed.emit(count, summary)

    def get_all_tags(self) -> List[str]:
        return self._tag_service.get_all_tags()
