import os
import logging
import config
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QMenu, QAbstractItemView, QVBoxLayout, QSpacerItem, QSizePolicy
from PyQt5.uic import loadUi
from PyQt5.QtCore import QDir, QModelIndex, QEvent, QItemSelectionModel

from widgets.directory_tree_widget import DirectoryTreeWidget
from widgets.file_list_widget import FileListWidget
from widgets.file_detail_widget import FileDetailWidget
from widgets.tag_control_widget import TagControlWidget
from widgets.search_widget import SearchWidget
from core.custom_tag_manager import CustomTagManager
from widgets.custom_tag_dialog import CustomTagDialog
from widgets.batch_remove_tags_dialog import BatchRemoveTagsDialog
from core.search_manager import SearchManager
from core.ui.ui_setup_manager import UISetupManager
from core.ui.signal_connection_manager import SignalConnectionManager
from core.ui.data_loading_manager import DataLoadingManager

# 새로 추가된 모듈 임포트
from core.events import EventBus
from core.repositories.tag_repository import TagRepository
from core.services.tag_service import TagService
from core.adapters.tag_manager_adapter import TagManagerAdapter
from viewmodels.tag_control_viewmodel import TagControlViewModel
from viewmodels.file_detail_viewmodel import FileDetailViewModel

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    def __init__(self, mongo_client):
        super().__init__()
        
        # --- 코어 로직 초기화 ---
        self.mongo_client = mongo_client
        
        # 새로운 아키텍처 컴포넌트 초기화
        self.event_bus = EventBus()
        self.tag_repository = TagRepository(mongo_client)
        self.tag_service = TagService(self.tag_repository, self.event_bus)
        self.tag_manager = TagManagerAdapter(self.tag_service) # TagManagerAdapter 사용
        
        self.custom_tag_manager = CustomTagManager()
        self.search_manager = SearchManager(self.tag_manager) # SearchManager는 TagManagerAdapter를 사용하도록 변경

        # ViewModel 초기화
        self.tag_control_viewmodel = TagControlViewModel(self.tag_service, self.event_bus)
        self.file_detail_viewmodel = FileDetailViewModel(self.tag_service, self.event_bus)

        # --- 분리된 관리자 클래스 활용 ---
        self.ui_setup = UISetupManager(self)
        self.ui_setup.setup_ui()

        self.signal_manager = SignalConnectionManager(self)
        self.signal_manager.connect_signals()

        self.data_loader = DataLoadingManager(self)
        self.data_loader.load_initial_data()

        self.statusbar.showMessage("준비 완료")
        self.show()

    def changeEvent(self, event):
        """창 상태 변경 이벤트를 처리하여 전체 화면 시 레이아웃을 조정합니다."""
        if event.type() == QEvent.WindowStateChange:
            if self.isMaximized():
                # 전체 화면: file_detail을 80%, file_list를 20%로 설정
                self.splitter.setSizes([int(self.height() * 0.8), int(self.height() * 0.2)])
            else:
                # 일반 화면: 50:50 비율로 복원
                self.splitter.setSizes([self.height() // 2, self.height() // 2])
        super().changeEvent(event)

    # setup_connections 메서드는 더 이상 사용되지 않지만, 기존 함수를 참조하는 코드 호환을 위해 남겨둡니다.
    def setup_connections(self):
        """호환성 유지용 래퍼: SignalConnectionManager가 시그널 연결을 담당합니다."""
        if not hasattr(self, 'signal_manager'):
            self.signal_manager = SignalConnectionManager(self)
        self.signal_manager.connect_signals()

    def set_workspace(self):
        current_workspace = config.DEFAULT_WORKSPACE_PATH if config.DEFAULT_WORKSPACE_PATH and os.path.isdir(config.DEFAULT_WORKSPACE_PATH) else QDir.homePath()
        new_workspace = QFileDialog.getExistingDirectory(self, "작업 공간 선택", current_workspace)
        if new_workspace:
            try:
                with open("config.py", "r", encoding="utf-8") as f:
                    lines = f.readlines()
                with open("config.py", "w", encoding="utf-8") as f:
                    for line in lines:
                        if line.startswith("DEFAULT_WORKSPACE_PATH ="):
                            cleaned_path = new_workspace.replace('\\', '/')
                            f.write(f'DEFAULT_WORKSPACE_PATH = "{cleaned_path}"\n')
                        else:
                            f.write(line)
                config.DEFAULT_WORKSPACE_PATH = new_workspace
                self.directory_tree.set_root_path(new_workspace)
                self.file_list.set_path(new_workspace)
                self.file_detail.clear_preview()
                self.tag_control_viewmodel.update_for_target(None, False)
                self.statusbar.showMessage(f"작업 공간이 '{new_workspace}'로 설정되었습니다.", 5000)
            except Exception as e:
                QMessageBox.critical(self, "오류", f"작업 공간 설정 중 오류가 발생했습니다: {e}")
                self.statusbar.showMessage("작업 공간 설정 실패", 3000)

    def on_directory_selected(self, index: QModelIndex):
        # Get the actual file system path from the clicked index
        file_path = self.directory_tree.model.filePath(self.directory_tree.proxy_model.mapToSource(index))

        # Determine if the selected item is a directory or a file
        is_dir = self.directory_tree.model.isDir(self.directory_tree.proxy_model.mapToSource(index))

        recursive = self.directory_tree.recursive_checkbox.isChecked()
        # extensions_input이 제거되었으므로 빈 리스트로 설정
        file_extensions = []

        if is_dir:
            # If a directory is selected, update the file list with its contents
            self.file_list.set_path(file_path, recursive, file_extensions)
            self.file_detail.clear_preview()
            self.tag_control_viewmodel.update_for_target(file_path, True)
            self.statusbar.showMessage(f"'{file_path}' 디렉토리를 보고 있습니다.")
        else:
            # If a file is selected, update file detail and select it in the file list
            self.file_detail.update_preview(file_path)
            self.tag_control.update_for_target(file_path, False)
            self.statusbar.showMessage(f"'{file_path}' 파일을 선택했습니다.")

            # Select the file in the file_list
            file_list_index = self.file_list.index_from_path(file_path)
            if file_list_index.isValid():
                self.file_list.list_view.selectionModel().select(
                    file_list_index, QItemSelectionModel.ClearAndSelect
                )
            else:
                # If the file is not in the current file_list view (e.g., due to filters),
                # update the file_list to show the directory containing the file
                parent_dir = os.path.dirname(file_path)
                self.file_list.set_path(parent_dir, recursive, file_extensions)
                # Try selecting again after updating the path
                file_list_index = self.file_list.index_from_path(file_path)
                if file_list_index.isValid():
                    self.file_list.list_view.selectionModel().select(
                        file_list_index, QItemSelectionModel.ClearAndSelect
                    )

    def _on_directory_tree_filter_options_changed(self, recursive: bool, file_extensions: list):
        # Get the currently selected directory in the directory tree
        # If no directory is selected, use the current file_list directory or default workspace
        selected_index = self.directory_tree.tree_view.currentIndex()
        if selected_index.isValid():
            current_path = self.directory_tree.model.filePath(self.directory_tree.proxy_model.mapToSource(selected_index))
            # If the selected item is a file, use its parent directory
            if not self.directory_tree.model.isDir(self.directory_tree.proxy_model.mapToSource(selected_index)):
                current_path = os.path.dirname(current_path)
        else:
            current_path = self.file_list.model.current_directory
            if not current_path:
                current_path = config.DEFAULT_WORKSPACE_PATH if config.DEFAULT_WORKSPACE_PATH and os.path.isdir(config.DEFAULT_WORKSPACE_PATH) else QDir.homePath()

        self.file_list.set_path(current_path, recursive, file_extensions)
        self.file_detail.clear_preview() # Clear preview as the file list content might change
        self.tag_control_viewmodel.update_for_target(None, False) # Clear tag control as the file list content might change
        self.statusbar.showMessage(f"필터 옵션 변경: 재귀={recursive}, 확장자={', '.join(file_extensions) if file_extensions else '모두'}")

    def on_file_selection_changed(self, selected: QModelIndex, deselected: QModelIndex):
        selected_indexes = self.file_list.list_view.selectionModel().selectedIndexes()
        selected_file_paths = []
        processed_rows = set()
        for index in selected_indexes:
            if index.row() not in processed_rows:
                file_path = self.file_list.model.get_file_path(index)
                if file_path:
                    selected_file_paths.append(file_path)
                processed_rows.add(index.row())
        if len(selected_file_paths) == 1:
            file_path = selected_file_paths[0]
            self.file_detail.update_preview(file_path)
            self.tag_control_viewmodel.update_for_target(file_path, False)
            self.statusbar.showMessage(f"'{file_path}' 파일을 선택했습니다.")
        elif len(selected_file_paths) > 1:
            self.file_detail.clear_preview()
            self.tag_control_viewmodel.update_for_target(selected_file_paths, False)
            self.statusbar.showMessage(f"{len(selected_file_paths)}개 파일을 선택했습니다.")
        else:
            self.file_detail.clear_preview()
            self.tag_control_viewmodel.update_for_target(None, False)
            self.statusbar.showMessage("파일 선택이 해제되었습니다.")

    def on_search_requested(self, search_conditions: dict):
        self.statusbar.showMessage("검색 중...")
        search_results = self.search_manager.search_files(search_conditions)
        self.file_list.set_search_results(search_results)
        # 검색 조건 요약 문자열 생성
        summary = ""
        if 'tags' in search_conditions:
            tag_cond = search_conditions['tags']
            tag_query = tag_cond.get('query', '').strip()
            if tag_query:
                summary = f"태그: '{tag_query}'"
        elif 'filename' in search_conditions:
            filename_cond = search_conditions['filename']
            search_text = filename_cond.get('name', '').strip()
            if search_text:
                summary = f"파일명: '{search_text}'"
        self.search_widget.update_search_results(len(search_results), summary)
        self.statusbar.showMessage(f"검색 완료: {len(search_results)}개 파일")

    def on_search_cleared(self):
        """검색 초기화 처리"""
        workspace_path = config.DEFAULT_WORKSPACE_PATH if config.DEFAULT_WORKSPACE_PATH and os.path.isdir(config.DEFAULT_WORKSPACE_PATH) else QDir.homePath()
        self.file_list.set_path(workspace_path)
        self.file_detail.clear_preview()
        self.tag_control_viewmodel.update_for_target(None, False)
        self.statusbar.showMessage("검색이 초기화되었습니다.")

    def on_advanced_search_requested(self, advanced_conditions: dict):
        """고급 검색 패널 표시/숨김 처리"""
        visible = advanced_conditions.get('visible', False)
        if hasattr(self, 'advanced_panel_widget'):
            self.advanced_panel_widget.setVisible(visible)

    def on_tags_updated(self):
        """태그 업데이트 시 파일 목록의 태그 정보를 새로고침합니다."""
        # 현재 선택된 디렉토리 경로 가져오기
        selected_index = self.directory_tree.tree_view.currentIndex()
        if selected_index.isValid():
            current_path = self.directory_tree.model.filePath(self.directory_tree.proxy_model.mapToSource(selected_index))
            # If the selected item is a file, use its parent directory
            if not self.directory_tree.model.isDir(self.directory_tree.proxy_model.mapToSource(selected_index)):
                current_path = os.path.dirname(current_path)
        else:
            current_path = self.file_list.model.current_directory
            if not current_path:
                current_path = config.DEFAULT_WORKSPACE_PATH if config.DEFAULT_WORKSPACE_PATH and os.path.isdir(config.DEFAULT_WORKSPACE_PATH) else QDir.homePath()

        # 파일 목록의 태그 정보만 새로고침 (선택 상태 유지)
        self.file_list.refresh_tags_for_current_files()
        # TagControlWidget의 ViewModel에서 태그 목록을 새로고침하도록 요청
        self.tag_control_viewmodel.update_completer_model()
        self.tag_control_viewmodel.update_all_tags_list()

    def open_custom_tag_dialog(self):
        """커스텀 태그 관리 다이얼로그를 엽니다."""
        dialog = CustomTagDialog(self.custom_tag_manager, self)
        if dialog.exec_() == CustomTagDialog.Accepted:
            # 커스텀 태그가 변경되었으므로 빠른 태그 위젯들을 새로고침
            # 이 로직은 이제 TagControlWidget 내부에서 ViewModel을 통해 처리됩니다.
            self.statusbar.showMessage("빠른 태그가 업데이트되었습니다.", 3000)

    def on_directory_tree_context_menu(self, directory_path, global_pos):
        """디렉토리 트리 컨텍스트 메뉴 처리"""
        menu = QMenu(self)
        batch_remove_action = menu.addAction("일괄 태그 제거...")
        action = menu.exec_(global_pos)
        
        if action == batch_remove_action:
            self._open_batch_remove_tags_dialog(directory_path)

    def _open_batch_remove_tags_dialog(self, target_path):
        """일괄 태그 제거 다이얼로그를 엽니다."""
        # BatchRemoveTagsDialog에 TagManagerAdapter 인스턴스를 전달
        dialog = BatchRemoveTagsDialog(self.tag_manager, target_path, True, self)
        if dialog.exec_() == BatchRemoveTagsDialog.Accepted:
            self.on_tags_updated()
            self.statusbar.showMessage("일괄 태그 제거가 완료되었습니다.", 3000)