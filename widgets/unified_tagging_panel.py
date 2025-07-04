from PyQt5.QtWidgets import QWidget, QTabWidget, QVBoxLayout
from PyQt5.QtCore import pyqtSignal
from widgets.file_selection_and_preview_widget import FileSelectionAndPreviewWidget
from widgets.tag_input_widget import TagInputWidget
from widgets.quick_tags_widget import QuickTagsWidget
# from widgets.batch_tagging_panel import BatchTaggingPanel  # 일괄 태깅 서브 컴포넌트(필요시)

# 추후 실제 위젯 import로 대체 예정
# from .file_selection_and_preview_widget import FileSelectionAndPreviewWidget
# from .tag_input_widget import TagInputWidget
# from .quick_tags_widget import QuickTagsWidget
# from .batch_tagging_panel import BatchTaggingPanel
# from core.tag_ui_state_manager import TagUIStateManager

class UnifiedTaggingPanel(QWidget):
    mode_changed = pyqtSignal(str)  # 'individual' 또는 'batch'

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget(self)
        self.layout.addWidget(self.tab_widget)
        self.setLayout(self.layout)

        # 개별 태깅 탭
        self.individual_tab = QWidget()
        self.individual_tab_layout = QVBoxLayout(self.individual_tab)
        self.file_selection_widget = FileSelectionAndPreviewWidget(self.individual_tab)
        self.tag_input_widget = TagInputWidget(self.individual_tab)
        self.quick_tags_widget = QuickTagsWidget(parent=self.individual_tab)
        self.individual_tab_layout.addWidget(self.file_selection_widget)
        self.individual_tab_layout.addWidget(self.tag_input_widget)
        self.individual_tab_layout.addWidget(self.quick_tags_widget)
        self.individual_tab.setLayout(self.individual_tab_layout)

        # 일괄 태깅 탭
        self.batch_tab = QWidget()
        self.batch_tab_layout = QVBoxLayout(self.batch_tab)
        self.batch_file_selection_widget = FileSelectionAndPreviewWidget(self.batch_tab)
        self.batch_tag_input_widget = TagInputWidget(self.batch_tab)
        self.batch_quick_tags_widget = QuickTagsWidget(parent=self.batch_tab)
        # self.batch_panel = BatchTaggingPanel(self.batch_tab)  # 필요시 추가
        self.batch_tab_layout.addWidget(self.batch_file_selection_widget)
        self.batch_tab_layout.addWidget(self.batch_tag_input_widget)
        self.batch_tab_layout.addWidget(self.batch_quick_tags_widget)
        self.batch_tab.setLayout(self.batch_tab_layout)

        self.tab_widget.addTab(self.individual_tab, "개별 태깅")
        self.tab_widget.addTab(self.batch_tab, "일괄 태깅")

        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        self.state_manager = None

        # 시그널 연결(개별 태깅)
        self.file_selection_widget.file_selected.connect(self._on_file_selected)
        self.file_selection_widget.directory_selected.connect(self._on_directory_selected)
        self.tag_input_widget.tags_changed.connect(self._on_tags_changed)
        self.quick_tags_widget.tags_changed.connect(self._on_tags_changed)
        # 시그널 연결(일괄 태깅)
        self.batch_file_selection_widget.file_selected.connect(self._on_file_selected)
        self.batch_file_selection_widget.directory_selected.connect(self._on_directory_selected)
        self.batch_tag_input_widget.tags_changed.connect(self._on_tags_changed)
        self.batch_quick_tags_widget.tags_changed.connect(self._on_tags_changed)

    def set_state_manager(self, manager):
        """TagUIStateManager 인스턴스 연동"""
        self.state_manager = manager
        self.mode_changed.connect(self.state_manager.set_mode)
        self.state_manager.state_changed.connect(self._on_state_changed)

    def switch_mode(self, mode: str):
        """외부에서 모드 전환 요청 시 탭 변경"""
        if mode == 'individual':
            self.tab_widget.setCurrentIndex(0)
        elif mode == 'batch':
            self.tab_widget.setCurrentIndex(1)
        self.mode_changed.emit(mode)

    def _on_tab_changed(self, index):
        mode = 'individual' if index == 0 else 'batch'
        self.mode_changed.emit(mode)
        if self.state_manager:
            self.state_manager.set_mode(mode)

    def _on_file_selected(self, file_path):
        if self.state_manager:
            self.state_manager.set_selected_files([file_path])

    def _on_directory_selected(self, dir_path):
        if self.state_manager:
            self.state_manager.set_selected_directory(dir_path)

    def _on_tags_changed(self, tags):
        if self.state_manager:
            self.state_manager.set_tag_input_enabled(bool(tags))

    def _on_state_changed(self, state: dict):
        # 상태에 따라 각 위젯 활성/비활성 등 UI 동기화
        if state['mode'] == 'individual':
            self.tag_input_widget.set_enabled(state['tag_input_enabled'])
            self.quick_tags_widget.set_enabled(state['quick_tags_enabled'])
        else:
            self.batch_tag_input_widget.set_enabled(state['tag_input_enabled'])
            self.batch_quick_tags_widget.set_enabled(state['quick_tags_enabled']) 