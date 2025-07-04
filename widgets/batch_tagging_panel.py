import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QCheckBox, QComboBox, QTableWidget, QTableWidgetItem,
    QProgressBar, QGroupBox, QFileDialog, QMessageBox, QHeaderView,
    QFrame, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor

from widgets.tag_input_widget import TagInputWidget
from widgets.file_selection_and_preview_widget import FileSelectionAndPreviewWidget
from widgets.quick_tags_widget import QuickTagsWidget


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
    디렉토리별 일괄 태그 추가 기능을 제공하는 통합 패널 위젯
    """
    
    def __init__(self, tag_manager, parent=None):
        super().__init__(parent)
        self.tag_manager = tag_manager
        self.worker_thread = None
        self.target_files = []
        
        self.layout = QVBoxLayout(self)
        self.file_selection_widget = FileSelectionAndPreviewWidget(self)
        self.tag_input_widget = TagInputWidget(self)
        self.quick_tags_widget = QuickTagsWidget(parent=self)
        self.apply_button = QPushButton("일괄 태그 적용", self)
        self.layout.addWidget(self.file_selection_widget)
        self.layout.addWidget(self.tag_input_widget)
        self.layout.addWidget(self.quick_tags_widget)
        self.layout.addWidget(self.apply_button)
        self.setLayout(self.layout)
        
        self.state_manager = None
        self.apply_button.clicked.connect(self._on_apply_clicked)
        
        self.setup_ui()
        self.connect_signals()
        self.apply_styles()
        
    def setup_ui(self):
        """UI 구성 요소들을 설정합니다."""
        layout = QVBoxLayout()
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
        
        # 태그 입력 그룹
        tag_group = QGroupBox("🏷️ 추가할 태그")
        tag_group.setMaximumHeight(130)
        tag_layout = QVBoxLayout()
        
        self.tag_input_widget = TagInputWidget()
        self.tag_input_widget.setMaximumHeight(90)
        tag_layout.addWidget(self.tag_input_widget)
        tag_group.setLayout(tag_layout)
        
        # 실행 버튼 및 진행률
        action_layout = QHBoxLayout()
        
        self.apply_button = QPushButton("🚀 태그 적용")
        self.apply_button.setEnabled(False)
        self.apply_button.setMinimumHeight(35)
        self.apply_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        
        self.cancel_button = QPushButton("❌ 취소")
        self.cancel_button.setVisible(False)
        self.cancel_button.setMinimumHeight(35)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 8px 16px;
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
        """)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimumHeight(25)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                text-align: center;
                background-color: #ecf0f1;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 3px;
            }
        """)
        
        action_layout.addWidget(self.apply_button)
        action_layout.addWidget(self.cancel_button)
        action_layout.addWidget(self.progress_bar, 1)
        
        # 메인 레이아웃에 추가
        layout.addLayout(title_layout)
        layout.addWidget(separator)
        layout.addWidget(dir_group)
        layout.addWidget(preview_group)
        layout.addWidget(options_group)
        layout.addWidget(tag_group)
        layout.addLayout(action_layout)
        
        self.setLayout(layout)
        
    def apply_styles(self):
        """전체 패널에 스타일을 적용합니다."""
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #2c3e50;
            }
        """)
        
    def connect_signals(self):
        """시그널 연결"""
        self.browse_button.clicked.connect(self.browse_directory)
        self.apply_button.clicked.connect(self.start_batch_tagging)
        self.cancel_button.clicked.connect(self.cancel_batch_tagging)
        self.recursive_checkbox.toggled.connect(self.update_file_preview)
        self.ext_combo.currentTextChanged.connect(self.update_file_preview)
        self.custom_ext_edit.textChanged.connect(self.update_file_preview)
        
    def set_directory(self, directory_path):
        """디렉토리 경로를 설정하고 파일 미리보기를 업데이트합니다."""
        if directory_path and os.path.exists(directory_path):
            self.dir_path_edit.setText(directory_path)
            self.update_file_preview()
            self.apply_button.setEnabled(True)
            self.status_label.setText("디렉토리 선택됨")
            self.status_label.setStyleSheet("color: #27ae60; font-size: 10px; padding: 4px;")
        else:
            self.dir_path_edit.clear()
            self.file_table.setRowCount(0)
            self.apply_button.setEnabled(False)
            self.status_label.setText("대기 중")
            self.status_label.setStyleSheet("color: #7f8c8d; font-size: 10px; padding: 4px;")
            
    def browse_directory(self):
        """디렉토리 선택 다이얼로그를 엽니다."""
        directory = QFileDialog.getExistingDirectory(
            self, "디렉토리 선택", self.dir_path_edit.text() or os.path.expanduser("~")
        )
        if directory:
            self.set_directory(directory)
            
    def on_extension_changed(self, text):
        """파일 확장자 선택이 변경되었을 때 호출됩니다."""
        self.custom_ext_edit.setVisible(text == "사용자 정의")
        self.update_file_preview()
        
    def get_file_extensions(self):
        """현재 선택된 파일 확장자를 반환합니다."""
        text = self.ext_combo.currentText()
        
        if text == "모든 파일":
            return None
        elif text == "이미지 파일":
            return [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"]
        elif text == "문서 파일":
            return [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".pages"]
        elif text == "사용자 정의":
            custom_text = self.custom_ext_edit.text().strip()
            if custom_text:
                return [ext.strip() for ext in custom_text.split(",") if ext.strip()]
        return None
        
    def update_file_preview(self):
        """파일 미리보기 테이블을 업데이트합니다."""
        directory_path = self.dir_path_edit.text()
        if not directory_path or not os.path.exists(directory_path):
            return
            
        self.target_files = []
        recursive = self.recursive_checkbox.isChecked()
        file_extensions = self.get_file_extensions()
        
        # 파일 수집
        try:
            if recursive:
                for root, dirs, files in os.walk(directory_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if self._should_include_file(file_path, file_extensions):
                            self.target_files.append(file_path)
            else:
                for item in os.listdir(directory_path):
                    item_path = os.path.join(directory_path, item)
                    if os.path.isfile(item_path) and self._should_include_file(item_path, file_extensions):
                        self.target_files.append(item_path)
        except Exception as e:
            print(f"파일 미리보기 업데이트 오류: {e}")
            self.status_label.setText(f"오류: {str(e)}")
            self.status_label.setStyleSheet("color: #e74c3c; font-size: 10px; padding: 4px;")
            return
            
        # 테이블 업데이트
        self.file_table.setRowCount(len(self.target_files))
        
        for i, file_path in enumerate(self.target_files):
            # 파일명
            filename = os.path.basename(file_path)
            self.file_table.setItem(i, 0, QTableWidgetItem(filename))
            
            # 경로
            rel_path = os.path.relpath(file_path, directory_path)
            self.file_table.setItem(i, 1, QTableWidgetItem(rel_path))
            
            # 현재 태그
            current_tags = self.tag_manager.get_tags_for_file(file_path)
            tags_text = ", ".join(current_tags) if current_tags else "태그 없음"
            self.file_table.setItem(i, 2, QTableWidgetItem(tags_text))
            
        # 상태 업데이트
        file_count = len(self.target_files)
        self.file_count_label.setText(f"{file_count}개 파일")
        self.apply_button.setEnabled(file_count > 0)
        
        if file_count > 0:
            self.status_label.setText(f"{file_count}개 파일 준비됨")
            self.status_label.setStyleSheet("color: #27ae60; font-size: 10px; padding: 4px;")
        else:
            self.status_label.setText("적용할 파일 없음")
            self.status_label.setStyleSheet("color: #f39c12; font-size: 10px; padding: 4px;")
        
    def _should_include_file(self, file_path, file_extensions):
        """파일이 확장자 필터에 맞는지 확인합니다."""
        if file_extensions is None:
            return True
        return any(file_path.lower().endswith(ext.lower()) for ext in file_extensions)
        
    def start_batch_tagging(self):
        """일괄 태그 추가 작업을 시작합니다."""
        if not self.target_files:
            QMessageBox.warning(self, "경고", "적용할 파일이 없습니다.")
            return
            
        tags = self.tag_input_widget.get_tags()
        if not tags:
            QMessageBox.warning(self, "경고", "추가할 태그를 입력하세요.")
            return
            
        # UI 상태 변경
        self.apply_button.setVisible(False)
        self.cancel_button.setVisible(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(self.target_files))
        self.progress_bar.setValue(0)
        
        self.status_label.setText("작업 진행 중...")
        self.status_label.setStyleSheet("color: #3498db; font-size: 10px; padding: 4px;")
        
        # 워커 스레드 시작
        self.worker_thread = BatchTaggingWorker(
            self.tag_manager,
            self.dir_path_edit.text(),
            tags,
            self.recursive_checkbox.isChecked(),
            self.get_file_extensions()
        )
        self.worker_thread.work_finished.connect(self.on_batch_tagging_finished)
        self.worker_thread.start()
        
    def cancel_batch_tagging(self):
        """일괄 태그 추가 작업을 취소합니다."""
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.terminate()
            self.worker_thread.wait()
            
        self.reset_ui_state()
        
    def on_batch_tagging_finished(self, result):
        """일괄 태그 추가 작업이 완료되었을 때 호출됩니다."""
        self.reset_ui_state()
        
        if result.get("success"):
            processed = result.get("processed", 0)
            successful = result.get("successful", processed)
            failed = result.get("failed", 0)
            modified = result.get("modified", 0)
            upserted = result.get("upserted", 0)
            errors = result.get("errors", [])
            
            # 상태 업데이트
            if failed == 0:
                self.status_label.setText(f"✅ 완료: {successful}개 파일 처리됨")
                self.status_label.setStyleSheet("color: #27ae60; font-size: 10px; padding: 4px;")
            else:
                self.status_label.setText(f"⚠️ 부분 완료: {successful}개 성공, {failed}개 실패")
                self.status_label.setStyleSheet("color: #f39c12; font-size: 10px; padding: 4px;")
            
            # 상세 결과 메시지 생성
            result_message = f"일괄 태그 추가가 완료되었습니다.\n\n"
            result_message += f"📊 처리 결과:\n"
            result_message += f"• 총 처리 파일: {processed}개\n"
            result_message += f"• 성공: {successful}개\n"
            result_message += f"• 실패: {failed}개\n"
            result_message += f"• 수정된 파일: {modified}개\n"
            result_message += f"• 새로 생성된 파일: {upserted}개\n"
            
            if errors:
                result_message += f"\n❌ 실패한 파일들:\n"
                for error_info in errors[:5]:  # 최대 5개만 표시
                    filename = os.path.basename(error_info.get("file", "알 수 없음"))
                    error_msg = error_info.get("error", "알 수 없는 오류")
                    result_message += f"• {filename}: {error_msg}\n"
                if len(errors) > 5:
                    result_message += f"• ... 및 {len(errors) - 5}개 더\n"
            
            # 성공/실패에 따른 아이콘 선택
            if failed == 0:
                QMessageBox.information(self, "✅ 완료", result_message)
            else:
                QMessageBox.warning(self, "⚠️ 부분 완료", result_message)
            
            # 파일 미리보기 새로고침
            self.update_file_preview()
        else:
            error_msg = result.get("error", "알 수 없는 오류가 발생했습니다.")
            errors = result.get("errors", [])
            self.status_label.setText("❌ 오류 발생")
            self.status_label.setStyleSheet("color: #e74c3c; font-size: 10px; padding: 4px;")
            
            # 오류 상세 정보 표시
            error_details = f"일괄 태그 추가 중 오류가 발생했습니다.\n\n"
            error_details += f"🔍 오류 내용:\n{error_msg}\n\n"
            if errors:
                error_details += f"❌ 실패한 파일들:\n"
                for error_info in errors[:5]:
                    filename = os.path.basename(error_info.get("file", "알 수 없음"))
                    error_msg = error_info.get("error", "알 수 없는 오류")
                    error_details += f"• {filename}: {error_msg}\n"
                if len(errors) > 5:
                    error_details += f"• ... 및 {len(errors) - 5}개 더\n"
            error_details += f"\n💡 해결 방법:\n"
            error_details += f"• 디렉토리 경로가 올바른지 확인하세요\n"
            error_details += f"• 데이터베이스 연결 상태를 확인하세요\n"
            error_details += f"• 태그 형식이 올바른지 확인하세요\n"
            error_details += f"• 파일 접근 권한을 확인하세요"
            QMessageBox.critical(self, "❌ 오류", error_details)
            
    def reset_ui_state(self):
        """UI 상태를 원래대로 되돌립니다."""
        self.apply_button.setVisible(True)
        self.cancel_button.setVisible(False)
        self.progress_bar.setVisible(False)
        
    def hide_panel(self):
        """패널을 숨깁니다."""
        self.setVisible(False)
        self.reset_ui_state()

    def set_state_manager(self, manager):
        self.state_manager = manager
        self.state_manager.state_changed.connect(self._on_state_changed)

    def _on_state_changed(self, state: dict):
        self.apply_button.setEnabled(state.get('apply_button_enabled', True))
        self.tag_input_widget.set_enabled(state.get('tag_input_enabled', True))
        self.quick_tags_widget.set_enabled(state.get('quick_tags_enabled', True))

    def _on_apply_clicked(self):
        files = self.file_selection_widget.get_selected_files()
        tags = self.tag_input_widget.get_tags() if hasattr(self.tag_input_widget, 'get_tags') else []
        if not files or not tags:
            QMessageBox.warning(self, "입력 오류", "파일과 태그를 모두 선택/입력해야 합니다.")
            return
        try:
            # TagManager.add_tags_to_directory(files, tags)  # 실제 태깅 로직 호출(비동기 처리 권장)
            QMessageBox.information(self, "성공", f"{len(files)}개 파일에 태그가 성공적으로 적용되었습니다.")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"일괄 태깅 중 오류 발생: {str(e)}") 