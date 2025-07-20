import pytest
from unittest.mock import Mock, MagicMock
from typing import List, Dict
from PyQt5.QtCore import QObject
from viewmodels.tag_control_viewmodel import TagControlViewModel
from viewmodels.search_viewmodel import SearchViewModel
from core.services.tag_service import TagService
from core.search_manager import SearchManager
from core.repositories.tag_repository import TagRepository
from core.events import EventBus, TagAddedEvent, TagRemovedEvent


class TestEnhancedTagControlViewModel:
    """개선된 TagControlViewModel 테스트"""
    
    @pytest.fixture
    def mock_tag_service(self):
        """Mock TagService"""
        return Mock(spec=TagService)
    
    @pytest.fixture
    def mock_event_bus(self):
        """Mock EventBus"""
        return Mock(spec=EventBus)
    
    @pytest.fixture
    def mock_tag_repository(self):
        """Mock TagRepository"""
        return Mock(spec=TagRepository)
    
    @pytest.fixture
    def view_model(self, mock_tag_service, mock_event_bus, mock_tag_repository):
        """TagControlViewModel 인스턴스"""
        return TagControlViewModel(mock_tag_service, mock_event_bus, mock_tag_repository)
    
    def test_initial_data_loading(self, view_model, mock_tag_repository):
        """초기 데이터 로드 테스트"""
        # Mock 설정
        mock_tag_repository.get_tag_statistics.return_value = {
            "total_tags": 100,
            "total_files": 500,
            "popular_tags": [{"tag_name": "개발", "count": 50}]
        }
        
        mock_tag_repository.get_recently_tagged_files.return_value = ["file1.txt", "file2.txt"]
        mock_tag_service.get_tags_for_file.side_effect = [["태그1", "태그2"], ["태그2", "태그3"]]
        
        # 초기화 시 데이터 로드 확인
        assert view_model.get_tag_statistics()["total_tags"] == 100
        assert len(view_model.get_recent_tags()) > 0
    
    def test_tag_suggestions_search(self, view_model, mock_tag_repository, mock_tag_service):
        """태그 자동완성 제안 테스트"""
        # Mock 설정
        mock_tag_repository.search_tags_by_text.return_value = ["개발태그", "테스트태그"]
        mock_tag_service.get_all_tags.return_value = ["개발태그", "테스트태그", "문서태그"]
        
        # 태그 제안 검색
        suggestions = view_model.search_tag_suggestions("개발")
        
        assert "개발태그" in suggestions
        assert "테스트태그" in suggestions
        mock_tag_repository.search_tags_by_text.assert_called_once_with("개발", 10)
    
    def test_tag_suggestions_empty_query(self, view_model):
        """빈 쿼리로 태그 제안 검색"""
        suggestions = view_model.search_tag_suggestions("")
        assert suggestions == []
        
        suggestions = view_model.search_tag_suggestions("a")
        assert suggestions == []
    
    def test_refresh_tag_data(self, view_model, mock_tag_repository, mock_tag_service):
        """태그 데이터 새로고침 테스트"""
        # Mock 설정
        mock_tag_repository.get_tag_statistics.return_value = {"total_tags": 200}
        mock_tag_repository.get_recently_tagged_files.return_value = ["file1.txt"]
        mock_tag_service.get_tags_for_file.return_value = ["새태그"]
        
        # 데이터 새로고침
        view_model.refresh_tag_data()
        
        # 메서드들이 호출되었는지 확인
        assert mock_tag_repository.get_tag_statistics.call_count >= 2
        assert mock_tag_repository.get_recently_tagged_files.call_count >= 2
    
    def test_event_handling_with_data_refresh(self, view_model, mock_event_bus):
        """이벤트 처리 시 데이터 새로고침 테스트"""
        # 이벤트 발생 시뮬레이션
        event = TagAddedEvent("test.txt", "새태그")
        view_model._on_tag_added(event)
        
        # 이벤트가 처리되었는지 확인
        assert True  # 예외가 발생하지 않으면 성공


class TestEnhancedSearchViewModel:
    """개선된 SearchViewModel 테스트"""
    
    @pytest.fixture
    def mock_tag_service(self):
        """Mock TagService"""
        return Mock(spec=TagService)
    
    @pytest.fixture
    def mock_search_manager(self):
        """Mock SearchManager"""
        return Mock(spec=SearchManager)
    
    @pytest.fixture
    def mock_tag_repository(self):
        """Mock TagRepository"""
        return Mock(spec=TagRepository)
    
    @pytest.fixture
    def view_model(self, mock_tag_service, mock_search_manager, mock_tag_repository):
        """SearchViewModel 인스턴스"""
        return SearchViewModel(mock_tag_service, mock_search_manager, mock_tag_repository)
    
    def test_perform_search_with_history(self, view_model, mock_search_manager):
        """검색 히스토리가 포함된 검색 테스트"""
        # Mock 설정
        search_conditions = {"exact": {"tags": {"exact": ["테스트"]}}}
        mock_search_manager.search_files.return_value = ["file1.txt", "file2.txt"]
        
        # 검색 수행
        view_model.perform_search(search_conditions)
        
        # 검색 히스토리에 추가되었는지 확인
        history = view_model.get_search_history()
        assert len(history) == 1
        assert history[0]["result_count"] == 2
        assert history[0]["conditions"] == search_conditions
    
    def test_search_history_duplicate_removal(self, view_model, mock_search_manager):
        """중복 검색 히스토리 제거 테스트"""
        # Mock 설정
        search_conditions = {"exact": {"tags": {"exact": ["테스트"]}}}
        mock_search_manager.search_files.return_value = ["file1.txt"]
        
        # 동일한 조건으로 두 번 검색
        view_model.perform_search(search_conditions)
        view_model.perform_search(search_conditions)
        
        # 히스토리에 하나만 있어야 함
        history = view_model.get_search_history()
        assert len(history) == 1
    
    def test_search_history_limit(self, view_model, mock_search_manager):
        """검색 히스토리 크기 제한 테스트"""
        # Mock 설정
        mock_search_manager.search_files.return_value = []
        
        # 55번 검색 (제한은 50개)
        for i in range(55):
            search_conditions = {"exact": {"tags": {"exact": [f"태그{i}"]}}}
            view_model.perform_search(search_conditions)
        
        # 히스토리 크기가 50개로 제한되었는지 확인
        history = view_model.get_search_history()
        assert len(history) == 50
    
    def test_search_suggestions_tag_based(self, view_model, mock_tag_repository):
        """태그 기반 검색 제안 테스트"""
        # Mock 설정
        mock_tag_repository.search_tags_by_text.return_value = ["개발태그", "테스트태그"]
        
        # 태그 기반 제안
        suggestions = view_model.get_search_suggestions("tag:개발")
        
        assert "tag:개발태그" in suggestions
        assert "tag:테스트태그" in suggestions
    
    def test_search_suggestions_file_based(self, view_model, mock_tag_service):
        """파일명 기반 검색 제안 테스트"""
        # Mock 설정
        view_model._search_history = [{
            "conditions": {"filename": {"name": "test.txt"}},
            "summary": "파일명: 'test.txt'"
        }]
        
        # 파일명 기반 제안
        suggestions = view_model.get_search_suggestions("file:test")
        
        assert "file:test.txt" in suggestions
    
    def test_search_suggestions_general(self, view_model, mock_tag_service):
        """일반 검색 제안 테스트"""
        # Mock 설정
        view_model._search_history = [{
            "conditions": {"exact": {"tags": {"exact": ["개발"]}}},
            "summary": "정확한 태그: 개발"
        }]
        mock_tag_service.get_all_tags.return_value = ["개발태그", "테스트태그"]
        
        # 일반 검색 제안
        suggestions = view_model.get_search_suggestions("개발")
        
        assert "정확한 태그: 개발" in suggestions
        assert "tag:개발태그" in suggestions
    
    def test_repeat_last_search(self, view_model, mock_search_manager):
        """마지막 검색 반복 테스트"""
        # Mock 설정
        search_conditions = {"exact": {"tags": {"exact": ["테스트"]}}}
        mock_search_manager.search_files.return_value = ["file1.txt"]
        
        # 첫 번째 검색
        view_model.perform_search(search_conditions)
        
        # 마지막 검색 반복
        view_model.repeat_last_search()
        
        # 두 번 호출되었는지 확인
        assert mock_search_manager.search_files.call_count == 2
    
    def test_clear_search_history(self, view_model, mock_search_manager):
        """검색 히스토리 초기화 테스트"""
        # Mock 설정
        mock_search_manager.search_files.return_value = []
        
        # 검색 수행
        view_model.perform_search({"exact": {"tags": {"exact": ["테스트"]}}})
        
        # 히스토리 초기화
        view_model.clear_search_history()
        
        # 히스토리가 비어있는지 확인
        assert len(view_model.get_search_history()) == 0
    
    def test_generate_summary_new_format(self, view_model):
        """새로운 형식의 검색 조건 요약 생성 테스트"""
        # 새로운 형식 테스트
        conditions = {
            "exact": {"tags": {"exact": ["개발", "중요"]}},
            "partial": {"tags": {"partial": ["테스트"]}}
        }
        
        summary = view_model._generate_summary(conditions)
        
        assert "정확한 태그: 개발, 중요" in summary
        assert "부분 태그: 테스트" in summary
    
    def test_generate_summary_legacy_format(self, view_model):
        """기존 형식의 검색 조건 요약 생성 테스트"""
        # 기존 형식 테스트
        conditions = {
            "filename": {"name": "test.txt"},
            "tags": {"query": "개발"},
            "extensions": ["txt", "pdf"]
        }
        
        summary = view_model._generate_summary(conditions)
        
        assert "파일명: 'test.txt'" in summary
        assert "태그: '개발'" in summary
        assert "확장자: txt, pdf" in summary
    
    def test_error_handling_in_search(self, view_model, mock_search_manager):
        """검색 중 에러 처리 테스트"""
        # Mock 설정 - 예외 발생
        mock_search_manager.search_files.side_effect = Exception("Search failed")
        
        # 검색 수행
        view_model.perform_search({"exact": {"tags": {"exact": ["테스트"]}}})
        
        # 에러가 처리되었는지 확인 (예외가 발생하지 않으면 성공)
        assert True
    
    def test_cached_results_access(self, view_model, mock_search_manager):
        """캐시된 검색 결과 접근 테스트"""
        # Mock 설정
        mock_search_manager.search_files.return_value = ["file1.txt", "file2.txt"]
        
        # 검색 수행
        view_model.perform_search({"exact": {"tags": {"exact": ["테스트"]}}})
        
        # 캐시된 결과 확인
        cached_results = view_model.get_cached_results()
        assert cached_results == ["file1.txt", "file2.txt"]
    
    def test_last_search_conditions_access(self, view_model, mock_search_manager):
        """마지막 검색 조건 접근 테스트"""
        # Mock 설정
        search_conditions = {"exact": {"tags": {"exact": ["테스트"]}}}
        mock_search_manager.search_files.return_value = []
        
        # 검색 수행
        view_model.perform_search(search_conditions)
        
        # 마지막 검색 조건 확인
        last_conditions = view_model.get_last_search_conditions()
        assert last_conditions == search_conditions 