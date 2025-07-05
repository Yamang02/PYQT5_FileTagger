from PyQt5.QtWidgets import QWidget, QLabel, QPushButton
from PyQt5.QtCore import pyqtSignal
from PyQt5 import uic

from widgets.tag_input_widget import TagInputWidget
from widgets.batch_tagging_options_widget import BatchTaggingOptionsWidget

class UnifiedTaggingPanel(QWidget):
    mode_changed = pyqtSignal(str)
    tags_applied = pyqtSignal(str, list)

    def __init__(self, state_manager, tag_manager, parent=None):
        super().__init__(parent)
        self.state_manager = state_manager
        self.tag_manager = tag_manager
        self.current_target_path = None
        self.is_current_target_dir = False
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        """UI를 설정합니다."""
        uic.loadUi('ui/unified_tagging_panel.ui', self)
        
        # .ui 파일에서 로드된 위젯 참조
        self.target_label = self.findChild(QLabel, 'target_label')
        self.tag_input_widget = self.findChild(TagInputWidget, 'tag_input_widget')
        self.batch_options_widget = self.findChild(BatchTaggingOptionsWidget, 'batch_options_widget')
        self.save_tags_button = self.findChild(QPushButton, 'save_tags_button')

        # 일괄 태깅 옵션 위젯 (기본적으로 숨김)
        self.batch_options_widget.setVisible(False)

    def connect_signals(self):
        """시그널을 연결합니다."""
        self.save_tags_button.clicked.connect(self.save_tags)

    def update_target(self, item_path, is_dir):
        """선택된 대상이 변경될 때 UI를 업데이트합니다."""
        self.current_target_path = item_path
        self.is_current_target_dir = is_dir

        if item_path:
            self.target_label.setText(f"Selected: {item_path}")
            # 선택된 대상의 태그를 TagInputWidget에 설정
            if not is_dir: # 파일인 경우에만 기존 태그 로드
                tags = self.tag_manager.get_tags_for_file(item_path)
                self.tag_input_widget.set_tags(tags)
            else:
                self.tag_input_widget.set_tags([]) # 디렉토리 선택 시 태그 입력 필드 초기화
        else:
            self.target_label.setText("Selected Target: None")
            self.tag_input_widget.set_tags([])

        self.batch_options_widget.setVisible(is_dir)

    def save_tags(self):
        """현재 입력된 태그를 저장합니다."""
        if not self.current_target_path:
            print("저장할 대상이 선택되지 않았습니다.")
            return

        tags_to_save = self.tag_input_widget.get_tags()

        if self.is_current_target_dir:
            # 일괄 태깅 로직 (하위 디렉토리 포함 여부 확인)
            include_subdirs = self.batch_options_widget.is_include_subdirectories_checked()
            print(f"디렉토리 '{self.current_target_path}'에 태그 {tags_to_save} 저장 (하위 디렉토리 포함: {include_subdirs})")
            self.tag_manager.add_tags_to_directory(self.current_target_path, tags_to_save, recursive=include_subdirs)
        else:
            # 개별 태깅 로직
            print(f"파일 '{self.current_target_path}'에 태그 {tags_to_save} 저장")
            self.tag_manager.update_tags(self.current_target_path, tags_to_save)

        self.tags_applied.emit(self.current_target_path, tags_to_save)

    def switch_to_mode(self, mode):
        # 이 메소드는 signal_connector.py에서 호출되므로 빈 형태로 추가합니다.
        # 추후 모드 전환에 따른 UI 변경 로직을 여기에 구현할 수 있습니다.
        self.mode_changed.emit(mode)

    def update_tag_autocomplete(self):
        # 이 메소드는 signal_connector.py에서 호출되므로 빈 형태로 추가합니다。
        # 추후 태그 자동 완성 로직을 여기에 구현할 수 있습니다.
        pass