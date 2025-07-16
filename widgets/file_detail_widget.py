import os
import datetime
import logging
import fitz  # type: ignore # PyMuPDF

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTextBrowser,
    QScrollArea,
    QStackedWidget,
    QSlider,
    QToolButton,
    QStyle,
    QMessageBox,
    QSizePolicy,
    QSpacerItem,
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, pyqtSignal, QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget

from viewmodels.file_detail_viewmodel import FileDetailViewModel

logger = logging.getLogger(__name__)


class ClickableSlider(QSlider):
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # 클릭 위치를 슬라이더 값으로 변환
            if self.orientation() == Qt.Horizontal:
                value = (
                    self.minimum()
                    + ((self.maximum() - self.minimum()) * event.x()) / self.width()
                )
            else:  # Qt.Vertical
                value = (
                    self.maximum()
                    - ((self.maximum() - self.minimum()) * event.y()) / self.height()
                )
            self.setValue(int(value))
            self.sliderMoved.emit(int(value))
        super().mousePressEvent(event)


class FileDetailWidget(QWidget):
    """파일 상세 정보 및 미리보기를 표시하는 위젯"""
    
    # 지원 파일 확장자
    PDF_EXTENSIONS = [".pdf"]
    IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg", ".bmp", ".gif"]
    VIDEO_EXTENSIONS = [".mp4", ".avi", ".mkv", ".mov", ".webm"]
    TEXT_EXTENSIONS = [".txt", ".md", ".py", ".js", ".html", ".css"]
    
    MAX_PDF_PAGES_TO_PREVIEW = 3

    def __init__(self, viewmodel: FileDetailViewModel, parent=None):
        super().__init__(parent)
        self.viewmodel = viewmodel
        self.current_file_path = None
        self.media_player = None
        
        self.setup_ui()
        self.connect_viewmodel_signals()

    def connect_viewmodel_signals(self):
        """ViewModel 시그널 연결"""
        logger.info(f"FileDetailWidget: ViewModel 시그널 연결 중... ViewModel: {self.viewmodel}")
        self.viewmodel.file_details_updated.connect(self.on_viewmodel_file_details_updated)
        self.viewmodel.show_message.connect(
            lambda msg, duration: (
                QMessageBox.information(self, "정보", msg)
                if duration == 0
                else self.window().statusbar.showMessage(msg, duration)
            )
        )
        logger.info("FileDetailWidget: ViewModel 시그널 연결 완료")

    def setup_ui(self):
        """UI 초기화 - 근본적인 단순화"""
        self.setObjectName("fileDetailPanel")
        
        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. 메인 미리보기 영역 (QStackedWidget 제거, 직접 위젯 사용)
        self._create_preview_widgets()
        
        # 2. 하단 정보 바
        info_layout = QHBoxLayout()
        info_layout.setContentsMargins(8, 4, 8, 4)
        info_layout.setSpacing(8)
        
        # 파일 경로 라벨
        self.file_path_label = QLabel("파일을 선택하세요")
        self.file_path_label.setStyleSheet("color: #666; font-size: 11px;")
        self.file_path_label.setWordWrap(True)
        
        # 확장 공간
        info_layout.addWidget(self.file_path_label, 1)
        info_layout.addItem(QSpacerItem(20, 0, QSizePolicy.Fixed, QSizePolicy.Minimum))
        
        # 파일 정보 라벨
        self.file_info_label = QLabel("")
        self.file_info_label.setStyleSheet("color: #666; font-size: 11px;")
        self.file_info_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        info_layout.addWidget(self.file_info_label)
        
        # 레이아웃에 추가
        main_layout.addWidget(self.current_preview_widget, 1)  # 확장 가능
        main_layout.addLayout(info_layout, 0)  # 고정 크기

    def _create_preview_widgets(self):
        """각 파일 형식별 미리보기 위젯 생성 - 단순화된 구조"""
        
        # 1. 이미지 미리보기 위젯
        self.image_preview_label = QLabel("이미지 미리보기")
        self.image_preview_label.setAlignment(Qt.AlignCenter)
        self.image_preview_label.setStyleSheet(
            "background-color: #f8f9fa; border: 1px solid #e9ecef; padding: 20px;"
        )
        self.image_preview_label.setMinimumSize(400, 300)
        self.image_preview_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 2. 텍스트 미리보기 위젯 (스크롤 기능 내장)
        self.text_browser = QTextBrowser()
        self.text_browser.setLineWrapMode(QTextBrowser.NoWrap)
        self.text_browser.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.text_browser.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.text_browser.setMinimumSize(400, 300)
        self.text_browser.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.text_browser.setStyleSheet(
            "QTextBrowser { background-color: #ffffff; border: 1px solid #e9ecef; padding: 20px; }"
        )
        
        # 3. PDF 미리보기 위젯
        self.pdf_preview_label = QLabel("PDF 미리보기")
        self.pdf_preview_label.setAlignment(Qt.AlignCenter)
        self.pdf_preview_label.setStyleSheet(
            "background-color: #f8f9fa; border: 1px solid #e9ecef; padding: 20px;"
        )
        self.pdf_preview_label.setMinimumSize(400, 300)
        self.pdf_preview_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 4. 비디오 미리보기 위젯
        self.video_widget_container = QWidget()  # 비디오 위젯을 담는 컨테이너
        video_layout = QVBoxLayout(self.video_widget_container)
        video_layout.setContentsMargins(0, 0, 0, 0)  # 여백 제거
        video_layout.setSpacing(0)  # 간격 제거
        
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumSize(400, 300)
        self.video_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_widget.setStyleSheet(
            "QVideoWidget { background-color: #000000; border-radius: 8px; }"
        )
        video_layout.addWidget(self.video_widget)
        
        # 현대적인 비디오 컨트롤 패널
        self.controls_panel = QWidget()
        self.controls_panel.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 8px;
                border: 1px solid rgba(0, 0, 0, 0.1);
            }
        """)
        self.controls_panel.setMaximumHeight(100)
        
        controls_layout = QVBoxLayout(self.controls_panel)
        controls_layout.setContentsMargins(12, 8, 12, 8)
        controls_layout.setSpacing(1)
        
        # 상단: 진행바
        progress_layout = QHBoxLayout()
        progress_layout.setContentsMargins(0, 5, 0, 5)
        progress_layout.setSpacing(8)
        
        self.current_time_label = QLabel("00:00")
        self.current_time_label.setStyleSheet("""
            QLabel {
                color: #333333;
                font-size: 10px;
                font-weight: 500;
                min-width: 35px;
                max-width: 35px;
                min-height: 14px;
                padding: 0px;
                border: none;
                background: transparent;
            }
        """)
        
        self.position_slider = ClickableSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.sliderMoved.connect(self.set_position)
        self.position_slider.setStyleSheet("""
            QSlider {
                border: none;
                background: transparent;
            }
            QSlider::groove:horizontal {
                border: none;
                height: 4px;
                background: rgba(0, 0, 0, 0.2);
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: #0078d4;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #ffffff;
                border: 2px solid #0078d4;
                width: 12px;
                height: 12px;
                border-radius: 6px;
                margin: -4px 0;
            }
            QSlider::handle:horizontal:hover {
                background: #f0f0f0;
            }
        """)
        
        self.total_time_label = QLabel("00:00")
        self.total_time_label.setStyleSheet("""
            QLabel {
                color: #333333;
                font-size: 10px;
                font-weight: 500;
                min-width: 35px;
                max-width: 35px;
                min-height: 14px;
                padding: 0px;
                border: none;
                background: transparent;
            }
        """)
        
        progress_layout.addWidget(self.current_time_label)
        progress_layout.addWidget(self.position_slider, 1)
        progress_layout.addWidget(self.total_time_label)
        
        # 하단: 컨트롤 버튼들 (가운데 정렬)
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 5, 0, 15)
        buttons_layout.setSpacing(10)
        
        # 공통 버튼 스타일
        button_style = """
            QToolButton {
                background-color: rgba(0, 0, 0, 0.1);
                border: none;
                border-radius: 10px;
                padding: 2px;
                width: 18px;
                height: 18px;
            }
            QToolButton:hover {
                background-color: rgba(0, 0, 0, 0.2);
            }
            QToolButton:pressed {
                background-color: rgba(0, 0, 0, 0.3);
            }
        """
        
        # 재생/일시정지 버튼
        self.play_button = QToolButton()
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_button.setStyleSheet(button_style)
        self.play_button.setFixedSize(18, 18)
        
        # 정지 버튼
        self.stop_button = QToolButton()
        self.stop_button.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.stop_button.setStyleSheet(button_style)
        self.stop_button.setFixedSize(18, 18)
        
        # 볼륨 버튼
        self.volume_button = QToolButton()
        self.volume_button.setIcon(self.style().standardIcon(QStyle.SP_MediaVolume))
        self.volume_button.setStyleSheet(button_style)
        self.volume_button.setFixedSize(18, 18)
        
        # 버튼들을 가운데 정렬
        buttons_layout.addItem(QSpacerItem(20, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        buttons_layout.addWidget(self.play_button)
        buttons_layout.addWidget(self.stop_button)
        buttons_layout.addWidget(self.volume_button)
        buttons_layout.addItem(QSpacerItem(20, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        # 레이아웃 조립
        controls_layout.addLayout(progress_layout)
        controls_layout.addLayout(buttons_layout)
        
        # 볼륨 슬라이더 (개선된 디자인)
        self.volume_slider = QSlider(Qt.Vertical)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.hide()
        self.volume_slider.setMinimumHeight(80)
        self.volume_slider.setMaximumHeight(80)
        self.volume_slider.setFixedWidth(20)
        self.volume_slider.setParent(self.video_widget_container)
        self.volume_slider.setStyleSheet("""
            QSlider {
                border: none;
                background: transparent;
            }
            QSlider::groove:vertical {
                border: none;
                width: 4px;
                background: rgba(0, 0, 0, 0.2);
                border-radius: 2px;
            }
            QSlider::sub-page:vertical {
                background: #0078d4;
                border-radius: 2px;
            }
            QSlider::handle:vertical {
                background: #ffffff;
                border: 2px solid #0078d4;
                width: 12px;
                height: 12px;
                border-radius: 6px;
                margin: 0 -4px;
            }
            QSlider::handle:vertical:hover {
                background: #f0f0f0;
            }
        """)
        
        # 컨트롤 패널을 비디오 레이아웃에 추가 (여백 포함)
        video_layout.addWidget(self.controls_panel)
        video_layout.setContentsMargins(8, 8, 8, 8)  # 비디오 컨테이너에 여백 추가
        video_layout.setSpacing(10)  # 비디오 위젯과 컨트롤 패널 사이 간격
        
        # 5. 지원하지 않는 형식 위젯
        self.unsupported_label = QLabel("미리보기를 지원하지 않는 형식입니다.")
        self.unsupported_label.setAlignment(Qt.AlignCenter)
        self.unsupported_label.setStyleSheet(
            "background-color: #f8f9fa; border: 1px solid #e9ecef; padding: 20px; color: #666;"
        )
        self.unsupported_label.setMinimumSize(400, 300)
        self.unsupported_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 초기 미리보기 위젯 설정
        self.current_preview_widget = self.unsupported_label
        
        # 비디오 플레이어 설정
        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.media_player.setVideoOutput(self.video_widget)
        
        # 비디오 컨트롤 연결
        self.play_button.clicked.connect(self.toggle_play_pause)
        self.stop_button.clicked.connect(self.media_player.stop)
        self.volume_button.clicked.connect(self.toggle_volume_slider)
        self.volume_slider.valueChanged.connect(self.media_player.setVolume)
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)
        self.media_player.stateChanged.connect(self.update_play_button_icon)

    def _switch_preview_widget(self, new_widget):
        """미리보기 위젯을 전환합니다."""
        if self.current_preview_widget != new_widget:
            # 기존 위젯을 숨김
            self.current_preview_widget.hide()
            # 새 위젯을 레이아웃에 추가(이미 있으면 무시)
            main_layout = self.layout()
            if main_layout:
                main_layout.replaceWidget(main_layout.itemAt(0).widget(), new_widget)
            new_widget.show()
            self.current_preview_widget = new_widget

    def update_preview(self, file_path):
        """파일 미리보기를 업데이트합니다."""
        if self.current_file_path != file_path:
            self.clear_preview()
        
        self.current_file_path = file_path
        
        if not file_path or not os.path.isfile(file_path):
            self._switch_preview_widget(self.unsupported_label)
            self._update_info_bar(file_path, "파일을 찾을 수 없습니다")
            return
        
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            
            # ViewModel에 파일 업데이트 요청
            self.viewmodel.update_for_file(file_path)
            
            # 하단 정보 바 업데이트
            self._update_info_bar(file_path)
            
            # 파일 형식별 처리
            if file_ext in self.IMAGE_EXTENSIONS:
                self._handle_image_file(file_path)
            elif file_ext in self.TEXT_EXTENSIONS:
                self._handle_text_file(file_path, file_ext)
            elif file_ext in self.PDF_EXTENSIONS:
                self._handle_pdf_file(file_path)
            elif file_ext in self.VIDEO_EXTENSIONS:
                self._handle_video_file(file_path)
            else:
                self._switch_preview_widget(self.unsupported_label)
                
        except Exception as e:
            logger.error(f"Error updating preview for {file_path}: {e}")
            self.clear_preview()

    def _handle_image_file(self, file_path):
        """이미지 파일 처리"""
        logger.debug(f"이미지 파일 처리 시작: {file_path}")
        self._switch_preview_widget(self.image_preview_label)
        
        if not os.path.exists(file_path):
            self.image_preview_label.setText("파일을 찾을 수 없습니다.")
            return
        
        pixmap = QPixmap(file_path)
        if not pixmap.isNull():
            # 이미지를 라벨에 맞춰 스케일링 (QScrollArea 제거로 단순화)
            scaled_pixmap = pixmap.scaled(
                self.image_preview_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_preview_label.setPixmap(scaled_pixmap)
            logger.debug(f"이미지 로드 성공: {file_path}, 크기: {pixmap.size()}")
        else:
            self.image_preview_label.setText("이미지 로드 실패")
            logger.error(f"이미지 로드 실패: {file_path}")

    def _handle_text_file(self, file_path, file_ext):
        """텍스트 파일 처리"""
        logger.info(f"텍스트 파일 처리 시작: {file_path}")
        self._switch_preview_widget(self.text_browser)
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                if file_ext == ".md":
                    content = f.read()
                    self.text_browser.setMarkdown(content)
                else:
                    content = f.read(1024 * 50)  # 50KB로 증가
                    self.text_browser.setPlainText(content)
                
                logger.debug(f"텍스트 파일 로드: {file_path}, 읽은 크기: {len(content)} 문자")
        except Exception as e:
            self.text_browser.setPlainText(f"파일을 읽을 수 없습니다: {e}")
            logger.error(f"텍스트 파일 로드 실패: {file_path}, 오류: {e}")

    def _handle_pdf_file(self, file_path):
        """PDF 파일 처리"""
        logger.debug(f"PDF 파일 처리 시작: {file_path}")
        self._switch_preview_widget(self.pdf_preview_label)
        
        doc = None
        try:
            doc = fitz.open(file_path)
            pix = None
            
            for page_num in range(min(doc.page_count, self.MAX_PDF_PAGES_TO_PREVIEW)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                
                qimage = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qimage)
                
                # PDF를 라벨에 맞춰 스케일링
                scaled_pixmap = pixmap.scaled(
                    self.pdf_preview_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.pdf_preview_label.setPixmap(scaled_pixmap)
                logger.debug(f"PDF 렌더링: {file_path}")
                break
                
            if pix is None:
                self.pdf_preview_label.setText("PDF 페이지를 렌더링할 수 없습니다.")
                
        except Exception as e:
            logger.exception(f"PDF 렌더링 오류: {file_path}")
            self.pdf_preview_label.setText(f"PDF 미리보기 오류: {e}")
        finally:
            if doc:
                doc.close()

    def _handle_video_file(self, file_path):
        """비디오 파일 처리"""
        logger.debug(f"비디오 파일 처리 시작: {file_path}")
        # 비디오 위젯 컨테이너를 직접 사용
        self._switch_preview_widget(self.video_widget_container)
        
        # 비디오 플레이어 초기화
        self._clear_video_player()
        
        self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(file_path)))
        self.media_player.play()

    def _clear_video_player(self):
        """비디오 플레이어 관련 객체들을 초기화합니다."""
        if hasattr(self, 'media_player') and self.media_player:
            if self.media_player.state() == QMediaPlayer.PlayingState:
                self.media_player.stop()
            self.media_player.setMedia(QMediaContent())
            if hasattr(self, 'position_slider') and self.position_slider:
                self.position_slider.setRange(0, 0)
                self.position_slider.setValue(0)
            if hasattr(self, 'current_time_label') and self.current_time_label:
                self.current_time_label.setText("00:00")
            if hasattr(self, 'total_time_label') and self.total_time_label:
                self.total_time_label.setText("00:00")
            if hasattr(self, 'play_button') and self.play_button:
                self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        
        # 볼륨 슬라이더 숨기기
        if hasattr(self, 'volume_slider') and self.volume_slider:
            self.volume_slider.hide()
            self.volume_slider.setValue(50)
        
        # 시간 라벨 강제 업데이트
        if hasattr(self, 'current_time_label') and self.current_time_label:
            self.current_time_label.setText("00:00")
        if hasattr(self, 'total_time_label') and self.total_time_label:
            self.total_time_label.setText("00:00")

    def _update_info_bar(self, file_path, error_message=None):
        """하단 정보 바 업데이트"""
        if error_message:
            self.file_path_label.setText(error_message)
            self.file_info_label.setText("")
            return
        
        if not file_path:
            self.file_path_label.setText("파일을 선택하세요")
            self.file_info_label.setText("")
            return
        
        try:
            # 파일 경로 (긴 경로는 축약)
            display_path = file_path
            if len(display_path) > 80:
                display_path = "..." + display_path[-77:]
            self.file_path_label.setText(display_path)
            
            # 파일 정보
            file_size = os.path.getsize(file_path)
            mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
            
            size_text = f"{file_size / (1024*1024):.2f} MB" if file_size > 1024*1024 else f"{file_size / 1024:.1f} KB"
            info_text = f"{size_text} | {mod_time.strftime('%Y-%m-%d %H:%M')}"
            self.file_info_label.setText(info_text)
            
        except Exception as e:
            logger.error(f"정보 바 업데이트 실패: {e}")
            self.file_path_label.setText(file_path)
            self.file_info_label.setText("")

    def clear_preview(self):
        """모든 미리보기를 초기화합니다."""
        # 미리보기 초기화 (안전장치 추가)
        if hasattr(self, 'image_preview_label') and self.image_preview_label:
            self.image_preview_label.clear()
            self.image_preview_label.setText("이미지 미리보기")
        if hasattr(self, 'text_browser') and self.text_browser:
            self.text_browser.clear()
        if hasattr(self, 'pdf_preview_label') and self.pdf_preview_label:
            self.pdf_preview_label.clear()
            self.pdf_preview_label.setText("PDF 미리보기")
        
        # 정보 바 초기화
        self._update_info_bar(None)
        
        # 지원하지 않는 형식 위젯으로 설정 (안전장치 추가)
        if hasattr(self, 'unsupported_label') and self.unsupported_label:
            self._switch_preview_widget(self.unsupported_label)
        
        self.current_file_path = None

    def on_viewmodel_file_details_updated(self, file_path: str, tags: list):
        """ViewModel에서 받은 정보로 UI 업데이트"""
        try:
            # 현재는 태그 정보를 사용하지 않음 (읽기 전용)
            pass
        except Exception as e:
            logger.error(f"태그 정보 업데이트 실패: {file_path}, 오류: {e}")

    # 비디오 컨트롤 메서드들
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
        if self.volume_slider.isVisible():
            self.volume_slider.hide()
        else:
            # 볼륨 버튼의 위치를 기준으로 슬라이더 배치
            volume_button_rect = self.volume_button.geometry()
            
            # 볼륨 버튼을 기준으로 슬라이더 위치 계산
            # 버튼 위쪽에 슬라이더를 배치
            x = volume_button_rect.x() - 5  # 버튼 왼쪽으로 5px
            y = volume_button_rect.y() - 85  # 버튼 위쪽으로 85px (슬라이더 높이 + 간격)
            
            self.volume_slider.setGeometry(x, y, 20, 80)
            self.volume_slider.show()
            self.volume_slider.raise_()  # 최상위로

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
