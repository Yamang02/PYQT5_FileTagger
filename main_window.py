import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QMessageBox, QMenu
from PyQt5.uic import loadUi
from PyQt5.QtCore import QDir, QModelIndex, Qt, QEvent
from PyQt5.QtGui import QKeySequence
import os
import config
import logging

logger = logging.getLogger(__name__)

# 위젯 임포트
from widgets.directory_tree_widget import DirectoryTreeWidget
from widgets.file_list_widget import FileListWidget
from widgets.file_detail_widget import FileDetailWidget
from widgets.tag_control_widget import TagControlWidget


# 코어 로직 임포트
from core.tag_manager import TagManager
from core.custom_tag_manager import CustomTagManager
from widgets.custom_tag_dialog import CustomTagDialog
from widgets.batch_remove_tags_dialog import BatchRemoveTagsDialog

class MainWindow(QMainWindow):
    def __init__(self, file_server):
        super().__init__()
        loadUi('ui/main_window.ui', self)

        # --- 코어 로직 초기화 ---
        self.tag_manager = TagManager()
        self.custom_tag_manager = CustomTagManager()

        # --- 위젯 인스턴스 생성 ---
        initial_workspace = config.DEFAULT_WORKSPACE_PATH if config.DEFAULT_WORKSPACE_PATH and os.path.isdir(config.DEFAULT_WORKSPACE_PATH) else QDir.homePath()
        self.directory_tree = DirectoryTreeWidget(initial_workspace)
        self.file_list = FileListWidget(self.tag_manager)
        # FileDetailWidget에 file_server 인스턴스 전달
        self.file_detail = FileDetailWidget(self.tag_manager, file_server)
        self.tag_control = TagControlWidget(self.tag_manager, self.custom_tag_manager)

        # --- 3열 레이아웃 구성 (QSplitter 사용) ---
        self.mainSplitter.insertWidget(0, self.directory_tree)
        self.mainSplitter.insertWidget(1, self.splitter)
        self.mainSplitter.insertWidget(2, self.tag_control)
        self.directoryTreeWidget.deleteLater()
        self.tagControlWidget.deleteLater()

        # 2열: 파일 상세 정보(상)와 파일 목록(하)을 담는 Splitter
        self.splitter.insertWidget(0, self.file_detail)
        self.splitter.insertWidget(1, self.file_list)
        self.fileDetailWidget.deleteLater()
        self.fileListWidget.deleteLater()

        # 초기 크기 설정
        self.mainSplitter.setSizes([150, self.width() - 300, 150])
        self.splitter.setSizes([self.height() // 2, self.height() // 2])

        # --- 연결 설정 ---
        self.setup_connections()
        self.statusbar.showMessage("준비 완료")
        self.show()

    def changeEvent(self, event):
        """창 상태 변경 이벤트를 처리하여 전체 화면 시 레이아웃을 조정합니다."""
        if event.type() == QEvent.WindowStateChange:
            if self.isMaximized():
                # 전체 화면: file_detail을 80%, file_list를 20%로 설정
                self.splitter.setSizes([self.height() * 0.8, self.height() * 0.2])
            else:
                # 일반 화면: 50:50 비율로 복원
                self.splitter.setSizes([self.height() // 2, self.height() // 2])
        super().changeEvent(event)

    def setup_connections(self):
        self.actionExit.triggered.connect(self.close)
        self.actionSetWorkspace.triggered.connect(self.set_workspace)
        self.actionManageQuickTags.triggered.connect(self.open_custom_tag_dialog)
        self.directory_tree.tree_view.clicked.connect(self.on_directory_selected)
        self.directory_tree.filter_options_changed.connect(self.on_directory_selected)
        self.file_list.list_view.selectionModel().selectionChanged.connect(self.on_file_selection_changed)
        self.directory_tree.tag_filter_changed.connect(self.file_list.set_tag_filter)
        self.directory_tree.global_file_search_requested.connect(self.on_global_file_search_requested)
        self.tag_control.tags_updated.connect(self.on_tags_updated)
        self.file_detail.file_tags_changed.connect(self.on_tags_updated)
        self.directory_tree.directory_context_menu_requested.connect(self.on_directory_tree_context_menu)

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
                self.tag_control.clear_view()
                self.statusbar.showMessage(f"작업 공간이 '{new_workspace}'로 설정되었습니다.", 5000)
            except Exception as e:
                QMessageBox.critical(self, "오류", f"작업 공간 설정 중 오류가 발생했습니다: {e}")
                self.statusbar.showMessage("작업 공간 설정 실패", 3000)

    def on_directory_selected(self, *args):
        path = None
        recursive = self.directory_tree.recursive_checkbox.isChecked()
        extensions_text = self.directory_tree.extensions_input.text().strip()
        file_extensions = [ext.strip() for ext in extensions_text.split(',') if ext.strip()]
        if isinstance(args[0], QModelIndex):
            index = args[0]
            path = self.directory_tree.model.filePath(self.directory_tree.proxy_model.mapToSource(index))
        else:
            path = self.file_list.model.current_directory
            if not path:
                path = config.DEFAULT_WORKSPACE_PATH if config.DEFAULT_WORKSPACE_PATH and os.path.isdir(config.DEFAULT_WORKSPACE_PATH) else QDir.homePath()
        if path:
            self.file_list.set_path(path, recursive, file_extensions)
            self.file_detail.clear_preview()
            self.tag_control.update_for_target(path, True)
            self.statusbar.showMessage(f"'{path}' 디렉토리를 보고 있습니다.")
        else:
            self.statusbar.showMessage("디렉토리를 선택해주세요.")

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
            self.tag_control.update_for_target(file_path, False)
            self.statusbar.showMessage(f"'{file_path}' 파일을 선택했습니다.")
        elif len(selected_file_paths) > 1:
            self.file_detail.clear_preview()
            self.tag_control.update_for_target(selected_file_paths, False)
            self.statusbar.showMessage(f"{len(selected_file_paths)}개 파일을 선택했습니다.")
        else:
            self.file_detail.clear_preview()
            self.tag_control.clear_view()
            self.statusbar.showMessage("파일 선택이 해제되었습니다.")

    def on_global_file_search_requested(self, search_text):
        workspace_path = config.DEFAULT_WORKSPACE_PATH if config.DEFAULT_WORKSPACE_PATH and os.path.isdir(config.DEFAULT_WORKSPACE_PATH) else QDir.homePath()
        if not search_text:
            self.file_list.set_path(workspace_path)
            self.file_detail.clear_preview()
            self.tag_control.clear_view()
            self.statusbar.showMessage("전역 검색이 초기화되었습니다.")
            return
        self.statusbar.showMessage(f"'{search_text}' 검색 중...")
        search_results = []
        for root, _, files in os.walk(workspace_path):
            for file in files:
                if search_text.lower() in file.lower():
                    search_results.append(os.path.join(root, file))
        self.file_list.set_search_results(search_results)
        self.file_detail.clear_preview()
        self.tag_control.clear_view()
        self.statusbar.showMessage(f"'{search_text}' 검색 완료: {len(search_results)}개 파일 발견.")

    def on_tags_updated(self):
        self.statusbar.showMessage("태그가 업데이트되었습니다.", 3000)
        selected_file_paths = self.file_list.get_selected_file_paths()
        self.file_list.model.layoutChanged.emit()
        if len(selected_file_paths) == 1:
            self.file_detail.update_preview(selected_file_paths[0])
        else:
            self.file_detail.clear_preview()
        self.tag_control.update_all_tags_list()
        self.tag_control.update_completer_model()

    def open_custom_tag_dialog(self):
        dialog = CustomTagDialog(self.custom_tag_manager, self)
        if dialog.exec_():
            self.tag_control.individual_quick_tags.load_quick_tags()
            self.tag_control.batch_quick_tags.load_quick_tags()

    def on_directory_tree_context_menu(self, directory_path, global_pos):
        menu = QMenu(self)
        remove_tags_action = menu.addAction("일괄 태그 제거...")
        action = menu.exec_(global_pos)
        if action == remove_tags_action:
            self._open_batch_remove_tags_dialog(directory_path)

    def _open_batch_remove_tags_dialog(self, target_path):
        dialog = BatchRemoveTagsDialog(self.tag_manager, target_path, self)
        if dialog.exec_():
            tags_to_remove = dialog.get_tags_to_remove()
            if tags_to_remove:
                all_files_in_directory = self.tag_manager.get_files_in_directory(target_path, recursive=True, file_extensions=None)
                if all_files_in_directory:
                    result = self.tag_manager.remove_tags_from_files(all_files_in_directory, tags_to_remove)
                    if result and result.get("success"):
                        QMessageBox.information(self, "일괄 태그 제거 완료", f"{result.get('successful', 0)}개 항목에서 태그가 성공적으로 제거되었습니다.")
                        self.on_tags_updated()
                    else:
                        error_msg = result.get("error") if result else "알 수 없는 오류"
                        QMessageBox.critical(self, "일괄 태그 제거 실패", f"오류: {error_msg}")
                else:
                    QMessageBox.information(self, "정보", "선택된 디렉토리 내에 태그를 제거할 파일이 없습니다.")
            else:
                QMessageBox.information(self, "정보", "제거할 태그가 선택되지 않았습니다.")