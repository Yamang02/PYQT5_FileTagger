from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import QTimer

from core.tag_manager import TagManager
from core.tag_ui_state_manager import TagUIStateManager
from ui_initializer import UIInitializer
from signal_connector import SignalConnector
from data_loader import DataLoader








class MainWindow(QMainWindow):
    """
    메인 윈도우의 UI와 모든 동작을 관리합니다.
    사용자 요청에 따라 3분할 레이아웃을 구현합니다.
    - 왼쪽: 디렉토리 트리뷰
    - 가운데: 파일 목록 테이블뷰 및 미리보기
    - 오른쪽: 통합 태깅 패널 (개별/일괄 태깅 탭 포함)
    """

    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("FileTagger")
        self.setGeometry(100, 100, 1200, 800) # 기본 윈도우 크기 설정

        # 핵심 컴포넌트 초기화
        self.tag_manager = TagManager()
        self.state_manager = TagUIStateManager()
        
        # UI 구성 요소 설정
        from ui_initializer import UIInitializer
        self.ui_initializer = UIInitializer(self, self.tag_manager, self.state_manager)
        self.ui_initializer.setup_ui()
        self.batch_tagging_options_widget = self.ui_initializer.batch_tagging_options_widget # UIInitializer에서 생성된 위젯 참조
        self.unified_tagging_panel = self.ui_initializer.main_window.unified_tagging_panel # UIInitializer에서 생성된 위젯 참조
        self.file_selection_and_preview_widget = self.ui_initializer.main_window.file_selection_and_preview_widget # UIInitializer에서 생성된 위젯 참조
        self.tree_view_dirs = self.ui_initializer.main_window.tree_view_dirs # UIInitializer에서 생성된 위젯 참조
        self.dir_model = self.ui_initializer.main_window.dir_model # UIInitializer에서 생성된 위젯 참조
        self.open_dir_action = self.ui_initializer.main_window.open_dir_action # UIInitializer에서 생성된 위젯 참조
        self.individual_mode_action = self.ui_initializer.main_window.individual_mode_action # UIInitializer에서 생성된 위젯 참조
        self.batch_mode_action = self.ui_initializer.main_window.batch_mode_action # UIInitializer에서 생성된 위젯 참조
        self.clear_filter_action = self.ui_initializer.main_window.clear_filter_action # UIInitializer에서 생성된 위젯 참조

        # 데이터 로더 초기화 및 데이터 로드
        from data_loader import DataLoader
        self.data_loader = DataLoader(self, self.tag_manager, self.state_manager)
        self.data_loader.initialize_data()

        # 시그널 연결
        from signal_connector import SignalConnector
        self.signal_connector = SignalConnector(self, self.tag_manager, self.state_manager)
        self.signal_connector.connect_all_signals()

    def closeEvent(self, event):
        """애플리케이션 종료 시 정리 작업을 수행합니다."""
        try:
            # 태그 매니저 연결 해제
            if hasattr(self, 'tag_manager'):
                self.tag_manager.disconnect()
                
            # 상태 관리자 정리
            if hasattr(self, 'state_manager'):
                # 등록된 위젯들 정리
                for widget_name in list(self.state_manager.get_registered_widgets()):
                    self.state_manager.unregister_widget(widget_name)
                    
            print("[MainWindow] 정리 작업 완료")
            
        except Exception as e:
            print(f"[MainWindow] 종료 시 정리 작업 중 오류: {e}")
            
        event.accept()

    
