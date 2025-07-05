import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QCheckBox, QComboBox, QTableWidget, QTableWidgetItem,
    QProgressBar, QGroupBox, QFileDialog, QMessageBox, QHeaderView,
    QFrame, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor


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
        self.target_files = []
        self.current_directory = ""
        self.state_manager = None
        
        self.setup_ui()
        self.connect_signals()
        self.apply_styles()
        self.dir_path_edit.setText("") # 초기화 시 경로 필드를 비움
        
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
        
        # 파일 미리보기 그룹
        preview_group = QGroupBox("📋 파일 미리보기")
        preview_layout = QVBoxLayout()
        
        # 파일 수 표시
        self.file_count_label = QLabel("0개 파일")
        self.file_count_label.setStyleSheet("color: #7f8c8d; font-size: 11px; padding: 4px;")
        
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(3)
        self.file_table.setHorizontalHeaderLabels(["파일명", "경로", "현재 태그"])
        self.file_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.file_table.setMaximumHeight(180)
        self.file_table.setMinimumHeight(120)
        self.file_table.setAlternatingRowColors(True)
        self.file_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #ecf0f1;
                background-color: white;
                alternate-background-color: #f8f9fa;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 6px;
                border: none;
                font-weight: bold;
            }
        """)
        
        preview_layout.addWidget(self.file_count_label)
        preview_layout.addWidget(self.file_table)
        preview_group.setLayout(preview_layout)
        
        # 옵션 그룹
        options_group = QGroupBox("⚙️ 적용 옵션")
        options_group.setMaximumHeight(130)
        options_layout = QVBoxLayout()
        
        # 재귀 옵션
        self.recursive_checkbox = QCheckBox("하위 디렉토리 포함")
        self.recursive_checkbox.setStyleSheet("""
            QCheckBox {
                spacing: 8px;
                font-size: 11px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
        """)
        
        # 파일 확장자 필터
        ext_layout = QHBoxLayout()
        ext_layout.addWidget(QLabel("확장자:"))
        self.ext_combo = QComboBox()
        self.ext_combo.addItems(["모든 파일", "이미지 파일", "문서 파일", "사용자 정의"])
        self.ext_combo.setStyleSheet("""
            QComboBox {
                padding: 4px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #7f8c8d;
            }
        """)
        
        self.custom_ext_edit = QLineEdit()
        self.custom_ext_edit.setPlaceholderText(".jpg,.png,.pdf")
        self.custom_ext_edit.setVisible(False)
        self.custom_ext_edit.setMaximumWidth(150)
        self.custom_ext_edit.setStyleSheet("""
            QLineEdit {
                padding: 4px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
            }
        """)
        
        ext_layout.addWidget(self.ext_combo)
        ext_layout.addWidget(self.custom_ext_edit)
        ext_layout.addStretch()
        options_layout.addLayout(ext_layout)
        options_layout.addWidget(self.recursive_checkbox)
        options_group.setLayout(options_layout)
        
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
        layout.addWidget(preview_group)
        layout.addWidget(options_group)
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
        

    def set_directory(self, directory_path):
        """디렉토리를 설정하고 파일 미리보기를 업데이트합니다."""
        print(f"[BatchTaggingPanel] set_directory 호출: {directory_path}") # 디버그 출력
        if os.path.exists(directory_path) and os.path.isdir(directory_path):
            self.current_directory = directory_path
            self.dir_path_edit.setText(directory_path)
            self.update_file_preview()
            self.directory_changed.emit(directory_path)
            
            # 상태 관리자에 알림
            if self.state_manager:
                self.state_manager.set_selected_directory(directory_path)
        else:
            QMessageBox.warning(self, "경로 오류", "유효하지 않은 디렉토리 경로입니다.")

    def browse_directory(self):
        """디렉토리 선택 대화상자를 엽니다."""
        directory = QFileDialog.getExistingDirectory(self, "일괄 태그 적용할 디렉토리 선택")
        if directory:
            self.set_directory(directory)

    def on_extension_changed(self, text):
        """확장자 선택이 변경될 때 호출됩니다."""
        self.custom_ext_edit.setVisible(text == "사용자 정의")
        self.update_file_preview()

    def get_file_extensions(self):
        """현재 선택된 파일 확장자 목록을 반환합니다."""
        current_text = self.ext_combo.currentText()
        
        if current_text == "모든 파일":
            return []
        elif current_text == "이미지 파일":
            return [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".svg"]
        elif current_text == "문서 파일":
            return [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".xls", ".xlsx", ".ppt", ".pptx"]
        elif current_text == "사용자 정의":
            custom_text = self.custom_ext_edit.text().strip()
            if custom_text:
                # 쉼표로 구분된 확장자 파싱
                extensions = [ext.strip() for ext in custom_text.split(",")]
                # 점(.)이 없는 확장자에 점 추가
                extensions = [ext if ext.startswith(".") else f".{ext}" for ext in extensions if ext]
                return extensions
            return []
        
        return []

    def update_file_preview(self):
        """파일 미리보기를 업데이트합니다."""
        print(f"[BatchTaggingPanel] update_file_preview 호출. 현재 디렉토리: {self.current_directory}") # 디버그 출력
        if not self.current_directory:
            self.file_table.setRowCount(0)
            self.file_count_label.setText("0개 파일")
            self.apply_button.setEnabled(False)
            print("[BatchTaggingPanel] 현재 디렉토리 없음. 미리보기 업데이트 중단.") # 디버그 출력
            return
            
        try:
            file_extensions = self.get_file_extensions()
            recursive = self.recursive_checkbox.isChecked()
            
            # 파일 목록 수집
            files = []
            if recursive:
                for root, dirs, file_names in os.walk(self.current_directory):
                    for file_name in file_names:
                        file_path = os.path.join(root, file_name)
                        if self._should_include_file(file_path, file_extensions):
                            files.append(file_path)
            else:
                for file_name in os.listdir(self.current_directory):
                    file_path = os.path.join(self.current_directory, file_name)
                    if os.path.isfile(file_path) and self._should_include_file(file_path, file_extensions):
                        files.append(file_path)
            
            # 파일명으로 정렬
            files.sort(key=lambda x: os.path.basename(x).lower())
            
            # 테이블 업데이트
            self.file_table.setRowCount(len(files))
            for i, file_path in enumerate(files):
                # 파일명
                file_name_item = QTableWidgetItem(os.path.basename(file_path))
                file_name_item.setFlags(file_name_item.flags() & ~Qt.ItemIsEditable)
                
                # 상대 경로
                try:
                    relative_path = os.path.relpath(file_path, self.current_directory)
                except ValueError:
                    relative_path = file_path
                path_item = QTableWidgetItem(relative_path)
                path_item.setFlags(path_item.flags() & ~Qt.ItemIsEditable)
                
                # 현재 태그
                try:
                    tags = self.tag_manager.get_tags_for_file(file_path)
                    tags_text = ", ".join(tags) if tags else ""
                except Exception:
                    tags_text = ""
                tags_item = QTableWidgetItem(tags_text)
                tags_item.setFlags(tags_item.flags() & ~Qt.ItemIsEditable)
                
                self.file_table.setItem(i, 0, file_name_item)
                self.file_table.setItem(i, 1, path_item)
                self.file_table.setItem(i, 2, tags_item)
            
            # 대상 파일 목록 업데이트
            self.target_files = files
            
            # 파일 수 표시 및 버튼 활성화
            self.file_count_label.setText(f"{len(files)}개 파일")
            self.apply_button.setEnabled(len(files) > 0)
            
            # 상태 관리자에 알림
            if self.state_manager:
                self.state_manager.set_batch_target_files(files)
                self.state_manager.set_batch_options(recursive, file_extensions)
                
        except Exception as e:
            QMessageBox.critical(self, "파일 미리보기 오류", f"파일 목록을 가져오는 중 오류가 발생했습니다:\n{str(e)}")
            self.file_table.setRowCount(0)
            self.file_count_label.setText("0개 파일")
            self.apply_button.setEnabled(False)
            print(f"[BatchTaggingPanel] 파일 미리보기 업데이트 중 오류: {e}") # 디버그 출력

    def _should_include_file(self, file_path, file_extensions):
        """파일이 포함되어야 하는지 확인합니다."""
        if not file_extensions:  # 모든 파일
            return True
        
        file_ext = os.path.splitext(file_path)[1].lower()
        return file_ext in [ext.lower() for ext in file_extensions]

    def start_batch_tagging(self):
        """일괄 태그 추가 작업을 시작합니다."""
        # 태그 입력 위젯에서 태그 가져오기 (통합 패널에서 제공)
        tags = []
        if hasattr(self.parent(), 'individual_tag_input'):
            tags = self.parent().individual_tag_input.get_tags()
        print(f"[BatchTaggingPanel] start_batch_tagging 호출. 가져온 태그: {tags}") # 디버그 출력
            
        if not tags:
            QMessageBox.warning(self, "태그 입력 필요", "적용할 태그를 입력해주세요.")
            print("[BatchTaggingPanel] 태그 없음. 작업 중단.") # 디버그 출력
            return
            
        if not self.target_files:
            QMessageBox.warning(self, "파일 선택 필요", "태그를 적용할 파일이 없습니다.")
            print("[BatchTaggingPanel] 대상 파일 없음. 작업 중단.") # 디버그 출력
            return
            
        # 확인 대화상자
        reply = QMessageBox.question(
            self, 
            "일괄 태그 적용 확인", 
            f"{len(self.target_files)}개 파일에 다음 태그를 적용하시겠습니까?\n\n태그: {', '.join(tags)}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            print("[BatchTaggingPanel] 사용자 취소. 작업 중단.") # 디버그 출력
            return
            
        # UI 상태 변경
        self.apply_button.setVisible(False)
        self.cancel_button.setVisible(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(self.target_files))
        self.progress_bar.setValue(0)
        self.status_label.setText("작업 진행 중...")
        print("[BatchTaggingPanel] 워커 스레드 시작 준비.") # 디버그 출력
        
        # 워커 스레드 시작
        self.worker_thread = BatchTaggingWorker(
            self.tag_manager,
            self.current_directory,
            tags,
            self.recursive_checkbox.isChecked(),
            self.get_file_extensions()
        )
        
        self.worker_thread.progress_updated.connect(self.progress_bar.setValue)
        self.worker_thread.work_finished.connect(self.on_batch_tagging_finished)
        self.worker_thread.start()
        
        # 시그널 발송
        self.batch_tagging_started.emit()

    def cancel_batch_tagging(self):
        """일괄 태그 추가 작업을 취소합니다."""
        print("[BatchTaggingPanel] cancel_batch_tagging 호출.") # 디버그 출력
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.terminate()
            self.worker_thread.wait()
            
        self.reset_ui_state()
        self.status_label.setText("작업이 취소되었습니다")
        QTimer.singleShot(3000, lambda: self.status_label.setText("대기 중"))

    def on_batch_tagging_finished(self, result):
        """일괄 태그 추가 작업이 완료될 때 호출됩니다."""
        print(f"[BatchTaggingPanel] on_batch_tagging_finished 호출. 결과: {result}") # 디버그 출력
        self.reset_ui_state()
        
        if result.get("success", False):
            # 성공
            processed_count = result.get("processed_count", 0)
            self.status_label.setText(f"완료: {processed_count}개 파일 처리됨")
            
            # 파일 미리보기 새로고침 (태그 정보 업데이트)
            self.update_file_preview()
            
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
        print("[BatchTaggingPanel] reset_ui_state 호출.") # 디버그 출력
        self.apply_button.setVisible(True)
        self.cancel_button.setVisible(False)
        self.progress_bar.setVisible(False)
        self.apply_button.setEnabled(len(self.target_files) > 0)

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
        print(f"[BatchTaggingPanel] _on_state_changed 호출. 상태: {state.get('mode')}, 디렉토리: {state.get('selected_directory')}") # 디버그 출력
        # 일괄 태깅 모드일 때만 반응
        if state.get('mode') == 'batch':
            directory = state.get('selected_directory', '')
            if directory and directory != self.current_directory:
                self.set_directory(directory)

    def get_target_files(self):
        """현재 대상 파일 목록을 반환합니다."""
        return self.target_files.copy()
        
    def get_current_directory(self):
        """현재 디렉토리를 반환합니다."""
        return self.current_directory
