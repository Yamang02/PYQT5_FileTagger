from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton, QScrollArea, QSizePolicy
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5 import uic
from core.custom_tag_manager import CustomTagManager

class QuickTagsWidget(QWidget):
    """
    자주 사용하는 태그를 빠르게 선택할 수 있는 위젯입니다.
    버튼 형태로 태그를 표시하고, 클릭 시 토글 방식으로 태그를 추가/제거합니다.
    """

    tag_toggled = pyqtSignal(str, bool)  # (tag_name, is_added) 시그널
    tags_changed = pyqtSignal(str)

    def __init__(self, custom_tag_manager: CustomTagManager, parent=None):
        super().__init__(parent)
        # Material Design 스타일 적용
        self.setObjectName("quickTagsPanel")
        
        uic.loadUi('ui/quick_tags_widget.ui', self)
        
        # 부모 위젯의 너비를 해치지 않도록 엄격한 크기 정책 설정
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.setMaximumHeight(60)  # 최대 높이 제한 (스크롤바 공간 확보)
        self.setMinimumHeight(50)  # 최소 높이 설정
        
        # 기존 horizontalLayout을 제거하고 스크롤 영역으로 교체
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setSpacing(0)
        
        # 스크롤 영역 생성 (투명하고 테두리 없음)
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setFrameStyle(0)  # 테두리 제거
        self.scroll_area.setMaximumHeight(60)
        self.scroll_area.setMinimumHeight(50)
        self.scroll_area.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        
        # 스크롤 영역 내부 위젯
        self.scroll_widget = QWidget()
        self.scroll_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.scroll_widget.setStyleSheet("QWidget { background: transparent; }")
        
        # 버튼 레이아웃 (하단 여백 추가)
        self.button_layout = QHBoxLayout(self.scroll_widget)
        self.button_layout.setContentsMargins(0, 0, 0, 8)  # 하단에 8px 여백 추가
        self.button_layout.setSpacing(4)
        self.button_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        # 스크롤 영역에 위젯 설정
        self.scroll_area.setWidget(self.scroll_widget)
        
        # 기존 horizontalLayout에 스크롤 영역 추가
        self.horizontalLayout.addWidget(self.scroll_area)
        
        self.custom_tag_manager = custom_tag_manager
        self._selected_tags: list[str] = []
        self._buttons: dict[str, QPushButton] = {}
        self.is_enabled = True  # 위젯 활성화 상태 추적
        self.load_quick_tags() # 커스텀 태그 로드

    def load_quick_tags(self):
        """퀵 태그 목록을 로드하고 버튼을 생성합니다."""
        self._quick_tags = self.custom_tag_manager.load_custom_quick_tags()
        self._create_buttons()

    def _create_buttons(self):
        """태그 버튼들을 생성합니다."""
        # 기존 버튼 제거
        for btn in self._buttons.values():
            self.button_layout.removeWidget(btn)
            btn.deleteLater()
        self._buttons.clear()
        
        # 새 버튼 생성
        for tag in self._quick_tags:
            btn = QPushButton(tag, self)
            btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)  # 버튼 크기 고정
            btn.setMaximumHeight(24)  # 버튼 높이 제한
            btn.setMinimumHeight(20)  # 최소 높이 설정
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #ffffff;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    padding: 2px 8px;
                    font-size: 11px;
                    color: #495057;
                }
                QPushButton:hover {
                    background-color: #f8f9fa;
                    border-color: #adb5bd;
                }
                QPushButton:pressed {
                    background-color: #e9ecef;
                }
            """)
            btn.clicked.connect(lambda _, t=tag: self._on_btn_clicked(t))
            self.button_layout.addWidget(btn)
            self._buttons[tag] = btn

    def _on_btn_clicked(self, tag):
        """태그 버튼 클릭 처리"""
        self.tags_changed.emit(tag)

    def set_enabled(self, enabled: bool):
        """위젯 전체 활성/비활성 상태를 설정합니다."""
        self.is_enabled = enabled  
        self.setEnabled(enabled)
        
        # 버튼들의 활성화 상태만 변경 (스타일은 QSS에서 처리)
        for button in self._buttons.values():
            button.setEnabled(enabled)
