# ui_initializer.py
from PyQt5.QtWidgets import (
    QMainWindow, QAction, QFileDialog, QWidget, QVBoxLayout, QHBoxLayout,
    QMenuBar, QStatusBar, QSplitter, QTreeView, QTableView, QFileSystemModel, QTabWidget
)
from PyQt5.QtCore import QDir, Qt
from PyQt5 import uic

from core.tag_manager import TagManager
from widgets.unified_tagging_panel import UnifiedTaggingPanel
from widgets.file_selection_and_preview_widget import FileSelectionAndPreviewWidget, FileTableModel
from core.tag_ui_state_manager import TagUIStateManager
from widgets.batch_tagging_options_widget import BatchTaggingOptionsWidget


class UIInitializer:
    def __init__(self, main_window: QMainWindow, tag_manager: TagManager, state_manager: TagUIStateManager):
        self.main_window = main_window
        self.tag_manager = tag_manager
        self.state_manager = state_manager

    def setup_ui(self):
        """메인 윈도우의 UI 컴포넌트를 설정합니다."""
        uic.loadUi('ui/main_window.ui', self.main_window)

        # 모델 설정
        self.main_window.dir_model = QFileSystemModel()
        self.main_window.dir_model.setRootPath(QDir.rootPath())
        self.main_window.dir_model.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot)
        self.main_window.treeView_dirs.setModel(self.main_window.dir_model)
        for i in range(1, self.main_window.dir_model.columnCount()):
            self.main_window.treeView_dirs.setColumnHidden(i, True)
        self.main_window.treeView_dirs.setHeaderHidden(True)

        # 파일 테이블 모델 설정
        self.main_window.file_model = FileTableModel(self.tag_manager)
        self.main_window.tableView_files.setModel(self.main_window.file_model)

        # UnifiedTaggingPanel에 tag_manager와 state_manager 전달
        # .ui 파일에서 로드된 위젯에 속성 설정
        self.main_window.unifiedTaggingPanel_individual.tag_manager = self.tag_manager
        self.main_window.unifiedTaggingPanel_individual.state_manager = self.state_manager
        

        
