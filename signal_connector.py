# signal_connector.py
import os
from PyQt5.QtCore import QModelIndex
from PyQt5.QtWidgets import QFileDialog

from core.tag_ui_state_manager import TagUIStateManager
from core.tag_manager import TagManager


class SignalConnector:
    def __init__(self, main_window, tag_manager: TagManager, state_manager: TagUIStateManager):
        self.main_window = main_window
        self.tag_manager = tag_manager
        self.state_manager = state_manager
        self.current_path = "" # 초기 경로 설정

    def connect_all_signals(self):
        """모든 시그널과 슬롯을 연결합니다."""
        # 메뉴 액션 시그널
        self.main_window.open_dir_action.triggered.connect(self.open_directory_dialog)
        self.main_window.individual_mode_action.triggered.connect(lambda: self.switch_tagging_mode('individual'))
        self.main_window.batch_mode_action.triggered.connect(lambda: self.switch_tagging_mode('batch'))
        self.main_window.clear_filter_action.triggered.connect(self.clear_filter)

        # 디렉토리 트리뷰 선택 시그널
        self.main_window.tree_view_dirs.clicked.connect(self.on_directory_tree_clicked)

        # 파일 선택 및 미리보기 위젯 시그널
        self.main_window.file_selection_and_preview_widget.file_selected.connect(self.on_file_selected)

        # 통합 태깅 패널 시그널
        self.main_window.unified_tagging_panel.mode_changed.connect(self.on_tagging_mode_changed)
        self.main_window.unified_tagging_panel.tags_applied.connect(self.on_tags_applied)

        # 상태 관리자 시그널
        self.state_manager.state_changed.connect(self.on_state_changed)

    def on_directory_tree_clicked(self, index: QModelIndex):
        """디렉토리 트리뷰에서 디렉토리가 선택될 때 호출됩니다."""
        path = self.main_window.dir_model.filePath(index)
        if os.path.isdir(path):
            self.current_path = path
            self.main_window.file_selection_and_preview_widget.set_directory(path)
            self.state_manager.set_selected_directory(path)
            self.main_window.statusBar().showMessage(f"디렉토리 변경: {path}", 3000)

    def open_directory_dialog(self):
        """디렉토리 선택 대화상자를 엽니다."""
        directory = QFileDialog.getExistingDirectory(
            self.main_window, 
            "디렉토리 선택", 
            self.current_path
        )
        if directory:
            self.current_path = directory
            self.main_window.file_selection_and_preview_widget.set_directory(directory)
            self.state_manager.set_selected_directory(directory)
            self.main_window.statusBar().showMessage(f"디렉토리 변경: {directory}", 3000)

    def switch_tagging_mode(self, mode):
        """태깅 모드를 전환합니다."""
        try:
            if self.main_window.unified_tagging_panel:
                self.main_window.unified_tagging_panel.switch_to_mode(mode)
                self.main_window.statusBar().showMessage(f"모드 변경: {mode}", 2000)
        except Exception as e:
            print(f"[SignalConnector] 모드 전환 중 오류: {e}")
            self.main_window.statusBar().showMessage(f"모드 전환 실패: {str(e)}", 3000)

    def on_tagging_mode_changed(self, mode):
        """태깅 모드가 변경될 때 호출됩니다."""
        # 메뉴 상태 업데이트
        self.main_window.individual_mode_action.setChecked(mode == 'individual')
        self.main_window.batch_mode_action.setChecked(mode == 'batch')
        
        # 상태바 메시지
        mode_text = "개별 태깅" if mode == 'individual' else "일괄 태깅"
        self.main_window.statusBar().showMessage(f"{mode_text} 모드로 전환되었습니다", 2000)

    def on_file_selected(self, file_path, tags=None):
        """파일이 선택될 때 호출됩니다."""
        if file_path:
            self.state_manager.set_selected_files([file_path])
            self.state_manager.set_current_file_tags(tags if tags is not None else [])
            self.main_window.statusBar().showMessage(f"파일 선택: {os.path.basename(file_path)}", 2000)
        else:
            self.state_manager.set_selected_files([])
            self.state_manager.set_current_file_tags([])
            self.main_window.statusBar().showMessage("파일 선택 해제", 1000)

    def on_tags_applied(self, file_path, tags):
        """태그가 적용될 때 호출됩니다."""
        tag_text = ", ".join(tags) if tags else "없음"
        self.main_window.statusBar().showMessage(
            f"태그 적용 완료 - {os.path.basename(file_path)}: {tag_text}", 
            3000
        )
        
        # 태그 자동 완성 모델 업데이트 (안전하게)
        try:
            if hasattr(self.main_window, 'unified_tagging_panel') and self.main_window.unified_tagging_panel:
                self.main_window.unified_tagging_panel.update_tag_autocomplete()
            
            # 가운데 섹션의 파일 목록 태그 정보 업데이트
            if hasattr(self.main_window, 'file_selection_and_preview_widget') and self.main_window.file_selection_and_preview_widget:
                self.main_window.file_selection_and_preview_widget.refresh_file_tags(file_path)
        except Exception as e:
            import traceback
            print(f"[SignalConnector] 태그 적용 후 자동 완성 업데이트 중 오류: {e}")
            traceback.print_exc()

    def on_state_changed(self, state):
        """상태 관리자의 상태가 변경될 때 호출됩니다."""
        # 현재는 상태 변경을 로깅만 함 (필요시 UI 업데이트 로직 추가)
        mode = state.get('mode', 'unknown')
        files_count = len(state.get('selected_files', []))
        
        # 일괄 태깅 옵션 위젯의 가시성 제어
        if mode == 'batch':
            self.main_window.batch_tagging_options_widget.setVisible(True)
        else:
            self.main_window.batch_tagging_options_widget.setVisible(False)

        # 디버깅용 로그 (필요시 제거)
        # print(f"[SignalConnector] 상태 변경 - 모드: {mode}, 선택된 파일: {files_count}개")

    def clear_filter(self):
        """필터를 초기화합니다."""
        # self.is_filtered = False # MainWindow에서 관리하던 변수이므로 제거
        self.main_window.clear_filter_action.setEnabled(False)
        self.state_manager.set_filter_mode(False)
        self.main_window.statusBar().showMessage("필터가 초기화되었습니다", 2000)
