from PyQt5.QtCore import QObject, pyqtSignal

class TagUIStateManager(QObject):
    """
    태그 관련 UI 위젯의 상태(활성/비활성, 선택/해제 등)를 중앙에서 일관성 있게 관리하는 클래스입니다.
    DRS-20250705-002에 따라 통합 패널의 전반적인 상태 관리 기능을 확장했습니다.
    """
    state_changed = pyqtSignal(dict)  # 상태 변경 시 전체 상태 딕셔너리 전달

    def __init__(self):
        super().__init__()
        # 기본 상태 변수들
        self._mode = 'individual'  # 'individual' 또는 'batch'
        self._selected_files = []
        self._selected_directory = ''
        self._tag_input_enabled = False
        self._quick_tags_enabled = False
        self._apply_button_enabled = False
        
        # 확장된 상태 변수들 (DRS 요구사항)
        self._current_file_tags = []  # 현재 선택된 파일의 태그
        self._batch_target_files = []  # 일괄 태깅 대상 파일들
        self._batch_options = {
            'recursive': False,
            'file_extensions': []
        }
        self._ui_visibility = {
            'individual_panel': True,
            'batch_panel': False,
            'file_selection_widget': True,
            'tag_input_widgets': True
        }
        
        # 등록된 위젯들
        self.widgets = {}
        
        # 순환 호출 방지를 위한 플래그
        self._updating_state = False

    def register_widget(self, name: str, widget):
        """관리할 위젯을 등록합니다."""
        self.widgets[name] = widget
        print(f"[TagUIStateManager] 위젯 등록: {name}")

    def unregister_widget(self, name: str):
        """위젯 등록을 해제합니다."""
        if name in self.widgets:
            del self.widgets[name]
            print(f"[TagUIStateManager] 위젯 등록 해제: {name}")

    # 모드 관리
    def set_mode(self, mode: str):
        print(f"[TUSM] set_mode 호출: {mode}")
        if mode in ['individual', 'batch'] and self._mode != mode:
            self._mode = mode
            print(f"[TUSM] _update_mode_dependent_state 호출 (모드: {mode})")
            self._update_mode_dependent_state()
            print(f"[TUSM] _emit_state 호출 (모드: {mode})")
            self._emit_state()
            print(f"[TagUIStateManager] 모드 변경: {mode}")

    def get_mode(self):
        """현재 모드를 반환합니다."""
        return self._mode

    # 파일 선택 관리
    def set_selected_files(self, files: list):
        """선택된 파일 목록을 설정합니다."""
        if self._updating_state:
            return  # 순환 호출 방지
            
        new_files = files.copy() if files else []
        if new_files != self._selected_files:
            self._selected_files = new_files
            self._update_file_selection_dependent_state()
            self._emit_state()

    def get_selected_files(self):
        """선택된 파일 목록을 반환합니다."""
        return self._selected_files.copy()

    def set_selected_directory(self, directory: str):
        """선택된 디렉토리를 설정합니다."""
        if self._updating_state:
            return  # 순환 호출 방지
            
        if directory != self._selected_directory:
            self._selected_directory = directory
            self._update_directory_dependent_state()
            self._emit_state()

    def get_selected_directory(self):
        """선택된 디렉토리를 반환합니다."""
        return self._selected_directory

    # 태그 관리
    def set_current_file_tags(self, tags: list):
        """현재 선택된 파일의 태그를 설정합니다."""
        new_tags = tags.copy() if tags else []
        if new_tags != self._current_file_tags:
            self._current_file_tags = new_tags
            self._emit_state()

    def get_current_file_tags(self):
        """현재 선택된 파일의 태그를 반환합니다."""
        return self._current_file_tags.copy()

    # 일괄 태깅 관리
    def set_batch_target_files(self, files: list):
        """일괄 태깅 대상 파일들을 설정합니다."""
        new_files = files.copy() if files else []
        if new_files != self._batch_target_files:
            self._batch_target_files = new_files
            self._emit_state()

    def get_batch_target_files(self):
        """일괄 태깅 대상 파일들을 반환합니다."""
        return self._batch_target_files.copy()

    def set_batch_options(self, recursive: bool = False, file_extensions: list = []):
        """일괄 태깅 옵션을 설정합니다."""
        changed = False
        if recursive is not None and self._batch_options['recursive'] != recursive:
            self._batch_options['recursive'] = recursive
            changed = True
        if file_extensions is not None and self._batch_options['file_extensions'] != file_extensions:
            self._batch_options['file_extensions'] = file_extensions.copy()
            changed = True
        
        if changed:
            self._emit_state()

    def get_batch_options(self):
        """일괄 태깅 옵션을 반환합니다."""
        return self._batch_options.copy()

    # UI 활성화 상태 관리
    def set_tag_input_enabled(self, enabled: bool):
        """태그 입력 위젯 활성화 상태를 설정합니다."""
        if self._tag_input_enabled != enabled:
            self._tag_input_enabled = enabled
            self._apply_widget_state('tag_input', enabled)
            self._emit_state()

    def set_quick_tags_enabled(self, enabled: bool):
        """빠른 태그 위젯 활성화 상태를 설정합니다."""
        if self._quick_tags_enabled != enabled:
            self._quick_tags_enabled = enabled
            self._apply_widget_state('quick_tags', enabled)
            self._emit_state()

    def set_apply_button_enabled(self, enabled: bool):
        """적용 버튼 활성화 상태를 설정합니다."""
        if self._apply_button_enabled != enabled:
            self._apply_button_enabled = enabled
            self._apply_widget_state('save_button', enabled)
            self._apply_widget_state('apply_button', enabled)
            self._emit_state()

    # UI 가시성 관리
    def set_ui_visibility(self, component: str, visible: bool):
        print(f"[TUSM] UI 가시성 설정 시도: {component}, {visible}")
        if component in self._ui_visibility and self._ui_visibility[component] != visible:
            self._ui_visibility[component] = visible
            self._emit_state()

    def get_ui_visibility(self, component: str):
        """UI 컴포넌트의 가시성을 반환합니다."""
        return self._ui_visibility.get(component, True)

    # 통합 상태 관리 메서드들
    def set_file_selected(self, selected: bool, file_path: str | None = None, tags: list | None = None):
        """파일 선택/해제에 따라 관련 위젯 상태를 일괄 변경합니다."""
        if self._updating_state:
            return  # 순환 호출 방지
            
        self._updating_state = True
        try:
            if selected and file_path:
                self.set_selected_files([file_path])
                if tags is not None:
                    self.set_current_file_tags(tags)
                
                # 위젯 활성화
                self.set_tag_input_enabled(True)
                self.set_quick_tags_enabled(True)
                self.set_apply_button_enabled(True)
                
                # 태그 설정
                if "tag_input" in self.widgets and tags is not None:
                    self.widgets["tag_input"].set_tags(tags)
                if "quick_tags" in self.widgets and tags is not None:
                    self.widgets["quick_tags"].set_selected_tags(tags)
                    
            else:
                # 파일 선택 해제
                self.set_selected_files([])
                self.set_current_file_tags([])
                
                # 위젯 비활성화
                self.set_tag_input_enabled(False)
                self.set_quick_tags_enabled(False)
                self.set_apply_button_enabled(False)
                
                # 태그 초기화
                if "tag_input" in self.widgets:
                    self.widgets["tag_input"].clear_tags()
                if "quick_tags" in self.widgets:
                    self.widgets["quick_tags"].clear_selection()
        finally:
            self._updating_state = False

    def set_filter_mode(self, enabled: bool):
        """필터링 모드 진입/해제에 따라 UI 상태를 변경합니다."""
        # 필터 모드에서는 태그 편집 비활성화
        if enabled:
            self.set_tag_input_enabled(False)
            self.set_quick_tags_enabled(False)
            self.set_apply_button_enabled(False)
        else:
            # 현재 선택된 파일이 있으면 다시 활성화
            if self._selected_files:
                self.set_tag_input_enabled(True)
                self.set_quick_tags_enabled(True)
                self.set_apply_button_enabled(True)
        
        self._emit_state()

    # 내부 헬퍼 메서드들
    def _update_mode_dependent_state(self):
        print(f"[TUSM] _update_mode_dependent_state 시작 (현재 모드: {self._mode})")
        if self._mode == 'individual':
            print("[TUSM] UI 가시성 설정 시도: individual_panel, True")
            self.set_ui_visibility('individual_panel', True)
            print("[TUSM] UI 가시성 설정 시도: batch_panel, False")
            self.set_ui_visibility('batch_panel', False)
        elif self._mode == 'batch':
            print("[TUSM] UI 가시성 설정 시도: individual_panel, False")
            self.set_ui_visibility('individual_panel', False)
            print("[TUSM] UI 가시성 설정 시도: batch_panel, True")
            self.set_ui_visibility('batch_panel', True)

    def _update_file_selection_dependent_state(self):
        """파일 선택에 따른 상태 업데이트"""
        if self._updating_state:
            return  # 순환 호출 방지
            
        has_files = bool(self._selected_files)
        
        if self._mode == 'individual':
            self.set_tag_input_enabled(has_files)
            self.set_quick_tags_enabled(has_files)
            self.set_apply_button_enabled(has_files)

    def _update_directory_dependent_state(self):
        """디렉토리 선택에 따른 상태 업데이트"""
        if self._updating_state:
            return  # 순환 호출 방지
            
        has_directory = bool(self._selected_directory)
        
        if self._mode == 'batch':
            # 일괄 태깅 모드에서는 디렉토리 선택 시 관련 위젯 활성화
            self.set_tag_input_enabled(has_directory)
            self.set_quick_tags_enabled(has_directory)
            self.set_apply_button_enabled(has_directory)

    def _apply_widget_state(self, widget_name: str, enabled: bool):
        """특정 위젯에 활성화 상태를 적용합니다."""
        if widget_name in self.widgets:
            widget = self.widgets[widget_name]
            try:
                if hasattr(widget, 'set_enabled'):
                    widget.set_enabled(enabled)
                elif hasattr(widget, 'setEnabled'):
                    widget.setEnabled(enabled)
            except Exception as e:
                print(f"[TagUIStateManager] 위젯 상태 적용 오류 ({widget_name}): {e}")

    def get_state(self) -> dict:
        """전체 상태를 딕셔너리로 반환합니다."""
        return {
            'mode': self._mode,
            'selected_files': self._selected_files.copy(),
            'selected_directory': self._selected_directory,
            'current_file_tags': self._current_file_tags.copy(),
            'batch_target_files': self._batch_target_files.copy(),
            'batch_options': self._batch_options.copy(),
            'tag_input_enabled': self._tag_input_enabled,
            'quick_tags_enabled': self._quick_tags_enabled,
            'apply_button_enabled': self._apply_button_enabled,
            'ui_visibility': self._ui_visibility.copy()
        }

    def _emit_state(self):
        """상태 변경 시그널을 발송합니다."""
        if not self._updating_state:  # 순환 호출 방지
            self.state_changed.emit(self.get_state())

    # 디버깅 및 모니터링
    def print_state(self):
        """현재 상태를 콘솔에 출력합니다 (디버깅용)"""
        state = self.get_state()
        print("[TagUIStateManager] 현재 상태:")
        for key, value in state.items():
            print(f"  {key}: {value}")

    def get_registered_widgets(self):
        """등록된 위젯 목록을 반환합니다."""
        return list(self.widgets.keys()) 