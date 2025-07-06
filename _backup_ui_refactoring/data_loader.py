# data_loader.py
from PyQt5.QtCore import QTimer
from core.tag_manager import TagManager
from core.tag_ui_state_manager import TagUIStateManager

class DataLoader:
    def __init__(self, main_window, tag_manager: TagManager, state_manager: TagUIStateManager):
        self.main_window = main_window
        self.tag_manager = tag_manager
        self.state_manager = state_manager

    def initialize_data(self):
        """애플리케이션 시작 시 필요한 데이터를 로드하고 초기 상태를 설정합니다."""
        # 데이터베이스 연결을 지연시켜 실행
        QTimer.singleShot(0, self._connect_to_db)

        # 초기 상태 설정
        self.state_manager.set_file_selected(False)

    def _connect_to_db(self):
        """
        백그라운드에서 데이터베이스 연결을 시도하고
        연결 성공 시 UI를 업데이트합니다.
        """
        if self.tag_manager.connect():
            # 통합 패널이 완전히 초기화된 후에 태그 관련 업데이트 수행
            QTimer.singleShot(100, self._update_tags_after_connection)
            self.main_window.statusBar().showMessage("데이터베이스 연결 성공", 3000)
        else:
            self.main_window.statusBar().showMessage(
                "Database connection failed. Please check settings and restart.", 5000
            )
    
    def _update_tags_after_connection(self):
        """데이터베이스 연결 후 태그 관련 업데이트를 수행합니다."""
        try:
            if hasattr(self.main_window, 'unified_tagging_panel') and self.main_window.unified_tagging_panel:
                # unified_tagging_panel의 update_all_tags_list와 update_tag_autocomplete는
                # SignalConnector의 on_tags_applied에서 호출되므로 여기서는 제거
                pass
        except Exception as e:
            import traceback
            print(f"[DataLoader] 연결 후 태그 업데이트 중 오류: {e}")
            traceback.print_exc()
