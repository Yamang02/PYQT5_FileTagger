import pytest
from PyQt5.QtWidgets import QApplication, QFileDialog, QTableWidgetItem, QMessageBox
from PyQt5.QtCore import Qt, QTimer
from main_window import MainWindow
from widgets.batch_tagging_panel import BatchTaggingPanel
from core.tag_manager import TagManager
from unittest.mock import MagicMock, patch
from pytest_mock import MockerFixture
import os

# Mock TagManager for UI tests
@pytest.fixture(scope="function")
def mock_tag_manager():
    """MagicMock을 사용하여 TagManager를 모의(Mock)합니다."""
    manager = MagicMock(spec=TagManager)
    manager.get_tags_for_file.return_value = []
    manager.get_all_unique_tags.return_value = []
    manager.add_tags_to_directory.return_value = {"success": True, "processed": 0, "successful": 0, "failed": 0, "modified": 0, "upserted": 0, "errors": []}
    manager.get_connection_status.return_value = {"connected": True, "status": "정상"}
    return manager

@pytest.fixture(scope="function")
def main_window(qtbot, mock_tag_manager):
    """테스트용 MainWindow 인스턴스를 생성하고 초기화합니다."""
    # TagManager를 mock 객체로 교체
    window = MainWindow()
    window.tag_manager = mock_tag_manager
    window.show()
    qtbot.addWidget(window)
    # 비동기 초기화 완료 대기
    qtbot.wait(100) 
    return window

@pytest.fixture(scope="function")
def batch_tagging_panel(main_window, qtbot):
    """BatchTaggingPanel을 활성화하고 반환합니다."""
    main_window.batch_tag_action.trigger()
    qtbot.wait(50) # UI 업데이트 대기
    return main_window.batch_tagging_panel

@pytest.mark.integration
@pytest.mark.ui
def test_batch_tagging_panel_visibility(main_window, qtbot):
    """일괄 태그 패널이 메뉴 액션에 따라 올바르게 표시/숨김되는지 테스트"""
    panel_container = main_window.batch_panel_container
    batch_tagging_panel = main_window.batch_tagging_panel

    # 초기에는 패널이 숨겨져 있어야 함
    assert not panel_container.isVisible()
    assert not batch_tagging_panel.isVisible()

    # '일괄 태그 추가' 메뉴 액션 트리거
    main_window.batch_tag_action.trigger()
    qtbot.wait(50) # UI 업데이트 대기

    # 패널이 표시되어야 함
    assert panel_container.isVisible()
    assert batch_tagging_panel.isVisible()
    assert "일괄 태그 패널이 열렸습니다" in main_window.statusbar.currentMessage()

    # 현재는 닫는 기능이 없으므로, 이 테스트는 패널이 열리는 것만 확인
    # TODO: 패널 닫는 기능 추가 시 테스트 확장

@pytest.mark.integration
@pytest.mark.ui
def test_batch_tagging_panel_directory_selection(batch_tagging_panel, qtbot, tmp_path):
    """디렉토리 선택 및 파일 미리보기 업데이트 테스트"""
    # 테스트용 임시 디렉토리 및 파일 생성
    test_dir = tmp_path / "test_batch_dir"
    test_dir.mkdir()
    (test_dir / "file1.txt").touch()
    (test_dir / "image.jpg").touch()
    (test_dir / "document.pdf").touch()

    # QFileDialog.getExistingDirectory를 모의(Mock)하여 특정 경로를 반환하도록 설정
    with patch.object(QFileDialog, 'getExistingDirectory', return_value=str(test_dir)) as mock_get_dir:
        batch_tagging_panel.browse_button.click()
        
        # status_label의 텍스트가 "3개 파일 준비됨"을 포함할 때까지 기다림
        qtbot.waitUntil(lambda: "3개 파일 준비됨" in batch_tagging_panel.status_label.text(), timeout=1000)

        # 디렉토리 선택 다이얼로그가 호출되었는지 확인
        mock_get_dir.assert_called_once()

        # dir_path_edit에 경로가 올바르게 설정되었는지 확인
        assert batch_tagging_panel.dir_path_edit.text() == str(test_dir)

        # file_table에 파일 목록이 올바르게 채워졌는지 확인
        assert batch_tagging_panel.file_table.rowCount() == 3
        # 파일명은 순서가 보장되지 않으므로, 존재하는지 여부만 확인
        expected_files = {"file1.txt", "image.jpg", "document.pdf"}
        actual_files = {batch_tagging_panel.file_table.item(i, 0).text() for i in range(3)}
        assert actual_files == expected_files

        # file_count_label이 올바르게 업데이트되었는지 확인
        assert batch_tagging_panel.file_count_label.text() == "3개 파일"
        assert "3개 파일 준비됨" in batch_tagging_panel.status_label.text()

@pytest.mark.integration
@pytest.mark.ui
def test_batch_tagging_panel_recursive_option(batch_tagging_panel, qtbot, tmp_path):
    """재귀 옵션에 따른 파일 미리보기 업데이트 테스트"""
    # 테스트용 임시 디렉토리 및 파일 생성
    test_dir = tmp_path / "test_recursive_dir"
    test_dir.mkdir()
    (test_dir / "file1.txt").touch()
    sub_dir = test_dir / "subdir"
    sub_dir.mkdir()
    (sub_dir / "subfile1.txt").touch()
    (sub_dir / "subfile2.jpg").touch()

    # 디렉토리 설정
    batch_tagging_panel.set_directory(str(test_dir))
    qtbot.wait(50)

    # 초기 (비재귀) 상태 확인
    assert batch_tagging_panel.file_table.rowCount() == 1 # file1.txt만 포함
    assert batch_tagging_panel.file_count_label.text() == "1개 파일"

    # 재귀 옵션 활성화
    batch_tagging_panel.recursive_checkbox.setChecked(True)
    qtbot.wait(100) # UI 업데이트 대기

    # 재귀 상태 확인 (모든 파일 포함)
    assert batch_tagging_panel.file_table.rowCount() == 3
    assert batch_tagging_panel.file_count_label.text() == "3개 파일"
    file_names = [batch_tagging_panel.file_table.item(i, 0).text() for i in range(3)]
    assert "file1.txt" in file_names
    assert "subfile1.txt" in file_names
    assert "subfile2.jpg" in file_names

@pytest.mark.integration
@pytest.mark.ui
def test_batch_tagging_panel_extension_filter(batch_tagging_panel, qtbot, tmp_path):
    """확장자 필터링에 따른 파일 미리보기 업데이트 테스트"""
    # 테스트용 임시 디렉토리 및 파일 생성
    test_dir = tmp_path / "test_filter_dir"
    test_dir.mkdir()
    (test_dir / "doc.txt").touch()
    (test_dir / "image.png").touch()
    (test_dir / "report.pdf").touch()
    (test_dir / "script.py").touch()

    # 디렉토리 설정
    batch_tagging_panel.set_directory(str(test_dir))
    qtbot.wait(50)

    # 초기 (모든 파일) 상태 확인
    assert batch_tagging_panel.file_table.rowCount() == 4

    # 이미지 파일 필터링
    batch_tagging_panel.ext_combo.setCurrentText("이미지 파일")
    qtbot.wait(100)
    assert batch_tagging_panel.file_table.rowCount() == 1
    assert batch_tagging_panel.file_table.item(0, 0).text() == "image.png"

    # 문서 파일 필터링
    batch_tagging_panel.ext_combo.setCurrentText("문서 파일")
    qtbot.wait(100)
    assert batch_tagging_panel.file_table.rowCount() == 2
    file_names = [batch_tagging_panel.file_table.item(i, 0).text() for i in range(2)]
    assert "doc.txt" in file_names
    assert "report.pdf" in file_names

    # 사용자 정의 확장자 필터링 (.py)
    batch_tagging_panel.ext_combo.setCurrentText("사용자 정의")
    batch_tagging_panel.custom_ext_edit.setText(".py")
    qtbot.wait(100)
    assert batch_tagging_panel.file_table.rowCount() == 1
    assert batch_tagging_panel.file_table.item(0, 0).text() == "script.py"

    # 사용자 정의 확장자 필터링 (.txt, .pdf)
    batch_tagging_panel.custom_ext_edit.setText(".txt,.pdf")
    qtbot.wait(100)
    assert batch_tagging_panel.file_table.rowCount() == 2
    file_names = [batch_tagging_panel.file_table.item(i, 0).text() for i in range(2)]
    assert "doc.txt" in file_names
    assert "report.pdf" in file_names

    # 모든 파일로 다시 변경
    batch_tagging_panel.ext_combo.setCurrentText("모든 파일")
    qtbot.wait(100)
    assert batch_tagging_panel.file_table.rowCount() == 4

@pytest.mark.integration
@pytest.mark.ui
def test_batch_tagging_panel_apply_tags(batch_tagging_panel, qtbot, tmp_path, mock_tag_manager, mocker):
    """태그 입력 및 적용 기능 테스트"""
    # 테스트용 임시 디렉토리 및 파일 생성
    test_dir = tmp_path / "test_apply_tags_dir"
    test_dir.mkdir()
    (test_dir / "fileA.txt").touch()
    (test_dir / "fileB.jpg").touch()

    # 디렉토리 설정
    batch_tagging_panel.set_directory(str(test_dir))
    qtbot.waitUntil(lambda: "2개 파일 준비됨" in batch_tagging_panel.status_label.text(), timeout=1000)

    # 태그 입력
    tags_to_add = ["new_tag1", "new_tag2"]
    for tag in tags_to_add:
        batch_tagging_panel.tag_input_widget.tag_input.setText(tag)
        qtbot.keyPress(batch_tagging_panel.tag_input_widget.tag_input, Qt.Key_Return)
        qtbot.wait(50)

    # 입력된 태그 확인
    assert batch_tagging_panel.tag_input_widget.get_tags() == tags_to_add

    # apply_button 클릭
    batch_tagging_panel.apply_button.click()
    qtbot.wait(200) # UI 업데이트 대기 시간을 늘림

    # UI 상태 확인 (작업 진행 중)
    assert not batch_tagging_panel.apply_button.isVisible()
    assert batch_tagging_panel.cancel_button.isVisible()
    assert batch_tagging_panel.progress_bar.isVisible()
    assert "작업 진행 중" in batch_tagging_panel.status_label.text()

    # add_tags_to_directory가 올바른 인자로 호출되었는지 확인
    mock_tag_manager.add_tags_to_directory.assert_called_once_with(
        str(test_dir),
        tags_to_add,
        False, # recursive 기본값
        None   # file_extensions 기본값
    )

    # Mock QMessageBox methods
    mock_information = mocker.patch('PyQt5.QtWidgets.QMessageBox.information', return_value=QMessageBox.Ok)
    mock_warning = mocker.patch('PyQt5.QtWidgets.QMessageBox.warning', return_value=QMessageBox.Ok)
    mock_critical = mocker.patch('PyQt5.QtWidgets.QMessageBox.critical', return_value=QMessageBox.Ok)

    # 작업 완료 시그널을 수동으로 발생시켜 테스트 진행
    # (실제 스레드 동작을 기다리지 않고 mock 결과를 바로 반영)
    mock_tag_manager.add_tags_to_directory.return_value = {
        "success": True,
        "processed": 2,
        "successful": 2,
        "failed": 0,
        "modified": 2,
        "upserted": 0,
        "errors": []
    }
    batch_tagging_panel.worker_thread.work_finished.emit(
        mock_tag_manager.add_tags_to_directory.return_value
    )
    qtbot.wait(100) # UI 업데이트 대기

    # 작업 완료 후 UI 상태 확인
    assert batch_tagging_panel.apply_button.isVisible()
    assert not batch_tagging_panel.cancel_button.isVisible()
    assert not batch_tagging_panel.progress_bar.isVisible()
    assert "✅ 완료" in batch_tagging_panel.status_label.text()

    # Assert that the correct QMessageBox method was called
    mock_information.assert_called_once()
    mock_warning.assert_not_called()
    mock_critical.assert_not_called()

@pytest.mark.integration
@pytest.mark.ui
def test_batch_tagging_panel_apply_tags_error_handling(batch_tagging_panel, qtbot, tmp_path, mock_tag_manager, mocker):
    """태그 적용 중 오류 발생 시 UI 동작 테스트"""
    # 테스트용 임시 디렉토리 및 파일 생성
    test_dir = tmp_path / "test_apply_tags_error_dir"
    test_dir.mkdir()
    (test_dir / "fileC.txt").touch()
    (test_dir / "fileD.jpg").touch()

    # 디렉토리 설정
    batch_tagging_panel.set_directory(str(test_dir))
    qtbot.waitUntil(lambda: "2개 파일 준비됨" in batch_tagging_panel.status_label.text(), timeout=1000)

    # 태그 입력
    tags_to_add = ["error_tag"]
    for tag in tags_to_add:
        batch_tagging_panel.tag_input_widget.tag_input.setText(tag)
        qtbot.keyPress(batch_tagging_panel.tag_input_widget.tag_input, Qt.Key_Return)
        qtbot.wait(50)

    # apply_button 클릭
    batch_tagging_panel.apply_button.click()
    qtbot.wait(50)

    # Mock QMessageBox methods
    mock_information = mocker.patch('PyQt5.QtWidgets.QMessageBox.information', return_value=QMessageBox.Ok)
    mock_warning = mocker.patch('PyQt5.QtWidgets.QMessageBox.warning', return_value=QMessageBox.Ok)
    mock_critical = mocker.patch('PyQt5.QtWidgets.QMessageBox.critical', return_value=QMessageBox.Ok)

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
            {"file": str(test_dir / "fileC.txt"), "error": "DB write error"},
            {"file": str(test_dir / "fileD.jpg"), "error": "Permission denied"}
        ]
    }
    batch_tagging_panel.worker_thread.work_finished.emit(
        mock_tag_manager.add_tags_to_directory.return_value
    )
    qtbot.wait(100)

    # 작업 완료 후 UI 상태 확인
    assert batch_tagging_panel.apply_button.isVisible()
    assert not batch_tagging_panel.cancel_button.isVisible()
    assert not batch_tagging_panel.progress_bar.isVisible()
    assert "❌ 오류" in batch_tagging_panel.status_label.text()

    # Assert that the critical QMessageBox method was called with the error message
    mock_critical.assert_called_once()
    args, kwargs = mock_critical.call_args
    assert "일괄 태그 추가 중 오류 발생" in args[1]
    assert "데이터베이스 연결 오류" in args[1]
    assert "2개 파일 중 0개 성공, 2개 실패" in args[1]
    assert str(test_dir / "fileC.txt") in args[1]
    assert str(test_dir / "fileD.jpg") in args[1]

    mock_information.assert_not_called()
    mock_warning.assert_not_called()
