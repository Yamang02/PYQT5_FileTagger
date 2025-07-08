from PyQt5.QtWidgets import QDialog, QMessageBox, QListWidgetItem
from PyQt5.uic import loadUi

class BatchRemoveTagsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        loadUi('ui/batch_remove_tags_dialog.ui', self)
        self.tags_to_remove = []
        self.setup_connections()

    def setup_connections(self):
        self.add_tag_button.clicked.connect(self._add_tag)
        self.remove_selected_tag_button.clicked.connect(self._remove_selected_tag)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def _add_tag(self):
        new_tag_text = self.tag_input_line_edit.text().strip()
        if new_tag_text:
            tags = [tag.strip() for tag in new_tag_text.split(',') if tag.strip()]
            for tag in tags:
                if tag not in self.tags_to_remove:
                    self.tags_to_remove.append(tag)
                    self.tags_to_remove_list_widget.addItem(tag)
            self.tag_input_line_edit.clear()
        else:
            QMessageBox.warning(self, "경고", "제거할 태그를 입력해주세요.")

    def _remove_selected_tag(self):
        selected_items = self.tags_to_remove_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "경고", "제거할 태그를 선택해주세요.")
            return
        
        for item in selected_items:
            tag_text = item.text()
            self.tags_to_remove.remove(tag_text)
            self.tags_to_remove_list_widget.takeItem(self.tags_to_remove_list_widget.row(item))

    def get_tags_to_remove(self) -> list[str]:
        return self.tags_to_remove
