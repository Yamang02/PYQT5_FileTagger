# ui_initializer.py
from PyQt5.QtWidgets import (
    QMainWindow, QAction, QFileDialog, QWidget, QVBoxLayout, QHBoxLayout,
    QMenuBar, QStatusBar, QSplitter, QTreeView, QTableView, QFileSystemModel
)
from PyQt5.QtCore import QDir, Qt

from core.tag_manager import TagManager
from widgets.unified_tagging_panel import UnifiedTaggingPanel
from widgets.file_selection_and_preview_widget import FileSelectionAndPreviewWidget
from core.tag_ui_state_manager import TagUIStateManager
from widgets.batch_tagging_options_widget import BatchTaggingOptionsWidget


class UIInitializer:
    def __init__(self, main_window: QMainWindow, tag_manager: TagManager, state_manager: TagUIStateManager):
        self.main_window = main_window
        self.tag_manager = tag_manager
        self.state_manager = state_manager

        self.batch_tagging_options_widget = None # 초기화

    def setup_ui(self):
        """메인 윈도우의 UI 컴포넌트를 설정합니다."""
        self._setup_menubar_and_statusbar()
        self._setup_main_layout()

    def _setup_menubar_and_statusbar(self):
        """메뉴바와 상태바를 직접 설정합니다."""
        # 메뉴바 설정
        self.main_window.setMenuBar(QMenuBar(self.main_window))
        file_menu = self.main_window.menuBar().addMenu("&File")

        # 디렉토리 열기 액션
        self.main_window.open_dir_action = QAction("&Open Directory...", self.main_window)
        file_menu.addAction(self.main_window.open_dir_action)

        # 구분선
        file_menu.addSeparator()

        # 모드 전환 액션들
        self.main_window.individual_mode_action = QAction("&개별 태깅 모드", self.main_window)
        file_menu.addAction(self.main_window.individual_mode_action)

        self.main_window.batch_mode_action = QAction("&일괄 태깅 모드", self.main_window)
        file_menu.addAction(self.main_window.batch_mode_action)

        # 필터 관련 메뉴 추가
        filter_menu = self.main_window.menuBar().addMenu("&Filter")
        self.main_window.clear_filter_action = QAction("&Clear Filter", self.main_window)
        self.main_window.clear_filter_action.setEnabled(False)  # 초기에는 비활성화
        filter_menu.addAction(self.main_window.clear_filter_action)

        # 상태바 설정
        self.main_window.setStatusBar(QStatusBar(self.main_window))

    def _setup_main_layout(self):
        """3분할 메인 레이아웃을 설정합니다."""
        self.main_window.central_widget = QWidget(self.main_window)
        self.main_window.setCentralWidget(self.main_window.central_widget)
        main_h_layout = QHBoxLayout(self.main_window.central_widget)
        main_h_layout.setContentsMargins(0, 0, 0, 0)
        main_h_layout.setSpacing(0)

        self.main_window.main_splitter = QSplitter(Qt.Horizontal)
        main_h_layout.addWidget(self.main_window.main_splitter)

        # 1. 왼쪽 섹션: 디렉토리 트리뷰
        self.main_window.tree_view_dirs = QTreeView(self.main_window)
        self.main_window.dir_model = QFileSystemModel()
        self.main_window.dir_model.setRootPath(QDir.rootPath())
        self.main_window.dir_model.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot)
        self.main_window.tree_view_dirs.setModel(self.main_window.dir_model)
        for i in range(1, self.main_window.dir_model.columnCount()):
            self.main_window.tree_view_dirs.setColumnHidden(i, True)
        self.main_window.tree_view_dirs.setHeaderHidden(True)
        self.main_window.main_splitter.addWidget(self.main_window.tree_view_dirs)

        # 2. 가운데 섹션: 파일 목록 및 옵션
        center_panel_layout = QVBoxLayout()
        self.main_window.file_selection_and_preview_widget = FileSelectionAndPreviewWidget(
            self.state_manager, self.tag_manager, self.main_window
        )
        center_panel_layout.addWidget(self.main_window.file_selection_and_preview_widget)

        # BatchTaggingOptionsWidget 초기화
        self.batch_tagging_options_widget = BatchTaggingOptionsWidget(
            self.state_manager, self.main_window
        )
        center_panel_layout.addWidget(self.batch_tagging_options_widget)
        self.main_window.batch_tagging_options_widget = self.batch_tagging_options_widget # MainWindow에 속성으로 저장

        center_panel_container = QWidget()
        center_panel_container.setLayout(center_panel_layout)
        self.main_window.main_splitter.addWidget(center_panel_container)

        # 3. 오른쪽 섹션: 통합 태깅 패널 (UnifiedTaggingPanel)
        self.main_window.unified_tagging_panel = UnifiedTaggingPanel(
            self.state_manager, self.tag_manager, self.main_window
        )
        self.main_window.main_splitter.addWidget(self.main_window.unified_tagging_panel)

        # 스플리터 초기 크기 비율 설정 (예: 1:3:1)
        self.main_window.main_splitter.setSizes([1, 3, 1])
