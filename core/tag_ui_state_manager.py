class TagUIStateManager:
    """
    태그 관련 UI 위젯의 상태(활성/비활성, 선택/해제 등)를 중앙에서 일관성 있게 관리하는 클래스입니다.
    """
    def __init__(self):
        self.widgets = {}

    def register_widget(self, name: str, widget):
        """관리할 위젯을 등록합니다."""
        self.widgets[name] = widget

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