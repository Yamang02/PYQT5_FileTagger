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
        print(f"[DEBUG] SearchViewModel.perform_search 호출: {search_conditions}")
        search_results = self._search_manager.search_files(search_conditions)
        print(f"[DEBUG] 검색 결과: {len(search_results)}개 파일")
        summary = self._generate_summary(search_conditions)
        self.search_completed.emit(len(search_results), summary)
        self.search_results_ready.emit(search_results)

    def clear_search(self):
        self.search_cleared.emit()

    def update_search_results(self, count: int, summary: str):
        self.search_completed.emit(count, summary)

    def get_all_tags(self) -> List[str]:
        return self._tag_service.get_all_tags()

    def _generate_summary(self, search_conditions: Dict) -> str:
        summary_parts = []
        if search_conditions.get("filename"):
            summary_parts.append(f"파일명: '{search_conditions['filename']}'")
        if search_conditions.get("tags"):
            tag_query = search_conditions['tags'].get('query')
            if tag_query:
                summary_parts.append(f"태그: '{tag_query}'")
        if search_conditions.get("extensions"):
            summary_parts.append(f"확장자: {', '.join(search_conditions['extensions'])}")
        
        if not summary_parts:
            return "모든 파일"
        return ", ".join(summary_parts)
