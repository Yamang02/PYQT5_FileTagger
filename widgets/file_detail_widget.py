from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextBrowser
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from PyQt5.uic import loadUi
import os
import datetime

from widgets.tag_chip import TagChip
from core.tag_manager import TagManager

class FileDetailWidget(QWidget):
    def __init__(self, tag_manager: TagManager, parent=None):
        super().__init__(parent)
        self.tag_manager = tag_manager
        self.setup_ui()

    def setup_ui(self):
        loadUi('ui/file_detail_content_widget.ui', self)
        self.thumbnail_label.setAlignment(Qt.AlignCenter)
        self.clear_preview()

    def update_preview(self, file_path):
        self.clear_preview()

        if not file_path or not os.path.isfile(file_path):
            return

        # --- 썸네일 업데이트 ---
        pixmap = QPixmap(file_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(self.thumbnail_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.thumbnail_label.setPixmap(scaled_pixmap)
            self.thumbnail_label.setText("")
        else:
            self.thumbnail_label.setText("미리보기 불가")

        # --- 메타데이터 업데이트 ---
        file_info = f"<b>파일 이름:</b> {os.path.basename(file_path)}<br>"
        file_info += f"<b>경로:</b> {file_path}<br>"
        try:
            file_size = os.path.getsize(file_path)
            file_info += f"<b>크기:</b> {file_size / (1024*1024):.2f} MB<br>"
            mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
            file_info += f"<b>수정일:</b> {mod_time.strftime('%Y-%m-%d %H:%M:%S')}<br>"
        except Exception as e:
            file_info += f"<b>정보 로드 오류:</b> {e}<br>"
        self.metadata_browser.setHtml(file_info)

        # --- 태그 칩 업데이트 ---
        tags = self.tag_manager.get_tags_for_file(file_path)
        self._refresh_tag_chips(tags)

    def clear_preview(self):
        self.thumbnail_label.setText("파일을 선택하세요.")
        self.thumbnail_label.setPixmap(QPixmap()) # 기존 이미지 제거
        self.metadata_browser.clear()
        self._clear_tag_chips()

    def _refresh_tag_chips(self, tags):
        self._clear_tag_chips()
        for tag in tags:
            chip = TagChip(tag)
            # 파일 상세 정보에서는 태그 삭제 버튼이 필요 없으므로 숨김
            chip.delete_button.setVisible(False)
            self.tag_chip_layout.insertWidget(self.tag_chip_layout.count() - 1, chip)

    def _clear_tag_chips(self):
        while self.tag_chip_layout.count() > 1:
            item = self.tag_chip_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()