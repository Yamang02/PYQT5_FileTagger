import pytest
from unittest.mock import Mock, MagicMock
from pymongo import MongoClient
from bson import ObjectId
from core.repositories.tag_repository import TagRepository


class TestTagRepository:
    """TagRepository 클래스 테스트"""
    
    @pytest.fixture
    def mock_mongo_client(self):
        """Mock MongoDB 클라이언트"""
        mock_client = Mock(spec=MongoClient)
        mock_db = Mock()
        mock_tags_collection = Mock()
        mock_tagged_files_collection = Mock()
        
        mock_client.filetagger_db = mock_db
        mock_db.tags = mock_tags_collection
        mock_db.tagged_files = mock_tagged_files_collection
        
        return mock_client, mock_tags_collection, mock_tagged_files_collection
    
    @pytest.fixture
    def tag_repository(self, mock_mongo_client):
        """TagRepository 인스턴스"""
        mock_client, _, _ = mock_mongo_client
        return TagRepository(mock_client)
    
    def test_init_creates_indexes(self, mock_mongo_client):
        """초기화 시 인덱스 생성"""
        mock_client, mock_tags, mock_tagged_files = mock_mongo_client
        
        TagRepository(mock_client)
        
        # 인덱스 생성 호출 확인
        mock_tags.create_index.assert_called()
        mock_tagged_files.create_index.assert_called()
    
    def test_add_tag_success(self, tag_repository, mock_mongo_client):
        """태그 추가 성공"""
        _, mock_tags, mock_tagged_files = mock_mongo_client
        
        # Mock 설정
        mock_tags.find_one.return_value = None  # 태그가 존재하지 않음
        mock_tags.insert_one.return_value.inserted_id = ObjectId()
        mock_tagged_files.update_one.return_value.modified_count = 1
        
        result = tag_repository.add_tag("C:/test/file.txt", "테스트태그")
        
        assert result is True
        mock_tagged_files.update_one.assert_called_once()
    
    def test_add_tag_existing_tag(self, tag_repository, mock_mongo_client):
        """기존 태그 추가"""
        _, mock_tags, mock_tagged_files = mock_mongo_client
        
        # Mock 설정 - 기존 태그 존재
        existing_tag_id = ObjectId()
        mock_tags.find_one.return_value = {"_id": existing_tag_id}
        mock_tagged_files.update_one.return_value.modified_count = 1
        
        result = tag_repository.add_tag("C:/test/file.txt", "기존태그")
        
        assert result is True
        mock_tags.insert_one.assert_not_called()  # 새 태그 생성하지 않음
    
    def test_add_tag_invalid_name(self, tag_repository):
        """유효하지 않은 태그 이름"""
        result = tag_repository.add_tag("C:/test/file.txt", "")
        assert result is False
    
    def test_remove_tag_success(self, tag_repository, mock_mongo_client):
        """태그 제거 성공"""
        _, mock_tags, mock_tagged_files = mock_mongo_client
        
        # Mock 설정
        tag_id = ObjectId()
        mock_tags.find_one.return_value = {"_id": tag_id}
        mock_tagged_files.update_one.return_value.modified_count = 1
        
        result = tag_repository.remove_tag("C:/test/file.txt", "테스트태그")
        
        assert result is True
        mock_tagged_files.update_one.assert_called_once()
    
    def test_remove_tag_not_found(self, tag_repository, mock_mongo_client):
        """존재하지 않는 태그 제거"""
        _, mock_tags, _ = mock_mongo_client
        
        # Mock 설정 - 태그가 존재하지 않음
        mock_tags.find_one.return_value = None
        
        result = tag_repository.remove_tag("C:/test/file.txt", "없는태그")
        
        assert result is False
    
    def test_get_tags_for_file(self, tag_repository, mock_mongo_client):
        """파일의 태그 조회"""
        _, mock_tags, mock_tagged_files = mock_mongo_client
        
        # Mock 설정
        tag_ids = [ObjectId(), ObjectId()]
        mock_tagged_files.find_one.return_value = {"tags": tag_ids}
        mock_tags.find.return_value = [
            {"name": "태그1"},
            {"name": "태그2"}
        ]
        
        result = tag_repository.get_tags_for_file("C:/test/file.txt")
        
        assert result == ["태그1", "태그2"]
    
    def test_get_tags_for_file_no_tags(self, tag_repository, mock_mongo_client):
        """태그가 없는 파일"""
        _, _, mock_tagged_files = mock_mongo_client
        
        # Mock 설정 - 태그가 없음
        mock_tagged_files.find_one.return_value = {"tags": []}
        
        result = tag_repository.get_tags_for_file("C:/test/file.txt")
        
        assert result == []
    
    def test_get_all_tags(self, tag_repository, mock_mongo_client):
        """모든 태그 조회"""
        _, mock_tags, _ = mock_mongo_client
        
        # Mock 설정
        mock_tags.find.return_value = [
            {"name": "태그1"},
            {"name": "태그2"},
            {"name": "태그3"}
        ]
        
        result = tag_repository.get_all_tags()
        
        assert result == ["태그1", "태그2", "태그3"]
    
    def test_get_files_by_tags(self, tag_repository, mock_mongo_client):
        """태그로 파일 조회"""
        _, mock_tags, mock_tagged_files = mock_mongo_client
        
        # Mock 설정
        tag_id = ObjectId()
        mock_tags.find_one.return_value = {"_id": tag_id}
        mock_tagged_files.find.return_value = [
            {"file_path": "C:/test/file1.txt"},
            {"file_path": "C:/test/file2.txt"}
        ]
        
        result = tag_repository.get_files_by_tags(["테스트태그"])
        
        assert result == ["C:/test/file1.txt", "C:/test/file2.txt"]
    
    def test_get_files_by_tags_empty(self, tag_repository):
        """빈 태그 목록으로 파일 조회"""
        result = tag_repository.get_files_by_tags([])
        assert result == []
    
    def test_delete_file_entry(self, tag_repository, mock_mongo_client):
        """파일 태그 정보 삭제"""
        _, _, mock_tagged_files = mock_mongo_client
        
        # Mock 설정
        mock_tagged_files.delete_one.return_value.deleted_count = 1
        
        result = tag_repository.delete_file_entry("C:/test/file.txt")
        
        assert result is True
    
    def test_find_files(self, tag_repository, mock_mongo_client):
        """여러 파일의 태그 정보 조회"""
        _, mock_tags, mock_tagged_files = mock_mongo_client
        
        # Mock 설정
        tag_ids = [ObjectId()]
        mock_tagged_files.find.return_value = [
            {"file_path": "C:/test/file1.txt", "tags": tag_ids},
            {"file_path": "C:/test/file2.txt", "tags": []}
        ]
        mock_tags.find.return_value = [{"name": "테스트태그"}]
        
        result = tag_repository.find_files(["C:/test/file1.txt", "C:/test/file2.txt"])
        
        expected = {
            "C:/test/file1.txt": ["테스트태그"],
            "C:/test/file2.txt": []
        }
        assert result == expected
    
    def test_bulk_update_tags(self, tag_repository, mock_mongo_client):
        """일괄 태그 업데이트"""
        _, _, mock_tagged_files = mock_mongo_client
        
        # Mock 설정
        mock_result = Mock()
        mock_result.modified_count = 5
        mock_result.upserted_count = 2
        mock_tagged_files.bulk_write.return_value = mock_result
        
        operations = [Mock(), Mock()]  # Mock UpdateOne operations
        result = tag_repository.bulk_update_tags(operations)
        
        expected = {"modified": 5, "upserted": 2}
        assert result == expected
    
    def test_bulk_update_tags_empty(self, tag_repository):
        """빈 작업 목록으로 일괄 업데이트"""
        result = tag_repository.bulk_update_tags([])
        expected = {"modified": 0, "upserted": 0}
        assert result == expected 