from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTreeView, QFileSystemModel, QLineEdit, QHBoxLayout, QCheckBox, QLabel
from PyQt5.QtCore import QDir, QSortFilterProxyModel, Qt, pyqtSignal

class DirectoryTreeWidget(QWidget):
    # 시그널 정의
    tag_filter_changed = pyqtSignal(str) # 태그 필터 텍스트가 변경될 때 방출
    global_file_search_requested = pyqtSignal(str) # 전역 파일 검색 요청 시 방출
    filter_options_changed = pyqtSignal(bool, list) # 재귀 여부, 파일 확장자 리스트가 변경될 때 방출

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

        # 파일 목록 필터링 옵션
        filter_options_layout = QHBoxLayout()
        self.recursive_checkbox = QCheckBox("하위 폴더 포함")
        self.recursive_checkbox.setChecked(True) # 기본값 True
        self.recursive_checkbox.stateChanged.connect(self._emit_filter_options_changed)
        filter_options_layout.addWidget(self.recursive_checkbox)

        filter_options_layout.addWidget(QLabel("확장자:"))
        self.extensions_input = QLineEdit()
        self.extensions_input.setPlaceholderText(".jpg, .png (쉼표로 구분)")
        self.extensions_input.textChanged.connect(self._emit_filter_options_changed)
        filter_options_layout.addWidget(self.extensions_input)
        layout.addLayout(filter_options_layout)

        # 파일 시스템 모델 생성
        self.model = QFileSystemModel()
        self.model.setRootPath(initial_root_path) # 초기 경로를 외부에서 전달받음
        # 디렉토리만 표시되도록 필터 변경 (기존 유지)
        self.model.setFilter(QDir.NoDotAndDotDot | QDir.AllDirs) 
        
        # 프록시 모델 생성 및 설정 (필터링 기능은 이제 사용하지 않음)
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        # self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive) # 필터링 기능 제거로 불필요
        # self.proxy_model.setFilterKeyColumn(0) # 필터링 기능 제거로 불필요

        # 트리 뷰 생성 및 모델 설정
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.proxy_model) # 프록시 모델 사용 (필터링 없이 원본 모델 그대로 보여줌)
        self.tree_view.setRootIndex(self.proxy_model.mapFromSource(self.model.index(initial_root_path)))
        
        # 최소 너비 설정 (예: 150 픽셀)
        self.tree_view.setMinimumWidth(150)

        # 불필요한 컬럼 숨기기 (이름만 표시)
        self.tree_view.hideColumn(1) # Size
        self.tree_view.hideColumn(2) # Type
        self.tree_view.hideColumn(3) # Date Modified
        
        # 레이아웃에 트리 뷰 추가
        layout.addWidget(self.tree_view)
        self.setLayout(layout)

        # 시그널 연결 (디렉토리 필터링 시그널 제거)
        self.global_file_search_input.textChanged.connect(self.global_file_search_requested.emit)
        self.tag_search_input.textChanged.connect(self.tag_filter_changed.emit)

    def set_root_path(self, path):
        """트리 뷰의 루트 경로를 설정합니다."""
        self.model.setRootPath(path)
        self.tree_view.setRootIndex(self.proxy_model.mapFromSource(self.model.index(path)))

    def _emit_filter_options_changed(self):
        recursive = self.recursive_checkbox.isChecked()
        extensions_text = self.extensions_input.text().strip()
        file_extensions = [ext.strip() for ext in extensions_text.split(',') if ext.strip()]
        self.filter_options_changed.emit(recursive, file_extensions)

    # _on_tree_search_text_changed 메서드 제거
