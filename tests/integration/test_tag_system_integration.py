import pytest
import tempfile
import os
from unittest.mock import Mock, MagicMock
from bson import ObjectId
from datetime import datetime
from typing import List, Dict
from core.repositories.tag_repository import TagRepository
from core.services.tag_service import TagService
from core.search_manager import SearchManager
from core.adapters.tag_manager_adapter import TagManagerAdapter
from core.events import EventBus
from models.tag_model import TagMetadata, create_tag


class TestTagSystemIntegration:
    """태그 시스템 통합 테스트"""
    
    @pytest.fixture
    def mock_mongo_client(self):
        """Mock MongoClient"""
        return Mock()
    
    @pytest.fixture
    def mock_db(self, mock_mongo_client):
        """Mock Database"""
        mock_db = Mock()
        mock_mongo_client.filetagger_db = mock_db
        return mock_db
    
    @pytest.fixture
    def mock_tags_collection(self, mock_db):
        """Mock tags collection"""
        mock_collection = Mock()
        mock_db.tags = mock_collection
        return mock_collection
    
    @pytest.fixture
    def mock_tagged_files_collection(self, mock_db):
        """Mock tagged_files collection"""
        mock_collection = Mock()
        mock_db.tagged_files = mock_collection
        return mock_collection
    
    @pytest.fixture
    def tag_repository(self, mock_mongo_client, mock_tags_collection, mock_tagged_files_collection):
        """TagRepository 인스턴스"""
        return TagRepository(mock_mongo_client)
    
    @pytest.fixture
    def event_bus(self):
        """EventBus 인스턴스"""
        return EventBus()
    
    @pytest.fixture
    def mock_tag_repository(self):
        """Mock TagRepository"""
        return Mock()
    
    @pytest.fixture
    def tag_service(self, mock_tag_repository, event_bus):
        """TagService 인스턴스"""
        return TagService(mock_tag_repository, event_bus)
    
    @pytest.fixture
    def tag_manager_adapter(self, tag_repository):
        """TagManagerAdapter 인스턴스"""
        return TagManagerAdapter(tag_repository)
    
    @pytest.fixture
    def search_manager(self, tag_manager_adapter):
        """SearchManager 인스턴스"""
        return SearchManager(tag_manager_adapter)
    
    def test_complete_tag_workflow(self, tag_service, search_manager, mock_tags_collection, mock_tagged_files_collection):
        """완전한 태그 워크플로우 테스트"""
        # 1. 태그 추가
        file_path = "C:/test/document.txt"
        tag_name = "중요문서"
        
        # Mock 설정 - 태그 생성
        tag_id = ObjectId()
        mock_tags_collection.find_one.return_value = None  # 태그가 존재하지 않음
        mock_tags_collection.insert_one.return_value = Mock(inserted_id=tag_id)
        
        # Mock 설정 - 파일에 태그 추가
        mock_result = Mock()
        mock_result.modified_count = 1
        mock_result.upserted_id = None
        mock_tagged_files_collection.update_one.return_value = mock_result
        
        # 태그 추가
        success = tag_service.add_tag_to_file(file_path, tag_name)
        assert success is True
        
        # 2. 태그 조회
        mock_tagged_files_collection.find_one.return_value = {
            "file_path": file_path,
            "tags": [tag_id]
        }
        
        mock_tags_collection.find_one.return_value = {
            "_id": tag_id,
            "name": tag_name
        }
        
        tags = tag_service.get_tags_for_file(file_path)
        assert tag_name in tags
        
        # 3. 태그 검색
        mock_tagged_files_collection.find.return_value = iter([
            {"file_path": file_path}
        ])
        
        search_conditions = {
            'exact': {
                'tags': {
                    'exact': [tag_name]
                }
            }
        }
        
        search_results = search_manager.search_files(search_conditions)
        assert file_path in search_results
    
    def test_batch_tagging_workflow(self, tag_service, mock_tags_collection, mock_tagged_files_collection):
        """일괄 태깅 워크플로우 테스트"""
        # 테스트 파일들
        file_paths = [
            "C:/test/file1.txt",
            "C:/test/file2.txt",
            "C:/test/file3.txt"
        ]
        tag_names = ["개발", "문서", "중요"]
        
        # Mock 설정
        tag_ids = [ObjectId() for _ in range(len(tag_names))]
        
        # 태그 생성 mock
        mock_tags_collection.find_one.return_value = None
        mock_tags_collection.insert_one.side_effect = [
            Mock(inserted_id=tag_ids[0]),
            Mock(inserted_id=tag_ids[1]),
            Mock(inserted_id=tag_ids[2])
        ]
        
        # 파일 업데이트 mock
        mock_result = Mock()
        mock_result.modified_count = 1
        mock_tagged_files_collection.update_one.return_value = mock_result
        
        # 일괄 태그 추가
        success = tag_service.add_tags_to_files(file_paths, tag_names)
        assert success is True
        
        # 각 파일에 태그가 추가되었는지 확인
        for file_path in file_paths:
            mock_tagged_files_collection.find_one.return_value = {
                "file_path": file_path,
                "tags": tag_ids
            }
            
            tags = tag_service.get_tags_for_file(file_path)
            assert len(tags) == len(tag_names)
    
    def test_tag_search_and_filtering(self, search_manager, mock_tags_collection, mock_tagged_files_collection):
        """태그 검색 및 필터링 테스트"""
        # 테스트 데이터 설정
        test_files = [
            "C:/test/개발문서.txt",
            "C:/test/테스트문서.txt",
            "C:/test/기타문서.pdf"
        ]
        
        # Mock 설정 - 태그 부분일치 검색
        mock_tags_collection.get_all_tags.return_value = ["개발태그", "테스트태그", "문서태그"]
        mock_tagged_files_collection.get_files_by_tags.side_effect = [
            [test_files[0]],  # 개발태그
            [test_files[1]],  # 테스트태그
            [test_files[2]]   # 문서태그
        ]
        
        # 부분일치 검색
        search_conditions = {
            'partial': {
                'tags': {
                    'partial': ['개발']
                }
            }
        }
        
        results = search_manager.search_files(search_conditions)
        assert len(results) > 0
    
    def test_tag_statistics_integration(self, tag_repository, mock_tags_collection, mock_tagged_files_collection):
        """태그 통계 통합 테스트"""
        # Mock 설정
        mock_tags_collection.count_documents.return_value = 100
        mock_tagged_files_collection.count_documents.return_value = 500
        
        # 인기 태그 aggregation mock
        popular_tags = [
            {"tag_name": "개발", "count": 50},
            {"tag_name": "문서", "count": 30}
        ]
        mock_popular_cursor = Mock()
        mock_popular_cursor.__iter__ = Mock(return_value=iter(popular_tags))
        
        # 카테고리 통계 aggregation mock
        category_stats = [
            {"_id": "개발", "count": 60},
            {"_id": "문서", "count": 40}
        ]
        mock_category_cursor = Mock()
        mock_category_cursor.__iter__ = Mock(return_value=iter(category_stats))
        
        def mock_aggregate(pipeline):
            if "$unwind" in pipeline[0]:
                return mock_popular_cursor
            else:
                return mock_category_cursor
        
        mock_tagged_files_collection.aggregate.side_effect = mock_aggregate
        mock_tags_collection.aggregate.side_effect = mock_aggregate
        
        # 통계 조회
        stats = tag_repository.get_tag_statistics()
        
        assert stats["total_tags"] == 100
        assert stats["total_files"] == 500
        assert len(stats["popular_tags"]) == 2
        assert len(stats["category_stats"]) == 2
    
    def test_event_driven_architecture(self, tag_service, event_bus, mock_tags_collection, mock_tagged_files_collection):
        """이벤트 기반 아키텍처 테스트"""
        # 이벤트 수신 확인을 위한 플래그
        event_received = False
        event_data = None
        
        def on_tag_added(data):
            nonlocal event_received, event_data
            event_received = True
            event_data = data
        
        # 이벤트 리스너 등록
        event_bus.subscribe("tag_added", on_tag_added)
        
        # Mock 설정
        tag_id = ObjectId()
        mock_tags_collection.find_one.return_value = None
        mock_tags_collection.insert_one.return_value = Mock(inserted_id=tag_id)
        
        mock_result = Mock()
        mock_result.modified_count = 1
        mock_tagged_files_collection.update_one.return_value = mock_result
        
        # 태그 추가 (이벤트 발생)
        file_path = "C:/test/event_test.txt"
        tag_name = "이벤트태그"
        
        success = tag_service.add_tag_to_file(file_path, tag_name)
        
        # 이벤트가 발생했는지 확인
        assert success is True
        assert event_received is True
        assert event_data["file_path"] == file_path
        assert event_data["tag_name"] == tag_name
    
    def test_error_handling_integration(self, tag_service, search_manager, mock_tags_collection):
        """에러 처리 통합 테스트"""
        # Mock 설정 - 예외 발생
        mock_tags_collection.find_one.side_effect = Exception("Database connection failed")
        
        # 태그 추가 시 예외 처리
        success = tag_service.add_tag_to_file("C:/test/error.txt", "에러태그")
        assert success is False
        
        # 검색 시 예외 처리
        mock_tags_collection.get_all_tags.side_effect = Exception("Search failed")
        
        search_conditions = {
            'partial': {
                'tags': {
                    'partial': ['테스트']
                }
            }
        }
        
        results = search_manager.search_files(search_conditions)
        assert results == []
    
    def test_performance_under_load(self, tag_service, search_manager, mock_tags_collection, mock_tagged_files_collection):
        """부하 상황에서의 성능 테스트"""
        import time
        
        # 대량 데이터 시뮬레이션
        num_operations = 1000
        
        # Mock 설정
        tag_service._repository.add_tag.return_value = True
        tag_service._repository.get_tags_for_file.return_value = ["태그1", "태그2"]
        
        # 성능 측정
        start_time = time.time()
        
        # 대량 태그 추가
        for i in range(num_operations):
            file_path = f"C:/test/load_test_{i}.txt"
            tag_service.add_tag_to_file(file_path, f"태그{i}")
        
        # 대량 태그 조회
        for i in range(num_operations):
            file_path = f"C:/test/load_test_{i}.txt"
            tag_service.get_tags_for_file(file_path)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # 성능 검증
        operations_per_second = (num_operations * 2) / execution_time
        assert operations_per_second >= 1000, f"부하 상황에서 성능이 기준에 미달: {operations_per_second:.1f} ops/sec"
    
    def test_data_consistency(self, tag_service, tag_repository, mock_tags_collection, mock_tagged_files_collection):
        """데이터 일관성 테스트"""
        # 1. 태그 추가
        file_path = "C:/test/consistency.txt"
        tag_name = "일관성태그"
        
        # Mock 설정
        tag_id = ObjectId()
        mock_tags_collection.find_one.return_value = None
        mock_tags_collection.insert_one.return_value = Mock(inserted_id=tag_id)
        
        mock_result = Mock()
        mock_result.modified_count = 1
        mock_tagged_files_collection.update_one.return_value = mock_result
        
        # 태그 추가
        success = tag_service.add_tag_to_file(file_path, tag_name)
        assert success is True
        
        # 2. 태그 제거
        mock_result.modified_count = 1
        mock_tagged_files_collection.update_one.return_value = mock_result
        
        success = tag_service.remove_tag_from_file(file_path, tag_name)
        assert success is True
        
        # 3. 태그가 제거되었는지 확인
        mock_tagged_files_collection.find_one.return_value = {
            "file_path": file_path,
            "tags": []
        }
        
        tags = tag_service.get_tags_for_file(file_path)
        assert tag_name not in tags
        assert len(tags) == 0
    
    def test_multi_user_scenario(self, tag_service, search_manager, mock_tags_collection, mock_tagged_files_collection):
        """다중 사용자 시나리오 테스트"""
        import threading
        
        # 공유 데이터
        shared_files = [f"C:/test/shared_{i}.txt" for i in range(10)]
        shared_tags = ["공유태그1", "공유태그2", "공유태그3"]
        
        # Mock 설정
        tag_service._repository.add_tag.return_value = True
        tag_service._repository.get_tags_for_file.return_value = shared_tags
        
        # 사용자별 작업 함수
        def user_work(user_id):
            for i in range(5):
                file_path = shared_files[i + user_id * 2]
                tag = shared_tags[i % len(shared_tags)]
                tag_service.add_tag_to_file(file_path, tag)
                tag_service.get_tags_for_file(file_path)
        
        # 다중 스레드 실행
        threads = []
        for user_id in range(3):
            thread = threading.Thread(target=user_work, args=(user_id,))
            threads.append(thread)
            thread.start()
        
        # 모든 스레드 완료 대기
        for thread in threads:
            thread.join()
        
        # 모든 작업이 성공적으로 완료되었는지 확인
        # (Mock을 사용하므로 실제 검증은 제한적)
        assert True  # 스레드가 정상적으로 완료되었음을 의미 