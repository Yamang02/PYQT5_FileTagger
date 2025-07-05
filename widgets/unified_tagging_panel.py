from PyQt5.QtWidgets import (
    QWidget, QTabWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QSplitter, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
import traceback

from widgets.tag_input_widget import TagInputWidget
from widgets.quick_tags_widget import QuickTagsWidget
from widgets.batch_tagging_panel import BatchTaggingPanel
from widgets.file_selection_and_preview_widget import FileSelectionAndPreviewWidget


class UnifiedTaggingPanel(QWidget):
    """
    개별 태깅과 일괄 태깅을 통합하는 탭 기반 패널
    DRS-20250705-002의 핵심 요구사항을 구현합니다.
    """
    
    # 시그널 정의
    mode_changed = pyqtSignal(str)  # 'individual' 또는 'batch'
    file_selected = pyqtSignal(str, list)  # 파일 경로, 태그 목록
    tags_applied = pyqtSignal(str, list)  # 파일 경로, 적용된 태그 목록
    
    def __init__(self, state_manager, tag_manager, parent=None):
        super().__init__(parent)
        self.state_manager = state_manager
        self.tag_manager = tag_manager
        
        # 순환 호출 방지를 위한 플래그
        self._updating_from_state = False
        
        self.setup_ui()
        self.connect_signals()
        
        # 상태 관리자에 위젯 등록
        self.state_manager.register_widget('unified_panel', self)
        
        print("[UnifiedTaggingPanel] 초기화 완료")
        
    def setup_ui(self):
        """통합 패널의 UI를 설정합니다."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        # 제목 영역
        title_layout = QHBoxLayout()
        title_label = QLabel("📎 파일 태깅 관리")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setStyleSheet("color: #2c3e50; padding: 4px;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # 구분선
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #bdc3c7;")
        
        # 탭 위젯 생성
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                border: 1px solid #bdc3c7;
                border-bottom: none;
                border-radius: 4px 4px 0 0;
                padding: 8px 16px;
                margin-right: 2px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 1px solid white;
            }
            QTabBar::tab:hover {
                background-color: #d5dbdb;
            }
        """)
        
        # 개별 태깅 탭 생성
        self.individual_tab = self.create_individual_tab()
        self.tab_widget.addTab(self.individual_tab, "🔖 개별 태깅")
        
        # 일괄 태깅 탭 생성
        self.batch_tab = self.create_batch_tab()
        self.tab_widget.addTab(self.batch_tab, "📁 일괄 태깅")
        
        # 레이아웃에 추가
        main_layout.addLayout(title_layout)
        main_layout.addWidget(separator)
        main_layout.addWidget(self.tab_widget)
        
    def create_individual_tab(self):
        """개별 태깅 탭을 생성합니다."""
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # 스플리터로 파일 선택과 태그 입력 영역을 분할
        splitter = QSplitter(Qt.Horizontal)
        
        # 파일 선택 및 미리보기 위젯
        self.file_selection_widget = FileSelectionAndPreviewWidget(self.state_manager, self.tag_manager, self)
        self.file_selection_widget.file_selected.connect(self.on_file_selected)
        splitter.addWidget(self.file_selection_widget)
        
        # 태그 입력 영역
        tag_panel = QWidget()
        tag_layout = QVBoxLayout(tag_panel)
        tag_layout.setContentsMargins(8, 8, 8, 8)
        tag_layout.setSpacing(8)
        
        # 태그 입력 제목
        tag_title = QLabel("🏷️ 태그 관리")
        tag_title.setFont(QFont("Arial", 12, QFont.Bold))
        tag_title.setStyleSheet("color: #34495e; padding: 4px;")
        
        # 태그 입력 위젯
        self.individual_tag_input = TagInputWidget(self)
        self.individual_tag_input.tags_changed.connect(self.on_individual_tags_changed)
        
        # 빠른 태그 위젯
        self.individual_quick_tags = QuickTagsWidget(parent=self)
        self.individual_quick_tags.tags_changed.connect(self.on_individual_quick_tags_changed)
        
        # 태그 저장 버튼
        self.save_tags_button = QPushButton("💾 태그 저장")
        self.save_tags_button.setEnabled(False)
        self.save_tags_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        self.save_tags_button.clicked.connect(self.save_individual_tags)
        
        # 태그 패널 레이아웃 구성
        tag_layout.addWidget(tag_title)
        tag_layout.addWidget(self.individual_tag_input)
        tag_layout.addWidget(self.individual_quick_tags)
        tag_layout.addWidget(self.save_tags_button)
        tag_layout.addStretch()
        
        splitter.addWidget(tag_panel)
        splitter.setSizes([2, 1])  # 파일 선택:태그 입력 = 2:1 비율
        
        layout.addWidget(splitter)
        
        return tab_widget
        
    def create_batch_tab(self):
        """일괄 태깅 탭을 생성합니다."""
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # BatchTaggingPanel을 통합하되, 중복 UI 요소는 제거
        self.batch_tagging_panel = BatchTaggingPanel(self.tag_manager, self)
        
        # BatchTaggingPanel의 상태 관리자 설정
        self.batch_tagging_panel.set_state_manager(self.state_manager)
        
        layout.addWidget(self.batch_tagging_panel)
        
        return tab_widget
        
    def connect_signals(self):
        """시그널과 슬롯을 연결합니다."""
        # 탭 변경 시그널
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        # 개별 태깅 위젯 시그널
        self.individual_tag_input.tags_changed.connect(self.on_individual_tags_changed)
        self.individual_quick_tags.tags_changed.connect(self.on_individual_quick_tags_changed)
        
        # 상태 관리자와 연결
        if self.state_manager:
            self.state_manager.state_changed.connect(self.on_state_changed)
        
    def on_tab_changed(self, index):
        print(f"[UTP] on_tab_changed 호출, 인덱스: {index}")
        if self._updating_from_state:
            return
        if index == 0:
            self.current_mode = 'individual'
            print(f"[UTP] 상태 매니저 모드 설정 요청: individual")
            self.state_manager.set_mode('individual')
        elif index == 1:
            self.current_mode = 'batch'
            print(f"[UTP] 상태 매니저 모드 설정 요청: batch")
            self.state_manager.set_mode('batch')
        self.mode_changed.emit(self.current_mode)
        
    def on_file_selected(self, file_path, tags):
        """파일이 선택될 때 호출됩니다."""
        if self._updating_from_state:
            return  # 순환 호출 방지
            
        self.current_selected_file = file_path
        
        if file_path:
            # 선택된 파일의 기존 태그 로드
            existing_tags = self.tag_manager.get_tags_for_file(file_path)
            
            # 태그 입력 위젯에 기존 태그 설정
            self.individual_tag_input.set_tags(existing_tags)
            self.individual_quick_tags.set_selected_tags(existing_tags)
            
            # 위젯 활성화
            self.individual_tag_input.set_enabled(True)
            self.individual_quick_tags.set_enabled(True)
            self.save_tags_button.setEnabled(True)
            
            # 상태 관리자에 알림
            self.state_manager.set_selected_files([file_path])
            
        else:
            # 파일 선택 해제 시 위젯 비활성화
            self.individual_tag_input.set_enabled(False)
            self.individual_quick_tags.set_enabled(False)
            self.save_tags_button.setEnabled(False)
            
            # 상태 관리자에 알림
            self.state_manager.set_selected_files([])
        
    def on_individual_tags_changed(self, tags):
        """개별 태깅에서 태그가 변경될 때 호출됩니다."""
        # 빠른 태그 위젯과 동기화
        self.individual_quick_tags.set_selected_tags(tags)
        
    def on_individual_quick_tags_changed(self, tags):
        """개별 태깅에서 빠른 태그가 변경될 때 호출됩니다."""
        # 태그 입력 위젯과 동기화
        self.individual_tag_input.set_tags(tags)
        
    def save_individual_tags(self):
        """개별 파일의 태그를 저장합니다."""
        if not hasattr(self, 'current_selected_file') or not self.current_selected_file:
            return
            
        tags = self.individual_tag_input.get_tags()
        
        try:
            # 태그 저장
            self.tag_manager.set_tags_for_file(self.current_selected_file, tags)
            
            # 파일 선택 위젯의 태그 표시 업데이트
            self.file_selection_widget.refresh_file_tags(self.current_selected_file)
            
            # 시그널 발송
            self.tags_applied.emit(self.current_selected_file, tags)
            
            # 상태바 메시지 (부모 윈도우에서 처리)
            if self.parent():
                self.parent().statusbar.showMessage(f"태그가 저장되었습니다: {self.current_selected_file}", 3000)
                
        except Exception as e:
            if self.parent():
                self.parent().statusbar.showMessage(f"태그 저장 실패: {str(e)}", 5000)
                
    def on_state_changed(self, state):
        print(f"[UTP] on_state_changed 호출, 상태: {state.get('mode')}")
        if self._updating_from_state:
            return
        self._updating_from_state = True
        try:
            current_mode = state.get('mode', 'individual')
            current_tab_index = self.tab_widget.currentIndex()
            expected_tab_index = 0 if current_mode == 'individual' else 1
            if current_tab_index != expected_tab_index:
                print(f"[UTP] on_state_changed - 탭 인덱스 변경 시도: {expected_tab_index}")
                self.tab_widget.setCurrentIndex(expected_tab_index)
            selected_files = state.get('selected_files', [])
            if selected_files and current_mode == 'individual':
                current_file_tags = state.get('current_file_tags', [])
        except Exception as e:
            print(f"[UTP] on_state_changed 오류: {e}")
        finally:
            self._updating_from_state = False
        
    def set_state_manager(self, state_manager):
        """상태 관리자를 설정합니다."""
        self.state_manager = state_manager
        
        # 하위 위젯들에도 상태 관리자 설정
        if hasattr(self.file_selection_widget, 'set_state_manager'):
            self.file_selection_widget.set_state_manager(state_manager)
            
        if hasattr(self.batch_tagging_panel, 'set_state_manager'):
            self.batch_tagging_panel.set_state_manager(state_manager)
            
        # 상태 관리자에 위젯들 등록
        state_manager.register_widget('individual_tag_input', self.individual_tag_input)
        state_manager.register_widget('individual_quick_tags', self.individual_quick_tags)
        state_manager.register_widget('save_tags_button', self.save_tags_button)
        
    def get_current_mode(self):
        """현재 모드를 반환합니다."""
        return self.current_mode
        
    def switch_to_mode(self, mode):
        print(f"[UTP] switch_to_mode 호출: {mode}")
        print(f"[UTP] tab_widget: {self.tab_widget}, type: {type(self.tab_widget)}")
        try:
            if not hasattr(self, 'tab_widget') or not self.tab_widget:
                print(f"[UTP] tab_widget이 존재하지 않음")
                return
            if mode == 'individual':
                print(f"[UTP] 탭 인덱스 변경 시도: {mode}")
                try:
                    self.tab_widget.setCurrentIndex(0)
                    print(f"[UTP] setCurrentIndex(0) 성공")
                except Exception as e:
                    print(f"[UTP] setCurrentIndex(0) 예외: {e}")
                    traceback.print_exc()
                    raise
            elif mode == 'batch':
                print(f"[UTP] 탭 인덱스 변경 시도: {mode}")
                try:
                    self.tab_widget.setCurrentIndex(1)
                    print(f"[UTP] setCurrentIndex(1) 성공")
                except Exception as e:
                    print(f"[UTP] setCurrentIndex(1) 예외: {e}")
                    traceback.print_exc()
                    raise
        except RuntimeError as e:
            if "wrapped C/C++ object" in str(e):
                print(f"[UTP] switch_to_mode RuntimeError(wrapped C/C++ object): {e}")
                return
            else:
                print(f"[UTP] switch_to_mode RuntimeError: {e}")
                traceback.print_exc()
                raise
        except Exception as e:
            print(f"[UTP] switch_to_mode 예외: {e}")
            traceback.print_exc()
            raise

    def cleanup(self):
        """정리 작업을 수행합니다."""
        # 상태 관리자에서 위젯 등록 해제
        self.state_manager.unregister_widget('unified_panel')
        print("[UnifiedTaggingPanel] 정리 완료") 