import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QMessageBox, QMenu
from PyQt5.uic import loadUi
from PyQt5.QtCore import QDir, QModelIndex
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
    def __init__(self):
        super().__init__()
        loadUi('ui/main_window.ui', self)

        # --- 코어 로직 초기화 ---
        self.tag_manager = TagManager()
        self.custom_tag_manager = CustomTagManager()

        # --- 위젯 인스턴스 생성 ---
        # 초기 작업 공간 경로 설정
        initial_workspace = config.DEFAULT_WORKSPACE_PATH if config.DEFAULT_WORKSPACE_PATH and os.path.isdir(config.DEFAULT_WORKSPACE_PATH) else QDir.homePath()
        self.directory_tree = DirectoryTreeWidget(initial_workspace)
        logger.debug(f"[MainWindow] DirectoryTreeWidget recursive_checkbox: {self.directory_tree.recursive_checkbox.isChecked()}")
        logger.debug(f"[MainWindow] DirectoryTreeWidget extensions_input: {self.directory_tree.extensions_input.text()}")
        self.file_list = FileListWidget(self.tag_manager)
        self.file_detail = FileDetailWidget(self.tag_manager)
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

        # 초기 크기 설정 (픽셀 단위)
        self.mainSplitter.setSizes([150, self.width() - 300, 150])
        self.splitter.setSizes([self.height() // 2, self.height() // 2])

        # --- 연결 설정 ---
        self.setup_connections()
        self.statusbar.showMessage("준비 완료")

        self.show()

    def setup_connections(self):
        """위젯 및 메뉴 액션의 시그널-슬롯을 연결합니다."""
        # 메뉴 액션
        self.actionExit.triggered.connect(self.close)
        self.actionSetWorkspace.triggered.connect(self.set_workspace)
        self.actionManageQuickTags.triggered.connect(self.open_custom_tag_dialog)

        # 위젯 간 연결
        self.directory_tree.tree_view.clicked.connect(self.on_directory_selected)
        self.directory_tree.filter_options_changed.connect(self.on_directory_selected) # 필터 옵션 변경 시에도 디렉토리 재선택 효과
        # selectionChanged 시그널을 사용하여 다중 선택 처리
        self.file_list.list_view.selectionModel().selectionChanged.connect(self.on_file_selection_changed)
        self.directory_tree.tag_filter_changed.connect(self.file_list.set_tag_filter)
        self.directory_tree.global_file_search_requested.connect(self.on_global_file_search_requested)
        self.tag_control.tags_updated.connect(self.on_tags_updated)
        self.file_detail.file_tags_changed.connect(self.on_tags_updated) # 파일 상세 위젯에서 태그 변경 시
        self.directory_tree.directory_context_menu_requested.connect(self.on_directory_tree_context_menu)

    def set_workspace(self):
        """사용자에게 작업 공간 디렉토리를 설정하도록 요청합니다."""
        current_workspace = config.DEFAULT_WORKSPACE_PATH if config.DEFAULT_WORKSPACE_PATH and os.path.isdir(config.DEFAULT_WORKSPACE_PATH) else QDir.homePath()
        new_workspace = QFileDialog.getExistingDirectory(self, "작업 공간 선택", current_workspace)

        if new_workspace:
            # config.py 업데이트
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
                
                # 현재 실행 중인 config 모듈 업데이트 (선택 사항, 재시작이 더 확실)
                config.DEFAULT_WORKSPACE_PATH = new_workspace

                self.directory_tree.set_root_path(new_workspace)
                self.file_list.set_path(new_workspace) # 작업 공간 변경 시 파일 목록도 업데이트
                self.file_detail.clear_preview()
                self.tag_control.clear_view()
                self.statusbar.showMessage(f"작업 공간이 '{new_workspace}'로 설정되었습니다.", 5000)
            except Exception as e:
                QMessageBox.critical(self, "오류", f"작업 공간 설정 중 오류가 발생했습니다: {e}")
                self.statusbar.showMessage("작업 공간 설정 실패", 3000)

    def on_directory_selected(self, *args):
        logger.debug(f"[MainWindow] on_directory_selected 호출됨. args: {args}")
        path = None
        recursive = self.directory_tree.recursive_checkbox.isChecked()
        extensions_text = self.directory_tree.extensions_input.text().strip()
        file_extensions = [ext.strip() for ext in extensions_text.split(',') if ext.strip()]

        if isinstance(args[0], QModelIndex):
            index = args[0]
            path = self.directory_tree.model.filePath(self.directory_tree.proxy_model.mapToSource(index))
        else:
            # 필터 옵션 변경 시에는 현재 선택된 디렉토리 경로를 사용
            path = self.file_list.model.current_directory
            if not path:
                # 초기 로드 시 current_directory가 비어있을 수 있으므로, workspace_path 사용
                path = config.DEFAULT_WORKSPACE_PATH if config.DEFAULT_WORKSPACE_PATH and os.path.isdir(config.DEFAULT_WORKSPACE_PATH) else QDir.homePath()

        if path:
            logger.debug(f"[MainWindow] Calling file_list.set_path with path={path}, recursive={recursive}, file_extensions={file_extensions}")
            self.file_list.set_path(path, recursive, file_extensions) # 디렉토리 선택 시 파일 목록을 해당 디렉토리 내용으로 설정
            self.file_detail.clear_preview()
            logger.debug(f"[MainWindow] Calling tag_control.update_for_target with path={path}, is_dir=True")
            self.tag_control.update_for_target(path, True) # 디렉토리 선택 시
            self.statusbar.showMessage(f"'{path}' 디렉토리를 보고 있습니다.")
        else:
            self.statusbar.showMessage("디렉토리를 선택해주세요.")

    def on_file_selection_changed(self, selected: QModelIndex, deselected: QModelIndex):
        
        """파일 리스트에서 선택이 변경될 때 호출됩니다. 단일/다중 선택을 처리합니다."""
        selected_indexes = self.file_list.list_view.selectionModel().selectedIndexes()

        selected_file_paths = []
        processed_rows = set() # To handle multiple selected columns in the same row

        for index in selected_indexes:
            if index.row() not in processed_rows:
                file_path = self.file_list.model.get_file_path(index)
                if file_path:
                    selected_file_paths.append(file_path)
                processed_rows.add(index.row())

        if len(selected_file_paths) == 1:
            
            # 단일 파일 선택
            file_path = selected_file_paths[0]
            self.file_detail.update_preview(file_path)
            self.tag_control.update_for_target(file_path, False) # 파일 선택 시
            self.statusbar.showMessage(f"'{file_path}' 파일을 선택했습니다.")
        elif len(selected_file_paths) > 1:
            
            # 다중 파일 선택
            self.file_detail.clear_preview() # 상세 정보 초기화
            self.tag_control.update_for_target(selected_file_paths, False) # 다중 파일 선택 시 (TagControlWidget에서 처리)
            self.statusbar.showMessage(f"{len(selected_file_paths)}개 파일을 선택했습니다.")
        else:
            # 선택 해제
            
            self.file_detail.clear_preview()
            self.tag_control.clear_view()
            self.statusbar.showMessage("파일 선택이 해제되었습니다.")

    def on_global_file_search_requested(self, search_text):
        """전역 파일 검색 요청 시 파일을 검색하고 파일 목록을 업데이트합니다."""
        workspace_path = config.DEFAULT_WORKSPACE_PATH if config.DEFAULT_WORKSPACE_PATH and os.path.isdir(config.DEFAULT_WORKSPACE_PATH) else QDir.homePath()

        if not search_text:
            # 검색 텍스트가 비어있으면 현재 작업 공간의 파일 목록으로 돌아감
            self.file_list.set_path(workspace_path)
            self.file_detail.clear_preview()
            self.tag_control.clear_view()
            self.statusbar.showMessage("전역 검색이 초기화되었습니다.")
            return

        self.statusbar.showMessage(f"'{search_text}'로 파일 검색 중...")
        search_results = []
        # 작업 공간을 검색 시작 경로로 사용
        for root, _, files in os.walk(workspace_path):
            for file in files:
                if search_text.lower() in file.lower():
                    search_results.append(os.path.join(root, file))
        
        self.file_list.set_search_results(search_results)
        self.file_detail.clear_preview()
        self.tag_control.clear_view()
        self.statusbar.showMessage(f"'{search_text}' 검색 완료: {len(search_results)}개 파일 발견.")

    def on_tags_updated(self):
        """TagControlWidget에서 태그가 업데이트된 후 호출되는 슬롯."""
        self.statusbar.showMessage("태그가 업데이트되었습니다.", 3000)
        
        # 현재 선택된 파일 경로들을 다시 가져옴
        selected_file_paths = self.file_list.get_selected_file_paths()

        # 파일 목록 위젯의 태그 정보 새로고침
        # 현재는 모델을 리셋하는 방식으로 간단히 구현
        # 파일 목록 위젯의 태그 정보 새로고침
        # self.file_list.refresh_tags_for_current_files()
        self.file_list.model.layoutChanged.emit()

        # 파일 상세 위젯의 정보 새로고침
        if len(selected_file_paths) == 1:
            self.file_detail.update_preview(selected_file_paths[0])
        else:
            self.file_detail.clear_preview()

        # TagControlWidget의 전체 태그 목록 및 자동완성 업데이트
        self.tag_control.update_all_tags_list()
        self.tag_control.update_completer_model()

    def open_custom_tag_dialog(self):
        dialog = CustomTagDialog(self.custom_tag_manager, self)
        if dialog.exec_():
            # 다이얼로그에서 태그가 업데이트되었을 경우 QuickTagsWidget을 새로고침
            self.tag_control.individual_quick_tags.load_quick_tags()
            self.tag_control.batch_quick_tags.load_quick_tags()

    def on_directory_tree_context_menu(self, directory_path, global_pos):
        print(f"DEBUG: on_directory_tree_context_menu called for {directory_path}") # 진단용
        menu = QMenu(self)
        remove_tags_action = menu.addAction("일괄 태그 제거...")
        print(f"DEBUG: Menu created, action added. Executing menu at {global_pos}") # 진단용
        action = menu.exec_(global_pos)

        if action == remove_tags_action:
            print(f"DEBUG: '일괄 태그 제거...' action triggered for {directory_path}") # 진단용
            self._open_batch_remove_tags_dialog(directory_path)

    def _open_batch_remove_tags_dialog(self, target_path):
        dialog = BatchRemoveTagsDialog(self.tag_manager, target_path, self)
        if dialog.exec_():
            tags_to_remove = dialog.get_tags_to_remove()
            if tags_to_remove:
                # TagManager의 remove_tags_from_files 또는 clear_all_tags_from_file 호출
                # 여기서는 디렉토리 경로를 받았으므로, 해당 디렉토리 내 파일들에 대해 일괄 제거를 수행해야 함
                # TagManager에 디렉토리 내 파일에서 태그를 제거하는 새로운 메서드가 필요할 수 있음
                # 현재는 remove_tags_from_files를 사용하되, 대상 파일 목록을 먼저 가져와야 함
                
                # 임시: 디렉토리 내 모든 파일에 대해 태그 제거 (재귀적으로)
                # 이 부분은 TagManager에 새로운 메서드를 추가하거나, 여기서 파일 목록을 가져와 처리해야 함
                # 현재 TagManager에는 add_tags_to_directory는 있지만 remove_tags_from_directory는 없음
                # 따라서, 여기서는 일단 선택된 디렉토리의 모든 파일에 대해 remove_tags_from_files를 호출하는 방식으로 구현
                
                # TODO: TagManager에 remove_tags_from_directory 메서드 추가 필요
                # 현재는 임시로 디렉토리 내 모든 파일을 가져와서 처리
                
                # 디렉토리 내 파일 목록 가져오기 (recursive=True, file_extensions=None)
                # TagManager의 _get_files_in_directory 메서드를 활용해야 하지만, private 메서드이므로 직접 호출 불가
                # TagManager에 public 메서드로 get_files_in_directory를 추가하거나, 다른 방식으로 파일 목록을 가져와야 함
                
                # 일단은 임시로 TagManager의 add_tags_to_directory에서 사용하는 _get_files_in_directory 로직을 참고하여 구현
                # 이 부분은 추후 리팩토링 필요
                
                # TagManager의 get_files_in_directory 메서드를 사용하여 파일 목록 가져오기
                all_files_in_directory = self.tag_manager.get_files_in_directory(target_path, recursive=True, file_extensions=None)

                if all_files_in_directory:
                    result = self.tag_manager.remove_tags_from_files(all_files_in_directory, tags_to_remove)
                    if result and result.get("success"):
                        QMessageBox.information(self, "일괄 태그 제거 완료", f"{result.get('successful', 0)}개 항목에서 태그가 성공적으로 제거되었습니다.")
                        self.on_tags_updated() # UI 업데이트
                    else:
                        error_msg = result.get("error") if result else "알 수 없는 오류"
                        QMessageBox.critical(self, "일괄 태그 제거 실패", f"오류: {error_msg}")
                else:
                    QMessageBox.information(self, "정보", "선택된 디렉토리 내에 태그를 제거할 파일이 없습니다.")
            else:
                QMessageBox.information(self, "정보", "제거할 태그가 선택되지 않았습니다.")