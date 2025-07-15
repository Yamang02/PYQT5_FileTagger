import pytest
from unittest.mock import Mock, patch
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QDir, QModelIndex
import os

from main_window import MainWindow
from core.services.tag_service import TagService
from core.events import EventBus
from core.custom_tag_manager import CustomTagManager
from core.repositories.tag_repository import TagRepository # For mocking MongoClient

@pytest.fixture(scope="session")
def qapp():
    # QApplication 인스턴스가 없으면 생성
    if QApplication.instance():
        return QApplication.instance()
    return QApplication([])

@pytest.fixture
def mock_mongo_client():
    return Mock()

@pytest.fixture
def mock_tag_service():
    mock_service = Mock(spec=TagService)
    # Explicitly define the behavior of the mock methods
    mock_service.get_all_tags = Mock(return_value=["tagA", "tagB", "tagC"])
    mock_service.get_tags_for_file = Mock(return_value=[])
    # You might also need to mock other methods that are called
    mock_service.add_tag_to_file.return_value = True
    mock_service.remove_tag_from_file.return_value = True
    mock_service.add_tags_to_files.return_value = {"success": True, "processed": 0, "successful": 0}
    mock_service.add_tags_to_directory.return_value = {"success": True, "processed": 0, "successful": 0}
    mock_service.get_files_in_directory.return_value = []
    mock_service.remove_tags_from_files.return_value = {"success": True, "processed": 0, "successful": 0}
    return mock_service

@pytest.fixture
def mock_event_bus():
    return Mock(spec=EventBus)

@pytest.fixture
def mock_custom_tag_manager():
    mock_manager = Mock(spec=CustomTagManager)
    mock_manager.load_custom_quick_tags.return_value = ["quick1", "quick2"]
    return mock_manager

@pytest.fixture
def main_window(qapp, mock_mongo_client, mock_tag_service, mock_event_bus, mock_custom_tag_manager):
    with patch('core.services.tag_service.TagService', return_value=mock_tag_service), \
         patch('core.events.EventBus', return_value=mock_event_bus), \
         patch('core.custom_tag_manager.CustomTagManager', return_value=mock_custom_tag_manager), \
         patch('viewmodels.tag_control_viewmodel.TagControlViewModel') as MockTagControlViewModel:
        
        # TagControlViewModel mock 설정
        mock_viewmodel = MockTagControlViewModel.return_value
        mock_viewmodel.get_all_tags.return_value = ["tagA", "tagB", "tagC"]
        mock_viewmodel.get_tags_for_file.return_value = []
        mock_viewmodel.add_tag_to_individual.return_value = True
        mock_viewmodel.remove_tag_from_individual.return_value = True
        mock_viewmodel.apply_batch_tags.return_value = True
        mock_viewmodel.get_current_batch_tags.return_value = []
        mock_viewmodel.get_current_target_path.return_value = ""
        mock_viewmodel.get_current_target_paths.return_value = []
        mock_viewmodel.is_current_target_dir.return_value = False
        
        window = MainWindow(mock_mongo_client)
        window.show()
        yield window
        window.close()

@pytest.fixture
def temp_test_dir(tmp_path):
    # 임시 디렉토리 생성
    base_dir = tmp_path / "test_root"
    base_dir.mkdir()
    (base_dir / "fileA.txt").touch()
    (base_dir / "fileB.jpg").touch()
    (base_dir / "subdir").mkdir()
    (base_dir / "subdir" / "fileC.pdf").touch()
    return base_dir

class TestMainWindowIntegration:

    def test_initial_ui_setup(self, main_window):
        assert main_window.isVisible()
        assert main_window.directory_tree is not None
        assert main_window.file_list is not None
        assert main_window.file_detail is not None
        assert main_window.tag_control is not None
        assert main_window.search_widget is not None
        assert main_window.statusbar.isVisible()

    def test_directory_selection_updates_file_list(self, main_window, mock_tag_service, temp_test_dir):
        # Given
        main_window.directory_tree.set_root_path(str(temp_test_dir))
        QApplication.processEvents() # UI 업데이트 대기

        # Mock get_tags_for_file for file_list_viewmodel
        mock_tag_service.get_tags_for_file.return_value = []

        # When: Select the root directory in the tree view
        root_index = main_window.directory_tree.tree_view.model().index(str(temp_test_dir))
        main_window.directory_tree.tree_view.setCurrentIndex(root_index)
        main_window.directory_tree.directory_selected.emit(str(temp_test_dir), True)
        QApplication.processEvents() # UI 업데이트 대기

        # Then: File list should be updated
        assert main_window.file_list.model.rowCount() > 0
        assert main_window.file_list.model.data(main_window.file_list.model.index(0, 0), role=0) == "fileA.txt"
        assert main_window.file_list.model.data(main_window.file_list.model.index(1, 0), role=0) == "fileB.jpg"
        
        # Verify tag_control_viewmodel is updated for directory
        assert main_window.tag_control_viewmodel._current_target_path == str(temp_test_dir)
        assert main_window.tag_control_viewmodel._is_current_target_dir is True
        assert main_window.tag_control.tagging_tab_widget.currentIndex() == 1 # Should switch to batch tagging tab

    def test_file_selection_updates_file_detail_and_tag_control(self, main_window, mock_tag_service, temp_test_dir):
        # Given
        main_window.directory_tree.set_root_path(str(temp_test_dir))
        QApplication.processEvents()
        
        # Mock get_tags_for_file for file_detail_viewmodel and tag_control_viewmodel
        mock_tag_service.get_tags_for_file.return_value = ["existing_tag"]

        # When: Select a file in the file list
        file_path = str(temp_test_dir / "fileA.txt")
        # Simulate selection by emitting the signal directly
        main_window.file_list.file_selection_changed.emit([file_path])
        QApplication.processEvents() # UI 업데이트 대기

        # Then: File detail and tag control should be updated
        assert main_window.file_detail.file_path_label.text() == file_path
        assert main_window.tag_control_viewmodel._current_target_path == file_path
        assert main_window.tag_control_viewmodel._is_current_target_dir is False
        assert main_window.tag_control.tagging_tab_widget.currentIndex() == 0 # Should switch to individual tagging tab

    def test_filter_options_change_updates_file_list(self, main_window, mock_tag_service, temp_test_dir):
        # Given
        main_window.directory_tree.set_root_path(str(temp_test_dir))
        QApplication.processEvents()
        mock_tag_service.get_tags_for_file.return_value = [] # For file list updates

        # When: Change filter options (e.g., uncheck recursive)
        main_window.directory_tree.recursive_checkbox.setChecked(False)
        main_window.directory_tree.filter_options_changed.emit(False, [])
        QApplication.processEvents()

        # Then: File list should reflect non-recursive content (subdir should not be listed)
        # This test assumes that the file list model correctly filters based on the signal.
        # A more robust test would check the actual content of the file list.
        # For now, we verify the signal was emitted and the viewmodel received it.
        assert main_window.file_list_viewmodel._recursive is False
        # You might need to add assertions to check the actual file list content if the model updates synchronously.

    def test_add_tag_via_tag_control_individual(self, main_window, mock_tag_service, mock_event_bus, temp_test_dir):
        # Given
        file_path = str(temp_test_dir / "fileA.txt")
        mock_tag_service.get_tags_for_file.return_value = [] # No initial tags
        main_window.file_list.file_selection_changed.emit([file_path])
        QApplication.processEvents()

        mock_tag_service.add_tag_to_file.return_value = True
        mock_tag_service.get_tags_for_file.return_value = ["new_tag"] # After adding

        # When: Add a tag via the individual tag input
        main_window.tag_control.individual_tag_input.setText("new_tag")
        main_window.tag_control.individual_tag_input.returnPressed.emit()
        QApplication.processEvents()

        # Then
        mock_tag_service.add_tag_to_file.assert_called_once_with(file_path, "new_tag")
        # Verify UI update (e.g., tag chip appears in file detail)
        # This requires inspecting the actual UI, which is more complex.
        # For now, we rely on the ViewModel's internal state and service calls.
        assert "new_tag" in main_window.tag_control_viewmodel._individual_tags

    def test_add_tag_via_tag_control_batch(self, main_window, mock_tag_service, mock_event_bus, temp_test_dir):
        # Given
        file_paths = [str(temp_test_dir / "fileA.txt"), str(temp_test_dir / "fileB.jpg")]
        mock_tag_service.get_tags_for_file.side_effect = [[], []] # No initial tags for common tags calculation
        main_window.file_list.file_selection_changed.emit(file_paths)
        QApplication.processEvents()

        mock_tag_service.add_tags_to_files.return_value = {"success": True, "processed": 2, "successful": 2}
        mock_tag_service.get_tags_for_file.side_effect = [["batch_tag"], ["batch_tag"]] # After adding

        # When: Add a tag via the batch tag input
        main_window.tag_control.batch_tag_input.setText("batch_tag")
        main_window.tag_control.batch_tag_input.returnPressed.emit()
        QApplication.processEvents()
        
        # Simulate apply button click
        main_window.tag_control.apply_batch_tags()
        QApplication.processEvents()

        # Then
        mock_tag_service.add_tags_to_files.assert_called_once_with(file_paths, ["batch_tag"])
        assert "batch_tag" in main_window.tag_control_viewmodel._batch_tags

    def test_batch_remove_tags_dialog_call(self, main_window, mock_tag_service, temp_test_dir):
        # Given
        dir_path = str(temp_test_dir)
        mock_tag_service.get_files_in_directory.return_value = [str(temp_test_dir / "fileA.txt")]
        mock_tag_service.get_all_tags.return_value = ["tag1", "tag2"] # For dialog population

        # When: Simulate context menu request and action click
        # We need to mock the dialog execution to avoid actual UI interaction
        with patch('widgets.batch_remove_tags_dialog.BatchRemoveTagsDialog') as MockBatchRemoveTagsDialog:
            mock_dialog_instance = MockBatchRemoveTagsDialog.return_value
            mock_dialog_instance.exec_.return_value = True # Simulate OK button click
            mock_dialog_instance.get_tags_to_remove.return_value = ["tag1"] # Simulate tags selected for removal

            # Simulate the signal from directory_tree_widget
            main_window.directory_tree.batch_remove_tags_requested.emit(dir_path)
            QApplication.processEvents()

            # Then: Verify dialog was created and executed
            MockBatchRemoveTagsDialog.assert_called_once_with(mock_tag_service, dir_path, main_window.tag_control)
            mock_dialog_instance.exec_.assert_called_once()
            # Verify that the tags_updated signal was emitted by tag_control
            # This is implicitly tested if the dialog.exec_() returns True and the subsequent logic runs.
            # A more direct way would be to mock the signal and assert it was emitted.
