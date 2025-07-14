import pytest
from unittest.mock import Mock, patch
from PyQt5.QtCore import QObject, pyqtSignal

from viewmodels.tag_control_viewmodel import TagControlViewModel
from core.services.tag_service import TagService
from core.events import EventBus, TagAddedEvent, TagRemovedEvent

@pytest.fixture
def mock_tag_service():
    return Mock(spec=TagService)

@pytest.fixture
def mock_event_bus():
    return Mock(spec=EventBus)

@pytest.fixture
def tag_control_viewmodel(mock_tag_service, mock_event_bus):
    return TagControlViewModel(mock_tag_service, mock_event_bus)

class TestTagControlViewModel:

    def test_update_for_single_file_target(self, tag_control_viewmodel, mock_tag_service):
        # Given
        file_path = "C:/test/file.txt"
        mock_tag_service.get_tags_for_file.return_value = ["tag1", "tag2"]
        
        # When
        tag_control_viewmodel.update_for_target(file_path, False)

        # Then
        assert tag_control_viewmodel._current_target_path == file_path
        assert tag_control_viewmodel._is_current_target_dir is False
        assert tag_control_viewmodel._individual_tags == ["tag1", "tag2"]
        mock_tag_service.get_tags_for_file.assert_called_once_with(file_path)

    def test_update_for_directory_target(self, tag_control_viewmodel, mock_tag_service):
        # Given
        dir_path = "C:/test/dir"
        
        # When
        tag_control_viewmodel.update_for_target(dir_path, True)

        # Then
        assert tag_control_viewmodel._current_target_path == dir_path
        assert tag_control_viewmodel._is_current_target_dir is True
        # For directory, individual_tags should be empty, batch_tags will be common tags (not tested here)

    def test_update_for_multiple_files_target(self, tag_control_viewmodel, mock_tag_service):
        # Given
        file_paths = ["C:/test/file1.txt", "C:/test/file2.txt"]
        mock_tag_service.get_tags_for_file.side_effect = [["tagA", "tagB"], ["tagB", "tagC"]] # Mock common tags
        
        # When
        tag_control_viewmodel.update_for_target(file_paths, False) # is_dir=False for multiple files

        # Then
        assert tag_control_viewmodel._current_target_paths == file_paths
        assert tag_control_viewmodel._is_current_target_dir is False
        assert tag_control_viewmodel._batch_tags == ["tagB"] # Common tag
        assert mock_tag_service.get_tags_for_file.call_count == 2 # Called for each file to find common tags

    def test_add_tag_to_individual_success(self, tag_control_viewmodel, mock_tag_service, mock_event_bus):
        # Given
        file_path = "C:/test/file.txt"
        tag = "new_tag"
        mock_tag_service.get_tags_for_file.return_value = [] # Initial tags for update_for_target
        tag_control_viewmodel.update_for_target(file_path, False)
        mock_tag_service.add_tag_to_file.return_value = True
        
        # When
        tag_control_viewmodel.add_tag_to_individual(tag)

        # Then
        mock_tag_service.add_tag_to_file.assert_called_once_with(file_path, tag)
        # Verify show_message signal is emitted
        # mock_event_bus.publish_tag_added.assert_called_once() # EventBus is mocked, so check its method

    def test_remove_tag_from_individual_success(self, tag_control_viewmodel, mock_tag_service, mock_event_bus):
        # Given
        file_path = "C:/test/file.txt"
        tag = "old_tag"
        mock_tag_service.get_tags_for_file.return_value = ["old_tag"] # Initial tags for update_for_target
        tag_control_viewmodel.update_for_target(file_path, False)
        mock_tag_service.remove_tag_from_file.return_value = True
        
        # When
        tag_control_viewmodel.remove_tag_from_individual(tag)

        # Then
        mock_tag_service.remove_tag_from_file.assert_called_once_with(file_path, tag)
        # Verify show_message signal is emitted
        # mock_event_bus.publish_tag_removed.assert_called_once() # EventBus is mocked, so check its method

    def test_apply_batch_tags_multiple_files(self, tag_control_viewmodel, mock_tag_service, mock_event_bus):
        # Given
        file_paths = ["C:/test/file1.txt", "C:/test/file2.txt"]
        tags_to_add = ["batch_tag"]
        mock_tag_service.get_tags_for_file.side_effect = [["tagA"], ["tagB"]] # Initial tags for update_for_target
        tag_control_viewmodel.update_for_target(file_paths, False) # Multiple files
        mock_tag_service.add_tags_to_files.return_value = {"success": True, "processed": 2, "successful": 2}

        # When
        tag_control_viewmodel.apply_batch_tags(tags_to_add, False, [])

        # Then
        mock_tag_service.add_tags_to_files.assert_called_once_with(file_paths, tags_to_add)
        # Verify show_message signal is emitted
        # EventBus publish_tag_added will be called by tag_service, not directly by viewmodel here

    def test_apply_batch_tags_directory(self, tag_control_viewmodel, mock_tag_service, mock_event_bus):
        # Given
        dir_path = "C:/test/dir"
        tags_to_add = ["dir_tag"]
        mock_tag_service.get_tags_for_file.return_value = [] # Initial tags for update_for_target
        tag_control_viewmodel.update_for_target(dir_path, True) # Directory
        mock_tag_service.add_tags_to_directory.return_value = {"success": True, "processed": 5, "successful": 5}

        # When
        tag_control_viewmodel.apply_batch_tags(tags_to_add, True, ["txt"])

        # Then
        mock_tag_service.add_tags_to_directory.assert_called_once_with(dir_path, tags_to_add, recursive=True, file_extensions=["txt"])
        # Verify show_message signal is emitted
        # EventBus publish_tag_added will be called by tag_service, not directly by viewmodel here

    def test_on_tag_added_event_updates_current_file(self, tag_control_viewmodel, mock_tag_service, mock_event_bus):
        # Given
        file_path = "C:/test/file.txt"
        mock_tag_service.get_tags_for_file.return_value = ["tag1", "tag2"] # Initial tags for update_for_target
        tag_control_viewmodel.update_for_target(file_path, False)
        mock_tag_service.get_tags_for_file.reset_mock() # Reset mock after initial update_for_target
        mock_tag_service.get_tags_for_file.return_value = ["tag1", "tag2", "new_tag"] # Mock updated tags

        event = TagAddedEvent(file_path, "new_tag", 123.45)
        
        # When
        tag_control_viewmodel._on_tag_added(event)

        # Then
        mock_tag_service.get_tags_for_file.assert_called_once_with(file_path)
        # Verify tags_updated signal is emitted (assuming update_tags_for_current_target emits it)

    def test_on_tag_removed_event_updates_current_file(self, tag_control_viewmodel, mock_tag_service, mock_event_bus):
        # Given
        file_path = "C:/test/file.txt"
        mock_tag_service.get_tags_for_file.return_value = ["tag1", "tag2", "removed_tag"] # Initial tags for update_for_target
        tag_control_viewmodel.update_for_target(file_path, False)
        mock_tag_service.get_tags_for_file.reset_mock() # Reset mock after initial update_for_target
        mock_tag_service.get_tags_for_file.return_value = ["tag1", "tag2"] # Mock updated tags

        event = TagRemovedEvent(file_path, "removed_tag", 123.45)
        
        # When
        tag_control_viewmodel._on_tag_removed(event)

        # Then
        mock_tag_service.get_tags_for_file.assert_called_once_with(file_path)
