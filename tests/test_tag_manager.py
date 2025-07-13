import pytest
from unittest.mock import MagicMock, patch
from core.tag_manager import TagManager, TagManagerError
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
def tag_manager(mock_mongo_client):
    """테스트용 TagManager 인스턴스를 생성합니다."""
    # TagRepository를 모의(patch)하여 실제 DB 호출을 막습니다.
    with patch('core.tag_manager.TagRepository') as MockRepository:
        mock_repository_instance = MockRepository.return_value
        manager = TagManager(mock_mongo_client)
        manager.repository = mock_repository_instance
        yield manager

# --- 기본 CRUD 테스트 ---

@pytest.mark.unit
def test_get_tags_for_file(tag_manager):
    file_path = "/test/file.txt"
    expected_tags = ["a", "b"]
    tag_manager.repository.get_tags_for_file.return_value = expected_tags

    tags = tag_manager.get_tags_for_file(file_path)

    assert tags == expected_tags
    tag_manager.repository.get_tags_for_file.assert_called_once_with(file_path)

@pytest.mark.unit
def test_update_tags(tag_manager):
    file_path = "/test/file.txt"
    tags = ["a", "b"]
    tag_manager.repository.update_tags.return_value = True

    result = tag_manager.update_tags(file_path, tags)

    assert result is True
    tag_manager.repository.update_tags.assert_called_once_with(file_path, tags)

@pytest.mark.unit
def test_remove_tags_from_file(tag_manager):
    file_path = "/test/file.txt"
    tags_to_remove = ["b"]
    # get_tags_for_file이 먼저 호출되어 기존 태그를 가져옵니다.
    tag_manager.repository.get_tags_for_file.return_value = ["a", "b", "c"]
    tag_manager.repository.update_tags.return_value = True

    result = tag_manager.remove_tags_from_file(file_path, tags_to_remove)

    assert result is True
    tag_manager.repository.get_tags_for_file.assert_called_once_with(file_path)
    # 최종적으로 update_tags가 호출되어 태그를 업데이트합니다.
    tag_manager.repository.update_tags.assert_called_once_with(file_path, ["a", "c"])

@pytest.mark.unit
def test_clear_all_tags_from_file(tag_manager):
    file_path = "/test/file.txt"
    tag_manager.repository.update_tags.return_value = True

    result = tag_manager.clear_all_tags_from_file(file_path)

    assert result is True
    tag_manager.repository.update_tags.assert_called_once_with(file_path, [])

# --- 일괄 처리 테스트 ---

@pytest.mark.unit
def test_add_tags_to_files(tag_manager):
    file_paths = ["/test/file1.txt", "/test/file2.txt"]
    tags_to_add = ["new_tag"]
    
    # find_files가 반환할 모의 데이터 설정
    tag_manager.repository.find_files.return_value = {
        normalize_path("/test/file1.txt"): ["existing_tag"],
        normalize_path("/test/file2.txt"): []
    }
    # bulk_update_tags가 반환할 모의 결과 설정
    tag_manager.repository.bulk_update_tags.return_value = {"success": True, "modified": 2, "upserted": 0}

    result = tag_manager.add_tags_to_files(file_paths, tags_to_add)

    assert result["success"] is True
    assert result["processed"] == 2
    tag_manager.repository.find_files.assert_called_once_with(file_paths)
    # bulk_update_tags가 올바른 인자와 함께 호출되었는지 확인
    assert tag_manager.repository.bulk_update_tags.call_count == 1

@pytest.mark.unit
def test_remove_tags_from_files(tag_manager):
    file_paths = ["/test/file1.txt", "/test/file2.txt"]
    tags_to_remove = ["existing_tag"]

    tag_manager.repository.find_files.return_value = {
        normalize_path("/test/file1.txt"): ["existing_tag", "other_tag"],
        normalize_path("/test/file2.txt"): ["existing_tag"]
    }
    tag_manager.repository.bulk_update_tags.return_value = {"success": True, "modified": 2, "upserted": 0}

    result = tag_manager.remove_tags_from_files(file_paths, tags_to_remove)

    assert result["success"] is True
    assert result["processed"] == 2
    tag_manager.repository.find_files.assert_called_once_with(file_paths)
    assert tag_manager.repository.bulk_update_tags.call_count == 1

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
@patch('core.tag_manager.TagManager._get_files_in_directory')
def test_add_tags_to_directory(mock_get_files, tag_manager, test_directory):
    # _get_files_in_directory가 반환할 파일 목록을 모의 설정
    mock_get_files.return_value = [os.path.join(test_directory, "file1.txt")]
    tags_to_add = ["dir_tag"]

    # add_tags_to_files는 내부적으로 호출되므로, 이 메서드도 모의 설정
    with patch.object(tag_manager, 'add_tags_to_files') as mock_add_tags:
        mock_add_tags.return_value = {"success": True, "processed": 1}
        result = tag_manager.add_tags_to_directory(test_directory, tags_to_add)

        assert result["success"] is True
        mock_get_files.assert_called_once_with(test_directory, False, None)
        mock_add_tags.assert_called_once_with([os.path.join(test_directory, "file1.txt")], tags_to_add)

# --- 유효성 검사 테스트 ---

@pytest.mark.unit
def test_validate_tags(tag_manager):
    assert tag_manager._validate_tags(["a", "b"]) is True
    assert tag_manager._validate_tags(["a", ""]) is False # 빈 태그
    assert tag_manager._validate_tags(["a", "b" * 60]) is False # 너무 긴 태그
    assert tag_manager._validate_tags(["a", "<script>"]) is False # 특수 문자
    assert tag_manager._validate_tags("not a list") is False # 리스트가 아님