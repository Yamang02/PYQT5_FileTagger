"""
시그널 연결 관리자 - MainWindow의 시그널-슬롯 연결 로직을 분리

이 모듈은 MainWindow의 시그널 연결 책임을 분리하여 단일 책임 원칙을 준수하고
시그널 연결 구조를 명확하게 관리합니다.
"""

from PyQt5.QtCore import QItemSelectionModel


class SignalConnectionManager:
    """MainWindow의 시그널-슬롯 연결을 담당하는 관리자 클래스"""
    
    def __init__(self, main_window):
        """
        시그널 연결 관리자 초기화
        
        Args:
            main_window: MainWindow 인스턴스
        """
        self.main_window = main_window
        
    def connect_signals(self):
        """모든 시그널-슬롯 연결을 설정합니다."""
        self._connect_menu_actions()
        self._connect_widget_signals()
        self._connect_search_signals()
        
    def _connect_menu_actions(self):
        """메뉴 액션들의 시그널을 연결합니다."""
        self.main_window.actionExit.triggered.connect(self.main_window.close)
        self.main_window.actionSetWorkspace.triggered.connect(self.main_window.set_workspace)
        self.main_window.actionManageQuickTags.triggered.connect(self.main_window.ui_setup.get_widget('tag_control').open_custom_tag_dialog)
        
    def _connect_widget_signals(self):
        """위젯들의 시그널을 연결합니다."""
        # 디렉토리 트리 시그널
        self.main_window.ui_setup.get_widget('directory_tree').directory_selected.connect(
            self.main_window.on_directory_selected
        )
        self.main_window.ui_setup.get_widget('directory_tree').filter_options_changed.connect(
            self.main_window._on_directory_tree_filter_options_changed
        )
        self.main_window.ui_setup.get_widget('directory_tree').batch_remove_tags_requested.connect(
            self.main_window.ui_setup.get_widget('tag_control').open_batch_remove_tags_dialog
        )
        
        # 파일 리스트 시그널
        self.main_window.file_list.file_selection_changed.connect(
            self.main_window.on_file_selection_changed
        )
        
        
        
        # 파일 상세 정보 위젯은 읽기 전용이므로 태그 변경 시그널 연결 불필요
        
    def _connect_search_signals(self):
        """검색 위젯의 시그널을 연결합니다."""
        
        
        
    def disconnect_all_signals(self):
        """모든 시그널 연결을 해제합니다. (테스트나 정리 시 사용)"""
        try:
            # 메뉴 액션 시그널 해제
            self.main_window.actionExit.triggered.disconnect()
            self.main_window.actionSetWorkspace.triggered.disconnect()
            self.main_window.actionManageQuickTags.triggered.disconnect()
            
            # 위젯 시그널 해제
            self.main_window.ui_setup.get_widget('directory_tree').tree_view.clicked.disconnect()
            self.main_window.ui_setup.get_widget('directory_tree').filter_options_changed.disconnect()
            self.main_window.ui_setup.get_widget('directory_tree').directory_context_menu_requested.disconnect()
            
            self.main_window.ui_setup.get_widget('file_list').list_view.selectionModel().selectionChanged.disconnect()
            self.main_window.ui_setup.get_widget('tag_control').tags_updated.disconnect()
            # 파일 상세 정보 위젯은 읽기 전용이므로 tags_updated 시그널 없음
            
            # 검색 시그널 해제
            self.main_window.ui_setup.get_widget('search_widget').search_requested.disconnect()
            self.main_window.ui_setup.get_widget('search_widget').search_cleared.disconnect()
            self.main_window.ui_setup.get_widget('search_widget').advanced_search_requested.disconnect()
            
        except Exception as e:
            # 시그널 해제 실패는 로그만 남기고 계속 진행
            print(f"Signal disconnection warning: {e}")
            
    def get_signal_connections_info(self):
        """현재 연결된 시그널 정보를 반환합니다. (디버깅 용도)"""
        connections = {
            'menu_actions': [
                'actionExit.triggered',
                'actionSetWorkspace.triggered', 
                'actionManageQuickTags.triggered'
            ],
            'widget_signals': [
                'directory_tree.tree_view.clicked',
                'directory_tree.filter_options_changed',
                'directory_tree.directory_context_menu_requested',
                'file_list.list_view.selectionModel().selectionChanged',
                'tag_control.tags_updated',
                'file_detail.file_tags_changed'
            ],
            'search_signals': [
                'search_widget.search_requested',
                'search_widget.search_cleared',
                'search_widget.advanced_search_requested'
            ]
        }
        return connections 