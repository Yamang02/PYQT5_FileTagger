import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QCheckBox, QComboBox, QTableWidget, QTableWidgetItem,
    QProgressBar, QGroupBox, QFileDialog, QMessageBox, QHeaderView
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont

from widgets.tag_input_widget import TagInputWidget


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
        
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        """UI 구성 요소들을 설정합니다."""
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # 디렉토리 선택 그룹
        dir_group = QGroupBox("대상 디렉토리")
        dir_group.setMaximumHeight(80)
        dir_layout = QHBoxLayout()
        
        self.dir_label = QLabel("디렉토리:")
        self.dir_path_edit = QLineEdit()
        self.dir_path_edit.setReadOnly(True)
        self.dir_path_edit.setPlaceholderText("디렉토리를 선택하세요")
        
        self.browse_button = QPushButton("찾아보기")
        self.browse_button.setMaximumWidth(80)
        
        dir_layout.addWidget(self.dir_label)
        dir_layout.addWidget(self.dir_path_edit, 1)
        dir_layout.addWidget(self.browse_button)
        dir_group.setLayout(dir_layout)
        
        # 파일 미리보기 그룹
        preview_group = QGroupBox("파일 미리보기")
        preview_layout = QVBoxLayout()
        
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(3)
        self.file_table.setHorizontalHeaderLabels(["파일명", "경로", "현재 태그"])
        self.file_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.file_table.setMaximumHeight(150)
        self.file_table.setMinimumHeight(100)
        
        preview_layout.addWidget(self.file_table)
        preview_group.setLayout(preview_layout)
        
        # 옵션 그룹
        options_group = QGroupBox("적용 옵션")
        options_group.setMaximumHeight(120)
        options_layout = QVBoxLayout()
        
        # 재귀 옵션
        self.recursive_checkbox = QCheckBox("하위 디렉토리 포함")
        
        # 파일 확장자 필터
        ext_layout = QHBoxLayout()
        ext_layout.addWidget(QLabel("확장자:"))
        self.ext_combo = QComboBox()
        self.ext_combo.addItems(["모든 파일", "이미지 파일", "문서 파일", "사용자 정의"])
        self.ext_combo.currentTextChanged.connect(self.on_extension_changed)
        
        self.custom_ext_edit = QLineEdit()
        self.custom_ext_edit.setPlaceholderText(".jpg,.png,.pdf")
        self.custom_ext_edit.setVisible(False)
        self.custom_ext_edit.setMaximumWidth(120)
        
        ext_layout.addWidget(self.ext_combo)
        ext_layout.addWidget(self.custom_ext_edit)
        options_layout.addLayout(ext_layout)
        options_layout.addWidget(self.recursive_checkbox)
        options_group.setLayout(options_layout)
        
        # 태그 입력 그룹
        tag_group = QGroupBox("추가할 태그")
        tag_group.setMaximumHeight(120)
        tag_layout = QVBoxLayout()
        
        self.tag_input_widget = TagInputWidget()
        self.tag_input_widget.setMaximumHeight(80)
        tag_layout.addWidget(self.tag_input_widget)
        tag_group.setLayout(tag_layout)
        
        # 실행 버튼 및 진행률
        action_layout = QHBoxLayout()
        
        self.apply_button = QPushButton("태그 적용")
        self.apply_button.setEnabled(False)
        
        self.cancel_button = QPushButton("취소")
        self.cancel_button.setVisible(False)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        action_layout.addWidget(self.apply_button)
        action_layout.addWidget(self.cancel_button)
        action_layout.addWidget(self.progress_bar, 1)
        
        # 메인 레이아웃에 추가
        layout.addWidget(dir_group)
        layout.addWidget(preview_group)
        layout.addWidget(options_group)
        layout.addWidget(tag_group)
        layout.addLayout(action_layout)
        
        self.setLayout(layout)
        
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
        else:
            self.dir_path_edit.clear()
            self.file_table.setRowCount(0)
            self.apply_button.setEnabled(False)
            
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
        elif text == "이미지 파일 (.jpg, .png, .gif)":
            return [".jpg", ".jpeg", ".png", ".gif", ".bmp"]
        elif text == "문서 파일 (.pdf, .doc, .txt)":
            return [".pdf", ".doc", ".docx", ".txt", ".rtf"]
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
        self.apply_button.setEnabled(len(self.target_files) > 0)
        
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
            QMessageBox.information(
                self, 
                "완료", 
                f"일괄 태그 추가가 완료되었습니다.\n처리된 파일: {processed}개"
            )
            # 파일 미리보기 새로고침
            self.update_file_preview()
        else:
            error_msg = result.get("error", "알 수 없는 오류가 발생했습니다.")
            QMessageBox.critical(self, "오류", f"일괄 태그 추가 중 오류가 발생했습니다:\n{error_msg}")
            
    def reset_ui_state(self):
        """UI 상태를 원래대로 되돌립니다."""
        self.apply_button.setVisible(True)
        self.cancel_button.setVisible(False)
        self.progress_bar.setVisible(False)
        
    def hide_panel(self):
        """패널을 숨깁니다."""
        self.setVisible(False)
        self.reset_ui_state() 