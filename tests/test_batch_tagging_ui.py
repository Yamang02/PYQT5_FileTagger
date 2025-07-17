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
    
    assert search_widget.extension_filter_combo.currentText() == "모든 파일"
    assert not search_widget.custom_extension_input.isVisible()
    assert search_widget.custom_extension_input.text() == ""

@pytest.mark.ui
def test_search_widget_extension_filter_options(search_widget, qtbot):
    """확장자 필터 옵션 변경 테스트"""
    # 고급 검색 패널 열기
    search_widget.advanced_toggle.click()
    qtbot.wait(100)
    
    # 이미지 파일 필터 선택
    search_widget.extension_filter_combo.setCurrentText("이미지 파일")
    assert search_widget.extension_filter_combo.currentText() == "이미지 파일"
    assert not search_widget.custom_extension_input.isVisible()
    
    # 문서 파일 필터 선택
    search_widget.extension_filter_combo.setCurrentText("문서 파일")
    assert search_widget.extension_filter_combo.currentText() == "문서 파일"
    assert not search_widget.custom_extension_input.isVisible()
    
    # 사용자 정의 필터 선택
    search_widget.extension_filter_combo.setCurrentText("사용자 정의")
    assert search_widget.extension_filter_combo.currentText() == "사용자 정의"
    assert search_widget.custom_extension_input.isVisible()
    
    # 사용자 정의 확장자 입력
    search_widget.custom_extension_input.setText(".txt,.pdf")
    assert search_widget.custom_extension_input.text() == ".txt,.pdf"

@pytest.mark.ui
def test_search_widget_get_extension_filter_extensions(search_widget, qtbot):
    """_get_extension_filter_extensions 메서드 테스트"""
    # 고급 검색 패널 열기
    search_widget.advanced_toggle.click()
    qtbot.wait(100)
    
    # 모든 파일 선택 시
    search_widget.extension_filter_combo.setCurrentText("모든 파일")
    extensions = search_widget._get_extension_filter_extensions()
    assert extensions == []
    
    # 이미지 파일 선택 시
    search_widget.extension_filter_combo.setCurrentText("이미지 파일")
    extensions = search_widget._get_extension_filter_extensions()
    assert ".jpg" in extensions
    assert ".png" in extensions
    assert ".svg" in extensions
    
    # 문서 파일 선택 시 (md 포함)
    search_widget.extension_filter_combo.setCurrentText("문서 파일")
    extensions = search_widget._get_extension_filter_extensions()
    assert ".txt" in extensions
    assert ".pdf" in extensions
    assert ".md" in extensions  # md 확장자 추가 확인
    
    # 사용자 정의 선택 시
    search_widget.extension_filter_combo.setCurrentText("사용자 정의")
    search_widget.custom_extension_input.setText(".py,.js")
    extensions = search_widget._get_extension_filter_extensions()
    assert extensions == [".py", ".js"]

