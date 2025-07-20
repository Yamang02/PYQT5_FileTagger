import pytest
from unittest.mock import Mock, MagicMock
from bson import ObjectId
from datetime import datetime
from typing import List, Dict, Any
from core.repositories.tag_repository import TagRepository
from models.tag_model import TagMetadata, create_tag


class TestTagRepositoryAdvanced:
    """TagRepository 고급 기능 테스트"""
    
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
    
    def test_search_tags_by_text(self, tag_repository, mock_tags_collection):
        """텍스트 검색으로 태그 찾기"""
        # Mock 설정
        mock_cursor = Mock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.__iter__ = Mock(return_value=iter([
            {"name": "테스트태그", "score": 1.5},
            {"name": "개발태그", "score": 1.2}
        ]))
        
        mock_tags_collection.find.return_value = mock_cursor
        
        result = tag_repository.search_tags_by_text("테스트", limit=10)
        
        assert result == ["테스트태그", "개발태그"]
        mock_tags_collection.find.assert_called_once()
    
    def test_get_recently_tagged_files(self, tag_repository, mock_tagged_files_collection):
        """최근 태깅된 파일 조회"""
        # Mock 설정
        mock_cursor = Mock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.__iter__ = Mock(return_value=iter([
            {"file_path": "C:/test/file1.txt", "updated_at": datetime.utcnow()},
            {"file_path": "C:/test/file2.txt", "updated_at": datetime.utcnow()}
        ]))
        
        mock_tagged_files_collection.find.return_value = mock_cursor
        
        result = tag_repository.get_recently_tagged_files(limit=10)
        
        assert result == ["C:/test/file1.txt", "C:/test/file2.txt"]
        mock_tagged_files_collection.find.assert_called_once()
    
    def test_get_most_tagged_files(self, tag_repository, mock_tagged_files_collection):
        """태그가 가장 많은 파일 조회"""
        # Mock 설정
        mock_cursor = Mock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.__iter__ = Mock(return_value=iter([
            {"file_path": "C:/test/file1.txt", "tag_count": 5},
            {"file_path": "C:/test/file2.txt", "tag_count": 3}
        ]))
        
        mock_tagged_files_collection.find.return_value = mock_cursor
        
        result = tag_repository.get_most_tagged_files(limit=10)
        
        assert result == ["C:/test/file1.txt", "C:/test/file2.txt"]
        mock_tagged_files_collection.find.assert_called_once()
    
    def test_get_tags_by_category(self, tag_repository, mock_tags_collection):
        """카테고리별 태그 조회"""
        # Mock 설정
        mock_cursor = Mock()
        mock_cursor.__iter__ = Mock(return_value=iter([
            {"name": "개발태그"},
            {"name": "테스트태그"}
        ]))
        
        mock_tags_collection.find.return_value = mock_cursor
        
        result = tag_repository.get_tags_by_category("개발")
        
        assert result == ["개발태그", "테스트태그"]
        mock_tags_collection.find.assert_called_once_with({"category": "개발"}, {"name": 1})
    
    def test_get_tag_statistics(self, tag_repository, mock_tags_collection, mock_tagged_files_collection):
        """태그 통계 조회"""
        # Mock 설정
        mock_tags_collection.count_documents.return_value = 100
        mock_tagged_files_collection.count_documents.return_value = 500
        
        # 인기 태그 aggregation mock
        mock_popular_cursor = Mock()
        mock_popular_cursor.__iter__ = Mock(return_value=iter([
            {"tag_name": "개발", "count": 50},
            {"tag_name": "테스트", "count": 30}
        ]))
        
        # 카테고리 통계 aggregation mock
        mock_category_cursor = Mock()
        mock_category_cursor.__iter__ = Mock(return_value=iter([
            {"_id": "개발", "count": 60},
            {"_id": "문서", "count": 40}
        ]))
        
        # aggregation mock 설정 수정
        def mock_aggregate(pipeline):
            if "$unwind" in pipeline[0]:  # 인기 태그 aggregation
                return mock_popular_cursor
            else:  # 카테고리 통계 aggregation
                return mock_category_cursor
        
        mock_tagged_files_collection.aggregate.side_effect = mock_aggregate
        mock_tags_collection.aggregate.side_effect = mock_aggregate
        
        result = tag_repository.get_tag_statistics()
        
        assert result["total_tags"] == 100
        assert result["total_files"] == 500
        assert len(result["popular_tags"]) == 2
        assert len(result["category_stats"]) == 2
    
    def test_update_tag_count(self, tag_repository, mock_tagged_files_collection):
        """태그 개수 업데이트"""
        # Mock 설정
        mock_tagged_files_collection.find_one.return_value = {
            "file_path": "C:/test/file.txt",
            "tags": [ObjectId(), ObjectId(), ObjectId()]
        }
        
        tag_repository._update_tag_count("C:/test/file.txt")
        
        # 태그 개수가 3으로 업데이트되었는지 확인
        mock_tagged_files_collection.update_one.assert_called_once_with(
            {"file_path": "C:/test/file.txt"},
            {"$set": {"tag_count": 3}}
        )
    
    def test_update_timestamp(self, tag_repository, mock_tagged_files_collection):
        """타임스탬프 업데이트"""
        tag_repository._update_timestamp("C:/test/file.txt")
        
        mock_tagged_files_collection.update_one.assert_called_once()
        # updated_at 필드가 설정되었는지 확인
        call_args = mock_tagged_files_collection.update_one.call_args
        assert "$set" in call_args[0][1]
        assert "updated_at" in call_args[0][1]["$set"]
    
    def test_add_tag_with_timestamp_and_count(self, tag_repository, mock_tags_collection, mock_tagged_files_collection):
        """타임스탬프와 태그 개수를 포함한 태그 추가"""
        # Mock 설정
        tag_id = ObjectId()
        mock_tags_collection.find_one.return_value = {"_id": tag_id, "name": "테스트태그"}
        
        mock_result = Mock()
        mock_result.modified_count = 1
        mock_result.upserted_id = None
        mock_tagged_files_collection.update_one.return_value = mock_result
        
        # 태그 개수 업데이트 mock
        mock_tagged_files_collection.find_one.return_value = {
            "file_path": "C:/test/file.txt",
            "tags": [tag_id]
        }
        
        result = tag_repository.add_tag("C:/test/file.txt", "테스트태그")
        
        assert result is True
        # 타임스탬프와 태그 개수 업데이트가 호출되었는지 확인
        assert mock_tagged_files_collection.update_one.call_count >= 2
    
    def test_remove_tag_with_timestamp_and_count(self, tag_repository, mock_tags_collection, mock_tagged_files_collection):
        """타임스탬프와 태그 개수를 포함한 태그 제거"""
        # Mock 설정
        tag_id = ObjectId()
        mock_tags_collection.find_one.return_value = {"_id": tag_id, "name": "테스트태그"}
        
        mock_result = Mock()
        mock_result.modified_count = 1
        mock_tagged_files_collection.update_one.return_value = mock_result
        
        # 태그 개수 업데이트 mock
        mock_tagged_files_collection.find_one.return_value = {
            "file_path": "C:/test/file.txt",
            "tags": []
        }
        
        result = tag_repository.remove_tag("C:/test/file.txt", "테스트태그")
        
        assert result is True
        # 타임스탬프와 태그 개수 업데이트가 호출되었는지 확인
        assert mock_tagged_files_collection.update_one.call_count >= 2
    
    def test_search_tags_by_text_empty_result(self, tag_repository, mock_tags_collection):
        """텍스트 검색 결과가 없는 경우"""
        # Mock 설정
        mock_cursor = Mock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.__iter__ = Mock(return_value=iter([]))
        
        mock_tags_collection.find.return_value = mock_cursor
        
        result = tag_repository.search_tags_by_text("존재하지않는태그")
        
        assert result == []
    
    def test_get_tag_statistics_exception_handling(self, tag_repository, mock_tags_collection):
        """태그 통계 조회 시 예외 처리"""
        # Mock 설정 - 예외 발생
        mock_tags_collection.count_documents.side_effect = Exception("Database error")
        
        result = tag_repository.get_tag_statistics()
        
        # 예외 발생 시 빈 딕셔너리 반환
        assert result == {} 