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

        self.tag_input.returnPressed.connect(self._on_return_pressed)

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

    def setup_completer(self):
        """자동 완성 기능을 설정합니다."""
        self.completer = QCompleter(self.completer_model, self)
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
            if tag_text not in self._tags:
                self._tags.append(tag_text)
                self._refresh_list()
                self.tags_changed.emit(self._tags)
                self.tag_input.clear()
            else:
                # 중복 태그인 경우 입력 필드만 클리어
                self.tag_input.clear()

    def remove_tag(self, tag_text):
        """특정 태그를 제거합니다."""
        if tag_text in self._tags:
            self._tags.remove(tag_text)
            self._refresh_list()
            self.tags_changed.emit(self._tags)

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

    def get_tags(self):
        """현재 태그 목록을 반환합니다."""
        return self._tags.copy()

    def get_tag_input_field(self):
        """태그 입력 필드를 반환합니다 (자동 완성 기능을 위해)."""
        return self.tag_input

    def update_completer_model(self, tags):
        if hasattr(self, 'completer') and self.completer:
            self.completer_model.setStringList(tags)

    def on_completer_activated(self, text):
        """자동 완성에서 태그가 선택되었을 때 호출됩니다."""
        if text and text not in self._tags:
            self._tags.append(text)
            self._refresh_list()
            self.tags_changed.emit(self._tags)
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

    def is_enabled(self):
        """위젯의 활성화 상태를 반환합니다."""
        return self.isEnabled()

    def clear_tags(self):
        self._tags = []
        self._refresh_list()
        self.tags_changed.emit([])

    def setup_ui(self):
        # 이 메서드는 이제 uic.loadUi로 대체됩니다.
        pass
