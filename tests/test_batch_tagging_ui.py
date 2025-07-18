import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch
from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox
from PyQt5.QtTest import QTest

from core.tag_ui_state_manager import TagUIStateManager
from core import TagManager
from widgets.search_widget import SearchWidget
from viewmodels.search_viewmodel import SearchViewModel
from core.search_manager import SearchManager

# Mock TagManager for UI tests
@pytest.fixture(scope="function")
def mock_tag_manager():
    """MagicMock을 사용하여 TagManager를 모의(Mock)합니다."""
    manager = MagicMock(spec=TagManager)
    manager.get_tags_for_file.return_value = []
    manager.get_all_unique_tags.return_value = []
    manager.get_connection_status.return_value = {"connected": True, "status": "정상"}
    # add_tags_to_directory의 기본 반환값: 성공 케이스
    manager.add_tags_to_directory.return_value = {
        "success": True,
        "processed": 0,
        "successful": 0,
        "failed": 0,
        "modified": 0,
        "upserted": 0,
        "errors": []
    }
    return manager

@pytest.fixture(scope="function")
def app():
    """QApplication 인스턴스를 제공합니다."""
    if not QApplication.instance():
        return QApplication([])
    return QApplication.instance()

@pytest.fixture(scope="function")
def state_manager():
    """TagUIStateManager 인스턴스를 제공합니다."""
    return TagUIStateManager()

@pytest.fixture
def search_widget(app):
    """SearchWidget 인스턴스를 생성합니다."""
    mock_tag_service = MagicMock()
    mock_search_manager = MagicMock()
    viewmodel = SearchViewModel(mock_tag_service, mock_search_manager)
    widget = SearchWidget(viewmodel)
    widget.show()
    return widget

@pytest.fixture
def temp_dir():
    """임시 디렉토리를 생성합니다."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)

@pytest.mark.ui
def test_search_widget_extension_filter_initial_state(search_widget, qtbot):
    """고급 검색 패널의 확장자 필터 초기 상태 테스트"""
    # 고급 검색 패널 열기
    search_widget.advanced_toggle.click()
    qtbot.wait(100)
    

    assert not search_widget.custom_extension_input.isVisible()
    assert search_widget.custom_extension_input.text() == ""


