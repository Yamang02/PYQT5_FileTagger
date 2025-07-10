from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QDialogButtonBox, QLabel, QScrollArea, QWidget, QGridLayout
from widgets.tag_chip import TagChip

class BatchRemoveTagsDialog(QDialog):
    def __init__(self, tag_manager, target_path, parent=None):
        super().__init__(parent)
        self.tag_manager = tag_manager
        self.target_path = target_path
        self.setWindowTitle("일괄 태그 제거")
        self.setMinimumWidth(400)

        self.all_tags = []
        self.tag_chips = []

        self.setup_ui()
        self.populate_tags()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        self.target_label = QLabel()
        self.target_label.setWordWrap(True)
        layout.addWidget(self.target_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("제거할 태그 검색...")
        self.search_input.textChanged.connect(self.filter_tags)
        layout.addWidget(self.search_input)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        container = QWidget()
        self.chip_layout = QGridLayout(container)
        scroll_area.setWidget(container)
        layout.addWidget(scroll_area)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        if isinstance(self.target_path, list):
            self.target_label.setText(f"<b>대상 파일:</b><br>{'<br>'.join(self.target_path[:5])}")
            if len(self.target_path) > 5:
                self.target_label.setText(self.target_label.text() + "...")
        elif isinstance(self.target_path, str):
            self.target_label.setText(f"<b>대상 디렉토리:</b><br>{self.target_path}")

    def populate_tags(self):
        files = []
        if isinstance(self.target_path, list):
            files = self.target_path
        elif isinstance(self.target_path, str):
            files = self.tag_manager.get_files_in_directory(self.target_path, recursive=True)

        if not files:
            return

        all_tags_set = set()
        for file_path in files:
            tags = self.tag_manager.get_tags_for_file(file_path)
            all_tags_set.update(tags)

        self.all_tags = sorted(list(all_tags_set))
        self.update_chip_layout(self.all_tags)

    def filter_tags(self, text):
        if not text:
            self.update_chip_layout(self.all_tags)
            return

        filtered_tags = [tag for tag in self.all_tags if text.lower() in tag.lower()]
        self.update_chip_layout(filtered_tags)

    def update_chip_layout(self, tags):
        self._clear_layout()
        self.tag_chips = []
        row, col = 0, 0
        max_cols = 3

        for tag in tags:
            chip = TagChip(tag, checkable=True)
            self.tag_chips.append(chip)
            self.chip_layout.addWidget(chip, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def _clear_layout(self):
        while self.chip_layout.count():
            child = self.chip_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def get_tags_to_remove(self):
        return [chip.tag_text for chip in self.tag_chips if chip.is_checked()]