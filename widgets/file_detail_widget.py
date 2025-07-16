import os
import datetime
import logging
import fitz # type: ignore # PyMuPDF

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTextBrowser, QSlider, 
                             QHBoxLayout, QToolButton, QStyle, QMessageBox, QSizePolicy)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, pyqtSignal, QUrl
from PyQt5.uic import loadUi
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget

from widgets.tag_chip import TagChip
from widgets.flow_layout import FlowLayout
from viewmodels.file_detail_viewmodel import FileDetailViewModel # FileDetailViewModel 임포트

logger = logging.getLogger(__name__)



class ClickableSlider(QSlider):
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # 클릭 위치를 슬라이더 값으로 변환
            if self.orientation() == Qt.Horizontal:
                value = self.minimum() + ((self.maximum() - self.minimum()) * event.x()) / self.width()
            else: # Qt.Vertical
                value = self.maximum() - ((self.maximum() - self.minimum()) * event.y()) / self.height()
            self.setValue(int(value))
            # 슬라이더 값이 변경되었음을 알리는 시그널을 발생시킵니다.
            self.sliderMoved.emit(int(value))
        super().mousePressEvent(event)

class FileDetailWidget(QWidget):
    PDF_EXTENSIONS = ['.pdf']
    MAX_PDF_PAGES_TO_PREVIEW = 3 # 미리보기할 최대 PDF 페이지 수
    # tags_updated 시그널 제거 - 읽기 전용이므로 태그 변경 시그널 불필요

    IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.bmp', '.gif']
    VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mkv', '.mov', '.webm'] # 추가된 비디오 확장자
    TEXT_EXTENSIONS = ['.txt', '.md', '.py', '.js', '.html', '.css']
    # MAX_VIDEO_SIZE_MB = 50 # Base64 인코딩 시 필요했으므로 제거

    def __init__(self, viewmodel: FileDetailViewModel, parent=None):
        super().__init__(parent)
        self.viewmodel = viewmodel # FileDetailViewModel 인스턴스 사용
        self.current_file_path = None
        self.media_player = None # QMediaPlayer 인스턴스 초기화
        self.setup_ui()
        self.connect_viewmodel_signals()

    def connect_viewmodel_signals(self):
        logger.info(f"FileDetailWidget: ViewModel 시그널 연결 중... ViewModel: {self.viewmodel}")
        self.viewmodel.file_details_updated.connect(self.on_viewmodel_file_details_updated)
        self.viewmodel.show_message.connect(lambda msg, duration: 
     QMessageBox.information(self, "정보", msg) if duration == 0 else self
                 .window().statusbar.showMessage(msg, duration))
        logger.info("FileDetailWidget: ViewModel 시그널 연결 완료")
   
    def resizeEvent(self, event):
        """창 크기 변경 시 레이아웃을 강제로 업데이트합니다."""
        super().resizeEvent(event)
        # 레이아웃 강제 업데이트
        self.update()
        self.repaint()
        # 현재 표시 중인 위젯의 레이아웃도 업데이트
        if hasattr(self, 'preview_stacked_widget'):
            current_widget = self.preview_stacked_widget.currentWidget()
            if current_widget:
                current_widget.update()
                current_widget.repaint()
   
    def on_viewmodel_file_details_updated(self, file_path: str, tags: list):
        """ViewModel에서 받은 정보로 UI 업데이트"""
        try:
            logger.info(f"[FILE_DETAIL] 태그 업데이트: {file_path}, 태그 수: {len(tags)}, 태그: {tags}")
            logger.debug("_refresh_tag_chips 호출 전")
            self._refresh_tag_chips(tags)
            logger.debug("_refresh_tag_chips 호출 후")
            
            # 태그 영역 가시성 확인
            if hasattr(self, 'tag_chip_scroll_area'):
                logger.info(f"태그 스크롤 영역 크기: {self.tag_chip_scroll_area.size()}")
                logger.info(f"태그 스크롤 영역 가시성: {self.tag_chip_scroll_area.isVisible()}")
                logger.info(f"태그 스크롤 영역 위치: {self.tag_chip_scroll_area.pos()}")
                logger.info(f"태그 컨테이너 크기: {self.tag_chip_container.size()}")
                logger.info(f"태그 컨테이너 가시성: {self.tag_chip_container.isVisible()}")
                logger.info(f"태그 컨테이너 위치: {self.tag_chip_container.pos()}")
                logger.info(f"FlowLayout 아이템 수: {self.tag_chip_flow_layout.count() if hasattr(self, 'tag_chip_flow_layout') else 0}")
            
            # ViewModel 업데이트 후 강제 레이아웃 새로고침 (최초 렌더링과 동일하게)
            self._force_layout_update()  # 추가: 최초 렌더링과 동일한 강제 업데이트
            self._force_splitter_refresh()
            
        except Exception as e:
            logger.error(f"태그 정보 업데이트 실패: {file_path}, 오류: {e}")
            self._clear_tag_chips()

    def setup_ui(self):
        # Material Design 스타일 적용
        self.setObjectName("fileDetailPanel")
        
        loadUi('ui/file_detail_content_widget.ui', self)
        
        # 태그 영역에 제목 추가
        self.tag_title_label = QLabel("파일 태그")
        self.tag_title_label.setStyleSheet("font-weight: bold; font-size: 10pt; color: #1a1a1a; margin-bottom: 8px; padding: 4px;")
        self.tag_title_label.setAlignment(Qt.AlignLeft)
        
        # 태그 스크롤 영역에 배경색 추가하여 가시성 향상
        self.tag_chip_scroll_area.setStyleSheet("QScrollArea { background-color: #f8f9fa; border: 1px solid #e9ecef; }")
        self.tag_chip_container.setStyleSheet("QWidget { background-color: #f8f9fa; }")
        
        # 태그 제목을 스크롤 영역 위에 추가
        tag_section_layout = QVBoxLayout()
        tag_section_layout.addWidget(self.tag_title_label)
        tag_section_layout.addWidget(self.tag_chip_scroll_area)
        
        # 기존 right_splitter의 태그 영역을 새로운 레이아웃으로 교체
        self.right_splitter.replaceWidget(1, QWidget())
        tag_widget = QWidget()
        tag_widget.setLayout(tag_section_layout)
        self.right_splitter.insertWidget(1, tag_widget)
        
        # 스크롤 영역 크기 정책 조정 - 태그가 보이도록 충분한 공간 확보
        self.tag_chip_scroll_area.setMinimumHeight(150)
        self.tag_chip_scroll_area.setMaximumHeight(300)
        
        # 태그 영역이 확실히 보이도록 설정
        self.tag_chip_scroll_area.setVisible(True)
        self.tag_chip_container.setVisible(True)
        self.tag_chip_scroll_area.show()
        self.tag_chip_container.show()
        
        # 스크롤 영역 설정 확인
        self.tag_chip_scroll_area.setWidgetResizable(True)
        self.tag_chip_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tag_chip_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 태그 칩 컨테이너에 FlowLayout 적용 (UI 파일에서 기존 레이아웃이 제거되었으므로 바로 설정)
        self.tag_chip_flow_layout = FlowLayout(margin=4, spacing=4)
        self.tag_chip_container.setLayout(self.tag_chip_flow_layout)
        
        # 스크롤 영역 크기 정책 조정
        self.tag_chip_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)

        self.image_preview_label = QLabel("이미지 미리보기")
        self.image_preview_label.setAlignment(Qt.AlignCenter)
        # 이미지 미리보기 라벨 크기 (50:50 비율에 맞게 조정)
        self.image_preview_label.setMinimumSize(300, 300)
        self.image_preview_label.setScaledContents(False)  # 라벨 크기에 맞춰 스케일링 방지
        # 배경색 설정으로 레이아웃 경계 명확화
        self.image_preview_label.setStyleSheet("background-color: #f8f9fa; border: 1px solid #e9ecef;")
        self.image_preview_page.setLayout(QVBoxLayout())
        self.image_preview_page.layout().addWidget(self.image_preview_label)

        # 텍스트 미리보기 페이지 설정
        self.text_browser = QTextBrowser()
        self.text_preview_page.setLayout(QVBoxLayout())
        self.text_preview_page.layout().addWidget(self.text_browser)

        # PDF 미리보기 페이지 설정
        self.pdf_preview_label = QLabel("PDF 미리보기")
        self.pdf_preview_label.setAlignment(Qt.AlignCenter)
        # PDF 미리보기 라벨 크기 (50:50 비율에 맞게 조정)
        self.pdf_preview_label.setMinimumSize(300, 300)
        self.pdf_preview_label.setScaledContents(False)
        # 배경색 설정으로 레이아웃 경계 명확화
        self.pdf_preview_label.setStyleSheet("background-color: #f8f9fa; border: 1px solid #e9ecef;")
        self.pdf_preview_page.setLayout(QVBoxLayout())
        self.pdf_preview_page.layout().addWidget(self.pdf_preview_label)

        # 비디오 미리보기 페이지 설정
        self.video_widget = QVideoWidget()
        video_page_layout = QVBoxLayout()
        video_page_layout.addWidget(self.video_widget)
        self.video_preview_page.setLayout(video_page_layout)

        # 비디오 컨트롤 추가
        self.play_button = QToolButton()
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_button.setProperty("class", "video-control")
        
        self.stop_button = QToolButton()
        self.stop_button.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.stop_button.setProperty("class", "video-control")

        # 볼륨 버튼 (음소거 아이콘)
        self.volume_button = QToolButton()
        self.volume_button.setIcon(self.style().standardIcon(QStyle.SP_MediaVolume))
        self.volume_button.setProperty("class", "video-control")

        # 볼륨 슬라이더 (세로, 초기 숨김)
        self.volume_slider = QSlider(Qt.Vertical, self.video_preview_page) # video_preview_page의 자식으로 설정
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50) # 초기 볼륨 설정
        self.volume_slider.hide() # 초기에는 숨김
        self.volume_slider.setMinimumHeight(100) # 최소 높이 설정

        self.position_slider = ClickableSlider(Qt.Horizontal)
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
        """파일 미리보기를 업데이트합니다."""
        # 이전 파일과 다른 경우에만 완전 초기화
        if self.current_file_path != file_path:
            self.clear_preview()
        
        self.current_file_path = file_path

        if not file_path or not os.path.isfile(file_path):
            self.preview_stacked_widget.setCurrentWidget(self.unsupported_preview_page)
            self.metadata_browser.clear()
            self._clear_tag_chips()
            return

        try:
            file_ext = os.path.splitext(file_path)[1].lower()

            # 메타데이터를 먼저 업데이트하여 즉시 표시
            self._update_metadata(file_path)
            
            # ViewModel에 파일 업데이트 요청 (비동기로 태그 정보 로드)
            self.viewmodel.update_for_file(file_path)

            if file_ext in self.IMAGE_EXTENSIONS:
                self.preview_stacked_widget.setCurrentWidget(self.image_preview_page)
                pixmap = QPixmap(file_path)
                if not pixmap.isNull():
                    # 50:50 비율에 맞는 크기로 스케일링
                    scaled_pixmap = pixmap.scaled(350, 320, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.image_preview_label.setPixmap(scaled_pixmap)
                else:
                    self.image_preview_label.setText("이미지 로드 실패")
            
            elif file_ext in self.VIDEO_EXTENSIONS:
                self.preview_stacked_widget.setCurrentWidget(self.video_preview_page)
                # 비디오 플레이어 상태 완전 초기화
                if self.media_player.state() == QMediaPlayer.PlayingState:
                    self.media_player.stop()
                self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(file_path)))
                # 비디오 로드 후 재생
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
            elif file_ext in self.PDF_EXTENSIONS:
                self.preview_stacked_widget.setCurrentWidget(self.pdf_preview_page)
                self._render_pdf_thumbnail(file_path)
            else:
                self.preview_stacked_widget.setCurrentWidget(self.unsupported_preview_page)

        except Exception as e:
            logger.error(f"Error updating preview for {file_path}: {e}")
            self.clear_preview()
            self.preview_stacked_widget.setCurrentWidget(self.unsupported_preview_page)
        
        # 레이아웃 강제 업데이트로 렌더링 오류 방지
        self._force_layout_update()
        
        # QSplitter와 HBoxLayout 강제 새로고침
        self._force_splitter_refresh()

    def _force_layout_update(self):
        """레이아웃을 강제로 업데이트하여 렌더링 오류를 방지합니다."""
        try:
            # 현재 위젯과 모든 자식 위젯의 레이아웃 업데이트
            self.updateGeometry()
            self.update()
            
            # 스택 위젯과 현재 페이지 업데이트
            if hasattr(self, 'preview_stacked_widget'):
                self.preview_stacked_widget.updateGeometry()
                self.preview_stacked_widget.update()
                
                current_widget = self.preview_stacked_widget.currentWidget()
                if current_widget:
                    current_widget.updateGeometry()
                    current_widget.update()
            
            # 메타데이터 브라우저 업데이트
            if hasattr(self, 'metadata_browser'):
                self.metadata_browser.updateGeometry()
                self.metadata_browser.update()
            
            # 태그 스크롤 영역 업데이트
            if hasattr(self, 'tag_chip_scroll_area'):
                self.tag_chip_scroll_area.updateGeometry()
                self.tag_chip_scroll_area.update()
                
        except Exception as e:
            logger.warning(f"레이아웃 강제 업데이트 중 오류: {e}")
    
    def _force_splitter_refresh(self):
        """QSplitter와 HBoxLayout의 강제 새로고침을 수행합니다."""
        try:
            # 메인 HBoxLayout 강제 업데이트
            if hasattr(self, 'layout') and self.layout():
                self.layout().update()
                self.layout().activate()
            
            # QSplitter 강제 새로고침
            if hasattr(self, 'right_splitter'):
                self.right_splitter.updateGeometry()
                self.right_splitter.update()
                
                # QSplitter의 크기를 미세하게 조정하여 강제 레이아웃 업데이트
                current_sizes = self.right_splitter.sizes()
                if current_sizes:
                    # 1픽셀씩 조정 후 즉시 원래대로 복원
                    temp_sizes = [size + 1 if size > 1 else size for size in current_sizes]
                    self.right_splitter.setSizes(temp_sizes)
                    
                    # 즉시 원래 크기로 복원
                    from PyQt5.QtCore import QTimer
                    QTimer.singleShot(1, lambda: self.right_splitter.setSizes(current_sizes))
            
            # 전체 위젯 강제 새로고침
            self.updateGeometry()
            self.update()
            self.repaint()
            
            logger.debug("[UI] QSplitter 강제 새로고침 완료")
            
        except Exception as e:
            logger.warning(f"QSplitter 강제 새로고침 중 오류: {e}")

    def _update_metadata(self, file_path):
        """파일 메타데이터를 업데이트합니다."""
        try:
            file_info = f"<b>파일 이름:</b> {os.path.basename(file_path)}<br>"
            file_info += f"<b>경로:</b> {file_path}<br>"
            
            file_size = os.path.getsize(file_path)
            file_info += f"<b>크기:</b> {file_size / (1024*1024):.2f} MB<br>"
            
            mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
            file_info += f"<b>수정일:</b> {mod_time.strftime('%Y-%m-%d %H:%M:%S')}<br>"
            
            # 파일 확장자 정보 추가
            file_ext = os.path.splitext(file_path)[1].lower()
            file_info += f"<b>형식:</b> {file_ext}<br>"
            
            self.metadata_browser.setHtml(file_info)
            logger.info(f"메타데이터 업데이트 완료: {file_path}")
            
            # 메타데이터 업데이트 후 레이아웃 새로고침
            self.metadata_browser.updateGeometry()
            self.metadata_browser.update()
            
        except Exception as e:
            error_info = f"<b>파일 이름:</b> {os.path.basename(file_path)}<br>"
            error_info += f"<b>경로:</b> {file_path}<br>"
            error_info += f"<b>정보 로드 오류:</b> {e}<br>"
            self.metadata_browser.setHtml(error_info)
            logger.error(f"메타데이터 업데이트 실패: {file_path}, 오류: {e}")
            
            # 오류 시에도 레이아웃 새로고침
            self.metadata_browser.updateGeometry()
            self.metadata_browser.update()

    def clear_preview(self):
        """모든 미리보기 요소를 완전히 초기화합니다."""
        # 비디오 플레이어 완전 정지 및 초기화
        if self.media_player:
            if self.media_player.state() == QMediaPlayer.PlayingState:
                self.media_player.stop()
            self.media_player.setMedia(QMediaContent())
            # 비디오 플레이어 상태 초기화
            self.position_slider.setRange(0, 0)
            self.position_slider.setValue(0)
            self.current_time_label.setText("00:00")
            self.total_time_label.setText("00:00")
            # 재생 버튼 아이콘 초기화
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

        # 볼륨 슬라이더 숨기기 및 초기화
        self.volume_slider.hide()
        self.volume_slider.setValue(50)  # 기본 볼륨으로 초기화

        # 이미지 미리보기 초기화
        self.image_preview_label.clear()
        self.image_preview_label.setText("파일을 선택하세요.")
        
        # 텍스트 미리보기 초기화
        self.text_browser.clear()
        
        # PDF 미리보기 초기화
        self.pdf_preview_label.clear()
        self.pdf_preview_label.setText("PDF 미리보기")
        
        # 메타데이터 초기화
        self.metadata_browser.clear()
        
        # 태그 칩 초기화
        self._clear_tag_chips()
        
        # 스택 위젯을 기본 페이지로 설정
        self.preview_stacked_widget.setCurrentWidget(self.unsupported_preview_page)
        self.unsupported_label.setText("미리보기를 지원하지 않는 형식입니다.")
        
        # 현재 파일 경로 초기화
        self.current_file_path = None
        
        # 레이아웃 강제 업데이트
        self._force_layout_update()
        
        # QSplitter와 HBoxLayout 강제 새로고침
        self._force_splitter_refresh()

    def _render_pdf_thumbnail(self, file_path):
        """PDF 파일의 썸네일을 렌더링하여 표시합니다."""
        doc = None  # doc 변수를 try 블록 밖에서 초기화
        try:
            doc = fitz.open(file_path)
            pix = None
            # 첫 페이지 또는 미리보기할 페이지 수만큼 렌더링
            for page_num in range(min(doc.page_count, self.MAX_PDF_PAGES_TO_PREVIEW)):
                page = doc.load_page(page_num)
                # 높은 해상도로 렌더링 (예: 2배 확대)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                
                # QPixmap으로 변환
                qimage = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qimage)

                # 50:50 비율에 맞는 크기로 스케일링
                scaled_pixmap = pixmap.scaled(350, 320, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.pdf_preview_label.setPixmap(scaled_pixmap)
                # 여러 페이지를 보여줄 경우, 여기에 각 페이지를 위한 별도의 QLabel을 추가하거나
                # QScrollArea 내에 QVBoxLayout을 사용하여 동적으로 추가하는 로직이 필요합니다.
                # 현재는 마지막 페이지의 썸네일만 표시됩니다.
                break # 일단 첫 페이지만 표시

            if pix is None:
                self.pdf_preview_label.setText("PDF 페이지를 렌더링할 수 없습니다.")

        except RuntimeError as e: # PyMuPDF 관련 오류는 주로 RuntimeError로 발생합니다.
            logger.exception(f"PyMuPDF Error rendering PDF thumbnail for {file_path}")
            self.pdf_preview_label.setText(f"PDF 미리보기 오류: {e}\n(파일이 손상되었거나 지원되지 않는 형식일 수 있습니다.)")
        except Exception as e: # 그 외 예상치 못한 오류 처리
            logger.exception(f"General Error rendering PDF thumbnail for {file_path}")
            self.pdf_preview_label.setText(f"PDF 미리보기 오류: {e}")
        finally:
            if doc: # doc 객체가 성공적으로 생성되었다면 닫아줍니다.
                doc.close()

    def _refresh_tag_chips(self, tags):
        """태그 칩을 새로고침합니다."""
        try:
            logger.debug(f"_refresh_tag_chips 시작: {len(tags)}개 태그")
            self._clear_tag_chips()
            
            # 태그가 없을 때 플레이스홀더 표시
            if not tags:
                logger.info("태그가 없습니다.")
                placeholder_label = QLabel("태그가 없습니다.")
                placeholder_label.setAlignment(Qt.AlignCenter)
                placeholder_label.setStyleSheet("color: #666666; font-style: italic; padding: 20px;")
                # FlowLayout에 추가
                if hasattr(self, 'tag_chip_flow_layout'):
                    self.tag_chip_flow_layout.addWidget(placeholder_label)
                return
                
            # FlowLayout 사용 - 자동 줄바꿈
            if hasattr(self, 'tag_chip_flow_layout'):
                for tag in tags:
                    # 읽기 전용 TagChip 생성 (삭제 버튼 숨김)
                    chip = TagChip(tag)
                    chip.delete_button.setVisible(False)  # 삭제 버튼 숨김
                    chip.setToolTip(f"태그: {tag}\n(편집하려면 태그 관리 패널을 사용하세요)")
                    
                    # FlowLayout에 추가
                    self.tag_chip_flow_layout.addWidget(chip)
                    
                    # 태그칩이 실제로 보이는지 확인
                    chip.show()
                    chip.setVisible(True)
                    
            logger.info(f"태그 칩 업데이트 완료: {len(tags)}개 태그, FlowLayout 아이템 수: {self.tag_chip_flow_layout.count() if hasattr(self, 'tag_chip_flow_layout') else 0}")
            
            # 태그 칩 업데이트 후 강제 화면 새로고침
            if hasattr(self, 'tag_chip_scroll_area'):
                # FlowLayout 강제 업데이트
                if hasattr(self, 'tag_chip_flow_layout'):
                    self.tag_chip_flow_layout.update()
                    self.tag_chip_flow_layout.activate()
                
                # 단계별 강제 새로고침
                # 1. FlowLayout 내의 모든 태그칩 새로고침
                for i in range(self.tag_chip_flow_layout.count()):
                    item = self.tag_chip_flow_layout.itemAt(i)
                    if item and item.widget():
                        widget = item.widget()
                        widget.updateGeometry()
                        widget.update()
                        widget.repaint()
                
                # 2. 컨테이너 위젯들 강제 새로고침
                self.tag_chip_container.updateGeometry()
                self.tag_chip_container.update()
                self.tag_chip_container.repaint()
                
                # 3. 스크롤 영역 강제 새로고침  
                self.tag_chip_scroll_area.updateGeometry()
                self.tag_chip_scroll_area.update()
                self.tag_chip_scroll_area.repaint()
                
                # 4. 전체 위젯 강제 새로고침
                self.updateGeometry()
                self.update()
                self.repaint()
                
                # 5. 부모 위젯도 강제 새로고침
                if self.parent():
                    self.parent().update()
                    self.parent().repaint()
                
                logger.debug(f"[FILE_DETAIL] 태그 영역 강제 새로고침 완료 - 실제 표시된 태그칩 수: {self.tag_chip_flow_layout.count()}")
                
                # 6. 지연된 추가 새로고침 (PyQt 렌더링 타이밍 이슈 대응)
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(10, lambda: self._delayed_refresh())
                QTimer.singleShot(50, lambda: self._delayed_refresh())
                
                self.tag_chip_scroll_area.updateGeometry()
                self.tag_chip_scroll_area.update()
                self.tag_chip_container.updateGeometry()
                self.tag_chip_container.update()
                pass
                
        except Exception as e:
            logger.error(f"태그 칩 업데이트 실패: {e}")
            self._clear_tag_chips()

    def _clear_tag_chips(self):
        """기존 태그 칩들을 모두 제거합니다."""
        try:
            # FlowLayout에서 제거
            if hasattr(self, 'tag_chip_flow_layout'):
                while self.tag_chip_flow_layout.count() > 0:
                    item = self.tag_chip_flow_layout.takeAt(0)
                    if item and item.widget():
                        item.widget().deleteLater()
            pass
        except Exception as e:
            logger.error(f"태그 칩 제거 실패: {e}")

    # _on_tag_chip_removed 메서드 제거 - 읽기 전용으로 변경됨
    
    def _delayed_refresh(self):
        """지연된 강제 새로고침 - PyQt 렌더링 타이밍 이슈 해결용"""
        try:
            if hasattr(self, 'tag_chip_scroll_area') and hasattr(self, 'tag_chip_container'):
                self.tag_chip_container.update()
                self.tag_chip_container.repaint()
                self.tag_chip_scroll_area.update()
                self.tag_chip_scroll_area.repaint()
                self.update()
                self.repaint()
                logger.debug("[FILE_DETAIL] 지연된 새로고침 완료")
        except Exception as e:
            logger.warning(f"[FILE_DETAIL] 지연된 새로고침 중 오류: {e}")

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
