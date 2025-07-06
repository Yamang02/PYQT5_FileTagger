# signal_connector.py
import os
from PyQt5.QtCore import QModelIndex, Qt
from PyQt5.QtWidgets import QFileDialog, QAction

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
        self.main_window.findChild(QAction, 'action_open_directory').triggered.connect(self.open_directory_dialog)
        self.main_window.findChild(QAction, 'action_individual_mode').triggered.connect(lambda: self.switch_tagging_mode('individual'))
        self.main_window.findChild(QAction, 'action_batch_mode').triggered.connect(lambda: self.switch_tagging_mode('batch'))
        self.main_window.findChild(QAction, 'action_clear_filter').triggered.connect(self.clear_filter)

        # 디렉토리 트리뷰 선택 시그널
        self.main_window.treeView_dirs.clicked.connect(self.on_directory_tree_clicked)

        # 파일 테이블뷰 선택 시그널
        self.main_window.tableView_files.selectionModel().selectionChanged.connect(self.on_file_selection_changed)

        # 탭 위젯 변경 시그널
        self.main_window.tabWidget_tagging.currentChanged.connect(self.on_tab_changed)

        # UnifiedTaggingPanel 시그널 (개별 태깅 탭)
        self.main_window.unifiedTaggingPanel_individual.tags_applied.connect(self.on_tags_applied)

        # UnifiedTaggingPanel 시그널 (일괄 태깅 탭)
        self.main_window.unifiedTaggingPanel_batch.tags_applied.connect(self.on_tags_applied)

        # 상태 관리자 시그널
        self.state_manager.state_changed.connect(self.on_state_changed)

    def on_directory_tree_clicked(self, index: QModelIndex):
        """디렉토리 트리뷰에서 디렉토리가 선택될 때 호출됩니다."""
        path = self.main_window.dir_model.filePath(index)
        if os.path.isdir(path):
            self.current_path = path
            self.main_window.file_model.set_directory(path)
            self.state_manager.set_selected_directory(path)
            
            # UnifiedTaggingPanel 업데이트 (개별/일괄 모두)
            self.main_window.unifiedTaggingPanel_individual.update_target(path, is_dir=True)
            self.main_window.unifiedTaggingPanel_batch.update_target(path, is_dir=True)
            

            self.main_window.statusBar().showMessage(f"디렉토리 변경: {path}", 3000)

    def on_file_selection_changed(self, selected, deselected):
        """파일 테이블뷰에서 선택이 변경될 때 호출됩니다."""
        indexes = selected.indexes()
        if not indexes:
            self.state_manager.set_selected_files([])
            self.main_window.unifiedTaggingPanel_individual.update_target(None, is_dir=False)
            self.main_window.unifiedTaggingPanel_batch.update_target(None, is_dir=False)

            return

        # 첫 번째 선택된 파일만 처리 (단일 선택 모드 가정)
        index = indexes[0]
        file_path = self.main_window.file_model.data(index, Qt.UserRole)

        if file_path and os.path.isfile(file_path):
            tags = self.tag_manager.get_tags_for_file(file_path)
            self.state_manager.set_selected_files([file_path])
            self.state_manager.set_current_file_tags(tags if tags is not None else [])
            
            # UnifiedTaggingPanel 업데이트 (개별/일괄 모두)
            self.main_window.unifiedTaggingPanel_individual.update_target(file_path, is_dir=False)
            self.main_window.unifiedTaggingPanel_batch.update_target(file_path, is_dir=False)
            
            self.update_file_details(file_path)
            self.main_window.statusBar().showMessage(f"파일 선택: {os.path.basename(file_path)}", 2000)

    def update_file_details(self, file_path):
        """선택된 파일의 상세 정보를 업데이트합니다."""
        if not file_path or not os.path.exists(file_path):
            return

        try:
            file_info = f"<b>파일 이름:</b> {os.path.basename(file_path)}<br>"
            file_info += f"<b>경로:</b> {file_path}<br>"
            file_size = os.path.getsize(file_path)
            file_info += f"<b>크기:</b> {file_size / 1024:.2f} KB<br>"
            # self.main_window.textBrowser_file_details.setHtml(file_info) # 제거
        except Exception as e:
            # self.main_window.textBrowser_file_details.setText(f"파일 정보 로드 오류: {e}") # 제거
            pass

    def on_tab_changed(self, index):
        """태깅 탭이 변경될 때 호출됩니다."""
        tab_text = self.main_window.tabWidget_tagging.tabText(index)
        if tab_text == "개별 태깅":
            self.state_manager.set_mode('individual')
        elif tab_text == "일괄 태깅":
            self.state_manager.set_mode('batch')
        self.main_window.statusBar().showMessage(f"{tab_text} 모드로 전환되었습니다", 2000)

    def open_directory_dialog(self):
        """디렉토리 선택 대화상자를 엽니다."""
        directory = QFileDialog.getExistingDirectory(
            self.main_window, 
            "디렉토리 선택", 
            self.current_path
        )
        if directory:
            self.current_path = directory
            self.main_window.file_model.set_directory(directory)
            self.state_manager.set_selected_directory(directory)
            self.main_window.statusBar().showMessage(f"디렉토리 변경: {directory}", 3000)

    def switch_tagging_mode(self, mode):
        """태깅 모드를 전환합니다."""
        # 탭 위젯을 통해 모드 전환을 제어하므로, 이 메소드는 탭 위젯의 currentChanged 시그널에 연결될 필요가 없습니다.
        # 대신, 메뉴 액션에서 직접 탭을 변경하도록 합니다.
        if mode == 'individual':
            self.main_window.tabWidget_tagging.setCurrentIndex(0)
        elif mode == 'batch':
            self.main_window.tabWidget_tagging.setCurrentIndex(1)
        self.main_window.statusBar().showMessage(f"모드 변경: {mode}", 2000)

    def on_tagging_mode_changed(self, mode):
        """태깅 모드가 변경될 때 호출됩니다."""
        # 메뉴 상태 업데이트
        self.main_window.findChild(QAction, 'action_individual_mode').setChecked(mode == 'individual')
        self.main_window.findChild(QAction, 'action_batch_mode').setChecked(mode == 'batch')
        
        # 상태바 메시지
        mode_text = "개별 태깅" if mode == 'individual' else "일괄 태깅"
        self.main_window.statusBar().showMessage(f"{mode_text} 모드로 전환되었습니다", 2000)

    def on_tags_applied(self, file_path, tags):
        """태그가 적용될 때 호출됩니다."""
        tag_text = ", ".join(tags) if tags else "없음"
        self.main_window.statusBar().showMessage(
            f"태그 적용 완료 - {os.path.basename(file_path)}: {tag_text}", 
            3000
        )
        
        # 태그 자동 완성 모델 업데이트 (안전하게)
        try:
            # 현재 활성화된 UnifiedTaggingPanel의 update_tag_autocomplete 호출
            current_panel = self.main_window.tabWidget_tagging.currentWidget().findChild(UnifiedTaggingPanel)
            if current_panel:
                current_panel.update_tag_autocomplete()
            
            # 가운데 섹션의 파일 목록 태그 정보 업데이트
            # file_selection_and_preview_widget이 없으므로 file_model을 직접 사용
            self.main_window.file_model.refresh_file_tags(file_path)
        except Exception as e:
            import traceback
            print(f"[SignalConnector] 태그 적용 후 자동 완성 업데이트 중 오류: {e}")
            traceback.print_exc()

    def on_state_changed(self, state):
        """상태 관리자의 상태가 변경될 때 호출됩니다."""
        # 현재는 상태 변경을 로깅만 함 (필요시 UI 업데이트 로직 추가)
        mode = state.get('mode', 'unknown')
        files_count = len(state.get('selected_files', []))
        
        # 디버깅용 로그 (필요시 제거)
        # print(f"[SignalConnector] 상태 변경 - 모드: {mode}, 선택된 파일: {files_count}개")

    def clear_filter(self):
        """필터를 초기화합니다."""
        # self.is_filtered = False # MainWindow에서 관리하던 변수이므로 제거
        self.main_window.findChild(QAction, 'action_clear_filter').setEnabled(False)
        self.state_manager.set_filter_mode(False)
        self.main_window.statusBar().showMessage("필터가 초기화되었습니다", 2000)