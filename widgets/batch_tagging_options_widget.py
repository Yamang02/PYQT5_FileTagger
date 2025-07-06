import os
from PyQt5.QtWidgets import QWidget, QCheckBox, QComboBox, QLineEdit
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5 import uic


class BatchTaggingOptionsWidget(QWidget):
    """
    일괄 태깅 적용 옵션을 설정하는 위젯 (재귀, 파일 확장자 필터)
    """
    options_changed = pyqtSignal(bool, list) # recursive, file_extensions

    def __init__(self, state_manager=None, parent=None):
        super().__init__(parent)
        self.state_manager = state_manager
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        uic.loadUi('ui/batch_tagging_options_widget.ui', self)
        
        # .ui 파일에서 로드된 위젯 참조
        self.recursive_checkbox = self.findChild(QCheckBox, 'recursive_checkbox')
        self.ext_combo = self.findChild(QComboBox, 'ext_combo')
        self.custom_ext_edit = self.findChild(QLineEdit, 'custom_ext_edit')
        
        # 초기 상태 설정
        self.custom_ext_edit.setVisible(False)

    def apply_styles(self):
        # 이 메서드는 이제 사용되지 않거나, .ui 파일의 스타일을 보완하는 용도로만 사용됩니다.
        # 현재는 .ui 파일에 스타일이 정의되어 있으므로 비워둡니다.
        pass

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
        if self.state_manager:
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
        if self.state_manager:
            batch_options = self.state_manager.get_batch_options()
            self.recursive_checkbox.setChecked(batch_options.get('recursive', False))
            # TODO: ext_combo와 custom_ext_edit의 초기 상태 설정 로직 추가 필요