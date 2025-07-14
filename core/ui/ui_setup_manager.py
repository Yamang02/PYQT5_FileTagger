"""
UI 설정 관리자 - MainWindow의 UI 설정 로직을 분리

이 모듈은 MainWindow의 UI 설정 책임을 분리하여 단일 책임 원칙을 준수하고
코드의 가독성과 유지보수성을 향상시킵니다.
"""

import os
from PyQt5.QtWidgets import QVBoxLayout, QSizePolicy
from PyQt5.QtCore import QDir
from PyQt5.uic import loadUi
import config

from widgets.directory_tree_widget import DirectoryTreeWidget
from widgets.file_list_widget import FileListWidget
from widgets.file_detail_widget import FileDetailWidget
from widgets.tag_control_widget import TagControlWidget
from widgets.search_widget import SearchWidget


class UISetupManager:
    """MainWindow의 UI 설정을 담당하는 관리자 클래스"""
    
    def __init__(self, main_window):
        """
        UI 설정 관리자 초기화
        
        Args:
            main_window: MainWindow 인스턴스
        """
        self.main_window = main_window
        self.widgets = {}
        
    def setup_ui(self):
        """MainWindow의 UI를 설정합니다."""
        self._load_ui_file()
        self._create_widgets()
        self._setup_layout()
        self._configure_initial_sizes()
        
    def _load_ui_file(self):
        """UI 파일을 로드합니다."""
        loadUi('ui/main_window.ui', self.main_window)
        
    def _create_widgets(self):
        """필요한 위젯 인스턴스들을 생성합니다."""
        # 초기 작업공간 설정
        initial_workspace = (
            config.DEFAULT_WORKSPACE_PATH 
            if config.DEFAULT_WORKSPACE_PATH and os.path.isdir(config.DEFAULT_WORKSPACE_PATH) 
            else QDir.homePath()
        )
        
        # 위젯 인스턴스 생성
        self.widgets['directory_tree'] = DirectoryTreeWidget(initial_workspace)
        self.widgets['file_list'] = FileListWidget(self.main_window.file_list_viewmodel)
        self.widgets['file_detail'] = FileDetailWidget(self.main_window.file_detail_viewmodel)
        self.widgets['tag_control'] = TagControlWidget(
            self.main_window.tag_control_viewmodel, 
            self.main_window.custom_tag_manager
        )
        self.widgets['search_widget'] = SearchWidget(self.main_window.search_viewmodel)
        
        # MainWindow에 위젯 참조 설정
        self.main_window.directory_tree = self.widgets['directory_tree']
        self.main_window.file_list = self.widgets['file_list']
        self.main_window.file_detail = self.widgets['file_detail']
        self.main_window.tag_control = self.widgets['tag_control']
        self.main_window.search_widget = self.widgets['search_widget']
        
    def _setup_layout(self):
        """메인 레이아웃을 설정합니다."""
        # 기존 centralwidget 레이아웃 완전 삭제
        self._clear_existing_layout()
        
        # 새로운 VBox 레이아웃 생성
        vbox = QVBoxLayout()
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)
        self.main_window.centralwidget.setLayout(vbox)
        
        # 검색 툴바 추가
        vbox.addWidget(self.widgets['search_widget'])
        
        # 고급 검색 패널 추가 (기본 숨김)
        self.main_window.advanced_panel_widget = self.widgets['search_widget'].get_advanced_panel()
        self.main_window.advanced_panel_widget.setVisible(False)
        vbox.addWidget(self.main_window.advanced_panel_widget)
        
        # 3열 레이아웃 구성
        self._setup_splitter_layout()
        
        # 메인 스플리터를 VBox에 추가
        vbox.addWidget(self.main_window.mainSplitter)
        vbox.setStretchFactor(self.main_window.mainSplitter, 1)
        
    def _clear_existing_layout(self):
        """기존 레이아웃을 완전히 삭제합니다."""
        central_layout = self.main_window.centralwidget.layout()
        if central_layout is not None:
            while central_layout.count():
                item = central_layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.setParent(None)
            import sip
            sip.delete(central_layout)
            
    def _setup_splitter_layout(self):
        """스플리터 레이아웃을 설정합니다."""
        # 3열 레이아웃(mainSplitter) 구성
        self.main_window.mainSplitter.insertWidget(0, self.widgets['directory_tree'])
        self.main_window.mainSplitter.insertWidget(1, self.main_window.splitter)
        self.main_window.mainSplitter.insertWidget(2, self.widgets['tag_control'])
        
        # 기존 placeholder 위젯 삭제
        self.main_window.directoryTreeWidget.deleteLater()
        self.main_window.tagControlWidget.deleteLater()
        
        # 중앙 스플리터 구성
        self.main_window.splitter.insertWidget(0, self.widgets['file_detail'])
        self.main_window.splitter.insertWidget(1, self.widgets['file_list'])
        
        # 기존 placeholder 위젯 삭제
        self.main_window.fileDetailWidget.deleteLater()
        self.main_window.fileListWidget.deleteLater()
        
    def _configure_initial_sizes(self):
        """초기 크기를 설정합니다."""
        # 메인 스플리터 크기 설정
        self.main_window.mainSplitter.setSizes([150, self.main_window.width() - 300, 150])
        
        # 중앙 스플리터 크기 설정
        self.main_window.splitter.setSizes([
            self.main_window.height() // 2, 
            self.main_window.height() // 2
        ])
        
    def get_widget(self, widget_name: str):
        """생성된 위젯을 반환합니다."""
        return self.widgets.get(widget_name)
        
    def get_all_widgets(self):
        """모든 위젯을 반환합니다."""
        return self.widgets.copy() 