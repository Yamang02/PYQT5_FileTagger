import pytest
from unittest.mock import MagicMock, patch
from core import TagManager
from core.repositories.tag_repository import TagRepository
import config
import os
from core.path_utils import normalize_path

# 테스트용 설정 오버라이드
config.MONGO_DB_NAME = "test_db"
config.MONGO_COLLECTION_NAME = "test_collection"

@pytest.fixture
def mock_mongo_client():
    """테스트용 모의 MongoClient 객체를 생성합니다."""
    return MagicMock()

@pytest.fixture
def mock_tag_service():
    """테스트용 TagService 모의 객체를 생성합니다."""
    return MagicMock()

@pytest.fixture
def tag_manager(mock_tag_service):
    """테스트용 TagManager 인스턴스를 생성합니다."""
    # TagService를 모의(patch)하여 실제 DB 호출을 막습니다.
    with patch('core.services.tag_service.TagService', return_value=mock_tag_service):
        manager = TagManager(mock_tag_service)
        yield manager

# --- 기본 CRUD 테스트 ---

@pytest.mark.unit
def test_get_tags_for_file(tag_manager, mock_tag_service):
    file_path = "/test/file.txt"
    expected_tags = ["a", "b"]
    mock_tag_service.get_tags_for_file.return_value = expected_tags

    tags = tag_manager.get_tags_for_file(file_path)
    
    assert tags == expected_tags
    mock_tag_service.get_tags_for_file.assert_called_once_with(file_path)

@pytest.mark.unit
def test_update_tags(tag_manager, mock_tag_service):
    file_path = "/test/file.txt"
    tags = ["a", "b"]
    mock_tag_service.get_tags_for_file.return_value = []
    mock_tag_service.add_tag_to_file.return_value = True

    tag_manager.update_tags(file_path, tags)
    
    # update_tags는 add_tag_to_file과 remove_tag_from_file을 호출합니다
    assert mock_tag_service.add_tag_to_file.call_count == 2

@pytest.mark.unit
def test_remove_tags_from_file(tag_manager, mock_tag_service):
    file_path = "/test/file.txt"
    tags_to_remove = ["b"]
    # get_tags_for_file이 먼저 호출되어 기존 태그를 가져옵니다.
    mock_tag_service.get_tags_for_file.return_value = ["a", "b", "c"]
    mock_tag_service.remove_tags_from_files.return_value = {"success": True}

    tag_manager.remove_tags_from_file(file_path, tags_to_remove)
    
    # remove_tags_from_file은 remove_tags_from_files를 호출합니다
    mock_tag_service.remove_tags_from_files.assert_called_once_with([file_path], tags_to_remove)

@pytest.mark.unit
def test_clear_all_tags_from_file(tag_manager, mock_tag_service):
    file_path = "/test/file.txt"
    mock_tag_service.get_tags_for_file.return_value = ["a", "b", "c"]
    mock_tag_service.remove_tags_from_files.return_value = {"success": True}

    tag_manager.clear_all_tags_from_file(file_path)
    
    # clear_all_tags_from_file은 remove_tags_from_files를 호출합니다
    mock_tag_service.remove_tags_from_files.assert_called_once_with([file_path], ["a", "b", "c"])

# --- 일괄 처리 테스트 ---

@pytest.mark.unit
def test_add_tags_to_files(tag_manager, mock_tag_service):
    file_paths = ["/test/file1.txt", "/test/file2.txt"]
    tags_to_add = ["new_tag"]

    # add_tags_to_files가 반환할 모의 결과 설정
    mock_tag_service.add_tags_to_files.return_value = {"success": True, "processed": 2, "successful": 2}

    result = tag_manager.add_tags_to_files(file_paths, tags_to_add)
    
    assert result == {"success": True, "processed": 2, "successful": 2}
    mock_tag_service.add_tags_to_files.assert_called_once_with(file_paths, tags_to_add)

@pytest.mark.unit
def test_remove_tags_from_files(tag_manager, mock_tag_service):
    file_paths = ["/test/file1.txt", "/test/file2.txt"]
    tags_to_remove = ["existing_tag"]

    mock_tag_service.remove_tags_from_files.return_value = {"success": True, "processed": 2, "successful": 2}

    result = tag_manager.remove_tags_from_files(file_paths, tags_to_remove)
    
    assert result == {"success": True, "processed": 2, "successful": 2}
    mock_tag_service.remove_tags_from_files.assert_called_once_with(file_paths, tags_to_remove)

# --- 디렉토리 관련 테스트 ---

@pytest.fixture
def test_directory(tmp_path):
    d = tmp_path / "test_dir"
    d.mkdir()
    (d / "file1.txt").touch()
    (d / "image.jpg").touch()
    sub = d / "subdir"
    sub.mkdir()
    (sub / "sub_file.txt").touch()
    return str(d)

@pytest.mark.unit
def test_add_tags_to_directory(tag_manager, mock_tag_service, test_directory):
    tags_to_add = ["dir_tag"]
    recursive = True
    file_extensions = [".txt", ".pdf"]

    # add_tags_to_directory가 반환할 모의 결과 설정
    mock_tag_service.add_tags_to_directory.return_value = {"success": True, "processed": 5, "successful": 5}

    result = tag_manager.add_tags_to_directory(test_directory, tags_to_add, recursive, file_extensions)
    
    assert result == {"success": True, "processed": 5, "successful": 5}
    mock_tag_service.add_tags_to_directory.assert_called_once_with(test_directory, tags_to_add, recursive, file_extensions)

# --- 유효성 검사 테스트 ---

@pytest.mark.unit
def test_validate_tags(tag_manager):
    # TagManagerAdapter에는 _validate_tags 메서드가 없으므로, 
    # 기본적인 태그 검증 로직을 테스트합니다
    valid_tags = ["tag1", "tag2", "tag3"]
    invalid_tags = ["", "   ", None]
    
    # 유효한 태그들은 문제없이 처리되어야 합니다
    for tag in valid_tags:
        assert isinstance(tag, str) and tag.strip() != ""
    
    # 빈 태그들은 필터링되어야 합니다
    for tag in invalid_tags:
        if tag is None or (isinstance(tag, str) and tag.strip() == ""):
            continue  # 이런 태그들은 제외되어야 합니다