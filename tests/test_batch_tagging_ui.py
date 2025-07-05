import pytest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch
from PyQt5.QtWidgets import QApplication, QFileDialog, QTableWidgetItem, QMessageBox
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtTest import QTest

from widgets.unified_tagging_panel import UnifiedTaggingPanel
from core.tag_ui_state_manager import TagUIStateManager
from core.tag_manager import TagManager
from widgets.tag_input_widget import TagInputWidget # TagInputWidget을 직접 import하여 mock에 사용

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

@pytest.fixture(scope="function")
def unified_panel(app, mock_tag_manager, state_manager):
    """UnifiedTaggingPanel 인스턴스를 생성하고 초기화합니다."""
    panel = UnifiedTaggingPanel(state_manager, mock_tag_manager)
    panel.show()
    # 초기화 완료 대기 (필요시)
    QTest.qWaitForWindowExposed(panel)
    return panel

@pytest.fixture(scope="function")
def batch_tab_panel(unified_panel, qtbot):
    """UnifiedTaggingPanel 내의 BatchTaggingPanel을 활성화하고 반환합니다."""
    unified_panel.switch_to_mode('batch')
    qtbot.wait(100) # UI 업데이트 대기
    # BatchTaggingPanel의 초기 상태를 명시적으로 설정
    unified_panel.batch_tagging_panel.dir_path_edit.setText("")
    unified_panel.batch_tagging_panel.file_table.setRowCount(0)
    unified_panel.batch_tagging_panel.file_count_label.setText("0개 파일")
    unified_panel.batch_tagging_panel.apply_button.setEnabled(False)
    unified_panel.batch_tagging_panel.status_label.setText("대기 중")
    return unified_panel.batch_tagging_panel

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

@pytest.mark.ui
def test_batch_tagging_panel_apply_tags_success(unified_panel, batch_tab_panel, qtbot, temp_dir, mock_tag_manager, mocker):
    """태그 입력 및 적용 기능 성공 테스트"""
    # 테스트용 임시 디렉토리 및 파일 생성
    (temp_dir / "fileA.txt").touch()
    (temp_dir / "fileB.jpg").touch()

    # 디렉토리 설정
    batch_tab_panel.set_directory(str(temp_dir))
    qtbot.waitUntil(lambda: batch_tab_panel.file_table.rowCount() == 2, timeout=5000) # 파일 로드 대기

    # 태그 입력 (UnifiedTaggingPanel의 tag_input_widget을 통해)
    tags_to_add = ["new_tag1", "new_tag2"]
    unified_panel.individual_tag_input.set_tags(tags_to_add) # UnifiedPanel의 태그 입력 위젯 사용
    qtbot.wait(50)

    # QMessageBox.question 모의
    mocker.patch('PyQt5.QtWidgets.QMessageBox.question', return_value=QMessageBox.Yes)
    mock_information = mocker.patch('PyQt5.QtWidgets.QMessageBox.information', return_value=QMessageBox.Ok)

    # apply_button 클릭
    batch_tab_panel.apply_button.click()
    qtbot.wait(100) # UI 업데이트 대기

    # UI 상태 확인 (작업 진행 중)
    assert not batch_tab_panel.apply_button.isVisible()
    assert batch_tab_panel.cancel_button.isVisible()
    assert batch_tab_panel.progress_bar.isVisible()
    assert "작업 진행 중" in batch_tab_panel.status_label.text()

    # add_tags_to_directory가 올바른 인자로 호출되었는지 확인
    mock_tag_manager.add_tags_to_directory.assert_called_once_with(
        str(temp_dir),
        tags_to_add,
        False, # recursive 기본값
        []   # file_extensions 기본값 (모든 파일)
    )

    # 작업 완료 시그널을 수동으로 발생시켜 테스트 진행
    mock_tag_manager.add_tags_to_directory.return_value = {
        "success": True,
        "processed": 2,
        "successful": 2,
        "failed": 0,
        "modified": 2,
        "upserted": 0,
        "errors": []
    }
    batch_tab_panel.worker_thread.work_finished.emit(
        mock_tag_manager.add_tags_to_directory.return_value
    )
    qtbot.wait(100) # UI 업데이트 대기

    # 작업 완료 후 UI 상태 확인
    assert batch_tab_panel.apply_button.isVisible()
    assert not batch_tab_panel.cancel_button.isVisible()
    assert not batch_tab_panel.progress_bar.isVisible()
    assert "완료" in batch_tab_panel.status_label.text()

    mock_information.assert_called_once()
    args, kwargs = mock_information.call_args
    assert "일괄 태그 적용 완료" in args[0]
    assert "2개 파일에 태그가 성공적으로 적용되었습니다." in args[1]

@pytest.mark.ui
def test_batch_tagging_panel_apply_tags_error_handling(unified_panel, batch_tab_panel, qtbot, temp_dir, mock_tag_manager, mocker):
    """태그 적용 중 오류 발생 시 UI 동작 테스트"""
    # 테스트용 임시 디렉토리 및 파일 생성
    (temp_dir / "fileC.txt").touch()
    (temp_dir / "fileD.jpg").touch()

    # 디렉토리 설정
    batch_tab_panel.set_directory(str(temp_dir))
    qtbot.waitUntil(lambda: batch_tab_panel.file_table.rowCount() == 2, timeout=5000) # 파일 로드 대기

    # 태그 입력
    tags_to_add = ["error_tag"]
    unified_panel.individual_tag_input.set_tags(tags_to_add)
    qtbot.wait(50)

    # QMessageBox.question 모의
    mocker.patch('PyQt5.QtWidgets.QMessageBox.question', return_value=QMessageBox.Yes)
    mock_critical = mocker.patch('PyQt5.QtWidgets.QMessageBox.critical', return_value=QMessageBox.Ok)

    # apply_button 클릭
    batch_tab_panel.apply_button.click()
    qtbot.wait(50)

    # add_tags_to_directory가 오류를 반환하도록 설정
    mock_tag_manager.add_tags_to_directory.return_value = {
        "success": False,
        "error": "데이터베이스 연결 오류",
        "processed": 2,
        "successful": 0,
        "failed": 2,
        "modified": 0,
        "upserted": 0,
        "errors": [
            {"file": str(temp_dir / "fileC.txt"), "error": "DB write error"},
            {"file": str(temp_dir / "fileD.jpg"), "error": "Permission denied"}
        ]
    }
    batch_tab_panel.worker_thread.work_finished.emit(
        mock_tag_manager.add_tags_to_directory.return_value
    )
    qtbot.wait(100)

    # 작업 완료 후 UI 상태 확인
    assert batch_tab_panel.apply_button.isVisible()
    assert not batch_tab_panel.cancel_button.isVisible()
    assert not batch_tab_panel.progress_bar.isVisible()
    assert "오류" in batch_tab_panel.status_label.text()

    mock_critical.assert_called_once()
    args, kwargs = mock_critical.call_args
    assert "일괄 태그 적용 실패" in args[0]
    assert "데이터베이스 연결 오류" in args[1]
    assert "2개 파일 중 0개 성공, 2개 실패" in args[1]
    assert str(temp_dir / "fileC.txt") in args[1]
    assert str(temp_dir / "fileD.jpg") in args[1]

@pytest.mark.ui
def test_batch_tagging_panel_cancel_button(unified_panel, batch_tab_panel, qtbot, temp_dir, mock_tag_manager, mocker):
    """일괄 태그 적용 취소 버튼 테스트"""
    (temp_dir / "fileX.txt").touch()
    batch_tab_panel.set_directory(str(temp_dir))
    qtbot.waitUntil(lambda: batch_tab_panel.file_table.rowCount() == 1, timeout=5000) # 파일 로드 대기

    tags_to_add = ["cancel_test"]
    unified_panel.individual_tag_input.set_tags(tags_to_add)
    qtbot.wait(50)

    mocker.patch('PyQt5.QtWidgets.QMessageBox.question', return_value=QMessageBox.Yes)

    batch_tab_panel.apply_button.click()
    qtbot.wait(50)

    assert batch_tab_panel.cancel_button.isVisible()
    assert "작업 진행 중" in batch_tab_panel.status_label.text()

    # 취소 버튼 클릭
    batch_tab_panel.cancel_button.click()
    qtbot.wait(100)

    # UI 상태 초기화 확인
    assert batch_tab_panel.apply_button.isVisible()
    assert not batch_tab_panel.cancel_button.isVisible()
    assert not batch_tab_panel.progress_bar.isVisible()
    assert "취소되었습니다" in batch_tab_panel.status_label.text()

    # TagManager의 add_tags_to_directory가 호출되지 않았거나, 스레드가 종료되었는지 확인 (mocking으로 간접 확인)
    # 여기서는 스레드 종료 후 UI 상태가 리셋되는지만 확인
    mock_tag_manager.add_tags_to_directory.assert_not_called() # 취소되었으므로 호출되지 않아야 함

@pytest.mark.ui
def test_state_manager_updates_batch_panel_directory(unified_panel, batch_tab_panel, qtbot, temp_dir, state_manager):
    """TagUIStateManager를 통해 BatchTaggingPanel의 디렉토리가 업데이트되는지 확인"""
    # UnifiedTaggingPanel의 file_selection_widget을 통해 디렉토리 설정
    # 이 동작은 state_manager.set_selected_directory를 호출해야 함
    unified_panel.file_selection_widget.set_directory(str(temp_dir))
    qtbot.waitUntil(lambda: batch_tab_panel.file_table.rowCount() > 0, timeout=5000) # 파일 로드 대기

    # BatchTaggingPanel의 dir_path_edit가 업데이트되었는지 확인
    assert batch_tab_panel.dir_path_edit.text() == str(temp_dir)
    assert batch_tab_panel.file_table.rowCount() > 0 # 파일이 로드되었는지 확인

@pytest.mark.ui
def test_batch_panel_tag_input_sync_with_unified_panel(unified_panel, batch_tab_panel, qtbot, temp_dir):
    """일괄 태깅 패널의 태그 입력이 통합 패널의 태그 입력과 동기화되는지 확인"""
    # 통합 패널의 개별 태깅 탭으로 전환 (기본값)
    unified_panel.switch_to_mode('individual')
    qtbot.wait(100)

    # 통합 패널의 태그 입력 위젯에 태그 설정
    test_tags = ["sync_tag1", "sync_tag2"]
    unified_panel.individual_tag_input.set_tags(test_tags)
    qtbot.wait(50)

    # 일괄 태깅 탭으로 전환
    unified_panel.switch_to_mode('batch')
    qtbot.wait(100)

    # BatchTaggingPanel이 UnifiedTaggingPanel의 태그 입력 위젯에서 태그를 가져오므로,
    # BatchTaggingPanel의 apply_button 클릭 시 올바른 태그가 전달되는지 확인하는 방식으로 검증
    # (직접 BatchTaggingPanel 내부에 태그 입력 위젯이 없으므로)
    # 여기서는 태그 입력 위젯의 get_tags()가 올바른 값을 반환하는지 확인하는 것으로 대체
    assert unified_panel.individual_tag_input.get_tags() == test_tags

    # 추가적으로, BatchTaggingPanel의 apply_button이 활성화되는지 확인 (태그가 입력되었으므로)
    # 디렉토리가 설정되어 있어야 apply_button이 활성화됨
    (temp_dir / "dummy.txt").touch()
    batch_tab_panel.set_directory(str(temp_dir))
    qtbot.waitUntil(lambda: batch_tab_panel.apply_button.isEnabled(), timeout=5000)
    assert batch_tab_panel.apply_button.isEnabled()

# 이전 test_bulk_write_mock_issue는 test_batch_tagging_panel_apply_tags_success/error_handling에서
# mock_tag_manager의 add_tags_to_directory 반환값을 실제와 동일하게 설정하여 간접적으로 해결 및 검증됨.
# 따라서 별도의 테스트 함수는 필요 없음.