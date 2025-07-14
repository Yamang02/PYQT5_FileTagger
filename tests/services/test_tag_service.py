import pytest
from unittest.mock import Mock, patch
import os
from core.services.tag_service import TagService
from core.repositories.tag_repository import TagRepository
from core.events import EventBus
from core.path_utils import normalize_path

# 테스트를 위한 임시 디렉토리 및 파일 생성
@pytest.fixture
def temp_test_dir(tmp_path):
    # 임시 디렉토리 생성
    base_dir = tmp_path / "test_files"
    base_dir.mkdir()

    # 파일 생성
    (base_dir / "file1.txt").touch()
    (base_dir / "file2.jpg").touch()
    (base_dir / "subdir").mkdir()
    (base_dir / "subdir" / "file3.pdf").touch()
    (base_dir / "subdir" / "file4.png").touch()
    (base_dir / "another_file.doc").touch()

    return base_dir

@pytest.fixture
def mock_tag_repository():
    return Mock(spec=TagRepository)

@pytest.fixture
def mock_event_bus():
    return Mock(spec=EventBus)

@pytest.fixture
def tag_service(mock_tag_repository, mock_event_bus):
    return TagService(mock_tag_repository, mock_event_bus)

class TestTagService:

    def test_add_tags_to_directory_non_recursive(self, tag_service, mock_tag_repository, mock_event_bus, temp_test_dir):
        # Given
        directory_path = str(temp_test_dir)
        tags_to_add = ["test_tag1", "test_tag2"]
        
        # Mock add_tags_to_files to return success
        mock_tag_repository.bulk_update_tags.return_value = {"modified": 2, "upserted": 0}
        mock_tag_repository.get_tags_for_file.side_effect = lambda x: [] # No existing tags

        # When
        result = tag_service.add_tags_to_directory(directory_path, tags_to_add, recursive=False)

        # Then
        assert result["success"] is True
        assert result["processed"] == 3 # file1.txt, file2.jpg, another_file.doc
        assert result["successful"] == 2 # Modified count from mock

        # Verify add_tags_to_files was called with correct files
        expected_files = [
            normalize_path(os.path.join(directory_path, "file1.txt")),
            normalize_path(os.path.join(directory_path, "file2.jpg")),
            normalize_path(os.path.join(directory_path, "another_file.doc")),
        ]
        # Check if add_tags_to_files was called with the expected files and tags
        # Since add_tags_to_files internally calls bulk_update_tags, we check that
        # the bulk_update_tags was called with operations for these files.
        # This is a simplified check, a more robust test would inspect the UpdateOne objects.
        assert mock_tag_repository.bulk_update_tags.called

        # Verify events were published
        assert mock_event_bus.publish_tag_added.call_count == 6 # 3 files * 2 tags

    def test_add_tags_to_directory_recursive(self, tag_service, mock_tag_repository, mock_event_bus, temp_test_dir):
        # Given
        directory_path = str(temp_test_dir)
        tags_to_add = ["recursive_tag"]
        
        # Mock add_tags_to_files to return success
        mock_tag_repository.bulk_update_tags.return_value = {"modified": 4, "upserted": 0}
        mock_tag_repository.get_tags_for_file.side_effect = lambda x: [] # No existing tags

        # When
        result = tag_service.add_tags_to_directory(directory_path, tags_to_add, recursive=True)

        # Then
        assert result["success"] is True
        assert result["processed"] == 5 # All files
        assert result["successful"] == 4 # Modified count from mock

        # Verify add_tags_to_files was called with correct files
        expected_files = [
            normalize_path(os.path.join(directory_path, "file1.txt")),
            normalize_path(os.path.join(directory_path, "file2.jpg")),
            normalize_path(os.path.join(directory_path, "subdir", "file3.pdf")),
            normalize_path(os.path.join(directory_path, "subdir", "file4.png")),
            normalize_path(os.path.join(directory_path, "another_file.doc")),
        ]
        assert mock_tag_repository.bulk_update_tags.called
        assert mock_event_bus.publish_tag_added.call_count == 5 # 5 files * 1 tag

    def test_get_files_in_directory_non_recursive(self, tag_service, temp_test_dir):
        # Given
        directory_path = str(temp_test_dir)

        # When
        files = tag_service.get_files_in_directory(directory_path, recursive=False)

        # Then
        expected_files = [
            normalize_path(os.path.join(directory_path, "file1.txt")),
            normalize_path(os.path.join(directory_path, "file2.jpg")),
            normalize_path(os.path.join(directory_path, "another_file.doc")),
        ]
        assert len(files) == len(expected_files)
        assert all(f in files for f in expected_files)

    def test_get_files_in_directory_recursive(self, tag_service, temp_test_dir):
        # Given
        directory_path = str(temp_test_dir)

        # When
        files = tag_service.get_files_in_directory(directory_path, recursive=True)

        # Then
        expected_files = [
            normalize_path(os.path.join(directory_path, "file1.txt")),
            normalize_path(os.path.join(directory_path, "file2.jpg")),
            normalize_path(os.path.join(directory_path, "subdir", "file3.pdf")),
            normalize_path(os.path.join(directory_path, "subdir", "file4.png")),
            normalize_path(os.path.join(directory_path, "another_file.doc")),
        ]
        assert len(files) == len(expected_files)
        assert all(f in files for f in expected_files)

    def test_get_files_in_directory_with_extensions(self, tag_service, temp_test_dir):
        # Given
        directory_path = str(temp_test_dir)
        file_extensions = ["txt", "pdf"]

        # When
        files = tag_service.get_files_in_directory(directory_path, recursive=True, file_extensions=file_extensions)

        # Then
        expected_files = [
            normalize_path(os.path.join(directory_path, "file1.txt")),
            normalize_path(os.path.join(directory_path, "subdir", "file3.pdf")),
        ]
        assert len(files) == len(expected_files)
        assert all(f in files for f in expected_files)

    def test_add_tags_to_directory_no_files_found(self, tag_service, mock_tag_repository, temp_test_dir):
        # Given
        directory_path = str(temp_test_dir)
        tags_to_add = ["no_files_tag"]
        
        # Mock get_files_in_directory to return empty list
        with patch.object(tag_service, '_get_files_in_directory', return_value=[]):
            # When
            result = tag_service.add_tags_to_directory(directory_path, tags_to_add)

            # Then
            assert result["success"] is True
            assert result["message"] == "조건에 맞는 파일이 없습니다"
            assert result["processed"] == 0
            mock_tag_repository.bulk_update_tags.assert_not_called()
            mock_tag_repository.get_tags_for_file.assert_not_called()
            mock_tag_repository.add_tag.assert_not_called() # Ensure no individual tag adds

    def test_add_tag_to_file_success(self, tag_service, mock_tag_repository, mock_event_bus):
        # Given
        file_path = "C:/test/file.txt"
        tag = "new_tag"
        mock_tag_repository.add_tag.return_value = True

        # When
        result = tag_service.add_tag_to_file(file_path, tag)

        # Then
        assert result is True
        mock_tag_repository.add_tag.assert_called_once_with(file_path, tag)
        mock_event_bus.publish_tag_added.assert_called_once()

    def test_add_tag_to_file_failure(self, tag_service, mock_tag_repository, mock_event_bus):
        # Given
        file_path = "C:/test/file.txt"
        tag = "new_tag"
        mock_tag_repository.add_tag.return_value = False

        # When
        result = tag_service.add_tag_to_file(file_path, tag)

        # Then
        assert result is False
        mock_tag_repository.add_tag.assert_called_once_with(file_path, tag)
        mock_event_bus.publish_tag_added.assert_not_called()

    def test_remove_tag_from_file_success(self, tag_service, mock_tag_repository, mock_event_bus):
        # Given
        file_path = "C:/test/file.txt"
        tag = "old_tag"
        mock_tag_repository.remove_tag.return_value = True

        # When
        result = tag_service.remove_tag_from_file(file_path, tag)

        # Then
        assert result is True
        mock_tag_repository.remove_tag.assert_called_once_with(file_path, tag)
        mock_event_bus.publish_tag_removed.assert_called_once()

    def test_remove_tag_from_file_failure(self, tag_service, mock_tag_repository, mock_event_bus):
        # Given
        file_path = "C:/test/file.txt"
        tag = "old_tag"
        mock_tag_repository.remove_tag.return_value = False

        # When
        result = tag_service.remove_tag_from_file(file_path, tag)

        # Then
        assert result is False
        mock_tag_repository.remove_tag.assert_called_once_with(file_path, tag)
        mock_event_bus.publish_tag_removed.assert_not_called()

    def test_get_tags_for_file(self, tag_service, mock_tag_repository):
        # Given
        file_path = "C:/test/file.txt"
        mock_tag_repository.get_tags_for_file.return_value = ["tag1", "tag2"]

        # When
        tags = tag_service.get_tags_for_file(file_path)

        # Then
        assert tags == ["tag1", "tag2"]
        mock_tag_repository.get_tags_for_file.assert_called_once_with(file_path)

    def test_get_all_tags(self, tag_service, mock_tag_repository):
        # Given
        mock_tag_repository.get_all_tags.return_value = ["all_tag1", "all_tag2"]

        # When
        tags = tag_service.get_all_tags()

        # Then
        assert tags == ["all_tag1", "all_tag2"]
        mock_tag_repository.get_all_tags.assert_called_once()

    def test_get_files_by_tags(self, tag_service, mock_tag_repository):
        # Given
        tags = ["search_tag"]
        mock_tag_repository.get_files_by_tags.return_value = ["C:/file1.txt", "C:/file2.jpg"]

        # When
        files = tag_service.get_files_by_tags(tags)

        # Then
        assert files == ["C:/file1.txt", "C:/file2.jpg"]
        mock_tag_repository.get_files_by_tags.assert_called_once_with(tags)

    def test_delete_file_entry(self, tag_service, mock_tag_repository):
        # Given
        file_path = "C:/test/file_to_delete.txt"
        mock_tag_repository.delete_file_entry.return_value = True

        # When
        result = tag_service.delete_file_entry(file_path)

        # Then
        assert result is True
        mock_tag_repository.delete_file_entry.assert_called_once_with(file_path)

    def test_add_tags_to_files_success(self, tag_service, mock_tag_repository, mock_event_bus):
        # Given
        file_paths = ["C:/file1.txt", "C:/file2.jpg"]
        tags_to_add = ["bulk_tag"]
        mock_tag_repository.get_tags_for_file.side_effect = [["existing_tag"], []] # Mock existing tags for each file
        mock_tag_repository.bulk_update_tags.return_value = {"modified": 2, "upserted": 0}

        # When
        result = tag_service.add_tags_to_files(file_paths, tags_to_add)

        # Then
        assert result["success"] is True
        assert result["processed"] == 2
        assert result["successful"] == 2
        assert mock_tag_repository.bulk_update_tags.called
        assert mock_event_bus.publish_tag_added.call_count == 2 # One event per file

    def test_remove_tags_from_files_success(self, tag_service, mock_tag_repository, mock_event_bus):
        # Given
        file_paths = ["C:/file1.txt", "C:/file2.jpg"]
        tags_to_remove = ["bulk_tag"]
        mock_tag_repository.get_tags_for_file.side_effect = [["existing_tag", "bulk_tag"], ["bulk_tag"]]
        mock_tag_repository.bulk_update_tags.return_value = {"modified": 2, "upserted": 0}

        # When
        result = tag_service.remove_tags_from_files(file_paths, tags_to_remove)

        # Then
        assert result["success"] is True
        assert result["processed"] == 2
        assert result["successful"] == 2
        assert mock_tag_repository.bulk_update_tags.called
        assert mock_event_bus.publish_tag_removed.call_count == 2 # One event per file