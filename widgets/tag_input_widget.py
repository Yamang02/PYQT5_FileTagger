from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QLineEdit, QLabel, 
                             QPushButton, QFrame, QVBoxLayout, QScrollArea,
                             QCompleter)
from PyQt5.QtCore import pyqtSignal, Qt, QSize, QStringListModel
from PyQt5.QtGui import QFont, QPalette, QColor


class TagChip(QFrame):
    """
    개별 태그를 표시하는 칩 위젯입니다.
    태그 이름과 삭제 버튼을 포함합니다.
    """
    def __init__(self, tag_text, parent=None):
        super().__init__(parent)
        self.tag_text = tag_text
        self.setup_ui()
        
    def setup_ui(self):
        """태그 칩의 UI를 설정합니다."""
        # 레이아웃 설정
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)
        
        # 태그 텍스트 라벨
        self.tag_label = QLabel(self.tag_text)
        self.tag_label.setFont(QFont("Arial", 9))
        
        # 삭제 버튼
        self.delete_button = QPushButton("×")
        self.delete_button.setFixedSize(16, 16)
        self.delete_button.setFont(QFont("Arial", 10, QFont.Bold))
        self.delete_button.setStyleSheet("""
            QPushButton {
                background-color: #ff6b6b;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff5252;
            }
            QPushButton:pressed {
                background-color: #d32f2f;
            }
        """)
        
        # 위젯들을 레이아웃에 추가
        layout.addWidget(self.tag_label)
        layout.addWidget(self.delete_button)
        
        # 프레임 스타일 설정
        self.setFrameStyle(QFrame.NoFrame)
        self.setStyleSheet("""
            TagChip {
                background-color: #e3f2fd;
                border: 1px solid #2196f3;
                border-radius: 12px;
                padding: 2px;
            }
            TagChip:hover {
                background-color: #bbdefb;
                border: 1px solid #1976d2;
            }
        """)
        
        # 최소 크기 설정
        self.setMinimumHeight(24)
        self.setMaximumHeight(24)


class TagInputWidget(QWidget):
    """
    태그 입력 및 표시를 위한 커스텀 위젯입니다.
    태그 칩들을 동적으로 추가/제거할 수 있고, 새 태그 입력 필드를 포함합니다.
    """
    tags_changed = pyqtSignal(list)  # 태그가 변경될 때 방출되는 시그널
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tags = []
        self.completer = None
        self.setup_ui()
        self.setup_completer()
        
    def setup_ui(self):
        """위젯의 UI를 설정합니다."""
        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(4)
        
        # 태그 칩들을 담을 스크롤 영역
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setMaximumHeight(80)
        
        # 태그 칩 컨테이너 위젯
        self.chip_container = QWidget()
        self.chip_layout = QHBoxLayout(self.chip_container)
        self.chip_layout.setContentsMargins(4, 4, 4, 4)
        self.chip_layout.setSpacing(4)
        self.chip_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.chip_layout.setSizeConstraint(QHBoxLayout.SetMinAndMaxSize)
        
        # 새 태그 입력 필드
        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("새 태그 입력...")
        self.tag_input.setMaximumWidth(150)
        self.tag_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 12px;
                padding: 4px 8px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 1px solid #2196f3;
            }
        """)
        
        # 입력 필드를 레이아웃에 추가
        self.chip_layout.addWidget(self.tag_input)
        self.chip_layout.addStretch()  # 오른쪽 공간 채우기
        
        # 스크롤 영역에 컨테이너 설정
        self.scroll_area.setWidget(self.chip_container)
        
        # 메인 레이아웃에 스크롤 영역 추가
        main_layout.addWidget(self.scroll_area)
        
        # 시그널 연결
        self.tag_input.returnPressed.connect(self.add_tag_from_input)
        
    def setup_completer(self):
        """자동 완성 기능을 설정합니다."""
        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setWrapAround(False)
        
        # 자동 완성 팝업 크기 설정
        self.completer.popup().setMaximumHeight(150)
        self.completer.popup().setMaximumWidth(300)
        
        # 자동 완성 팝업 스타일 설정
        self.completer.popup().setStyleSheet("""
            QListView {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 2px;
                selection-background-color: #2196f3;
                selection-color: white;
            }
            QListView::item {
                padding: 4px 8px;
                border-radius: 2px;
            }
            QListView::item:hover {
                background-color: #e3f2fd;
            }
        """)
        
        # 입력 필드에 자동 완성 연결
        self.tag_input.setCompleter(self.completer)
        
        # 자동 완성 선택 시그널 연결
        self.completer.activated.connect(self.on_completer_activated)
        
        # 텍스트 변경 시 자동 완성 트리거
        self.tag_input.textChanged.connect(self.on_text_changed)
        
    def add_tag_from_input(self):
        """입력 필드에서 새 태그를 추가합니다."""
        tag_text = self.tag_input.text().strip()
        if tag_text:
            if tag_text not in self.tags:
                self.add_tag(tag_text)
                self.tag_input.clear()
            else:
                # 중복 태그인 경우 입력 필드만 클리어
                self.tag_input.clear()
            
    def add_tag(self, tag_text):
        """새로운 태그를 추가합니다."""
        if tag_text not in self.tags:
            self.tags.append(tag_text)
            self.create_tag_chip(tag_text)
            self.tags_changed.emit(self.tags.copy())
            
    def remove_tag(self, tag_text):
        """특정 태그를 제거합니다."""
        if tag_text in self.tags:
            self.tags.remove(tag_text)
            self.remove_tag_chip(tag_text)
            self.tags_changed.emit(self.tags.copy())
            
    def create_tag_chip(self, tag_text):
        """태그 칩을 생성하고 UI에 추가합니다."""
        chip = TagChip(tag_text)
        chip.delete_button.clicked.connect(lambda: self.remove_tag(tag_text))
        
        # 입력 필드 앞에 칩 추가
        self.chip_layout.insertWidget(self.chip_layout.count() - 1, chip)
        
    def remove_tag_chip(self, tag_text):
        """특정 태그 칩을 UI에서 제거합니다."""
        for i in range(self.chip_layout.count()):
            widget = self.chip_layout.itemAt(i).widget()
            if isinstance(widget, TagChip) and widget.tag_text == tag_text:
                widget.deleteLater()
                break
                
    def set_tags(self, tags):
        """태그 목록을 설정합니다."""
        # 기존 태그 칩들 제거
        self.clear_tags()
        
        # 새 태그들 추가
        self.tags = tags.copy()
        for tag in self.tags:
            self.create_tag_chip(tag)
            
        self.tags_changed.emit(self.tags.copy())
        
    def clear_tags(self):
        """모든 태그를 제거합니다."""
        # 기존 태그 칩들 제거
        for i in range(self.chip_layout.count() - 1, -1, -1):  # 뒤에서부터 제거
            widget = self.chip_layout.itemAt(i).widget()
            if isinstance(widget, TagChip):
                widget.deleteLater()
        
        self.tags.clear()
        
    def get_tags(self):
        """현재 태그 목록을 반환합니다."""
        return self.tags.copy()
        
    def get_tag_input_field(self):
        """태그 입력 필드를 반환합니다 (자동 완성 기능을 위해)."""
        return self.tag_input
        
    def update_completer_model(self, all_tags):
        """자동 완성 모델을 업데이트합니다."""
        if self.completer:
            # 현재 입력된 텍스트가 있으면 임시로 저장
            current_text = self.tag_input.text()
            cursor_position = self.tag_input.cursorPosition()
            
            # 모델 업데이트
            model = QStringListModel(all_tags)
            self.completer.setModel(model)
            
            # 현재 입력 텍스트와 커서 위치 복원
            self.tag_input.setText(current_text)
            self.tag_input.setCursorPosition(cursor_position)
            
    def on_completer_activated(self, text):
        """자동 완성에서 태그가 선택되었을 때 호출됩니다."""
        if text and text not in self.tags:
            self.add_tag(text)
            self.tag_input.clear()
            
    def get_completer(self):
        """자동 완성 객체를 반환합니다."""
        return self.completer
        
    def on_text_changed(self, text):
        """입력 텍스트가 변경될 때 호출됩니다."""
        # 2글자 이상 입력되면 자동 완성 팝업 표시
        if len(text) >= 2:
            self.completer.complete()
        else:
            # 2글자 미만이면 팝업 숨기기
            self.completer.popup().hide()
            
    def set_enabled(self, enabled):
        """위젯의 활성화/비활성화 상태를 설정합니다."""
        self.setEnabled(enabled)
        
        if not enabled:
            # 비활성화 시 입력 필드 클리어
            self.tag_input.clear()
            # 자동 완성 팝업 숨기기
            if self.completer:
                self.completer.popup().hide()
                
    def is_enabled(self):
        """위젯의 활성화 상태를 반환합니다."""
        return self.isEnabled() 