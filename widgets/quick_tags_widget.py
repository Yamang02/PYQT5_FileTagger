from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton, QMessageBox
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5 import uic
from core.custom_tag_manager import CustomTagManager

class QuickTagsWidget(QWidget):
    """
    자주 사용하는 태그를 빠르게 선택할 수 있는 위젯입니다.
    버튼 형태로 태그를 표시하고, 클릭 시 토글 방식으로 태그를 추가/제거합니다.
    """

    tag_toggled = pyqtSignal(str, bool)  # (tag_name, is_added) 시그널
    tags_changed = pyqtSignal(list)

    def __init__(self, custom_tag_manager: CustomTagManager, parent=None):
        super().__init__(parent)
        uic.loadUi('ui/quick_tags_widget.ui', self)
        self.layout = self.findChild(QHBoxLayout, 'horizontalLayout') # .ui 파일에서 로드된 레이아웃 참조
        self.layout.setAlignment(Qt.AlignLeft)  # 왼쪽 정렬 명시
        self.custom_tag_manager = custom_tag_manager
        self._selected_tags = []
        self._buttons = {}
        self.is_enabled = True  # 위젯 활성화 상태 추적
        self.load_quick_tags() # 커스텀 태그 로드

    def load_quick_tags(self):
        self._quick_tags = self.custom_tag_manager.load_custom_quick_tags()
        # 기존 버튼/레이아웃 제거
        try:
            for btn in self._buttons.values():
                self.layout.removeWidget(btn)
                btn.deleteLater()
            self._buttons.clear()
            self._init_buttons()
        except RuntimeError as e:
            # 위젯이 삭제된 경우 무시
            if "wrapped C/C++ object" in str(e):
                return
            else:
                raise

    def _init_buttons(self):
        for tag in self._quick_tags:
            btn = QPushButton(tag, self)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, t=tag: self._on_btn_clicked(t, checked))
            self.layout.addWidget(btn)
            self._buttons[tag] = btn


    def _on_btn_clicked(self, tag, checked):
        if checked:
            if tag not in self._selected_tags:
                self._selected_tags.append(tag)
            else:
                # 중복 선택 방지(이론상 불필요, 안전장치)
                QMessageBox.warning(self, "중복 태그", f"이미 선택된 태그입니다: {tag}")
        else:
            if tag in self._selected_tags:
                self._selected_tags.remove(tag)
        self.tags_changed.emit(self._selected_tags)

    def set_selected_tags(self, tags):
        self._selected_tags = list(tags)
        for tag, btn in self._buttons.items():
            btn.setChecked(tag in self._selected_tags)

    def set_enabled(self, enabled: bool):
        """위젯 전체 활성/비활성 상태를 설정합니다."""
        self.is_enabled = enabled  
        
        self.setEnabled(enabled)
        
        for button in self._buttons.values():
            button.setEnabled(enabled)
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

    def clear_selection(self):
        self._selected_tags = []
        for btn in self._buttons.values():
            btn.setChecked(False)
