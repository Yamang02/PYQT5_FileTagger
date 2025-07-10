from PyQt5.QtWidgets import QDialog, QMessageBox, QListWidgetItem, QVBoxLayout, QListWidget, QLineEdit, QPushButton, QDialogButtonBox, QLabel
from PyQt5.QtCore import Qt

class BatchRemoveTagsDialog(QDialog):
    def __init__(self, tag_manager, target_path, parent=None):
        super().__init__(parent)
        self.tag_manager = tag_manager
        self.target_path = target_path
        self.setWindowTitle("일괄 태그 제거")
        self.setMinimumWidth(400)

        self.all_tags = []
        self.tags_to_remove = []

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

        self.tags_list_widget = QListWidget()
        layout.addWidget(self.tags_list_widget)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        # 대상 경로 표시
        if isinstance(self.target_path, list):
            self.target_label.setText(f"<b>대상 파일:</b><br>{'<br>'.join(self.target_path[:5])}")
            if len(self.target_path) > 5:
                self.target_label.setText(self.target_label.text() + "...")
        elif isinstance(self.target_path, str):
            self.target_label.setText(f"<b>대상 디렉토리:</b><br>{self.target_path}")

    def populate_tags(self):
        # 대상 경로의 모든 파일에서 태그를 수집
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
        self.update_list_widget(self.all_tags)

    def filter_tags(self, text):
        if not text:
            self.update_list_widget(self.all_tags)
            return

        filtered_tags = [tag for tag in self.all_tags if text.lower() in tag.lower()]
        self.update_list_widget(filtered_tags)

    def update_list_widget(self, tags):
        self.tags_list_widget.clear()
        for tag in tags:
            item = QListWidgetItem(tag)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.tags_list_widget.addItem(item)

    def get_tags_to_remove(self):
        self.tags_to_remove = []
        for i in range(self.tags_list_widget.count()):
            item = self.tags_list_widget.item(i)
            if item.checkState() == Qt.Checked:
                self.tags_to_remove.append(item.text())
        return self.tags_to_remove
