from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QLabel, QPushButton, QFrame, QVBoxLayout, QScrollArea, QCompleter, QListWidget, QMessageBox
from PyQt5.QtCore import pyqtSignal, Qt, QStringListModel
from PyQt5.QtGui import QFont
from PyQt5 import uic


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
        uic.loadUi('ui/tag_chip.ui', self)
        self.tag_label = self.findChild(QLabel, 'tag_label')
        self.delete_button = self.findChild(QPushButton, 'delete_button')
        self.tag_label.setText(self.tag_text)

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
        uic.loadUi('ui/tag_input_widget.ui', self)
        
        # .ui 파일에서 로드된 위젯 참조
        self.scroll_area = self.findChild(QScrollArea, 'scroll_area')
        self.chip_container = self.findChild(QWidget, 'chip_container')
        self.chip_layout = self.findChild(QHBoxLayout, 'chip_layout')
        self.tag_input = self.findChild(QLineEdit, 'tag_input')
        
        self._tags = []

        self.tag_input.returnPressed.connect(self.add_tag_from_input)

        # completer 및 모델 초기화
        self.completer_model = QStringListModel()
        self.setup_completer() # setup_completer 호출

    def _on_return_pressed(self):
        tag = self.tag_input.text().strip()
        if not tag:
            QMessageBox.warning(self, "입력 오류", "빈 태그는 추가할 수 없습니다.")
            return
        if tag in self._tags:
            QMessageBox.warning(self, "중복 태그", "이미 추가된 태그입니다.")
            return
        self._tags.append(tag)
        self.tag_input.clear()
        self._refresh_list()
        self.tags_changed.emit(self._tags)

    def _on_item_double_clicked(self, item):
        # 이 메서드는 더 이상 사용되지 않습니다. 태그 칩의 삭제 버튼을 사용합니다.
        pass

    def _refresh_list(self):
        # 기존 칩 제거
        for i in reversed(range(self.chip_layout.count() - 1)): # 마지막 위젯(tag_input) 제외
            widget = self.chip_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

        # 새 칩 추가
        for tag in self._tags:
            self.create_tag_chip(tag)

    def set_tags(self, tags):
        self._tags = list(tags)
        self._refresh_list()

    def set_enabled(self, enabled: bool):
        self.tag_input.setEnabled(enabled)
        # 태그 칩들도 활성/비활성화
        for i in range(self.chip_layout.count()):
            widget = self.chip_layout.itemAt(i).widget()
            if widget is not None and isinstance(widget, TagChip):
                widget.setEnabled(enabled)

    def setup_ui(self):
        # 이 메서드는 이제 uic.loadUi로 대체됩니다.
        pass
