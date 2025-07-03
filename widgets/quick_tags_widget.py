from PyQt5.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QLabel,
    QScrollArea,
    QFrame,
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont


class QuickTagsWidget(QWidget):
    """
    자주 사용하는 태그를 빠르게 선택할 수 있는 위젯입니다.
    버튼 형태로 태그를 표시하고, 클릭 시 토글 방식으로 태그를 추가/제거합니다.
    """

    tag_toggled = pyqtSignal(str, bool)  # (tag_name, is_added) 시그널

    def __init__(self, parent=None):
        super().__init__(parent)
        self.quick_tags = []
        self.selected_tags = set()  # 현재 선택된 태그들
        self.tag_buttons = {}  # 태그명 -> 버튼 매핑
        self.is_enabled = True  # 위젯 활성화 상태 추적
        self.setup_ui()

    def setup_ui(self):
        """위젯의 UI를 설정합니다."""
        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # 제목 라벨
        title_label = QLabel("자주 사용하는 태그")
        title_label.setFont(QFont("Arial", 10, QFont.Bold))
        title_label.setStyleSheet("color: #333; padding: 4px;")
        main_layout.addWidget(title_label)

        # 스크롤 영역
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setMaximumHeight(120)
        self.scroll_area.setFrameStyle(QFrame.NoFrame)

        # 태그 버튼들을 담을 컨테이너
        self.button_container = QWidget()
        self.button_layout = QHBoxLayout(self.button_container)
        self.button_layout.setContentsMargins(4, 4, 4, 4)
        self.button_layout.setSpacing(6)
        self.button_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        # 스크롤 영역에 컨테이너 설정
        self.scroll_area.setWidget(self.button_container)
        main_layout.addWidget(self.scroll_area)

    def set_quick_tags(self, tags):
        """빠른 선택 태그 목록을 설정합니다."""
        self.quick_tags = tags.copy()
        self.create_tag_buttons()

    def create_tag_buttons(self):
        """태그 버튼들을 생성합니다."""
        # 기존 버튼들 제거
        for button in self.tag_buttons.values():
            button.deleteLater()
        self.tag_buttons.clear()

        # 새 버튼들 생성
        for tag in self.quick_tags:
            button = QPushButton(tag)
            button.setCheckable(True)  # 토글 가능하도록 설정
            button.setMaximumHeight(28)
            button.setStyleSheet("""
                QPushButton {
                    background-color: #f0f0f0;
                    border: 1px solid #ccc;
                    border-radius: 14px;
                    padding: 4px 12px;
                    font-size: 9px;
                    color: #333;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                    border: 1px solid #999;
                }
                QPushButton:checked {
                    background-color: #2196f3;
                    color: white;
                    border: 1px solid #1976d2;
                }
                QPushButton:checked:hover {
                    background-color: #1976d2;
                }
            """)

            # 시그널 연결
            button.toggled.connect(
                lambda checked, tag=tag: self.on_tag_button_toggled(tag, checked)
            )

            # 레이아웃에 추가
            self.button_layout.addWidget(button)
            self.tag_buttons[tag] = button

        # 오른쪽 공간 채우기
        self.button_layout.addStretch()

    def on_tag_button_toggled(self, tag, checked):
        """태그 버튼이 토글되었을 때 호출됩니다."""
        # 위젯이 비활성화된 경우 이벤트 무시
        if not self.is_enabled:
            return

        if checked:
            self.selected_tags.add(tag)
        else:
            self.selected_tags.discard(tag)

        # 시그널 방출
        self.tag_toggled.emit(tag, checked)

    def set_selected_tags(self, tags):
        """현재 선택된 태그들을 설정합니다."""
        self.selected_tags = set(tags)

        # 버튼 상태 업데이트
        for tag, button in self.tag_buttons.items():
            button.setChecked(tag in self.selected_tags)

    def get_selected_tags(self):
        """현재 선택된 태그들을 반환합니다."""
        return list(self.selected_tags)

    def clear_selection(self):
        """모든 선택을 해제합니다."""
        self.selected_tags.clear()
        for button in self.tag_buttons.values():
            button.setChecked(False)

    def add_quick_tag(self, tag):
        """빠른 선택 태그 목록에 새 태그를 추가합니다."""
        if tag not in self.quick_tags:
            self.quick_tags.append(tag)
            self.create_tag_buttons()

    def remove_quick_tag(self, tag):
        """빠른 선택 태그 목록에서 태그를 제거합니다."""
        if tag in self.quick_tags:
            self.quick_tags.remove(tag)
            self.selected_tags.discard(tag)
            self.create_tag_buttons()

    def set_enabled(self, enabled: bool):
        """위젯 전체 활성/비활성 상태를 설정합니다."""
        self.is_enabled = enabled  # 내부 상태 업데이트
        
        # 위젯 자체 비활성화
        self.setEnabled(enabled)
        
        # 모든 버튼 개별 비활성화
        for button in self.tag_buttons.values():
            button.setEnabled(enabled)
            # 버튼 스타일도 비활성화 상태에 맞게 조정
            if not enabled:
                button.setStyleSheet("""
                    QPushButton {
                        background-color: #f5f5f5;
                        border: 1px solid #ddd;
                        border-radius: 14px;
                        padding: 4px 12px;
                        font-size: 9px;
                        color: #999;
                    }
                """)
            else:
                # 활성화 상태 스타일 복원
                button.setStyleSheet("""
                    QPushButton {
                        background-color: #f0f0f0;
                        border: 1px solid #ccc;
                        border-radius: 14px;
                        padding: 4px 12px;
                        font-size: 9px;
                        color: #333;
                    }
                    QPushButton:hover {
                        background-color: #e0e0e0;
                        border: 1px solid #999;
                    }
                    QPushButton:checked {
                        background-color: #2196f3;
                        color: white;
                        border: 1px solid #1976d2;
                    }
                    QPushButton:checked:hover {
                        background-color: #1976d2;
                    }
                """)
