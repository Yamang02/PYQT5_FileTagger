from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextBrowser, QStackedWidget, QPushButton, QSlider, QHBoxLayout, QToolButton, QApplication
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, pyqtSignal, QUrl
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QStyle
import os
import datetime
import logging

# 비디오 재생을 위한 모듈 임포트
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget

logger = logging.getLogger(__name__)

from widgets.tag_chip import TagChip
from core.tag_manager import TagManager



class FileDetailWidget(QWidget):
    file_tags_changed = pyqtSignal()

    IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.bmp', '.gif']
    VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mkv', '.mov', '.webm'] # 추가된 비디오 확장자
    TEXT_EXTENSIONS = ['.txt', '.md', '.py', '.js', '.html', '.css']
    # MAX_VIDEO_SIZE_MB = 50 # Base64 인코딩 시 필요했으므로 제거

    def __init__(self, tag_manager: TagManager, parent=None):
        super().__init__(parent)
        self.tag_manager = tag_manager
        self.current_file_path = None
        self.media_player = None # QMediaPlayer 인스턴스 초기화
        self.setup_ui()

    def setup_ui(self):
        loadUi('ui/file_detail_content_widget.ui', self)

        self.image_preview_label = QLabel("이미지 미리보기")
        self.image_preview_label.setAlignment(Qt.AlignCenter)
        self.image_preview_page.setLayout(QVBoxLayout())
        self.image_preview_page.layout().addWidget(self.image_preview_label)

        # 텍스트 미리보기 페이지 설정
        self.text_browser = QTextBrowser()
        self.text_preview_page.setLayout(QVBoxLayout())
        self.text_preview_page.layout().addWidget(self.text_browser)

        # 비디오 미리보기 페이지 설정
        self.video_widget = QVideoWidget()
        video_page_layout = QVBoxLayout()
        video_page_layout.addWidget(self.video_widget)
        self.video_preview_page.setLayout(video_page_layout)

        # 비디오 컨트롤 추가
        self.play_button = QToolButton()
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.stop_button = QToolButton()
        self.stop_button.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))

        # 볼륨 버튼 (음소거 아이콘)
        self.volume_button = QToolButton()
        self.volume_button.setIcon(self.style().standardIcon(QStyle.SP_MediaVolume))

        # 볼륨 슬라이더 (세로, 초기 숨김)
        self.volume_slider = QSlider(Qt.Vertical, self.video_preview_page) # video_preview_page의 자식으로 설정
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50) # 초기 볼륨 설정
        self.volume_slider.hide() # 초기에는 숨김

        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 0) # 초기 범위는 0
        self.position_slider.sliderMoved.connect(self.set_position)

        self.current_time_label = QLabel("00:00")
        self.total_time_label = QLabel("00:00")

        video_controls_layout = QHBoxLayout()
        video_controls_layout.addWidget(self.play_button)
        video_controls_layout.addWidget(self.stop_button)
        video_controls_layout.addWidget(self.volume_button) # 볼륨 버튼 추가
        video_controls_layout.addWidget(self.current_time_label)
        video_controls_layout.addWidget(self.position_slider)
        video_controls_layout.addWidget(self.total_time_label)

        self.video_preview_page.layout().addLayout(video_controls_layout)

        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.media_player.setVideoOutput(self.video_widget)

        # 컨트롤 연결
        self.play_button.clicked.connect(self.toggle_play_pause)
        self.stop_button.clicked.connect(self.media_player.stop)
        self.volume_button.clicked.connect(self.toggle_volume_slider) # 볼륨 버튼 클릭 시 볼륨 슬라이더 토글
        self.volume_slider.valueChanged.connect(self.media_player.setVolume)
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)
        self.media_player.stateChanged.connect(self.update_play_button_icon) # 재생 상태 변경 시 아이콘 업데이트

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
                if self.media_player.state() == QMediaPlayer.PlayingState:
                    self.media_player.stop()
                self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(file_path)))
                self.media_player.play()
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
        # 비디오 플레이어 정지 및 미디어 해제
        if self.media_player and self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.stop()
        if self.media_player:
            self.media_player.setMedia(QMediaContent())

        # 볼륨 슬라이더 숨기기
        self.volume_slider.hide()

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

    def toggle_play_pause(self):
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()

    def update_play_button_icon(self, state):
        if state == QMediaPlayer.PlayingState:
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    def toggle_volume_slider(self):
        # 볼륨 슬라이더를 보이거나 숨깁니다.
        if self.volume_slider.isVisible():
            self.volume_slider.hide()
        else:
            # 볼륨 버튼의 위치를 기준으로 슬라이더 위치 조정
            button_rect = self.volume_button.geometry()
            # video_preview_page 내에서의 상대적 위치 계산
            # volume_button의 전역 위치를 video_preview_page의 지역 위치로 변환
            global_button_pos = self.volume_button.mapToGlobal(self.volume_button.rect().topLeft())
            local_pos_in_video_page = self.video_preview_page.mapFromGlobal(global_button_pos)

            slider_width = self.volume_slider.width()
            slider_height = self.volume_slider.height()

            # 볼륨 버튼 중앙 상단에 슬라이더가 위치하도록 조정
            x = local_pos_in_video_page.x() + (button_rect.width() - slider_width) // 2
            y = local_pos_in_video_page.y() - slider_height # 버튼 위로

            self.volume_slider.setGeometry(x, y, slider_width, slider_height)
            self.volume_slider.show()

    def position_changed(self, position):
        self.position_slider.setValue(position)
        self.current_time_label.setText(self.format_time(position))

    def duration_changed(self, duration):
        self.position_slider.setRange(0, duration)
        self.total_time_label.setText(self.format_time(duration))

    def set_position(self, position):
        self.media_player.setPosition(position)

    def format_time(self, milliseconds):
        seconds = int(milliseconds / 1000)
        minutes = int(seconds / 60)
        seconds %= 60
        return f"{minutes:02d}:{seconds:02d}"