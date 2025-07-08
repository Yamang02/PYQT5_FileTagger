from PyQt5.QtWidgets import QFrame, QLabel, QPushButton
from PyQt5.uic import loadUi
from PyQt5.QtCore import pyqtSignal

class TagChip(QFrame):
    """
    개별 태그를 표시하는 칩 위젯입니다.
    태그 이름과 삭제 버튼을 포함합니다.
    """
    tag_removed = pyqtSignal(str) # 태그 텍스트를 인자로 전달하는 시그널

    def __init__(self, tag_text, parent=None):
        super().__init__(parent)
        self.tag_text = tag_text
        self.setup_ui()

    def setup_ui(self):
        """태그 칩의 UI를 설정합니다."""
        loadUi('ui/tag_chip.ui', self)
        self.tag_label.setText(self.tag_text)
        self.delete_button.clicked.connect(self._on_delete_button_clicked)

        # 스타일시트 적용
        self.setStyleSheet("""
            QFrame {
                background-color: #e3f2fd;
                border: 1px solid #2196f3;
                border-radius: 12px;
                padding: 2px;
            }
            QFrame:hover {
                background-color: #bbdefb;
            }
            QPushButton {
                border-radius: 8px;
                background-color: #90caf9;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #42a5f5;
            }
            QPushButton:pressed {
                background-color: #1e88e5;
            }
        """)

    def _on_delete_button_clicked(self):
        """삭제 버튼 클릭 시 tag_removed 시그널을 발생시킵니다."""
        self.tag_removed.emit(self.tag_text)
