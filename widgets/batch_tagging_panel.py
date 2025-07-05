import os
from PyQt5.QtWidgets import QWidget, QFileDialog, QMessageBox, QProgressBar, QPushButton, QLineEdit, QLabel
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from PyQt5 import uic


class BatchTaggingWorker(QThread):
    """백그라운드에서 일괄 태그 추가 작업을 수행하는 워커 스레드"""
    
    progress_updated = pyqtSignal(int)
    work_finished = pyqtSignal(dict)
    
    def __init__(self, tag_manager, directory_path, tags, recursive, file_extensions):
        super().__init__()
        self.tag_manager = tag_manager
        self.directory_path = directory_path
        self.tags = tags
        self.recursive = recursive
        self.file_extensions = file_extensions
    
    def run(self):
        """백그라운드에서 일괄 태그 추가 작업 실행"""
        try:
            result = self.tag_manager.add_tags_to_directory(
                self.directory_path, 
                self.tags, 
                self.recursive, 
                self.file_extensions
            )
            self.work_finished.emit(result)
        except Exception as e:
            self.work_finished.emit({"success": False, "error": str(e)})


class BatchTaggingPanel(QWidget):
    """
    일괄 태깅에 특화된 기능을 제공하는 패널 위젯
    DRS-20250705-002에 따라 중복 UI 요소를 제거하고 일괄 태깅 전용 기능만 포함
    """
    
    # 시그널 정의
    batch_tagging_started = pyqtSignal()
    batch_tagging_finished = pyqtSignal(dict)
    directory_changed = pyqtSignal(str)
    
    def __init__(self, tag_manager, parent=None):
        super().__init__(parent)
        self.tag_manager = tag_manager
        self.worker_thread = None
        self.current_directory = "" # 현재 디렉토리 경로를 저장 (UI 표시용)
        self.state_manager = None
        
        self.setup_ui()
        self.connect_signals()
        self.apply_styles()
        
    def setup_ui(self):
        """UI 구성 요소들을 설정합니다."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # 제목 및 상태 표시
        title_layout = QHBoxLayout()
        title_label = QLabel("📁 일괄 태그 추가")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        title_label.setStyleSheet("color: #2c3e50; padding: 4px;")
        
        self.status_label = QLabel("대기 중")
        self.status_label.setStyleSheet("color: #7f8c8d; font-size: 10px; padding: 4px;")
        
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(self.status_label)
        
        # 구분선
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #bdc3c7;")
        
        # 디렉토리 선택 그룹
        dir_group = QGroupBox("📂 대상 디렉토리")
        dir_group.setMaximumHeight(90)
        dir_layout = QHBoxLayout()
        
        self.dir_label = QLabel("경로:")
        self.dir_path_edit = QLineEdit()
        self.dir_path_edit.setReadOnly(True)
        self.dir_path_edit.setPlaceholderText("디렉토리를 선택하세요")
        self.dir_path_edit.setStyleSheet("""
            QLineEdit {
                padding: 6px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: #f8f9fa;
            }
        """)
        
        self.browse_button = QPushButton("찾아보기")
        self.browse_button.setMaximumWidth(80)
        self.browse_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        
        dir_layout.addWidget(self.dir_label)
        dir_layout.addWidget(self.dir_path_edit, 1)
        dir_layout.addWidget(self.browse_button)
        dir_group.setLayout(dir_layout)
        
        # 작업 진행 상황 표시
        progress_group = QGroupBox("📊 진행 상황")
        progress_group.setMaximumHeight(80)
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                text-align: center;
                background-color: #ecf0f1;
            }
            QProgressBar::chunk {
                background-color: #27ae60;
                border-radius: 3px;
            }
        """)
        
        progress_layout.addWidget(self.progress_bar)
        progress_group.setLayout(progress_layout)
        
        # 실행 버튼 영역
        button_layout = QHBoxLayout()
        
        self.apply_button = QPushButton("🚀 일괄 태그 적용")
        self.apply_button.setEnabled(False)  # 초기에는 비활성화
        self.apply_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        
        self.cancel_button = QPushButton("❌ 취소")
        self.cancel_button.setVisible(False)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
            QPushButton:pressed {
                background-color: #6c7b7d;
            }
        """)
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.apply_button)
        
        # 레이아웃에 모든 그룹 추가
        layout.addLayout(title_layout)
        layout.addWidget(separator)
        layout.addWidget(dir_group)
        layout.addWidget(progress_group)
        layout.addLayout(button_layout)
        layout.addStretch()

    def apply_styles(self):
        """전체 패널에 스타일을 적용합니다."""
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 8px;
                background-color: #fafafa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #2c3e50;
                background-color: #fafafa;
            }
        """)

    def connect_signals(self):
        """시그널과 슬롯을 연결합니다."""
        self.browse_button.clicked.connect(self.browse_directory)
        
    def browse_directory(self):
        """디렉토리 선택 대화상자를 엽니다."""
        directory = QFileDialog.getExistingDirectory(self, "일괄 태그 적용할 디렉토리 선택")
        if directory:
            self.current_directory = directory # UI에 표시할 경로 업데이트
            self.dir_path_edit.setText(directory)
            self.directory_changed.emit(directory) # 상태 관리자에 디렉토리 변경 알림
            # 상태 관리자로부터 파일 목록을 받아와 apply_button 활성화 여부 결정
            if self.state_manager:
                target_files = self.state_manager.get('batch_target_files', [])
                self.apply_button.setEnabled(len(target_files) > 0)

    def start_batch_tagging(self):
        """일괄 태그 추가 작업을 시작합니다."""
        tags = self.state_manager.get('current_tags_for_batch', [])
        directory_path = self.state_manager.get('selected_directory', '')
        recursive = self.state_manager.get('batch_options', {}).get('recursive', False)
        file_extensions = self.state_manager.get('batch_options', {}).get('file_extensions', [])
        target_files = self.state_manager.get('batch_target_files', [])
            
        if not tags:
            QMessageBox.warning(self, "태그 입력 필요", "적용할 태그를 입력해주세요.")
            return
            
        if not target_files:
            QMessageBox.warning(self, "파일 선택 필요", "태그를 적용할 파일이 없습니다.")
            return
            
        # 확인 대화상자
        reply = QMessageBox.question(
            self, 
            "일괄 태그 적용 확인", 
            f"{len(target_files)}개 파일에 다음 태그를 적용하시겠습니까?\n\n태그: {', '.join(tags)}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
            
        # UI 상태 변경
        self.apply_button.setVisible(False)
        self.cancel_button.setVisible(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(target_files))
        self.progress_bar.setValue(0)
        self.status_label.setText("작업 진행 중...")
        
        # 워커 스레드 시작
        self.worker_thread = BatchTaggingWorker(
            self.tag_manager,
            directory_path,
            tags,
            recursive,
            file_extensions
        )
        
        self.worker_thread.progress_updated.connect(self.progress_bar.setValue)
        self.worker_thread.work_finished.connect(self.on_batch_tagging_finished)
        self.worker_thread.start()
        
        # 시그널 발송
        self.batch_tagging_started.emit()

    def cancel_batch_tagging(self):
        """일괄 태그 추가 작업을 취소합니다."""
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.terminate()
            self.worker_thread.wait()
            
        self.reset_ui_state()
        self.status_label.setText("작업이 취소되었습니다")
        QTimer.singleShot(3000, lambda: self.status_label.setText("대기 중"))

    def on_batch_tagging_finished(self, result):
        """일괄 태그 추가 작업이 완료될 때 호출됩니다."""
        self.reset_ui_state()
        
        if result.get("success", False):
            # 성공
            processed_count = result.get("processed_count", 0)
            self.status_label.setText(f"완료: {processed_count}개 파일 처리됨")
            
            # 성공 메시지
            QMessageBox.information(
                self, 
                "일괄 태그 적용 완료", 
                f"{processed_count}개 파일에 태그가 성공적으로 적용되었습니다."
            )
            
        else:
            # 실패
            error_message = result.get("error", "알 수 없는 오류가 발생했습니다.")
            self.status_label.setText("오류 발생")
            
            QMessageBox.critical(
                self, 
                "일괄 태그 적용 실패", 
                f"일괄 태그 적용 중 오류가 발생했습니다:\n\n{error_message}"
            )
        
        # 3초 후 상태 초기화
        QTimer.singleShot(3000, lambda: self.status_label.setText("대기 중"))
        
        # 시그널 발송
        self.batch_tagging_finished.emit(result)

    def reset_ui_state(self):
        """UI 상태를 초기화합니다."""
        target_files = self.state_manager.get('batch_target_files', [])
        self.apply_button.setVisible(True)
        self.cancel_button.setVisible(False)
        self.progress_bar.setVisible(False)
        self.apply_button.setEnabled(len(target_files) > 0)

    def hide_panel(self):
        """패널을 숨깁니다."""
        self.setVisible(False)

    def set_state_manager(self, manager):
        """상태 관리자를 설정합니다."""
        self.state_manager = manager
        if hasattr(manager, 'state_changed'):
            manager.state_changed.connect(self._on_state_changed)

    def _on_state_changed(self, state: dict):
        """상태 관리자 상태 변경 시 호출됩니다."""
        # 일괄 태깅 모드일 때만 반응
        if state.get('mode') == 'batch':
            directory = state.get('selected_directory', '')
            batch_target_files = state.get('batch_target_files', [])
            if directory and directory != self.current_directory:
                self.current_directory = directory
                self.dir_path_edit.setText(directory)
            self.apply_button.setEnabled(len(batch_target_files) > 0)