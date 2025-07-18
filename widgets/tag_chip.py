from PyQt5.QtWidgets import QFrame
from PyQt5.uic import loadUi
from PyQt5.QtCore import pyqtSignal

class TagChip(QFrame):
    """
    개별 태그를 표시하는 칩 위젯입니다.
    태그 이름과 삭제 버튼을 포함합니다.
    """
    tag_removed = pyqtSignal(str) # 태그 텍스트를 인자로 전달하는 시그널
    clicked = pyqtSignal() # TagChip이 클릭되었을 때 발생하는 시그널

    def __init__(self, tag_text, parent=None):
        super().__init__(parent)
        self.tag_text = tag_text
        self.setup_ui()

    def setup_ui(self):
        """태그 칩의 UI를 설정합니다."""
        loadUi('ui/tag_chip.ui', self)
        self.tag_label.setText(self.tag_text)
        self.delete_button.clicked.connect(self._on_delete_button_clicked)

        

    def mousePressEvent(self, event):
        """마우스 클릭 이벤트를 처리하여 clicked 시그널을 발생시킵니다."""
        self.clicked.emit()
        super().mousePressEvent(event)

        

    def _on_delete_button_clicked(self):
        self.tag_removed.emit(self.tag_text)
