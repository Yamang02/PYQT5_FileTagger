import pytest
from unittest.mock import Mock, patch
from PyQt5.QtCore import QObject, pyqtSignal

from viewmodels.file_detail_viewmodel import FileDetailViewModel
from core.services.tag_service import TagService
from core.events import EventBus, TagAddedEvent, TagRemovedEvent

@pytest.fixture
def mock_tag_service():
    return Mock(spec=TagService)

@pytest.fixture
def mock_event_bus():
    return Mock(spec=EventBus)

@pytest.fixture
def file_detail_viewmodel(mock_tag_service, mock_event_bus):
    return FileDetailViewModel(mock_tag_service, mock_event_bus)

class TestFileDetailViewModel:

    def test_update_for_file_with_tags(self, file_detail_viewmodel, mock_tag_service):
        # Given
        file_path = "C:/test/file.txt"
        mock_tag_service.get_tags_for_file.return_value = ["tag1", "tag2"]
        
        # When
        file_detail_viewmodel.update_for_file(file_path)

        # Then
        assert file_detail_viewmodel._current_file_path == file_path
        mock_tag_service.get_tags_for_file.assert_called_once_with(file_path)
        # Verify file_details_updated signal is emitted
        # (Assuming file_details_updated is connected and checked in a real UI test)

    def test_update_for_file_no_tags(self, file_detail_viewmodel, mock_tag_service):
        # Given
        file_path = "C:/test/empty_file.txt"
        mock_tag_service.get_tags_for_file.return_value = []
        
        # When
        file_detail_viewmodel.update_for_file(file_path)

        # Then
        assert file_detail_viewmodel._current_file_path == file_path
        mock_tag_service.get_tags_for_file.assert_called_once_with(file_path)

    def test_update_for_no_file(self, file_detail_viewmodel, mock_tag_service):
        # When
        file_detail_viewmodel.update_for_file(None)

        # Then
        assert file_detail_viewmodel._current_file_path is None
        mock_tag_service.get_tags_for_file.assert_not_called() # Ensure get_tags_for_file is not called for None

    def test_remove_tag_from_file_success(self, file_detail_viewmodel, mock_tag_service, mock_event_bus):
        # Given
        file_path = "C:/test/file.txt"
        tag = "tag_to_remove"
        # Set return_value for get_tags_for_file before update_for_file is called
        mock_tag_service.get_tags_for_file.return_value = ["tag1", "tag2", "tag_to_remove"]
        file_detail_viewmodel.update_for_file(file_path) # Set current file
        mock_tag_service.get_tags_for_file.reset_mock() # Reset mock after initial update_for_file
        mock_tag_service.remove_tag_from_file.return_value = True
        mock_tag_service.get_tags_for_file.return_value = ["tag1", "tag2"] # Mock tags after removal
        
        # When
        file_detail_viewmodel.remove_tag_from_file(tag)

        # Then
        mock_tag_service.remove_tag_from_file.assert_called_once_with(file_path, tag)
        # Verify show_message signal is emitted

    def test_remove_tag_from_file_failure(self, file_detail_viewmodel, mock_tag_service, mock_event_bus):
        # Given
        file_path = "C:/test/file.txt"
        tag = "tag_to_remove"
        # Set return_value for get_tags_for_file before update_for_file is called
        mock_tag_service.get_tags_for_file.return_value = ["tag1", "tag2", "tag_to_remove"]
        file_detail_viewmodel.update_for_file(file_path) # Set current file
        mock_tag_service.get_tags_for_file.reset_mock() # Reset mock after initial update_for_file
        mock_tag_service.remove_tag_from_file.return_value = False
        mock_tag_service.get_tags_for_file.return_value = ["tag1", "tag2", "tag_to_remove"] # Mock tags after failed removal
        
        # When
        file_detail_viewmodel.remove_tag_from_file(tag)

        # Then
        mock_tag_service.remove_tag_from_file.assert_called_once_with(file_path, tag)
        # Verify show_message signal is emitted

    def test_on_tag_added_event_updates_current_file(self, file_detail_viewmodel, mock_tag_service):
        # Given
        file_path = "C:/test/file.txt"
        mock_tag_service.get_tags_for_file.return_value = ["tag1", "tag2"] # Initial tags
        file_detail_viewmodel.update_for_file(file_path) # Set current file
        mock_tag_service.get_tags_for_file.reset_mock() # Reset mock after initial update_for_file
        mock_tag_service.get_tags_for_file.return_value = ["tag1", "tag2", "new_tag"] # Mock updated tags

        event = TagAddedEvent(file_path, "new_tag", 123.45)
        
        # When
        file_detail_viewmodel._on_tag_added(event)

        # Then
        mock_tag_service.get_tags_for_file.assert_called_once_with(file_path)

    def test_on_tag_removed_event_updates_current_file(self, file_detail_viewmodel, mock_tag_service):
        # Given
        file_path = "C:/test/file.txt"
        mock_tag_service.get_tags_for_file.return_value = ["tag1", "tag2", "removed_tag"] # Initial tags
        file_detail_viewmodel.update_for_file(file_path) # Set current file
        mock_tag_service.get_tags_for_file.reset_mock() # Reset mock after initial update_for_file
        mock_tag_service.get_tags_for_file.return_value = ["tag1", "tag2"] # Mock updated tags

        event = TagRemovedEvent(file_path, "removed_tag", 123.45)
        
        # When
        file_detail_viewmodel._on_tag_removed(event)

        # Then
        mock_tag_service.get_tags_for_file.assert_called_once_with(file_path)
