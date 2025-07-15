import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch
from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox
from PyQt5.QtTest import QTest

from core.tag_ui_state_manager import TagUIStateManager
from core import TagManager
from widgets.batch_tagging_options_widget import BatchTaggingOptionsWidget

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
def batch_tagging_options_widget(app):
    """BatchTaggingOptionsWidget 인스턴스를 생성합니다."""
    widget = BatchTaggingOptionsWidget()
    widget.show()
    return widget

@pytest.fixture
def temp_dir():
    """임시 디렉토리를 생성합니다."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)

@pytest.mark.ui
def test_batch_tagging_options_widget_initial_state(batch_tagging_options_widget, qtbot):
    """일괄 태그 옵션 위젯의 초기 상태 테스트"""
    assert batch_tagging_options_widget.isVisible()
    assert batch_tagging_options_widget.recursive_checkbox.isChecked()  # 기본값이 True로 설정됨
    assert batch_tagging_options_widget.ext_combo.currentText() == "모든 파일"
    assert batch_tagging_options_widget.custom_ext_edit.text() == ""

@pytest.mark.ui
def test_batch_tagging_options_widget_recursive_option(batch_tagging_options_widget, qtbot):
    """재귀 옵션 변경 테스트"""
    # 초기 상태 확인 (기본값이 True로 설정됨)
    assert batch_tagging_options_widget.recursive_checkbox.isChecked()
    
    # 재귀 옵션 비활성화
    batch_tagging_options_widget.recursive_checkbox.setChecked(False)
    assert not batch_tagging_options_widget.recursive_checkbox.isChecked()
    
    # 재귀 옵션 활성화
    batch_tagging_options_widget.recursive_checkbox.setChecked(True)
    assert batch_tagging_options_widget.recursive_checkbox.isChecked()

@pytest.mark.ui
def test_batch_tagging_options_widget_extension_filter(batch_tagging_options_widget, qtbot):
    """확장자 필터 변경 테스트"""
    # 초기 상태 확인
    assert batch_tagging_options_widget.ext_combo.currentText() == "모든 파일"
    assert batch_tagging_options_widget.custom_ext_edit.text() == ""
    
    # 이미지 파일 필터 선택
    batch_tagging_options_widget.ext_combo.setCurrentText("이미지 파일")
    assert batch_tagging_options_widget.ext_combo.currentText() == "이미지 파일"
    
    # 문서 파일 필터 선택
    batch_tagging_options_widget.ext_combo.setCurrentText("문서 파일")
    assert batch_tagging_options_widget.ext_combo.currentText() == "문서 파일"
    
    # 사용자 정의 필터 선택
    batch_tagging_options_widget.ext_combo.setCurrentText("사용자 정의")
    assert batch_tagging_options_widget.ext_combo.currentText() == "사용자 정의"
    
    # 사용자 정의 확장자 입력
    batch_tagging_options_widget.custom_ext_edit.setText(".txt,.pdf")
    assert batch_tagging_options_widget.custom_ext_edit.text() == ".txt,.pdf"

@pytest.mark.ui
def test_batch_tagging_options_widget_get_file_extensions(batch_tagging_options_widget, qtbot):
    """get_file_extensions 메서드 테스트"""
    # 모든 파일 선택 시
    batch_tagging_options_widget.ext_combo.setCurrentText("모든 파일")
    extensions = batch_tagging_options_widget._get_file_extensions()
    assert extensions == []
    
    # 이미지 파일 선택 시
    batch_tagging_options_widget.ext_combo.setCurrentText("이미지 파일")
    extensions = batch_tagging_options_widget._get_file_extensions()
    assert ".jpg" in extensions
    assert ".png" in extensions
    
    # 문서 파일 선택 시
    batch_tagging_options_widget.ext_combo.setCurrentText("문서 파일")
    extensions = batch_tagging_options_widget._get_file_extensions()
    assert ".txt" in extensions
    assert ".pdf" in extensions
    
    # 사용자 정의 선택 시
    batch_tagging_options_widget.ext_combo.setCurrentText("사용자 정의")
    batch_tagging_options_widget.custom_ext_edit.setText(".py,.js")
    extensions = batch_tagging_options_widget._get_file_extensions()
    assert extensions == [".py", ".js"]

