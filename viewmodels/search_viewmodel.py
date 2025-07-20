from PyQt5.QtCore import QObject, pyqtSignal
from typing import List, Dict, Optional
from core.services.tag_service import TagService
from core.search_manager import SearchManager
from core.repositories.tag_repository import TagRepository


class SearchViewModel(QObject):
    # UI 업데이트를 위한 시그널
    search_completed = pyqtSignal(int, str) # count, summary
    search_requested = pyqtSignal(dict) # search_conditions
    search_results_ready = pyqtSignal(list) # file_paths
    search_cleared = pyqtSignal() # no args
    
    # 새로운 시그널들
    search_history_updated = pyqtSignal(list)  # 검색 히스토리
    search_suggestions_updated = pyqtSignal(list)  # 검색 제안
    search_statistics_updated = pyqtSignal(dict)  # 검색 통계

    def __init__(self, tag_service: TagService, search_manager: SearchManager, tag_repository: TagRepository):
        super().__init__()
        self._tag_service = tag_service
        self._search_manager = search_manager
        self._tag_repository = tag_repository
        
        # 검색 히스토리 및 캐시
        self._search_history: List[Dict] = []
        self._recent_searches: List[str] = []
        self._search_suggestions: List[str] = []
        self._last_search_conditions: Optional[Dict] = None
        self._cached_results: List[str] = []

    def perform_search(self, search_conditions: Dict):
        """검색 수행"""
        print(f"[DEBUG] SearchViewModel.perform_search 호출: {search_conditions}")
        
        try:
            # 검색 실행
            search_results = self._search_manager.search_files(search_conditions)
            print(f"[DEBUG] 검색 결과: {len(search_results)}개 파일")
            
            # 결과 캐시
            self._cached_results = search_results
            self._last_search_conditions = search_conditions
            
            # 검색 히스토리에 추가
            self._add_to_search_history(search_conditions, len(search_results))
            
            # 요약 생성
            summary = self._generate_summary(search_conditions)
            
            # 시그널 발생
            self.search_completed.emit(len(search_results), summary)
            self.search_results_ready.emit(search_results)
            
            # 검색 통계 업데이트
            self._update_search_statistics()
            
        except Exception as e:
            print(f"[ERROR] 검색 실패: {e}")
            self.search_completed.emit(0, f"검색 실패: {str(e)}")
            self.search_results_ready.emit([])

    def _add_to_search_history(self, search_conditions: Dict, result_count: int):
        """검색 히스토리에 추가"""
        from datetime import datetime
        
        history_entry = {
            "conditions": search_conditions.copy(),
            "result_count": result_count,
            "timestamp": datetime.now(),
            "summary": self._generate_summary(search_conditions)
        }
        
        # 중복 제거 (동일한 조건이 있으면 제거)
        self._search_history = [entry for entry in self._search_history 
                              if entry["conditions"] != search_conditions]
        
        # 최신 항목을 맨 앞에 추가
        self._search_history.insert(0, history_entry)
        
        # 히스토리 크기 제한 (최대 50개)
        if len(self._search_history) > 50:
            self._search_history = self._search_history[:50]
        
        # 검색 히스토리 업데이트 시그널
        self.search_history_updated.emit(self._search_history)

    def get_search_history(self) -> List[Dict]:
        """검색 히스토리 반환"""
        return self._search_history

    def clear_search_history(self):
        """검색 히스토리 초기화"""
        self._search_history.clear()
        self.search_history_updated.emit([])

    def repeat_last_search(self):
        """마지막 검색 반복"""
        if self._last_search_conditions:
            self.perform_search(self._last_search_conditions)

    def get_search_suggestions(self, query: str) -> List[str]:
        """검색 제안 생성"""
        suggestions = []
        
        try:
            # 태그 기반 제안
            if query.startswith("tag:"):
                tag_query = query[4:].strip()
                if tag_query:
                    tag_suggestions = self._tag_repository.search_tags_by_text(tag_query, limit=5)
                    suggestions.extend([f"tag:{tag}" for tag in tag_suggestions])
            
            # 파일명 기반 제안
            elif query.startswith("file:"):
                file_query = query[5:].strip()
                if file_query:
                    # 최근 검색에서 파일명 패턴 찾기
                    for entry in self._search_history:
                        if "filename" in entry["conditions"]:
                            filename = entry["conditions"]["filename"].get("name", "")
                            if file_query.lower() in filename.lower():
                                suggestions.append(f"file:{filename}")
            
            # 일반 검색 제안
            else:
                # 최근 검색에서 제안
                for entry in self._search_history:
                    summary = entry["summary"]
                    if query.lower() in summary.lower():
                        suggestions.append(summary)
                
                # 태그 제안
                all_tags = self._tag_service.get_all_tags()
                for tag in all_tags:
                    if query.lower() in tag.lower():
                        suggestions.append(f"tag:{tag}")
            
            # 중복 제거 및 제한
            suggestions = list(set(suggestions))[:10]
            self._search_suggestions = suggestions
            self.search_suggestions_updated.emit(suggestions)
            
        except Exception as e:
            print(f"[ERROR] 검색 제안 생성 실패: {e}")
        
        return suggestions

    def _update_search_statistics(self):
        """검색 통계 업데이트"""
        try:
            stats = {
                "total_searches": len(self._search_history),
                "recent_searches": len([entry for entry in self._search_history 
                                      if (datetime.now() - entry["timestamp"]).days < 7]),
                "average_results": sum(entry["result_count"] for entry in self._search_history) / 
                                 max(len(self._search_history), 1),
                "most_common_conditions": self._get_most_common_search_conditions()
            }
            
            self.search_statistics_updated.emit(stats)
            
        except Exception as e:
            print(f"[ERROR] 검색 통계 업데이트 실패: {e}")

    def _get_most_common_search_conditions(self) -> List[str]:
        """가장 자주 사용된 검색 조건"""
        condition_counts = {}
        
        for entry in self._search_history:
            summary = entry["summary"]
            condition_counts[summary] = condition_counts.get(summary, 0) + 1
        
        # 빈도순으로 정렬
        sorted_conditions = sorted(condition_counts.items(), 
                                 key=lambda x: x[1], reverse=True)
        
        return [condition for condition, count in sorted_conditions[:5]]

    def clear_search(self):
        """검색 결과 초기화"""
        self._cached_results = []
        self._last_search_conditions = None
        self.search_cleared.emit()

    def update_search_results(self, count: int, summary: str):
        """검색 결과 업데이트"""
        self.search_completed.emit(count, summary)

    def get_all_tags(self) -> List[str]:
        """모든 태그 반환"""
        return self._tag_service.get_all_tags()

    def get_cached_results(self) -> List[str]:
        """캐시된 검색 결과 반환"""
        return self._cached_results

    def get_last_search_conditions(self) -> Optional[Dict]:
        """마지막 검색 조건 반환"""
        return self._last_search_conditions

    def _generate_summary(self, search_conditions: Dict) -> str:
        """검색 조건 요약 생성"""
        summary_parts = []
        
        # 새로운 검색 형식 지원
        if "exact" in search_conditions and search_conditions["exact"]:
            exact_conditions = search_conditions["exact"]
            if "tags" in exact_conditions and "exact" in exact_conditions["tags"]:
                tags = exact_conditions["tags"]["exact"]
                summary_parts.append(f"정확한 태그: {', '.join(tags)}")
        
        if "partial" in search_conditions and search_conditions["partial"]:
            partial_conditions = search_conditions["partial"]
            if "tags" in partial_conditions and "partial" in partial_conditions["tags"]:
                tags = partial_conditions["tags"]["partial"]
                summary_parts.append(f"부분 태그: {', '.join(tags)}")
        
        # 기존 형식 지원
        if "filename" in search_conditions:
            filename_cond = search_conditions["filename"]
            if "name" in filename_cond:
                summary_parts.append(f"파일명: '{filename_cond['name']}'")
            if "partial" in filename_cond:
                summary_parts.append(f"파일명 부분: '{filename_cond['partial']}'")
        
        if "tags" in search_conditions:
            tag_cond = search_conditions["tags"]
            if "query" in tag_cond:
                summary_parts.append(f"태그: '{tag_cond['query']}'")
        
        if "extensions" in search_conditions:
            ext_cond = search_conditions["extensions"]
            if "partial" in ext_cond:
                summary_parts.append(f"확장자: {', '.join(ext_cond['partial'])}")
            elif isinstance(ext_cond, list):
                summary_parts.append(f"확장자: {', '.join(ext_cond)}")
        
        if not summary_parts:
            return "모든 파일"
        
        return ", ".join(summary_parts)
