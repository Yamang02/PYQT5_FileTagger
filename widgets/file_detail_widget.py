from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextBrowser
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.uic import loadUi
import os
import datetime

import logging

logger = logging.getLogger(__name__)

from widgets.tag_chip import TagChip
from core.tag_manager import TagManager

class FileDetailWidget(QWidget):
    file_tags_changed = pyqtSignal() # 파일 태그 변경 시그널

    def __init__(self, tag_manager: TagManager, parent=None):
        super().__init__(parent)
        self.tag_manager = tag_manager
        self.current_file_path = None # 현재 선택된 파일 경로 저장
        self.setup_ui()

    def setup_ui(self):
        loadUi('ui/file_detail_content_widget.ui', self)
        self.thumbnail_label.setAlignment(Qt.AlignCenter)
        self.clear_preview()

        # 모든 태그 삭제 버튼 연결
        if hasattr(self, 'clear_all_tags_button') and self.clear_all_tags_button is not None:
            print(f"DEBUG: clear_all_tags_button found. Connecting...")
            self.clear_all_tags_button.clicked.connect(self._on_clear_all_tags_clicked)
            print(f"DEBUG: clear_all_tags_button connected.")
        else:
            print(f"DEBUG: clear_all_tags_button NOT found.")

    def update_preview(self, file_path):
        print(f"DEBUG: update_preview called for {file_path}")
        self.current_file_path = file_path # 현재 파일 경로 저장
        self.clear_preview()

        if not file_path or not os.path.isfile(file_path):
            print(f"DEBUG: Invalid file_path: {file_path}")
            return

        try:
            # --- 썸네일 업데이트 ---
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                # QLabel의 현재 크기를 사용하여 스케일링
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
        except Exception as e:
            self.clear_preview()
            self.thumbnail_label.setText(f"오류: {e}")

    def clear_preview(self):
        self.thumbnail_label.setText("파일을 선택하세요.")
        self.thumbnail_label.setPixmap(QPixmap()) # 기존 이미지 제거
        self.metadata_browser.clear()
        self._clear_tag_chips()

    def _refresh_tag_chips(self, tags):
        self._clear_tag_chips()
        row = 0
        col = 0
        max_cols = 3  # 한 행에 표시할 최대 태그 칩 수

        for tag in tags:
            chip = TagChip(tag)
            chip.tag_removed.connect(self._on_tag_chip_removed)
            print(f"DEBUG: TagChip {tag} delete button connected in FileDetailWidget.") # 진단용
            self.tag_chip_layout.addWidget(chip, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def _clear_tag_chips(self):
        print("DEBUG: _clear_tag_chips called.") # 진단용
        # 기존 칩 모두 제거
        while self.tag_chip_layout.count() > 0:
            item = self.tag_chip_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _on_tag_chip_removed(self, tag_text):
        print(f"DEBUG: _on_tag_chip_removed called. tag_text: {tag_text}, current_file_path: {self.current_file_path}") # 진단용
        if self.current_file_path:
            success = self.tag_manager.remove_tags_from_file(self.current_file_path, [tag_text])
            print(f"DEBUG: tag_manager.remove_tags_from_file returned: {success}") # 진단용
            if success:
                print(f"DEBUG: Tag removed from DB. Updating UI for {self.current_file_path}") # 진단용
                self.update_preview(self.current_file_path) # UI 업데이트
                self.file_tags_changed.emit() # 태그 변경 시그널 발생
            else:
                print(f"DEBUG: Tag removal from DB failed for {tag_text} on {self.current_file_path}") # 진단용

    def _on_clear_all_tags_clicked(self):
        print(f"DEBUG: _on_clear_all_tags_clicked called. current_file_path: {self.current_file_path}") # 진단용
        if self.current_file_path:
            success = self.tag_manager.clear_all_tags_from_file(self.current_file_path)
            print(f"DEBUG: tag_manager.clear_all_tags_from_file returned: {success}") # 진단용
            if success:
                print(f"DEBUG: All tags cleared from DB. Updating UI for {self.current_file_path}") # 진단용
                self.update_preview(self.current_file_path) # UI 업데이트
                self.file_tags_changed.emit() # 태그 변경 시그널 발생
            else:
                print(f"DEBUG: All tags clearing from DB failed for {self.current_file_path}") # 진단용
