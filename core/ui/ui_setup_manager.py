"""
UI 설정 관리자 - MainWindow의 UI 설정 로직을 분리

이 모듈은 MainWindow의 UI 설정 책임을 분리하여 단일 책임 원칙을 준수하고
코드의 가독성과 유지보수성을 향상시킵니다.
"""

import os
from PyQt5.QtWidgets import QVBoxLayout, QSizePolicy, QFrame, QGraphicsDropShadowEffect
from PyQt5.QtGui import QColor
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
        
    def _create_card_widget(self, widget, object_name=None):
        """
        위젯을 QFrame으로 래핑하고 그림자 효과를 적용합니다.
        """
        card_frame = QFrame()
        card_frame.setObjectName("card") # QSS 타겟팅을 위한 objectName
        if object_name:
            card_frame.setObjectName(object_name + "_card") # 특정 위젯을 위한 고유 objectName

        # QVBoxLayout을 사용하여 위젯을 QFrame 안에 배치
        layout = QVBoxLayout(card_frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(widget)

        # 그림자 효과 적용
        shadow = QGraphicsDropShadowEffect(card_frame)
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor("#d0d0d0")) # DRS에 명시된 색상
        card_frame.setGraphicsEffect(shadow)

        return card_frame

    def _create_widgets(self):
        """필요한 위젯 인스턴스들을 생성하고 카드 효과를 적용합니다."""
        # 초기 작업공간 설정
        initial_workspace = (
            config.DEFAULT_WORKSPACE_PATH
            if config.DEFAULT_WORKSPACE_PATH and os.path.isdir(config.DEFAULT_WORKSPACE_PATH)
            else QDir.homePath()
        )

        # 위젯 인스턴스 생성
        directory_tree_widget = DirectoryTreeWidget(initial_workspace)
        file_list_widget = FileListWidget(self.main_window.file_list_viewmodel)
        file_detail_widget = FileDetailWidget(self.main_window.file_detail_viewmodel)
        tag_control_widget = TagControlWidget(
            self.main_window.tag_control_viewmodel,
            self.main_window.custom_tag_manager
        )
        search_widget = SearchWidget(self.main_window.search_viewmodel)

        # 각 위젯에 카드 효과 적용 (래핑된 QFrame은 별도로 저장)
        self.main_window.directory_tree_frame = self._create_card_widget(directory_tree_widget, "directoryTree")
        self.main_window.file_list_frame = self._create_card_widget(file_list_widget, "fileList")
        self.main_window.file_detail_frame = self._create_card_widget(file_detail_widget, "fileDetail")
        self.main_window.tag_control_frame = self._create_card_widget(tag_control_widget, "tagControl")
        self.main_window.search_widget_frame = self._create_card_widget(search_widget, "search")

        # self.widgets 딕셔너리에는 실제 위젯 인스턴스를 저장
        self.widgets['directory_tree'] = directory_tree_widget
        self.widgets['file_list'] = file_list_widget
        self.widgets['file_detail'] = file_detail_widget
        self.widgets['tag_control'] = tag_control_widget
        self.widgets['search_widget'] = search_widget

        # MainWindow에 실제 위젯 참조 설정
        self.main_window.directory_tree = directory_tree_widget
        self.main_window.file_list = file_list_widget
        self.main_window.file_detail = file_detail_widget
        self.main_window.tag_control = tag_control_widget
        self.main_window.search_widget = search_widget
        
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
        self.main_window.mainSplitter.insertWidget(0, self.main_window.directory_tree_frame)
        self.main_window.mainSplitter.insertWidget(1, self.main_window.splitter)
        self.main_window.mainSplitter.insertWidget(2, self.main_window.tag_control_frame)

        # 기존 placeholder 위젯 삭제
        self.main_window.directoryTreeWidget.deleteLater()
        self.main_window.tagControlWidget.deleteLater()

        # 중앙 스플리터 구성
        self.main_window.splitter.insertWidget(0, self.main_window.file_detail_frame)
        self.main_window.splitter.insertWidget(1, self.main_window.file_list_frame)
        
        # 기존 placeholder 위젯 삭제
        self.main_window.fileDetailWidget.deleteLater()
        self.main_window.fileListWidget.deleteLater()
        
    def _configure_initial_sizes(self):
        """초기 크기를 설정합니다."""
        # 메인 스플리터 크기 설정 (확대된 좌우 영역)
        left_width = 200    # DirectoryTreeWidget (150px → 200px)
        right_width = 200   # TagControlWidget (150px → 200px)
        center_width = self.main_window.width() - left_width - right_width
        self.main_window.mainSplitter.setSizes([left_width, center_width, right_width])
        
        # 중앙 스플리터 크기 설정 (fileDetail 65%, fileList 35%)
        total_height = self.main_window.height()
        detail_height = int(total_height * 0.65)
        list_height = int(total_height * 0.35)
        self.main_window.splitter.setSizes([detail_height, list_height])
        
    def get_widget(self, widget_name: str):
        """생성된 위젯을 반환합니다."""
        return self.widgets.get(widget_name)
        
    def get_all_widgets(self):
        """모든 위젯을 반환합니다."""
        return self.widgets.copy()
    
    def adjust_layout(self):
        """창 상태에 따라 전체 레이아웃을 동적으로 조정합니다."""
        try:
            self._adjust_main_splitter()
            self._adjust_central_splitter()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"레이아웃 조정 중 오류: {e}")
    
    def _adjust_main_splitter(self):
        """mainSplitter (좌-중-우) 비율을 조정합니다."""
        if hasattr(self.main_window, 'mainSplitter') and self.main_window.mainSplitter:
            # 현재 상태 로깅
            import logging
            logger = logging.getLogger(__name__)
            
            current_sizes = self.main_window.mainSplitter.sizes()
            total_width = self.main_window.mainSplitter.width()
            window_state = "최대화" if (self.main_window.isMaximized() or self.main_window.isFullScreen()) else "기본"
            
            logger.info(f"[UI] 레이아웃 조정 - 상태: {window_state}, 너비: {total_width}")
            
            if total_width <= 0:
                logger.warning(f"[UI] mainSplitter 너비 오류: {total_width}")
                return
            
            # 모든 모드에서 좌측/우측 영역 크기 확대
            left_width = 200    # DirectoryTreeWidget (150px → 200px)
            right_width = 200   # TagControlWidget (150px → 200px)
            center_width = total_width - left_width - right_width
            
            new_sizes = [left_width, center_width, right_width]
            self.main_window.mainSplitter.setSizes(new_sizes)
            
            # 강제 업데이트
            self.main_window.mainSplitter.update()
            
            logger.info(f"[UI] mainSplitter 적용: 좌측={left_width}, 중앙={center_width}, 우측={right_width}")
    
    def _adjust_central_splitter(self):
        """중앙 splitter (상-하) 비율을 조정합니다."""
        if hasattr(self.main_window, 'splitter') and self.main_window.splitter:
            total_height = self.main_window.splitter.height()
            
            # 모든 모드에서 동일한 비율: fileDetail 65%, fileList 35%
            detail_height = int(total_height * 0.65)
            list_height = int(total_height * 0.35)
            
            self.main_window.splitter.setSizes([detail_height, list_height])
            
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"[UI] 중앙 splitter 적용: 상세영역={detail_height}(65%), 리스트영역={list_height}(35%)") 