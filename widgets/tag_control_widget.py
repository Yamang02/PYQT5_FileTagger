from PyQt5.QtWidgets import QWidget, QCompleter, QMessageBox
from PyQt5.uic import loadUi
from PyQt5.QtCore import Qt, QStringListModel

from widgets.tag_chip import TagChip

class TagControlWidget(QWidget):
    def __init__(self, tag_manager, parent=None):
        super().__init__(parent)
        self.tag_manager = tag_manager
        self.current_file_path = None
        self._tags = []

        self.setup_ui()
        self.setup_completer()
        self.connect_signals()

    def setup_ui(self):
        loadUi('ui/tag_control_widget.ui', self)
        self.set_enabled(False) # 처음에는 비활성화

    def connect_signals(self):
        self.tag_input.returnPressed.connect(self.add_tag_from_input)
        self.save_button.clicked.connect(self.save_tags)

    def setup_completer(self):
        self.completer_model = QStringListModel()
        self.completer = QCompleter(self.completer_model, self)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.tag_input.setCompleter(self.completer)
        self.update_completer_model()

    def update_completer_model(self):
        all_tags = self.tag_manager.get_all_tags()
        self.completer_model.setStringList(all_tags)

    def update_for_file(self, file_path):
        self.current_file_path = file_path
        self.selected_file_label.setText(f"파일: {file_path}")
        
        tags = self.tag_manager.get_tags_for_file(file_path)
        self.set_tags(tags)
        self.set_enabled(True)

    def clear_view(self):
        self.current_file_path = None
        self.selected_file_label.setText("선택된 파일 없음")
        self.set_tags([])
        self.set_enabled(False)

    def set_tags(self, tags):
        self._tags = list(tags)
        self._refresh_chip_layout()

    def add_tag_from_input(self):
        tag_text = self.tag_input.text().strip()
        if not tag_text:
            return
        
        if tag_text not in self._tags:
            self._tags.append(tag_text)
            self._refresh_chip_layout()
        self.tag_input.clear()

    def remove_tag(self, tag_text):
        if tag_text in self._tags:
            self._tags.remove(tag_text)
            self._refresh_chip_layout()

    def _refresh_chip_layout(self):
        # 기존 칩 모두 제거 (스페이서 제외)
        while self.chip_layout.count() > 1:
            item = self.chip_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 현재 태그 목록으로 새 칩 생성 및 추가
        for tag in self._tags:
            chip = TagChip(tag)
            chip.delete_button.clicked.connect(lambda _, t=tag: self.remove_tag(t))
            self.chip_layout.insertWidget(self.chip_layout.count() - 1, chip)

    def save_tags(self):
        if self.current_file_path:
            self.tag_manager.update_tags(self.current_file_path, self._tags)
            self.update_completer_model() # 새 태그가 추가되었을 수 있으므로 자동완성 모델 업데이트
            QMessageBox.information(self, "저장 완료", f"'{self.current_file_path}' 파일의 태그가 저장되었습니다.")

    def set_enabled(self, enabled):
        self.tag_input.setEnabled(enabled)
        self.save_button.setEnabled(enabled)
        # 칩들도 활성화/비활성화
        for i in range(self.chip_layout.count() - 1):
            widget = self.chip_layout.itemAt(i).widget()
            if widget:
                widget.setEnabled(enabled)
