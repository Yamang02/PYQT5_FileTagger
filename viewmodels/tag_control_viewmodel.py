from PyQt5.QtCore import QObject, pyqtSignal
from typing import List, Dict, Optional
from core.services.tag_service import TagService
from core.events import EventBus, TagAddedEvent, TagRemovedEvent
from core.repositories.tag_repository import TagRepository


class TagControlViewModel(QObject):
    # UI 업데이트를 위한 시그널
    tags_updated = pyqtSignal(list)
    target_info_updated = pyqtSignal(str, bool) # target_label, is_dir
    enable_ui = pyqtSignal(bool)
    show_message = pyqtSignal(str, int) # message, duration
    
    # 새로운 시그널들
    tag_suggestions_updated = pyqtSignal(list)  # 태그 자동완성 제안
    tag_statistics_updated = pyqtSignal(dict)   # 태그 통계 정보
    recent_tags_updated = pyqtSignal(list)      # 최근 사용된 태그
    popular_tags_updated = pyqtSignal(list)     # 인기 태그

    def __init__(self, tag_service: TagService, event_bus: EventBus, tag_repository: TagRepository):
        super().__init__()
        self._tag_service = tag_service
        self._event_bus = event_bus
        self._tag_repository = tag_repository

        self._current_target_path: str = None
        self._current_target_paths: List[str] = []
        self._is_current_target_dir: bool = False

        self._individual_tags: List[str] = []
        self._batch_tags: List[str] = []
        
        # 캐시된 데이터
        self._cached_tag_suggestions: List[str] = []
        self._cached_statistics: Dict = {}
        self._cached_recent_tags: List[str] = []
        self._cached_popular_tags: List[str] = []

        # EventBus 구독
        self._event_bus.tag_added.connect(self._on_tag_added)
        self._event_bus.tag_removed.connect(self._on_tag_removed)
        
        # 초기 데이터 로드
        self._load_initial_data()

    def _load_initial_data(self):
        """초기 데이터 로드"""
        try:
            # 태그 통계 로드
            self._load_tag_statistics()
            
            # 최근 태그 로드
            self._load_recent_tags()
            
            # 인기 태그 로드
            self._load_popular_tags()
            
        except Exception as e:
            print(f"[ERROR] 초기 데이터 로드 실패: {e}")

    def _load_tag_statistics(self):
        """태그 통계 로드"""
        try:
            stats = self._tag_repository.get_tag_statistics()
            self._cached_statistics = stats
            self.tag_statistics_updated.emit(stats)
        except Exception as e:
            print(f"[ERROR] 태그 통계 로드 실패: {e}")

    def _load_recent_tags(self):
        """최근 사용된 태그 로드"""
        try:
            recent_files = self._tag_repository.get_recently_tagged_files(limit=20)
            recent_tags = set()
            
            for file_path in recent_files:
                tags = self._tag_service.get_tags_for_file(file_path)
                recent_tags.update(tags)
            
            self._cached_recent_tags = list(recent_tags)[:10]
            self.recent_tags_updated.emit(self._cached_recent_tags)
        except Exception as e:
            print(f"[ERROR] 최근 태그 로드 실패: {e}")

    def _load_popular_tags(self):
        """인기 태그 로드"""
        try:
            stats = self._tag_repository.get_tag_statistics()
            popular_tags = [tag["tag_name"] for tag in stats.get("popular_tags", [])]
            self._cached_popular_tags = popular_tags[:10]
            self.popular_tags_updated.emit(self._cached_popular_tags)
        except Exception as e:
            print(f"[ERROR] 인기 태그 로드 실패: {e}")

    def search_tag_suggestions(self, query: str, limit: int = 10) -> List[str]:
        """태그 자동완성 제안"""
        try:
            if not query or len(query) < 2:
                return []
            
            # 텍스트 검색으로 태그 찾기
            suggestions = self._tag_repository.search_tags_by_text(query, limit=limit)
            
            # 최근 태그와 인기 태그에서도 검색
            all_tags = self._tag_service.get_all_tags()
            for tag in all_tags:
                if query.lower() in tag.lower() and tag not in suggestions:
                    suggestions.append(tag)
                    if len(suggestions) >= limit:
                        break
            
            self._cached_tag_suggestions = suggestions[:limit]
            self.tag_suggestions_updated.emit(suggestions)
            return suggestions
            
        except Exception as e:
            print(f"[ERROR] 태그 제안 검색 실패: {e}")
            return []

    def get_tag_suggestions(self) -> List[str]:
        """캐시된 태그 제안 반환"""
        return self._cached_tag_suggestions

    def get_tag_statistics(self) -> Dict:
        """태그 통계 반환"""
        return self._cached_statistics

    def get_recent_tags(self) -> List[str]:
        """최근 사용된 태그 반환"""
        return self._cached_recent_tags

    def get_popular_tags(self) -> List[str]:
        """인기 태그 반환"""
        return self._cached_popular_tags

    def refresh_tag_data(self):
        """태그 데이터 새로고침"""
        self._load_tag_statistics()
        self._load_recent_tags()
        self._load_popular_tags()

    def _on_tag_added(self, event: TagAddedEvent):
        # 현재 대상 파일/디렉토리와 관련된 태그 변경 시 UI 업데이트
        if event.file_path == self._current_target_path or event.file_path in self._current_target_paths:
            self.update_tags_for_current_target()
        
        # 태그 데이터 새로고침
        self.refresh_tag_data()

    def _on_tag_removed(self, event: TagRemovedEvent):
        # 현재 대상 파일/디렉토리와 관련된 태그 변경 시 UI 업데이트
        if event.file_path == self._current_target_path or event.file_path in self._current_target_paths:
            self.update_tags_for_current_target()
        
        # 태그 데이터 새로고침
        self.refresh_tag_data()

    def update_for_target(self, target, is_dir):
        self._current_target_path = None
        self._current_target_paths = []
        self._is_current_target_dir = is_dir

        if isinstance(target, list):
            self._current_target_paths = target
            self.target_info_updated.emit(f"선택된 파일: {len(target)}개", True)
            self.enable_ui.emit(True)
            self.update_tags_for_current_target()

        elif isinstance(target, str):
            self._current_target_path = target
            if not target:
                self.enable_ui.emit(False)
                self.target_info_updated.emit("선택된 파일 없음", False)
                self.tags_updated.emit([])
                return

            self.enable_ui.emit(True)
            if is_dir:
                self.target_info_updated.emit(f"대상 디렉토리: {target}", True)
            else:
                self.target_info_updated.emit(f"선택된 파일: {target}", False)
            self.update_tags_for_current_target()

        else:
            self.enable_ui.emit(False)
            self.target_info_updated.emit("선택된 파일 없음", False)
            self.tags_updated.emit([])

    def update_tags_for_current_target(self):
        if self._current_target_path and not self._is_current_target_dir:
            tags = self._tag_service.get_tags_for_file(self._current_target_path)
            self._individual_tags = tags
            self.tags_updated.emit(tags)
        elif self._current_target_paths:
            common_tags = self._get_common_tags_for_files(self._current_target_paths)
            self._batch_tags = common_tags
            self.tags_updated.emit(common_tags)
        else:
            self.tags_updated.emit([])

    def _get_common_tags_for_files(self, file_paths: List[str]) -> List[str]:
        if not file_paths:
            return []
        
        common_tags = set(self._tag_service.get_tags_for_file(file_paths[0]))
        for file_path in file_paths[1:]:
            file_tags = set(self._tag_service.get_tags_for_file(file_path))
            common_tags = common_tags.intersection(file_tags)
        return list(common_tags)

    def add_tag_to_individual(self, tag_text: str):
        if self._current_target_path and not self._is_current_target_dir:
            if self._tag_service.add_tag_to_file(self._current_target_path, tag_text):
                self.show_message.emit(f"'{tag_text}' 태그 추가됨", 2000)
            else:
                self.show_message.emit(f"'{tag_text}' 태그 추가 실패", 2000)
        else:
            self.show_message.emit("파일을 선택해주세요.", 2000)

    def remove_tag_from_individual(self, tag_text: str):
        if self._current_target_path and not self._is_current_target_dir:
            if self._tag_service.remove_tag_from_file(self._current_target_path, tag_text):
                self.show_message.emit(f"'{tag_text}' 태그 제거됨", 2000)
            else:
                self.show_message.emit(f"'{tag_text}' 태그 제거 실패", 2000)
        else:
            self.show_message.emit("파일을 선택해주세요.", 2000)

    def apply_batch_tags(self, tags_to_add: List[str], recursive: bool, file_extensions: List[str]):
        if not tags_to_add:
            self.show_message.emit("적용할 태그를 입력해주세요.", 2000)
            return

        if self._current_target_paths: # 다중 파일 선택
            result = self._tag_service.add_tags_to_files(self._current_target_paths, tags_to_add)
            if result.get("success"):
                self.show_message.emit(f"{result.get('successful', 0)}개 항목에 태그가 성공적으로 적용되었습니다.", 3000)
            else:
                self.show_message.emit(f"일괄 태깅 실패: {result.get('error', '알 수 없는 오류')}", 3000)

        elif self._current_target_path and self._is_current_target_dir: # 단일 디렉토리 선택
            result = self._tag_service.add_tags_to_directory(
                self._current_target_path, 
                tags_to_add, 
                recursive=recursive, 
                file_extensions=file_extensions
            )
            if result.get("success"):
                self.show_message.emit(f"{result.get('successful', 0)}개 항목에 태그가 성공적으로 적용되었습니다.", 3000)
            else:
                self.show_message.emit(f"일괄 태깅 실패: {result.get('error', '알 수 없는 오류')}", 3000)
        else:
            self.show_message.emit("태그를 적용할 대상(파일/디렉토리)이 선택되지 않았습니다.", 2000)

    def get_all_tags(self) -> List[str]:
        return self._tag_service.get_all_tags()

    def get_current_individual_tags(self) -> List[str]:
        return self._individual_tags

    def get_current_batch_tags(self) -> List[str]:
        return self._batch_tags

    def get_current_target_paths(self) -> List[str]:
        return self._current_target_paths

    def get_current_target_path(self) -> str:
        return self._current_target_path

    def is_current_target_dir(self) -> bool:
        return self._is_current_target_dir
