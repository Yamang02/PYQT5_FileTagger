from PyQt5.QtWidgets import QDialog, QMessageBox, QListWidgetItem
from PyQt5.uic import loadUi
from core.custom_tag_manager import CustomTagManager

class CustomTagDialog(QDialog):
    def __init__(self, custom_tag_manager: CustomTagManager, parent=None):
        super().__init__(parent)
        loadUi('ui/custom_tag_dialog.ui', self)
        self.custom_tag_manager = custom_tag_manager
        self.load_tags()
        self.setup_connections()

    def load_tags(self):
        tags = self.custom_tag_manager.load_custom_quick_tags()
        self.tag_list_widget.clear()
        for tag in tags:
            self.tag_list_widget.addItem(tag)

    def setup_connections(self):
        self.add_tag_button.clicked.connect(self._add_tag)
        self.remove_tag_button.clicked.connect(self._remove_selected_tag)
        self.move_up_button.clicked.connect(self._move_tag_up)
        self.move_down_button.clicked.connect(self._move_tag_down)
        self.buttonBox.accepted.connect(self._save_tags)
        self.buttonBox.rejected.connect(self.reject)
        self.tag_input_line_edit.returnPressed.connect(self._add_tag)
        

    def _add_tag(self):
        new_tag = self.tag_input_line_edit.text().strip()
        if new_tag:
            # 중복 태그 확인
            for i in range(self.tag_list_widget.count()):
                if self.tag_list_widget.item(i).text() == new_tag:
                    QMessageBox.warning(self, "경고", "이미 존재하는 태그입니다.")
                    return
            self.tag_list_widget.addItem(new_tag)
            self.tag_input_line_edit.clear()
        else:
            QMessageBox.warning(self, "경고", "태그를 입력해주세요.")

    def _remove_selected_tag(self):
        selected_items = self.tag_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "경고", "제거할 태그를 선택해주세요.")
            return
        
        for item in selected_items:
            self.tag_list_widget.takeItem(self.tag_list_widget.row(item))

    def _move_tag_up(self):
        current_row = self.tag_list_widget.currentRow()
        if current_row > 0:
            item = self.tag_list_widget.takeItem(current_row)
            self.tag_list_widget.insertItem(current_row - 1, item)
            self.tag_list_widget.setCurrentRow(current_row - 1)

    def _move_tag_down(self):
        current_row = self.tag_list_widget.currentRow()
        if current_row < self.tag_list_widget.count() - 1:
            item = self.tag_list_widget.takeItem(current_row)
            self.tag_list_widget.insertItem(current_row + 1, item)
            self.tag_list_widget.setCurrentRow(current_row + 1)

    def _save_tags(self):
        tags_to_save = []
        for i in range(self.tag_list_widget.count()):
            tags_to_save.append(self.tag_list_widget.item(i).text())
        
        if self.custom_tag_manager.save_custom_quick_tags(tags_to_save):
            QMessageBox.information(self, "저장", "태그가 성공적으로 저장되었습니다.")
            self.accept()
        else:
            QMessageBox.critical(self, "오류", "태그 저장에 실패했습니다.")

    def get_updated_tags(self) -> list[str]:
        tags = []
        for i in range(self.tag_list_widget.count()):
            tags.append(self.tag_list_widget.item(i).text())
        return tags
