import pytest
from unittest.mock import Mock, MagicMock
from typing import List, Dict
from core.services.tag_service import TagService
from core.repositories.tag_repository import TagRepository
from core.events import EventBus


class TestTagService:
    """TagService 클래스 테스트"""
    
    @pytest.fixture
    def mock_repository(self):
        """Mock TagRepository"""
        return Mock(spec=TagRepository)
    
    @pytest.fixture
    def mock_event_bus(self):
        """Mock EventBus"""
        return Mock(spec=EventBus)
    
    @pytest.fixture
    def tag_service(self, mock_repository, mock_event_bus):
        """TagService 인스턴스"""
        return TagService(mock_repository, mock_event_bus)
    
    def test_add_tag_to_file_success(self, tag_service, mock_repository, mock_event_bus):
        """태그 추가 성공"""
        # Mock 설정
        mock_repository.add_tag.return_value = True
        
        result = tag_service.add_tag_to_file("C:/test/file.txt", "테스트태그")
        
        assert result is True
        mock_repository.add_tag.assert_called_once_with("C:/test/file.txt", "테스트태그")
        mock_event_bus.publish_tag_added.assert_called_once_with("C:/test/file.txt", "테스트태그")
    
    def test_add_tag_to_file_invalid_tag(self, tag_service, mock_repository):
        """유효하지 않은 태그 추가"""
        result = tag_service.add_tag_to_file("C:/test/file.txt", "")
        assert result is False
        mock_repository.add_tag.assert_not_called()
    
    def test_add_tag_to_file_repository_failure(self, tag_service, mock_repository, mock_event_bus):
        """Repository 실패 시"""
        mock_repository.add_tag.return_value = False
        
        result = tag_service.add_tag_to_file("C:/test/file.txt", "테스트태그")
        
        assert result is False
        mock_event_bus.publish_tag_added.assert_not_called()
    
    def test_remove_tag_from_file_success(self, tag_service, mock_repository, mock_event_bus):
        """태그 제거 성공"""
        # Mock 설정
        mock_repository.remove_tag.return_value = True
        
        result = tag_service.remove_tag_from_file("C:/test/file.txt", "테스트태그")
        
        assert result is True
        mock_repository.remove_tag.assert_called_once_with("C:/test/file.txt", "테스트태그")
        mock_event_bus.publish_tag_removed.assert_called_once_with("C:/test/file.txt", "테스트태그")
    
    def test_remove_tag_from_file_repository_failure(self, tag_service, mock_repository, mock_event_bus):
        """Repository 실패 시"""
        mock_repository.remove_tag.return_value = False
        
        result = tag_service.remove_tag_from_file("C:/test/file.txt", "테스트태그")
        
        assert result is False
        mock_event_bus.publish_tag_removed.assert_not_called()
    
    def test_get_tags_for_file_cache_hit(self, tag_service, mock_repository):
        """캐시에서 태그 조회"""
        # 캐시에 데이터 설정
        tag_service._file_tags_cache["C:/test/file.txt"] = ["태그1", "태그2"]
        
        result = tag_service.get_tags_for_file("C:/test/file.txt")
        
        assert result == ["태그1", "태그2"]
        mock_repository.get_tags_for_file.assert_not_called()
    
    def test_get_tags_for_file_cache_miss(self, tag_service, mock_repository):
        """캐시 미스 시 DB에서 조회"""
        # Mock 설정
        mock_repository.get_tags_for_file.return_value = ["태그1", "태그2"]
        
        result = tag_service.get_tags_for_file("C:/test/file.txt")
        
        assert result == ["태그1", "태그2"]
        mock_repository.get_tags_for_file.assert_called_once_with("C:/test/file.txt")
        # 캐시에 저장되었는지 확인
        assert tag_service._file_tags_cache["C:/test/file.txt"] == ["태그1", "태그2"]
    
    def test_get_all_tags_cache_hit(self, tag_service, mock_repository):
        """캐시에서 모든 태그 조회"""
        # 캐시에 데이터 설정
        tag_service._all_tags_cache = ["태그1", "태그2", "태그3"]
        
        result = tag_service.get_all_tags()
        
        assert result == ["태그1", "태그2", "태그3"]
        mock_repository.get_all_tags.assert_not_called()
    
    def test_get_all_tags_cache_miss(self, tag_service, mock_repository):
        """캐시 미스 시 DB에서 조회"""
        # Mock 설정
        mock_repository.get_all_tags.return_value = ["태그1", "태그2", "태그3"]
        
        result = tag_service.get_all_tags()
        
        assert result == ["태그1", "태그2", "태그3"]
        mock_repository.get_all_tags.assert_called_once()
        # 캐시에 저장되었는지 확인
        assert tag_service._all_tags_cache == ["태그1", "태그2", "태그3"]
    
    def test_get_files_by_tags(self, tag_service, mock_repository):
        """태그로 파일 조회"""
        # Mock 설정
        mock_repository.get_files_by_tags.return_value = ["C:/test/file1.txt", "C:/test/file2.txt"]
        
        result = tag_service.get_files_by_tags(["테스트태그"])
        
        assert result == ["C:/test/file1.txt", "C:/test/file2.txt"]
        mock_repository.get_files_by_tags.assert_called_once_with(["테스트태그"])
    
    def test_delete_file_entry_success(self, tag_service, mock_repository):
        """파일 태그 정보 삭제 성공"""
        # Mock 설정
        mock_repository.delete_file_entry.return_value = True
        
        # 캐시에 데이터 설정
        tag_service._file_tags_cache["C:/test/file.txt"] = ["태그1", "태그2"]
        
        result = tag_service.delete_file_entry("C:/test/file.txt")
        
        assert result is True
        mock_repository.delete_file_entry.assert_called_once_with("C:/test/file.txt")
        # 캐시에서 제거되었는지 확인
        assert "C:/test/file.txt" not in tag_service._file_tags_cache
    
    def test_add_tags_to_files_success(self, tag_service, mock_repository, mock_event_bus):
        """일괄 태그 추가 성공"""
        # Mock 설정
        mock_repository.add_tag.return_value = True
        
        result = tag_service.add_tags_to_files(
            ["C:/test/file1.txt", "C:/test/file2.txt"], 
            ["태그1", "태그2"]
        )
        
        assert result["success"] is True
        assert result["processed"] == 2
        assert result["successful"] == 4  # 2개 파일 × 2개 태그
        
        # 각 파일-태그 조합에 대해 호출되었는지 확인
        assert mock_repository.add_tag.call_count == 4
        assert mock_event_bus.publish_tag_added.call_count == 4
    
    def test_add_tags_to_files_invalid_input(self, tag_service):
        """잘못된 입력으로 일괄 태그 추가"""
        result = tag_service.add_tags_to_files([], ["태그1"])
        assert result["success"] is False
        assert "잘못된 파일 경로 리스트" in result["error"]
    
    def test_add_tags_to_files_no_valid_tags(self, tag_service):
        """유효한 태그가 없는 경우"""
        result = tag_service.add_tags_to_files(["C:/test/file.txt"], ["", "   "])
        assert result["success"] is False
        assert "유효한 태그가 없습니다" in result["error"]
    
    def test_remove_tags_from_files_success(self, tag_service, mock_repository, mock_event_bus):
        """일괄 태그 제거 성공"""
        # Mock 설정
        mock_repository.remove_tag.return_value = True
        
        result = tag_service.remove_tags_from_files(
            ["C:/test/file1.txt", "C:/test/file2.txt"], 
            ["태그1", "태그2"]
        )
        
        assert result["success"] is True
        assert result["processed"] == 2
        assert result["successful"] == 4  # 2개 파일 × 2개 태그
        
        # 각 파일-태그 조합에 대해 호출되었는지 확인
        assert mock_repository.remove_tag.call_count == 4
        assert mock_event_bus.publish_tag_removed.call_count == 4
    
    def test_remove_tags_from_files_invalid_input(self, tag_service):
        """잘못된 입력으로 일괄 태그 제거"""
        result = tag_service.remove_tags_from_files([], ["태그1"])
        assert result["success"] is False
        assert "잘못된 파일 경로 리스트" in result["error"]
    
    def test_add_tags_to_directory_success(self, tag_service, mock_repository, mock_event_bus, tmp_path):
        """디렉토리 일괄 태깅 성공"""
        # 테스트 파일 생성
        test_file1 = tmp_path / "file1.txt"
        test_file1.write_text("test")
        test_file2 = tmp_path / "file2.txt"
        test_file2.write_text("test")
        
        # Mock 설정
        mock_repository.add_tag.return_value = True
        
        result = tag_service.add_tags_to_directory(str(tmp_path), ["태그1", "태그2"])
        
        assert result["success"] is True
        assert result["processed"] == 2
        assert result["successful"] == 4  # 2개 파일 × 2개 태그
    
    def test_add_tags_to_directory_no_files(self, tag_service, tmp_path):
        """조건에 맞는 파일이 없는 경우"""
        result = tag_service.add_tags_to_directory(str(tmp_path), ["태그1"], file_extensions=["pdf"])
        assert result["success"] is True
        assert result["message"] == "조건에 맞는 파일이 없습니다"
        assert result["processed"] == 0
    
    def test_get_files_in_directory(self, tag_service, tmp_path):
        """디렉토리 파일 목록 조회"""
        # 테스트 파일 생성
        test_file1 = tmp_path / "file1.txt"
        test_file1.write_text("test")
        test_file2 = tmp_path / "file2.pdf"
        test_file2.write_text("test")
        
        result = tag_service.get_files_in_directory(str(tmp_path), file_extensions=["txt"])
        
        assert len(result) == 1
        assert result[0].endswith("file1.txt")
    
    def test_clear_cache(self, tag_service):
        """캐시 초기화"""
        # 캐시에 데이터 설정
        tag_service._file_tags_cache["C:/test/file.txt"] = ["태그1"]
        tag_service._all_tags_cache = ["태그1", "태그2"]
        
        tag_service.clear_cache()
        
        assert len(tag_service._file_tags_cache) == 0
        assert tag_service._all_tags_cache is None
    
    def test_path_normalization(self, tag_service, mock_repository):
        """파일 경로 정규화 확인"""
        # Mock 설정
        mock_repository.get_tags_for_file.return_value = ["태그1"]
        
        # Windows 스타일 경로 사용
        result = tag_service.get_tags_for_file("C:\\test\\file.txt")
        
        # 정규화된 경로로 호출되었는지 확인
        mock_repository.get_tags_for_file.assert_called_once_with("C:/test/file.txt")
        assert result == ["태그1"]
    
    def test_tag_normalization(self, tag_service, mock_repository, mock_event_bus):
        """태그 이름 정규화 확인"""
        # Mock 설정
        mock_repository.add_tag.return_value = True
        
        # 공백이 포함된 태그 이름 사용
        result = tag_service.add_tag_to_file("C:/test/file.txt", "  테스트  태그  ")
        
        # 정규화된 태그 이름으로 호출되었는지 확인
        mock_repository.add_tag.assert_called_once_with("C:/test/file.txt", "테스트 태그")
        mock_event_bus.publish_tag_added.assert_called_once_with("C:/test/file.txt", "테스트 태그")
        assert result is True 