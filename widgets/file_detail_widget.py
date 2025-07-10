from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextBrowser, QStackedWidget
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, pyqtSignal, QUrl
from PyQt5.uic import loadUi
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
import os
import datetime
import logging

logger = logging.getLogger(__name__)

from widgets.tag_chip import TagChip
from core.tag_manager import TagManager
from core.local_server import LocalFileServer # LocalFileServer 임포트

class FileDetailWidget(QWidget):
    file_tags_changed = pyqtSignal()

    IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.bmp', '.gif']
    VIDEO_EXTENSIONS = ['.mp4', '.webm'] # AVI, MKV 등은 웹에서 표준 지원하지 않으므로 제외
    TEXT_EXTENSIONS = ['.txt', '.md', '.py', '.js', '.html', '.css']
    # MAX_VIDEO_SIZE_MB = 50 # Base64 인코딩 시 필요했으므로 제거

    def __init__(self, tag_manager: TagManager, file_server: LocalFileServer, parent=None):
        super().__init__(parent)
        self.tag_manager = tag_manager
        self.file_server = file_server # LocalFileServer 인스턴스 저장
        self.current_file_path = None
        self.setup_ui()

    def setup_ui(self):
        loadUi('ui/file_detail_content_widget.ui', self)

        self.image_preview_label = QLabel("이미지 미리보기")
        self.image_preview_label.setAlignment(Qt.AlignCenter)
        self.image_preview_page.setLayout(QVBoxLayout())
        self.image_preview_page.layout().addWidget(self.image_preview_label)

        self.web_engine_view = QWebEngineView()
        self.video_preview_page.setLayout(QVBoxLayout())
        self.video_preview_page.layout().addWidget(self.web_engine_view)

        self.web_engine_view.loadFinished.connect(self._on_web_engine_load_finished)
        self.web_engine_view.loadProgress.connect(self._on_web_engine_load_progress)
        self.web_engine_view.loadStarted.connect(self._on_web_engine_load_started)
        self.web_engine_view.renderProcessTerminated.connect(self._on_web_engine_render_process_terminated)

        self.text_browser = QTextBrowser()
        self.text_preview_page.setLayout(QVBoxLayout())
        self.text_preview_page.layout().addWidget(self.text_browser)

        self.clear_preview()

        if hasattr(self, 'clear_all_tags_button') and self.clear_all_tags_button is not None:
            self.clear_all_tags_button.clicked.connect(self._on_clear_all_tags_clicked)

    def update_preview(self, file_path):
        self.current_file_path = file_path
        self.clear_preview()

        if not file_path or not os.path.isfile(file_path):
            self.preview_stacked_widget.setCurrentWidget(self.unsupported_preview_page)
            return

        try:
            file_ext = os.path.splitext(file_path)[1].lower()

            if file_ext in self.IMAGE_EXTENSIONS:
                self.preview_stacked_widget.setCurrentWidget(self.image_preview_page)
                pixmap = QPixmap(file_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(self.image_preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.image_preview_label.setPixmap(scaled_pixmap)
                else:
                    self.image_preview_label.setText("이미지 로드 실패")
            
            elif file_ext in self.VIDEO_EXTENSIONS:
                self.preview_stacked_widget.setCurrentWidget(self.video_preview_page)
                video_url = self.file_server.get_file_url(file_path)
                # HTML 비디오 태그를 사용하여 QWebEngineView에 로드
                html_content = f"""
                <html>
                <body style="background-color:black; margin:0; display:flex; justify-content:center; align-items:center; height:100vh;">
                    <video controls autoplay muted style="max-width:100%; max-height:100%;">
                        <source src="{video_url}" type="video/{file_ext[1:]}">
                        Your browser does not support the video tag.
                    </video>
                </body>
                </html>
                """
                self.web_engine_view.setHtml(html_content)
                self.web_engine_view.setHtml(html_content)

            elif file_ext in self.TEXT_EXTENSIONS:
                self.preview_stacked_widget.setCurrentWidget(self.text_preview_page)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read(1024 * 5)
                        if file_ext == '.md':
                            self.text_browser.setMarkdown(content)
                        else:
                            self.text_browser.setPlainText(content)
                except Exception as e:
                    self.text_browser.setPlainText(f"파일을 읽을 수 없습니다: {e}")
            else:
                self.preview_stacked_widget.setCurrentWidget(self.unsupported_preview_page)

            self._update_metadata(file_path)
            tags = self.tag_manager.get_tags_for_file(file_path)
            self._refresh_tag_chips(tags)

        except Exception as e:
            logger.error(f"Error updating preview for {file_path}: {e}")
            self.clear_preview()
            self.preview_stacked_widget.setCurrentWidget(self.unsupported_preview_page)

    def _update_metadata(self, file_path):
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

    def clear_preview(self):
        self.web_engine_view.setUrl(QUrl("about:blank")) # 웹뷰 초기화
        self.image_preview_label.clear()
        self.image_preview_label.setText("파일을 선택하세요.")
        self.text_browser.clear()
        self.metadata_browser.clear()
        self._clear_tag_chips()
        self.preview_stacked_widget.setCurrentWidget(self.unsupported_preview_page)
        self.unsupported_label.setText("미리보기를 지원하지 않는 형식입니다.")

    def _refresh_tag_chips(self, tags):
        self._clear_tag_chips()
        row, col, max_cols = 0, 0, 3
        for tag in tags:
            chip = TagChip(tag)
            chip.tag_removed.connect(self._on_tag_chip_removed)
            self.tag_chip_layout.addWidget(chip, row, col)
            col += 1
            if col >= max_cols:
                col, row = 0, row + 1

    def _clear_tag_chips(self):
        while self.tag_chip_layout.count() > 0:
            item = self.tag_chip_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _on_tag_chip_removed(self, tag_text):
        if self.current_file_path:
            success = self.tag_manager.remove_tags_from_file(self.current_file_path, [tag_text])
            if success:
                self.update_preview(self.current_file_path)
                self.file_tags_changed.emit()

    def _on_clear_all_tags_clicked(self):
        if self.current_file_path:
            success = self.tag_manager.clear_all_tags_from_file(self.current_file_path)
            if success:
                self.update_preview(self.current_file_path)
                self.file_tags_changed.emit()

    def _on_web_engine_load_finished(self, ok):
        if ok:
            logger.info("QWebEngineView: Page loaded successfully.")
            # JavaScript를 사용하여 비디오 재생 시도 및 오류 로깅
            script = """
            var video = document.querySelector('video');
            if (video) {
                console.log('Video element found. Attempting to play...');
                video.play().then(() => {
                    console.log('Video playback started successfully.');
                }).catch(error => {
                    console.error('Video playback failed:', error.name, error);
                });
                video.onerror = function() {
                    console.error('Video error:', video.error.code, video.error.message);
                };
            } else {
                console.log('Video element not found.');
            }
            """
            self.web_engine_view.page().runJavaScript(script)
        else:
            logger.error("QWebEngineView: Page failed to load.")

    def _on_web_engine_load_progress(self, progress):
        logger.debug(f"QWebEngineView: Loading progress: {progress}%")

    def _on_web_engine_load_started(self):
        logger.info("QWebEngineView: Page load started.")

    def _on_web_engine_render_process_terminated(self, reason):
        logger.critical(f"QWebEngineView: Render process terminated. Reason: {reason}")
        # RenderProcessTerminationReason 열거형 값에 따라 메시지 출력
        if reason == QWebEngineView.RenderProcessTerminationReason.Crash:
            logger.critical("QWebEngineView: Render process crashed.")
        elif reason == QWebEngineView.RenderProcessTerminationReason.Oom:
            logger.critical("QWebEngineView: Render process out of memory.")
        elif reason == QWebEngineView.RenderProcessTerminationReason.CrashedWithErrors:
            logger.critical("QWebEngineView: Render process crashed with errors.")
        else:
            logger.critical("QWebEngineView: Render process terminated for unknown reason.")

    
