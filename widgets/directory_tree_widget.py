from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTreeView, QFileSystemModel, QLineEdit, QHBoxLayout, QCheckBox, QLabel
from PyQt5.QtCore import QDir, QSortFilterProxyModel, Qt, pyqtSignal

class DirectoryTreeWidget(QWidget):
    # 시그널 정의
    tag_filter_changed = pyqtSignal(str) # 태그 필터 텍스트가 변경될 때 방출
    global_file_search_requested = pyqtSignal(str) # 전역 파일 검색 요청 시 방출
    filter_options_changed = pyqtSignal(bool, list) # 재귀 여부, 파일 확장자 리스트가 변경될 때 방출 (for file_list)
    directory_context_menu_requested = pyqtSignal(str, object) # 디렉토리 경로와 전역 위치를 전달

    def __init__(self, initial_root_path, parent=None):
        super().__init__(parent)
        
        # 레이아웃 설정
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0) # 여백 최소화
        
        # 전역 파일 검색 입력란
        self.global_file_search_input = QLineEdit()
        self.global_file_search_input.setPlaceholderText("전역 파일 검색...")
        layout.addWidget(self.global_file_search_input)

        # 태그 검색 입력란
        self.tag_search_input = QLineEdit()
        self.tag_search_input.setPlaceholderText("태그 검색...")
        layout.addWidget(self.tag_search_input)

        # 확장자 입력 필드 (새로운 위치)
        extensions_layout = QHBoxLayout()
        extensions_layout.addWidget(QLabel("확장자:"))
        self.extensions_input = QLineEdit()
        self.extensions_input.setPlaceholderText(".jpg, .png (쉼표로 구분)")
        self.extensions_input.textChanged.connect(self._update_tree_view_filter) # Connect to a new update function
        extensions_layout.addWidget(self.extensions_input)
        layout.addLayout(extensions_layout)

        # 파일 표시 옵션 (새로운 위치)
        self.show_files_checkbox = QCheckBox("디렉토리 뷰에 파일 표시")
        self.show_files_checkbox.setChecked(True) # Default to showing files
        self.show_files_checkbox.stateChanged.connect(self._update_tree_view_filter) # Connect to a new update function
        layout.addWidget(self.show_files_checkbox)

        # 하위 폴더 포함 체크박스 (기존 위치 유지)
        self.recursive_checkbox = QCheckBox("하위 폴더 포함")
        self.recursive_checkbox.setChecked(True)
        self.recursive_checkbox.stateChanged.connect(self._emit_filter_options_changed) # This signal is for file_list, keep it.
        layout.addWidget(self.recursive_checkbox)

        # 파일 시스템 모델 생성
        self.model = QFileSystemModel()
        self.model.setRootPath(initial_root_path) # 초기 경로를 외부에서 전달받음
        
        # 프록시 모델 생성 및 설정
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)

        # 트리 뷰 생성 및 모델 설정
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.proxy_model)
        self.tree_view.setRootIndex(self.proxy_model.mapFromSource(self.model.index(initial_root_path)))
        
        # 최소 너비 설정 (예: 150 픽셀)
        self.tree_view.setMinimumWidth(150)

        # 불필요한 컬럼 숨기기 (이름만 표시)
        self.tree_view.hideColumn(1) # Size
        self.tree_view.hideColumn(2) # Type
        self.tree_view.hideColumn(3) # Date Modified
        
        # 컨텍스트 메뉴 활성화
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self._on_tree_view_context_menu_requested)

        # 레이아웃에 트리 뷰 추가
        layout.addWidget(self.tree_view)
        self.setLayout(layout)

        # 시그널 연결
        self.global_file_search_input.textChanged.connect(self.global_file_search_requested.emit)
        self.tag_search_input.textChanged.connect(self.tag_filter_changed.emit)

        # 초기 필터 적용
        self._update_tree_view_filter()

    def set_root_path(self, path):
        """트리 뷰의 루트 경로를 설정합니다."""
        self.model.setRootPath(path)
        self.tree_view.setRootIndex(self.proxy_model.mapFromSource(self.model.index(path)))
        self._update_tree_view_filter() # 루트 경로 변경 시 필터 다시 적용

    def _update_tree_view_filter(self):
        """트리 뷰의 파일 시스템 모델 필터를 업데이트합니다."""
        current_filter = QDir.NoDotAndDotDot | QDir.AllDirs
        if self.show_files_checkbox.isChecked():
            current_filter |= QDir.Files
        self.model.setFilter(current_filter)

        extensions_text = self.extensions_input.text().strip()
        if extensions_text:
            name_filters = [f"*{ext.strip()}" for ext in extensions_text.split(',') if ext.strip()]
            self.model.setNameFilters(name_filters)
            self.model.setNameFilterDisables(False) # Enable name filters
        else:
            self.model.setNameFilterDisables(True) # Disable name filters

    def _emit_filter_options_changed(self):
        recursive = self.recursive_checkbox.isChecked()
        extensions_text = self.extensions_input.text().strip()
        file_extensions = [ext.strip() for ext in extensions_text.split(',') if ext.strip()]
        self.filter_options_changed.emit(recursive, file_extensions)

    def _on_tree_view_context_menu_requested(self, position):
        index = self.tree_view.indexAt(position)
        if index.isValid():
            # 실제 파일 시스템 경로 가져오기
            file_path = self.model.filePath(self.proxy_model.mapToSource(index))
            # DRS에 따라 디렉토리인 경우에만 컨텍스트 메뉴를 요청
            if self.model.isDir(self.proxy_model.mapToSource(index)):
                self.directory_context_menu_requested.emit(file_path, self.tree_view.mapToGlobal(position))