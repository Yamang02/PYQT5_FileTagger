import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QCheckBox, QComboBox, QGroupBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


class BatchTaggingOptionsWidget(QWidget):
    """
    일괄 태깅 적용 옵션을 설정하는 위젯 (재귀, 파일 확장자 필터)
    """
    options_changed = pyqtSignal(bool, list) # recursive, file_extensions

    def __init__(self, state_manager, parent=None):
        super().__init__(parent)
        self.state_manager = state_manager
        self.setup_ui()
        self.connect_signals()
        self.apply_styles()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        options_group = QGroupBox("⚙️ 일괄 태깅 옵션")
        options_layout = QVBoxLayout()

        # 재귀 옵션
        self.recursive_checkbox = QCheckBox("하위 디렉토리 포함")
        options_layout.addWidget(self.recursive_checkbox)

        # 파일 확장자 필터
        ext_layout = QHBoxLayout()
        ext_layout.addWidget(QLabel("확장자:"))
        self.ext_combo = QComboBox()
        self.ext_combo.addItems(["모든 파일", "이미지 파일", "문서 파일", "사용자 정의"])
        self.custom_ext_edit = QLineEdit()
        self.custom_ext_edit.setPlaceholderText(".jpg,.png,.pdf")
        self.custom_ext_edit.setVisible(False)
        self.custom_ext_edit.setMaximumWidth(150)

        ext_layout.addWidget(self.ext_combo)
        ext_layout.addWidget(self.custom_ext_edit)
        ext_layout.addStretch()
        options_layout.addLayout(ext_layout)

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        layout.addStretch()

    def apply_styles(self):
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
            QCheckBox {
                spacing: 8px;
                font-size: 11px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
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
            QLineEdit {
                padding: 4px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
            }
        """)

    def connect_signals(self):
        self.recursive_checkbox.stateChanged.connect(self._on_options_changed)
        self.ext_combo.currentTextChanged.connect(self._on_extension_changed)
        self.custom_ext_edit.textChanged.connect(self._on_options_changed)

    def _on_extension_changed(self, text):
        self.custom_ext_edit.setVisible(text == "사용자 정의")
        self._on_options_changed()

    def _on_options_changed(self):
        recursive = self.recursive_checkbox.isChecked()
        file_extensions = self._get_file_extensions()
        self.options_changed.emit(recursive, file_extensions)
        self.state_manager.set_batch_options(recursive=recursive, file_extensions=file_extensions)

    def _get_file_extensions(self):
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
                extensions = [ext.strip() for ext in custom_text.split(",")]
                extensions = [ext if ext.startswith(".") else f".{ext}" for ext in extensions if ext]
                return extensions
            return []
        return []

    def set_state_manager(self, manager):
        self.state_manager = manager
        # 초기 상태 설정
        batch_options = self.state_manager.get_batch_options()
        self.recursive_checkbox.setChecked(batch_options.get('recursive', False))
        # TODO: ext_combo와 custom_ext_edit의 초기 상태 설정 로직 추가 필요