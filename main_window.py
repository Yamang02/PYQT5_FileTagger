import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QMessageBox
from PyQt5.uic import loadUi
from PyQt5.QtCore import QDir, QModelIndex
import os
import config

# 위젯 임포트
from widgets.directory_tree_widget import DirectoryTreeWidget
from widgets.file_list_widget import FileListWidget
from widgets.file_detail_widget import FileDetailWidget
from widgets.tag_control_widget import TagControlWidget

# 코어 로직 임포트
from core.tag_manager import TagManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        loadUi('ui/main_window.ui', self)

        # --- 코어 로직 초기화 ---
        self.tag_manager = TagManager()

        # --- 위젯 인스턴스 생성 ---
        # 초기 작업 공간 경로 설정
        initial_workspace = config.DEFAULT_WORKSPACE_PATH if config.DEFAULT_WORKSPACE_PATH and os.path.isdir(config.DEFAULT_WORKSPACE_PATH) else QDir.homePath()
        self.directory_tree = DirectoryTreeWidget(initial_workspace)
        self.file_list = FileListWidget(self.tag_manager)
        self.file_detail = FileDetailWidget(self.tag_manager)
        self.tag_control = TagControlWidget(self.tag_manager)

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
        self.actionBatchTagging.triggered.connect(self.open_batch_tagging_dialog)
        self.actionSetWorkspace.triggered.connect(self.set_workspace)

        # 위젯 간 연결
        self.directory_tree.tree_view.clicked.connect(self.on_directory_selected)
        # selectionChanged 시그널을 사용하여 다중 선택 처리
        self.file_list.list_view.selectionModel().selectionChanged.connect(self.on_file_selection_changed)
        self.directory_tree.tag_filter_changed.connect(self.file_list.set_tag_filter)
        self.directory_tree.global_file_search_requested.connect(self.on_global_file_search_requested)

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

    def on_directory_selected(self, index):
        """디렉토리 트리에서 항목 선택 시 파일 목록 및 태그 뷰를 업데이트합니다."""
        path = self.directory_tree.model.filePath(self.directory_tree.proxy_model.mapToSource(index))
        self.file_list.set_path(path) # 디렉토리 선택 시 파일 목록을 해당 디렉토리 내용으로 설정
        self.file_detail.clear_preview()
        self.tag_control.update_for_target(path, True) # 디렉토리 선택 시
        self.statusbar.showMessage(f"'{path}' 디렉토리를 보고 있습니다.")

    def on_file_selection_changed(self, selected: QModelIndex, deselected: QModelIndex):
        """파일 리스트에서 선택이 변경될 때 호출됩니다. 단일/다중 선택을 처리합니다."""
        selected_indexes = self.file_list.list_view.selectionModel().selectedIndexes()
        selected_file_paths = self.file_list.get_selected_file_paths()

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

    def open_batch_tagging_dialog(self):
        """일괄 태깅 다이얼로그를 엽니다. (구현 예정)"""
        self.statusbar.showMessage("일괄 태깅 기능이 실행되었습니다.")
        print("일괄 태깅 기능 실행")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())