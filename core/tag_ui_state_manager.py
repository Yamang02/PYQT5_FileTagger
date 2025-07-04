from PyQt5.QtCore import QObject, pyqtSignal

class TagUIStateManager(QObject):
    """
    태그 관련 UI 위젯의 상태(활성/비활성, 선택/해제 등)를 중앙에서 일관성 있게 관리하는 클래스입니다.
    """
    state_changed = pyqtSignal(dict)  # 상태 변경 시 전체 상태 딕셔너리 전달

    def __init__(self):
        super().__init__()
        self._mode = 'individual'  # 'individual' 또는 'batch'
        self._selected_files = []
        self._selected_directory = ''
        self._tag_input_enabled = False
        self._quick_tags_enabled = False
        self._apply_button_enabled = False
        self.widgets = {}

    def register_widget(self, name: str, widget):
        """관리할 위젯을 등록합니다."""
        self.widgets[name] = widget

    def set_mode(self, mode: str):
        self._mode = mode
        self._emit_state()

    def set_selected_files(self, files: list):
        self._selected_files = files
        self._emit_state()

    def set_selected_directory(self, directory: str):
        self._selected_directory = directory
        self._emit_state()

    def set_tag_input_enabled(self, enabled: bool):
        self._tag_input_enabled = enabled
        self._emit_state()

    def set_quick_tags_enabled(self, enabled: bool):
        self._quick_tags_enabled = enabled
        self._emit_state()

    def set_apply_button_enabled(self, enabled: bool):
        self._apply_button_enabled = enabled
        self._emit_state()

    def get_state(self) -> dict:
        return {
            'mode': self._mode,
            'selected_files': self._selected_files,
            'selected_directory': self._selected_directory,
            'tag_input_enabled': self._tag_input_enabled,
            'quick_tags_enabled': self._quick_tags_enabled,
            'apply_button_enabled': self._apply_button_enabled,
        }

    def _emit_state(self):
        self.state_changed.emit(self.get_state())

    def set_file_selected(self, selected: bool, tags: list = None):
        """파일 선택/해제에 따라 관련 위젯 상태를 일괄 변경합니다."""
        if "tag_input" in self.widgets:
            self.widgets["tag_input"].set_enabled(selected)
            if selected and tags is not None:
                self.widgets["tag_input"].set_tags(tags)
            else:
                self.widgets["tag_input"].clear_tags()
        if "quick_tags" in self.widgets:
            self.widgets["quick_tags"].set_enabled(selected)
            if selected and tags is not None:
                self.widgets["quick_tags"].set_selected_tags(tags)
            else:
                self.widgets["quick_tags"].clear_selection()
        # 필요시 다른 위젯도 추가

    def set_filter_mode(self, enabled: bool):
        """필터링 모드 진입/해제에 따라 UI 상태를 변경합니다."""
        # 추후 확장 가능
        pass 