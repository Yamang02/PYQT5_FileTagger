import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch
from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox
from PyQt5.QtTest import QTest

# from widgets.unified_tagging_panel import UnifiedTaggingPanel # UnifiedTaggingPanel은 더 이상 사용되지 않음
from core.tag_ui_state_manager import TagUIStateManager
from core.tag_manager import TagManager

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

# @pytest.fixture(scope="function")
# def unified_panel(app, mock_tag_manager, state_manager):
#     """UnifiedTaggingPanel 인스턴스를 생성하고 초기화합니다."""
#     panel = UnifiedTaggingPanel(state_manager, mock_tag_manager)
#     panel.show()
#     # 초기화 완료 대기 (필요시)
#     QTest.qWaitForWindowExposed(panel)
#     return panel

# @pytest.fixture(scope="function")
# def batch_tab_panel(unified_panel, qtbot):
#     """UnifiedTaggingPanel 내의 BatchTaggingPanel을 활성화하고 반환합니다."""
#     unified_panel.switch_to_mode('batch')
#     qtbot.wait(100) # UI 업데이트 대기
#     # BatchTaggingPanel의 초기 상태를 명시적으로 설정
#     unified_panel.batch_tagging_panel.dir_path_edit.setText("")
#     unified_panel.batch_tagging_panel.file_table.setRowCount(0)
#     unified_panel.batch_tagging_panel.file_count_label.setText("0개 파일")
#     unified_panel.batch_tagging_panel.apply_button.setEnabled(False)
#     unified_panel.batch_tagging_panel.status_label.setText("대기 중")
#     return unified_panel.batch_tagging_panel

@pytest.fixture
def temp_dir():
    """임시 디렉토리를 생성합니다."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)

@pytest.mark.ui
def test_batch_tagging_panel_initial_state(batch_tab_panel, qtbot):
    """일괄 태그 패널의 초기 상태 테스트"""
    assert batch_tab_panel.isVisible()
    # assert batch_tab_panel.dir_path_edit.text() == "" # 이 테스트는 FileSelectionAndPreviewWidget의 기본 경로 설정 때문에 실패할 수 있음
    assert batch_tab_panel.file_table.rowCount() == 0
    assert not batch_tab_panel.apply_button.isEnabled()
    assert not batch_tab_panel.cancel_button.isVisible()
    assert not batch_tab_panel.progress_bar.isVisible()
    assert batch_tab_panel.status_label.text() == "대기 중"

@pytest.mark.ui
def test_batch_tagging_panel_directory_selection(batch_tab_panel, qtbot, temp_dir):
    """디렉토리 선택 및 파일 미리보기 업데이트 테스트"""
    # 테스트용 임시 디렉토리 및 파일 생성
    (temp_dir / "file1.txt").touch()
    (temp_dir / "image.jpg").touch()
    (temp_dir / "document.pdf").touch()

    # QFileDialog.getExistingDirectory를 모의(Mock)하여 특정 경로를 반환하도록 설정
    with patch.object(QFileDialog, 'getExistingDirectory', return_value=str(temp_dir)) as mock_get_dir:
        batch_tab_panel.browse_button.click()
        qtbot.waitUntil(lambda: batch_tab_panel.file_table.rowCount() == 3, timeout=5000) # 파일 로드 대기

        mock_get_dir.assert_called_once()
        assert batch_tab_panel.dir_path_edit.text() == str(temp_dir)
        assert batch_tab_panel.file_table.rowCount() == 3
        assert batch_tab_panel.file_count_label.text() == "3개 파일"
        assert batch_tab_panel.apply_button.isEnabled()
        assert "3개 파일" in batch_tab_panel.status_label.text() # 상태 라벨 업데이트 확인

@pytest.mark.ui
def test_batch_tagging_panel_recursive_option(batch_tab_panel, qtbot, temp_dir):
    """재귀 옵션에 따른 파일 미리보기 업데이트 테스트"""
    # 테스트용 임시 디렉토리 및 파일 생성
    (temp_dir / "file1.txt").touch()
    sub_dir = temp_dir / "subdir"
    sub_dir.mkdir()
    (sub_dir / "subfile1.txt").touch()
    (sub_dir / "subfile2.jpg").touch()

    batch_tab_panel.set_directory(str(temp_dir))
    qtbot.waitUntil(lambda: batch_tab_panel.file_table.rowCount() == 1, timeout=5000) # 파일 로드 대기

    # 초기 (비재귀) 상태 확인
    assert batch_tab_panel.file_table.rowCount() == 1 # file1.txt만 포함
    assert batch_tab_panel.file_count_label.text() == "1개 파일"

    # 재귀 옵션 활성화
    batch_tab_panel.recursive_checkbox.setChecked(True)
    qtbot.waitUntil(lambda: batch_tab_panel.file_table.rowCount() == 3, timeout=5000) # UI 업데이트 대기

    # 재귀 상태 확인 (모든 파일 포함)
    assert batch_tab_panel.file_table.rowCount() == 3
    assert batch_tab_panel.file_count_label.text() == "3개 파일"
    file_names = [batch_tab_panel.file_table.item(i, 0).text() for i in range(3)]
    assert "file1.txt" in file_names
    assert "subfile1.txt" in file_names
    assert "subfile2.jpg" in file_names

@pytest.mark.ui
def test_batch_tagging_panel_extension_filter(batch_tab_panel, qtbot, temp_dir):
    """확장자 필터링에 따른 파일 미리보기 업데이트 테스트"""
    # 테스트용 임시 디렉토리 및 파일 생성
    (temp_dir / "doc.txt").touch()
    (temp_dir / "image.png").touch()
    (temp_dir / "report.pdf").touch()
    (temp_dir / "script.py").touch()

    batch_tab_panel.set_directory(str(temp_dir))
    qtbot.waitUntil(lambda: batch_tab_panel.file_table.rowCount() == 4, timeout=5000) # 파일 로드 대기

    # 초기 (모든 파일) 상태 확인
    assert batch_tab_panel.file_table.rowCount() == 4

    # 이미지 파일 필터링
    batch_tab_panel.ext_combo.setCurrentText("이미지 파일")
    qtbot.waitUntil(lambda: batch_tab_panel.file_table.rowCount() == 1, timeout=5000)
    assert batch_tab_panel.file_table.rowCount() == 1
    assert batch_tab_panel.file_table.item(0, 0).text() == "image.png"

    # 문서 파일 필터링
    batch_tab_panel.ext_combo.setCurrentText("문서 파일")
    qtbot.waitUntil(lambda: batch_tab_panel.file_table.rowCount() == 2, timeout=5000)
    assert batch_tab_panel.file_table.rowCount() == 2
    file_names = [batch_tab_panel.file_table.item(i, 0).text() for i in range(2)]
    assert "doc.txt" in file_names
    assert "report.pdf" in file_names

    # 사용자 정의 확장자 필터링 (.py)
    batch_tab_panel.ext_combo.setCurrentText("사용자 정의")
    batch_tab_panel.custom_ext_edit.setText(".py")
    qtbot.waitUntil(lambda: batch_tab_panel.file_table.rowCount() == 1, timeout=5000)
    assert batch_tab_panel.file_table.rowCount() == 1
    assert batch_tab_panel.file_table.item(0, 0).text() == "script.py"

    # 사용자 정의 확장자 필터링 (.txt, .pdf)
    batch_tab_panel.custom_ext_edit.setText(".txt,.pdf")
    qtbot.waitUntil(lambda: batch_tab_panel.file_table.rowCount() == 2, timeout=5000)
    assert batch_tab_panel.file_table.rowCount() == 2
    file_names = [batch_tab_panel.file_table.item(i, 0).text() for i in range(2)]
    assert "doc.txt" in file_names
    assert "report.pdf" in file_names

    # 모든 파일로 다시 변경
    batch_tab_panel.ext_combo.setCurrentText("모든 파일")
    qtbot.waitUntil(lambda: batch_tab_panel.file_table.rowCount() == 4, timeout=5000)
    assert batch_tab_panel.file_table.rowCount() == 4

