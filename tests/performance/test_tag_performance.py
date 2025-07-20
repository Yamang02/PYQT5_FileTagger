import pytest
import time
import random
from typing import List, Dict
from unittest.mock import Mock
from bson import ObjectId
from datetime import datetime
from core.repositories.tag_repository import TagRepository
from core.services.tag_service import TagService
from core.events import EventBus


class TestTagPerformance:
    """태그 시스템 성능 테스트"""
    
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
    def mock_event_bus(self):
        """Mock EventBus"""
        return Mock(spec=EventBus)
    
    @pytest.fixture
    def mock_tag_repository(self):
        """Mock TagRepository"""
        return Mock()
    
    @pytest.fixture
    def tag_service(self, mock_tag_repository, mock_event_bus):
        """TagService 인스턴스"""
        return TagService(mock_tag_repository, mock_event_bus)
    
    def generate_test_data(self, num_files: int, num_tags: int, tags_per_file: int) -> Dict:
        """테스트 데이터 생성"""
        # 태그 생성
        tags = [f"태그{i}" for i in range(num_tags)]
        
        # 파일 생성
        files = [f"C:/test/file{i}.txt" for i in range(num_files)]
        
        # 파일별 태그 할당
        file_tags = {}
        for file_path in files:
            file_tags[file_path] = random.sample(tags, min(tags_per_file, len(tags)))
        
        return {
            "tags": tags,
            "files": files,
            "file_tags": file_tags
        }
    
    def test_bulk_tag_addition_performance(self, tag_service, mock_event_bus):
        """대량 태그 추가 성능 테스트"""
        # 테스트 데이터 생성
        test_data = self.generate_test_data(num_files=1000, num_tags=100, tags_per_file=5)
        
        # Mock 설정
        tag_service._repository.add_tag.return_value = True
        
        # 성능 측정
        start_time = time.time()
        
        # 모든 파일에 태그 추가
        for file_path in test_data["files"]:
            for tag in test_data["file_tags"][file_path]:
                tag_service.add_tag_to_file(file_path, tag)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # 성능 검증
        total_operations = len(test_data["files"]) * 5  # 파일 수 × 태그 수
        operations_per_second = total_operations / execution_time
        
        print(f"[PERFORMANCE] 대량 태그 추가:")
        print(f"  - 총 작업 수: {total_operations}")
        print(f"  - 실행 시간: {execution_time:.3f}초")
        print(f"  - 초당 작업 수: {operations_per_second:.1f}")
        
        # 성능 기준: 초당 1000개 작업 이상
        assert operations_per_second >= 1000, f"성능이 기준에 미달: {operations_per_second:.1f} ops/sec"
    
    def test_tag_search_performance(self, tag_repository, mock_tags_collection, mock_tagged_files_collection):
        """태그 검색 성능 테스트"""
        # 대용량 테스트 데이터 생성
        num_files = 10000
        num_tags = 500
        
        # Mock 설정 - 대량 데이터 시뮬레이션
        mock_tags_collection.count_documents.return_value = num_tags
        
        # 태그 ID 목록 생성
        tag_ids = [ObjectId() for _ in range(num_tags)]
        
        # 파일 데이터 생성
        file_docs = []
        for i in range(num_files):
            file_tags = random.sample(tag_ids, random.randint(1, 10))
            file_docs.append({
                "file_path": f"C:/test/file{i}.txt",
                "tags": file_tags,
                "tag_count": len(file_tags)
            })
        
        # Mock cursor 설정
        mock_cursor = Mock()
        mock_cursor.__iter__ = Mock(return_value=iter(file_docs))
        mock_tagged_files_collection.find.return_value = mock_cursor
        
        # 성능 측정
        start_time = time.time()
        
        # 태그로 파일 검색
        result = tag_repository.get_files_by_tags(["태그1", "태그2", "태그3"])
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"[PERFORMANCE] 태그 검색:")
        print(f"  - 총 파일 수: {num_files}")
        print(f"  - 총 태그 수: {num_tags}")
        print(f"  - 검색 결과: {len(result)}개 파일")
        print(f"  - 실행 시간: {execution_time:.3f}초")
        
        # 성능 기준: 1초 이내
        assert execution_time < 1.0, f"검색 시간이 너무 김: {execution_time:.3f}초"
    
    def test_text_search_performance(self, tag_repository, mock_tags_collection):
        """텍스트 검색 성능 테스트"""
        # 대량 태그 데이터 생성
        num_tags = 10000
        tag_docs = []
        
        for i in range(num_tags):
            tag_docs.append({
                "name": f"태그{i}",
                "score": random.uniform(0.1, 2.0)
            })
        
        # Mock 설정
        mock_cursor = Mock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.__iter__ = Mock(return_value=iter(tag_docs[:50]))  # 상위 50개만 반환
        mock_tags_collection.find.return_value = mock_cursor
        
        # 성능 측정
        start_time = time.time()
        
        # 텍스트 검색 실행
        result = tag_repository.search_tags_by_text("태그", limit=50)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"[PERFORMANCE] 텍스트 검색:")
        print(f"  - 총 태그 수: {num_tags}")
        print(f"  - 검색 결과: {len(result)}개 태그")
        print(f"  - 실행 시간: {execution_time:.3f}초")
        
        # 성능 기준: 0.5초 이내
        assert execution_time < 0.5, f"텍스트 검색 시간이 너무 김: {execution_time:.3f}초"
    
    def test_statistics_performance(self, tag_repository, mock_tags_collection, mock_tagged_files_collection):
        """통계 조회 성능 테스트"""
        # 대용량 데이터 설정
        num_tags = 5000
        num_files = 50000
        
        # Mock 설정
        mock_tags_collection.count_documents.return_value = num_tags
        mock_tagged_files_collection.count_documents.return_value = num_files
        
        # 인기 태그 aggregation mock
        popular_tags = [{"tag_name": f"태그{i}", "count": random.randint(1, 100)} for i in range(10)]
        mock_popular_cursor = Mock()
        mock_popular_cursor.__iter__ = Mock(return_value=iter(popular_tags))
        
        # 카테고리 통계 aggregation mock
        category_stats = [{"_id": f"카테고리{i}", "count": random.randint(10, 500)} for i in range(5)]
        mock_category_cursor = Mock()
        mock_category_cursor.__iter__ = Mock(return_value=iter(category_stats))
        
        def mock_aggregate(pipeline):
            if "$unwind" in pipeline[0]:
                return mock_popular_cursor
            else:
                return mock_category_cursor
        
        mock_tagged_files_collection.aggregate.side_effect = mock_aggregate
        mock_tags_collection.aggregate.side_effect = mock_aggregate
        
        # 성능 측정
        start_time = time.time()
        
        # 통계 조회
        result = tag_repository.get_tag_statistics()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"[PERFORMANCE] 통계 조회:")
        print(f"  - 총 태그 수: {num_tags}")
        print(f"  - 총 파일 수: {num_files}")
        print(f"  - 실행 시간: {execution_time:.3f}초")
        
        # 성능 기준: 2초 이내
        assert execution_time < 2.0, f"통계 조회 시간이 너무 김: {execution_time:.3f}초"
    
    def test_cache_performance(self, tag_service, mock_event_bus):
        """캐시 성능 테스트"""
        # 테스트 데이터 생성
        test_data = self.generate_test_data(num_files=100, num_tags=50, tags_per_file=3)
        
        # Mock 설정
        tag_service._repository.get_tags_for_file.return_value = ["태그1", "태그2", "태그3"]
        
        # 캐시 미스 시 성능 측정
        start_time = time.time()
        
        for file_path in test_data["files"]:
            tag_service.get_tags_for_file(file_path)
        
        cache_miss_time = time.time() - start_time
        
        # 캐시 히트 시 성능 측정
        start_time = time.time()
        
        for file_path in test_data["files"]:
            tag_service.get_tags_for_file(file_path)
        
        cache_hit_time = time.time() - start_time
        
        print(f"[PERFORMANCE] 캐시 성능:")
        print(f"  - 캐시 미스 시간: {cache_miss_time:.3f}초")
        print(f"  - 캐시 히트 시간: {cache_hit_time:.3f}초")
        
        if cache_hit_time > 0:
            performance_improvement = cache_miss_time / cache_hit_time
            print(f"  - 성능 향상: {performance_improvement:.1f}배")
        else:
            print(f"  - 성능 향상: 무한대 (캐시 히트가 매우 빠름)")
        
        # 캐시 히트가 미스보다 최소 2배 빠르거나, 캐시 히트가 거의 즉시 완료되어야 함
        assert cache_hit_time < cache_miss_time / 2 or cache_hit_time < 0.001, "캐시 성능 향상이 부족함"
    
    def test_concurrent_operations_performance(self, tag_service, mock_event_bus):
        """동시 작업 성능 테스트"""
        import threading
        
        # 테스트 데이터
        num_threads = 10
        operations_per_thread = 100
        
        # Mock 설정
        tag_service._repository.add_tag.return_value = True
        tag_service._repository.get_tags_for_file.return_value = ["태그1", "태그2"]
        
        # 스레드별 작업 함수
        def worker_operations(thread_id):
            for i in range(operations_per_thread):
                file_path = f"C:/test/thread{thread_id}_file{i}.txt"
                tag_service.add_tag_to_file(file_path, f"태그{i}")
                tag_service.get_tags_for_file(file_path)
        
        # 성능 측정
        start_time = time.time()
        
        # 스레드 생성 및 실행
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=worker_operations, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 모든 스레드 완료 대기
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        total_operations = num_threads * operations_per_thread * 2  # 추가 + 조회
        operations_per_second = total_operations / execution_time
        
        print(f"[PERFORMANCE] 동시 작업:")
        print(f"  - 스레드 수: {num_threads}")
        print(f"  - 스레드당 작업 수: {operations_per_thread}")
        print(f"  - 총 작업 수: {total_operations}")
        print(f"  - 실행 시간: {execution_time:.3f}초")
        print(f"  - 초당 작업 수: {operations_per_second:.1f}")
        
        # 성능 기준: 초당 500개 작업 이상
        assert operations_per_second >= 500, f"동시 작업 성능이 기준에 미달: {operations_per_second:.1f} ops/sec" 