import os
from PyQt5.QtWidgets import (
    QMainWindow,
    QFileSystemModel,
    QAction,
    QFileDialog,
    QHeaderView,
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import QDir, QTimer
from PyQt5 import uic

from models.tagged_file import TaggedFile
from core.tag_manager import TagManager
from widgets.tag_input_widget import TagInputWidget
from widgets.quick_tags_widget import QuickTagsWidget
from core.tag_ui_state_manager import TagUIStateManager

# --- 이상적인 경로 설정 ---
ui_file_path = os.path.join(os.path.dirname(__file__), "ui/main_window.ui")
form_class = uic.loadUiType(ui_file_path)[0]


class MainWindow(QMainWindow, form_class):
    """
    메인 윈도우의 UI와 모든 동작을 관리합니다.
    UI 이벤트(시그널)를 받아서 core 비즈니스 로직과 연결하는 역할을 합니다.
    """

    def __init__(self):
        super().__init__()

        self.setupUi(self)

        self.current_path = os.path.dirname(__file__)
        self.is_filtered = False  # 필터링 모드 상태 추적

        self.tag_manager = TagManager()
        self.state_manager = TagUIStateManager()
        QTimer.singleShot(0, self.connect_to_db)

        self.setup_menubar()
        self.setup_ui_components()
        self.setup_tag_input_widget()  # TagInputWidget 설정 추가
        self.setup_quick_tags_widget()  # QuickTagsWidget 설정 추가
        self.connect_signals()

        # 모든 위젯 등록이 끝난 후, 태그 관련 UI를 비활성화 상태로 초기화
        self.state_manager.set_file_selected(False)

    def connect_to_db(self):
        """
        백그라운드에서 데이터베이스 연결을 시도하고
        연결 성공 시 UI를 업데이트합니다.
        """
        if self.tag_manager.connect():
            self.update_all_tags_list()
            self.update_tag_autocomplete()  # 자동 완성 모델 업데이트
        else:
            self.statusbar.showMessage(
                "Database connection failed. Please check settings and restart.", 5000
            )

    def setup_menubar(self):
        file_menu = self.menuBar().addMenu("&File")
        self.open_dir_action = QAction("&Open Directory...", self)
        file_menu.addAction(self.open_dir_action)

        # 필터 관련 메뉴 추가
        filter_menu = self.menuBar().addMenu("&Filter")
        self.clear_filter_action = QAction("&Clear Filter", self)
        self.clear_filter_action.setEnabled(False)  # 초기에는 비활성화
        filter_menu.addAction(self.clear_filter_action)

    def setup_ui_components(self):
        try:
            # 1. 중앙 파일 목록 모델 설정 (즉시 실행)
            self.file_list_model = QStandardItemModel()

            self.file_list_model.setHorizontalHeaderLabels(["File Name", "Tags"])

            self.tableView_files.setModel(self.file_list_model)

            # 헤더 설정을 지연시켜 실행
            QTimer.singleShot(100, self.setup_table_header)

            # 디렉토리 트리 로드를 지연시켜 실행
            QTimer.singleShot(200, self.deferred_load_directory_tree)

            if hasattr(self, 'btn_save_tags'):
                self.state_manager.register_widget('save_button', self.btn_save_tags)

        except Exception:
            import traceback

            traceback.print_exc()
            raise

    def setup_tag_input_widget(self):
        """TagInputWidget을 설정하고 기존 lineEdit_tags를 교체합니다."""
        try:
            # 기존 lineEdit_tags가 있는 레이아웃 찾기
            parent_layout = self.lineEdit_tags.parent().layout()

            # TagInputWidget 생성
            self.tag_input_widget = TagInputWidget()

            # 기존 lineEdit_tags 제거
            parent_layout.removeWidget(self.lineEdit_tags)
            self.lineEdit_tags.hide()

            # TagInputWidget을 같은 위치에 추가
            parent_layout.addWidget(self.tag_input_widget)

            # 초기 상태에서는 비활성화 (파일이 선택되지 않은 상태)
            self.tag_input_widget.set_enabled(False)

            # 초기 상태에서 태그 저장 버튼도 비활성화
            self.btn_save_tags.setEnabled(False)

            if hasattr(self, 'tag_input_widget'):
                self.state_manager.register_widget('tag_input', self.tag_input_widget)

            print("[MainWindow] TagInputWidget 설정 완료")

        except Exception as e:
            import traceback

            traceback.print_exc()
            print(f"[MainWindow] TagInputWidget 설정 중 오류: {e}")

    def setup_quick_tags_widget(self):
        """QuickTagsWidget을 설정합니다."""
        try:
            # QuickTagsWidget 생성
            self.quick_tags_widget = QuickTagsWidget()

            # 기본 빠른 선택 태그 설정 (나중에 사용자 설정으로 변경 가능)
            default_quick_tags = [
                "중요",
                "업무",
                "개인",
                "프로젝트",
                "문서",
                "이미지",
                "완료",
                "진행중",
                "검토필요",
                "백업",
                "임시",
            ]
            self.quick_tags_widget.set_quick_tags(default_quick_tags)

            # UI에 배치 (태그 입력 영역 아래에 배치)
            # TODO: UI 레이아웃에 적절한 위치에 배치
            # 현재는 임시로 TagInputWidget과 같은 부모에 배치
            if hasattr(self, "tag_input_widget"):
                parent_layout = self.tag_input_widget.parent().layout()
                parent_layout.addWidget(self.quick_tags_widget)

            if hasattr(self, 'quick_tags_widget'):
                self.state_manager.register_widget('quick_tags', self.quick_tags_widget)

            print("[MainWindow] QuickTagsWidget 설정 완료")

        except Exception as e:
            import traceback

            traceback.print_exc()
            print(f"[MainWindow] QuickTagsWidget 설정 중 오류: {e}")

    def deferred_load_directory_tree(self):
        """
        QFileSystemModel과 같이 잠재적으로 느린 초기화 코드를
        메인 이벤트 루프 시작 후 비동기적으로 실행합니다.
        """
        try:
            self.fs_model = QFileSystemModel()

            self.fs_model.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot)

            self.fs_model.setRootPath(self.current_path)

            self.treeView_dirs.setModel(self.fs_model)

            root_index = self.fs_model.index(self.current_path)
            self.treeView_dirs.setRootIndex(root_index)

            for i in range(1, 4):
                self.treeView_dirs.setColumnHidden(i, True)

        except Exception:
            import traceback

            traceback.print_exc()

    def setup_table_header(self):
        """
        테이블 헤더 설정을 지연 실행하는 메서드
        """
        try:
            header = self.tableView_files.horizontalHeader()

            header.setSectionResizeMode(0, QHeaderView.Stretch)

            self.tableView_files.setColumnWidth(1, 200)

        except Exception:
            import traceback

            traceback.print_exc()

    def connect_signals(self):
        self.open_dir_action.triggered.connect(self.open_directory_dialog)
        self.clear_filter_action.triggered.connect(self.clear_filter)
        self.treeView_dirs.clicked.connect(self.on_directory_selected)
        self.tableView_files.selectionModel().selectionChanged.connect(
            self.on_file_selected
        )
        self.btn_save_tags.clicked.connect(self.save_tags_for_selected_file)
        self.listWidget_all_tags.itemClicked.connect(self.on_tag_filter_selected)

        # TagInputWidget 시그널 연결
        if hasattr(self, "tag_input_widget"):
            self.tag_input_widget.tags_changed.connect(self.on_tags_changed)

        # QuickTagsWidget 시그널 연결
        if hasattr(self, "quick_tags_widget"):
            self.quick_tags_widget.tag_toggled.connect(self.on_quick_tag_toggled)

    # --- Slot (Event Handler) Methods ---

    def open_directory_dialog(self):
        path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if path:
            self.current_path = path
            self.treeView_dirs.setRootIndex(self.fs_model.index(self.current_path))
            self.update_file_list(self.current_path)

    def on_directory_selected(self, index):
        path = self.fs_model.filePath(index)
        if self.fs_model.isDir(index):
            self.current_path = path
            self.is_filtered = False  # 필터링 모드 해제
            self.update_file_list(self.current_path)

    def update_file_list(self, path, file_list=None):
        self.file_list_model.clear()
        self.file_list_model.setHorizontalHeaderLabels(["File Name", "Tags"])

        try:
            # file_list가 주어지지 않으면 os.listdir로 직접 읽음
            files_to_display = file_list if file_list is not None else os.listdir(path)

            for file_name in files_to_display:
                # file_list가 주어졌을 경우, file_name은 전체 경로일 수 있음
                base_name = os.path.basename(file_name)
                full_path = (
                    os.path.join(path, base_name) if file_list is None else file_name
                )

                if os.path.isfile(full_path):
                    tags = self.tag_manager.get_tags_for_file(full_path)

                    item_name = QStandardItem(base_name)
                    item_name.setEditable(False)
                    item_tags = QStandardItem(", ".join(tags))
                    item_tags.setEditable(False)

                    self.file_list_model.appendRow([item_name, item_tags])
        except Exception as e:
            print(f"디렉토리 읽기 오류: {e}")

    def on_file_selected(self, selected, deselected):
        indexes = self.tableView_files.selectionModel().selectedIndexes()
        if not indexes:
            self.state_manager.set_file_selected(False)
            self.btn_save_tags.setEnabled(False)
            self.textBrowser_file_details.clear()
            return
        file_name = self.file_list_model.itemFromIndex(indexes[0]).text()
        full_path = os.path.join(self.current_path, file_name)
        try:
            tagged_file = TaggedFile(full_path)
            tags = self.tag_manager.get_tags_for_file(full_path)
            tagged_file.tags = tags
            self.textBrowser_file_details.setHtml(tagged_file.get_display_info_html())
            self.state_manager.set_file_selected(True, tags)
            self.btn_save_tags.setEnabled(True)
        except FileNotFoundError as e:
            print(e)

    def save_tags_for_selected_file(self):
        indexes = self.tableView_files.selectionModel().selectedIndexes()
        if not indexes:
            self.statusbar.showMessage("No file selected.", 3000)
            return

        file_name = self.file_list_model.itemFromIndex(indexes[0]).text()
        full_path = os.path.join(self.current_path, file_name)

        # TagInputWidget에서 태그 목록 가져오기
        if hasattr(self, "tag_input_widget"):
            new_tags = self.tag_input_widget.get_tags()
        else:
            new_tags = []

        if self.tag_manager.update_tags(full_path, new_tags):
            self.statusbar.showMessage("Tags saved successfully!", 3000)
            self.update_file_list(self.current_path)  # 파일 목록의 태그 새로고침
            self.update_all_tags_list()  # 전체 태그 목록 업데이트
            self.update_tag_autocomplete()  # 자동 완성 모델 업데이트
        else:
            self.statusbar.showMessage("Failed to save tags.", 3000)

    def update_all_tags_list(self):
        all_tags = self.tag_manager.get_all_unique_tags()
        self.listWidget_all_tags.clear()
        self.listWidget_all_tags.addItems(all_tags)

    def update_tag_autocomplete(self):
        """태그 자동 완성 모델을 업데이트합니다."""
        if hasattr(self, "tag_input_widget"):
            all_tags = self.tag_manager.get_all_unique_tags()
            self.tag_input_widget.update_completer_model(all_tags)

    def on_tag_filter_selected(self, item):
        selected_tag = item.text()

        # 현재 선택된 파일이 있으면 해당 파일에 태그 추가
        indexes = self.tableView_files.selectionModel().selectedIndexes()
        if indexes and hasattr(self, "tag_input_widget"):
            if selected_tag not in self.tag_input_widget.get_tags():
                self.tag_input_widget.add_tag(selected_tag)
                self.statusbar.showMessage(f"태그 '{selected_tag}' 추가됨", 2000)
            else:
                self.statusbar.showMessage(
                    f"태그 '{selected_tag}'는 이미 추가되어 있습니다", 2000
                )
        else:
            # 파일이 선택되지 않은 경우 필터링 모드로 동작
            files_with_tag = self.tag_manager.get_files_by_tag(selected_tag)
            self.is_filtered = True  # 필터링 모드 설정
            self.clear_filter_action.setEnabled(True)  # Clear Filter 메뉴 활성화
            self.update_file_list(self.current_path, file_list=files_with_tag)
            self.statusbar.showMessage(
                f"태그 '{selected_tag}'로 필터링됨 ({len(files_with_tag)}개 파일)", 3000
            )

    def on_tags_changed(self, tags):
        """TagInputWidget에서 태그가 변경될 때 호출됩니다."""
        # 자동 완성 모델 업데이트 (새 태그가 추가되었을 수 있으므로)
        self.update_tag_autocomplete()

        # 자동 저장 기능 (선택사항)
        # self.save_tags_for_selected_file()
        pass

    def on_quick_tag_toggled(self, tag, is_added):
        """QuickTagsWidget의 태그가 토글되었을 때 호출됩니다."""
        if hasattr(self, "tag_input_widget"):
            if is_added:
                # 태그 추가
                if tag not in self.tag_input_widget.get_tags():
                    self.tag_input_widget.add_tag(tag)
                    self.statusbar.showMessage(f"빠른 태그 '{tag}' 추가됨", 2000)
                else:
                    self.statusbar.showMessage(
                        f"태그 '{tag}'는 이미 추가되어 있습니다", 2000
                    )
            else:
                # 태그 제거
                if tag in self.tag_input_widget.get_tags():
                    self.tag_input_widget.remove_tag(tag)
                    self.statusbar.showMessage(f"빠른 태그 '{tag}' 제거됨", 2000)

    def clear_filter(self):
        """필터를 해제하고 원래 디렉토리로 돌아갑니다."""
        if self.is_filtered:
            self.is_filtered = False
            self.clear_filter_action.setEnabled(False)
            self.update_file_list(self.current_path)
            self.statusbar.showMessage("필터가 해제되었습니다", 2000)

    def closeEvent(self, event):
        """
        애플리케이션이 닫힐 때 DB 연결을 안전하게 종료합니다.
        """
        self.tag_manager.disconnect()
        event.accept()
