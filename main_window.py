import os
from PyQt5.QtWidgets import (
    QMainWindow,
    QAction,
    QFileDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QMenuBar,
    QStatusBar,
    QSplitter,
    QTreeView,
    QTableView,
    QFileSystemModel
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import QDir, QTimer, Qt, QModelIndex

from core.tag_manager import TagManager
from widgets.unified_tagging_panel import UnifiedTaggingPanel
from widgets.file_selection_and_preview_widget import FileSelectionAndPreviewWidget
from core.tag_ui_state_manager import TagUIStateManager
from widgets.batch_tagging_options_widget import BatchTaggingOptionsWidget # 새로 추가된 import








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
        
        # BatchTaggingOptionsWidget 초기화 (setup_main_layout 전에)
        self.batch_tagging_options_widget = BatchTaggingOptionsWidget(
            self.state_manager, self
        )

        # 데이터베이스 연결을 지연시켜 실행
        QTimer.singleShot(0, self.connect_to_db)  # 다시 활성화

        # UI 구성 요소 설정
        self.setup_menubar_and_statusbar()
        self.setup_main_layout()
        self.connect_signals()

        # 초기 상태 설정
        self.state_manager.set_file_selected(False)

    def connect_to_db(self):
        """
        백그라운드에서 데이터베이스 연결을 시도하고
        연결 성공 시 UI를 업데이트합니다.
        """
        if self.tag_manager.connect():
            # 통합 패널이 완전히 초기화된 후에 태그 관련 업데이트 수행
            QTimer.singleShot(100, self.update_tags_after_connection)
            self.statusBar().showMessage("데이터베이스 연결 성공", 3000)
        else:
            self.statusBar().showMessage(
                "Database connection failed. Please check settings and restart.", 5000
            )
    
    def update_tags_after_connection(self):
        """데이터베이스 연결 후 태그 관련 업데이트를 수행합니다."""
        try:
            if hasattr(self, 'unified_tagging_panel') and self.unified_tagging_panel:
                self.unified_tagging_panel.update_all_tags_list()
                self.unified_tagging_panel.update_tag_autocomplete()
        except Exception as e:
            import traceback
            print(f"[MainWindow] 연결 후 태그 업데이트 중 오류: {e}")
            traceback.print_exc()

    def setup_menubar_and_statusbar(self):
        """메뉴바와 상태바를 직접 설정합니다."""
        # 메뉴바 설정
        self.setMenuBar(QMenuBar(self))
        file_menu = self.menuBar().addMenu("&File")
        
        # 디렉토리 열기 액션
        self.open_dir_action = QAction("&Open Directory...", self)
        self.open_dir_action.triggered.connect(self.open_directory_dialog)
        file_menu.addAction(self.open_dir_action)

        # 구분선
        file_menu.addSeparator()

        # 모드 전환 액션들
        self.individual_mode_action = QAction("&개별 태깅 모드", self)
        self.individual_mode_action.triggered.connect(lambda: self.switch_tagging_mode('individual'))
        file_menu.addAction(self.individual_mode_action)

        self.batch_mode_action = QAction("&일괄 태깅 모드", self)
        self.batch_mode_action.triggered.connect(lambda: self.switch_tagging_mode('batch'))
        file_menu.addAction(self.batch_mode_action)

        # 필터 관련 메뉴 추가
        filter_menu = self.menuBar().addMenu("&Filter")
        self.clear_filter_action = QAction("&Clear Filter", self)
        self.clear_filter_action.setEnabled(False)  # 초기에는 비활성화
        self.clear_filter_action.triggered.connect(self.clear_filter)
        filter_menu.addAction(self.clear_filter_action)

        # 상태바 설정
        self.setStatusBar(QStatusBar(self))

    def setup_main_layout(self):
        """3분할 메인 레이아웃을 설정합니다."""
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        main_h_layout = QHBoxLayout(self.central_widget)
        main_h_layout.setContentsMargins(0, 0, 0, 0)
        main_h_layout.setSpacing(0)

        self.main_splitter = QSplitter(Qt.Horizontal)
        main_h_layout.addWidget(self.main_splitter)

        # 1. 왼쪽 섹션: 디렉토리 트리뷰
        self.tree_view_dirs = QTreeView(self)
        self.dir_model = QFileSystemModel()
        self.dir_model.setRootPath(QDir.rootPath())
        self.dir_model.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot)
        self.tree_view_dirs.setModel(self.dir_model)
        for i in range(1, self.dir_model.columnCount()):
            self.tree_view_dirs.setColumnHidden(i, True)
        self.tree_view_dirs.setHeaderHidden(True)
        self.main_splitter.addWidget(self.tree_view_dirs)

        # 2. 가운데 섹션: 파일 목록 및 옵션
        center_panel_layout = QVBoxLayout()
        self.file_selection_and_preview_widget = FileSelectionAndPreviewWidget(
            self.state_manager, self.tag_manager, self
        )
        center_panel_layout.addWidget(self.file_selection_and_preview_widget)
        center_panel_layout.addWidget(self.batch_tagging_options_widget)

        center_panel_container = QWidget()
        center_panel_container.setLayout(center_panel_layout)
        self.main_splitter.addWidget(center_panel_container)

        # 3. 오른쪽 섹션: 통합 태깅 패널 (UnifiedTaggingPanel)
        self.unified_tagging_panel = UnifiedTaggingPanel(
            self.state_manager, self.tag_manager, self
        )
        self.main_splitter.addWidget(self.unified_tagging_panel)

        # 스플리터 초기 크기 비율 설정 (예: 1:3:1)
        self.main_splitter.setSizes([1, 3, 1])

    def connect_signals(self):
        """시그널과 슬롯을 연결합니다."""
        # 디렉토리 트리뷰 선택 시그널
        self.tree_view_dirs.clicked.connect(self.on_directory_tree_clicked)

        # 파일 선택 및 미리보기 위젯 시그널
        self.file_selection_and_preview_widget.file_selected.connect(self.on_file_selected)

        # 통합 태깅 패널 시그널
        self.unified_tagging_panel.mode_changed.connect(self.on_tagging_mode_changed)
        self.unified_tagging_panel.tags_applied.connect(self.on_tags_applied)

        # 상태 관리자 시그널
        self.state_manager.state_changed.connect(self.on_state_changed)

    def on_directory_tree_clicked(self, index: QModelIndex):
        """디렉토리 트리뷰에서 디렉토리가 선택될 때 호출됩니다."""
        path = self.dir_model.filePath(index)
        if os.path.isdir(path):
            self.current_path = path
            self.file_selection_and_preview_widget.set_directory(path)
            self.state_manager.set_selected_directory(path)
            self.statusBar().showMessage(f"디렉토리 변경: {path}", 3000)

    def open_directory_dialog(self):
        """디렉토리 선택 대화상자를 엽니다."""
        directory = QFileDialog.getExistingDirectory(
            self, 
            "디렉토리 선택", 
            self.current_path
        )
        if directory:
            self.current_path = directory
            self.file_selection_and_preview_widget.set_directory(directory)
            self.state_manager.set_selected_directory(directory)
            self.statusBar().showMessage(f"디렉토리 변경: {directory}", 3000)

    def switch_tagging_mode(self, mode):
        """태깅 모드를 전환합니다."""
        try:
            if self.unified_tagging_panel:
                self.unified_tagging_panel.switch_to_mode(mode)
                self.statusBar().showMessage(f"모드 변경: {mode}", 2000)
        except Exception as e:
            print(f"[MainWindow] 모드 전환 중 오류: {e}")
            self.statusBar().showMessage(f"모드 전환 실패: {str(e)}", 3000)

    def on_tagging_mode_changed(self, mode):
        """태깅 모드가 변경될 때 호출됩니다."""
        # 메뉴 상태 업데이트
        self.individual_mode_action.setChecked(mode == 'individual')
        self.batch_mode_action.setChecked(mode == 'batch')
        
        # 상태바 메시지
        mode_text = "개별 태깅" if mode == 'individual' else "일괄 태깅"
        self.statusBar().showMessage(f"{mode_text} 모드로 전환되었습니다", 2000)

    def on_file_selected(self, file_path, tags=None):
        """파일이 선택될 때 호출됩니다."""
        if file_path:
            self.state_manager.set_selected_files([file_path])
            self.state_manager.set_current_file_tags(tags if tags is not None else [])
            self.statusBar().showMessage(f"파일 선택: {os.path.basename(file_path)}", 2000)
        else:
            self.state_manager.set_selected_files([])
            self.state_manager.set_current_file_tags([])
            self.statusBar().showMessage("파일 선택 해제", 1000)

    def on_tags_applied(self, file_path, tags):
        """태그가 적용될 때 호출됩니다."""
        tag_text = ", ".join(tags) if tags else "없음"
        self.statusBar().showMessage(
            f"태그 적용 완료 - {os.path.basename(file_path)}: {tag_text}", 
            3000
        )
        
        # 태그 자동 완성 모델 업데이트 (안전하게)
        try:
            if hasattr(self, 'unified_tagging_panel') and self.unified_tagging_panel:
                self.unified_tagging_panel.update_tag_autocomplete()
            
            # 가운데 섹션의 파일 목록 태그 정보 업데이트
            if hasattr(self, 'file_selection_and_preview_widget') and self.file_selection_and_preview_widget:
                self.file_selection_and_preview_widget.refresh_file_tags(file_path)
        except Exception as e:
            import traceback
            print(f"[MainWindow] 태그 적용 후 자동 완성 업데이트 중 오류: {e}")
            traceback.print_exc()

    def on_state_changed(self, state):
        """상태 관리자의 상태가 변경될 때 호출됩니다."""
        # 현재는 상태 변경을 로깅만 함 (필요시 UI 업데이트 로직 추가)
        mode = state.get('mode', 'unknown')
        files_count = len(state.get('selected_files', []))
        
        # 일괄 태깅 옵션 위젯의 가시성 제어
        if mode == 'batch':
            self.batch_tagging_options_widget.setVisible(True)
        else:
            self.batch_tagging_options_widget.setVisible(False)

        # 디버깅용 로그 (필요시 제거)
        # print(f"[MainWindow] 상태 변경 - 모드: {mode}, 선택된 파일: {files_count}개")

    def update_all_tags_list(self):
        """모든 태그 목록을 업데이트합니다."""
        try:
            # 통합 패널이 생성되었는지 확인
            if not hasattr(self, 'unified_tagging_panel') or not self.unified_tagging_panel:
                return
                
            # 통합 패널의 빠른 태그 위젯에 태그 목록 설정
            all_tags = self.tag_manager.get_all_tags()
            if hasattr(self.unified_tagging_panel, 'individual_quick_tags'):
                # 자주 사용되는 태그들을 빠른 태그로 설정 (상위 10개)
                quick_tags = all_tags[:10] if len(all_tags) > 10 else all_tags
                self.unified_tagging_panel.individual_quick_tags.set_quick_tags(quick_tags)
                
        except RuntimeError as e:
            # 위젯이 삭제된 경우 무시
            if "wrapped C/C++ object" in str(e):
                return
            else:
                raise
        except Exception as e:
            import traceback
            print(f"[MainWindow] 태그 목록 업데이트 중 오류: {e}")
            traceback.print_exc()

    def update_tag_autocomplete(self):
        """태그 자동 완성 모델을 업데이트합니다."""
        try:
            # 통합 패널이 생성되었는지 확인
            if not hasattr(self, 'unified_tagging_panel') or not self.unified_tagging_panel:
                return
                
            all_tags = self.tag_manager.get_all_tags()
            
            # 개별 태깅 패널의 태그 입력 위젯 자동 완성 업데이트
            if hasattr(self.unified_tagging_panel, 'update_tag_autocomplete'):
                self.unified_tagging_panel.update_tag_autocomplete()
                
        except RuntimeError as e:
            # 위젯이 삭제된 경우 무시
            if "wrapped C/C++ object" in str(e):
                return
            else:
                raise
        except Exception as e:
            import traceback
            print(f"[MainWindow] 자동 완성 업데이트 중 오류: {e}")
            traceback.print_exc()

    def clear_filter(self):
        """필터를 초기화합니다."""
        self.is_filtered = False
        self.clear_filter_action.setEnabled(False)
        self.state_manager.set_filter_mode(False)
        self.statusBar().showMessage("필터가 초기화되었습니다", 2000)

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

    # 레거시 메서드들 (호환성을 위해 유지, 향후 제거 예정)
    def deferred_load_directory_tree(self):
        """레거시 메서드 - 더 이상 사용되지 않음"""
        pass

    def setup_table_header(self):
        """레거시 메서드 - 더 이상 사용되지 않음"""
        pass

    def on_directory_selected(self, index):
        """레거시 메서드 - 더 이상 사용되지 않음"""
        pass

    def update_file_list(self, path, file_list=None):
        """레거시 메서드 - 더 이상 사용되지 않음"""
        pass

    def save_tags_for_selected_file(self):
        """레거시 메서드 - 더 이상 사용되지 않음"""
        pass

    def on_tag_filter_selected(self, item):
        """레거시 메서드 - 더 이상 사용되지 않음"""
        pass

    def on_tags_changed(self, tags):
        """레거시 메서드 - 더 이상 사용되지 않음"""
        pass

    def on_quick_tag_toggled(self, tag, is_added):
        """레거시 메서드 - 더 이상 사용되지 않음"""
        pass

    def show_batch_tagging_panel(self):
        """레거시 메서드 - 일괄 태깅 모드로 전환"""
        self.switch_tagging_mode('batch')
