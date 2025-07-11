from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTreeView, QFileSystemModel, QLineEdit, QHBoxLayout, QCheckBox, QLabel, QSpacerItem, QSizePolicy
from PyQt5.QtCore import QDir, QSortFilterProxyModel, Qt, pyqtSignal

class DirectoryTreeWidget(QWidget):
    # 시그널 정의
    filter_options_changed = pyqtSignal(bool, list) # 재귀 여부, 파일 확장자 리스트가 변경될 때 방출 (for file_list)
    directory_context_menu_requested = pyqtSignal(str, object) # 디렉토리 경로와 전역 위치를 전달

    def __init__(self, initial_root_path, parent=None):
        super().__init__(parent)
        
        # 좌측 여백을 위한 HBoxLayout 래핑
        outer_layout = QHBoxLayout(self)
        outer_layout.setContentsMargins(16, 0, 0, 0)  # 왼쪽 여백 16px
        inner_layout = QVBoxLayout()
        inner_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.setSpacing(0)

        # 파일 표시 옵션 (기존 위치 유지)
        self.show_files_checkbox = QCheckBox("디렉토리 뷰에 파일 표시")
        self.show_files_checkbox.setChecked(True) # Default to showing files
        self.show_files_checkbox.stateChanged.connect(self._update_tree_view_filter) # Connect to a new update function
        inner_layout.addWidget(self.show_files_checkbox)

        # 하위 폴더 포함 체크박스 (기존 위치 유지)
        self.recursive_checkbox = QCheckBox("하위 폴더 포함")
        self.recursive_checkbox.setChecked(True)
        self.recursive_checkbox.stateChanged.connect(self._emit_filter_options_changed) # This signal is for file_list, keep it.
        inner_layout.addWidget(self.recursive_checkbox)

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
        inner_layout.addWidget(self.tree_view)
        self.setLayout(outer_layout)
        outer_layout.addLayout(inner_layout)

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

    def _emit_filter_options_changed(self):
        recursive = self.recursive_checkbox.isChecked()
        # extensions_input이 제거되었으므로 빈 리스트로 설정
        file_extensions = []
        self.filter_options_changed.emit(recursive, file_extensions)

    def _on_tree_view_context_menu_requested(self, position):
        index = self.tree_view.indexAt(position)
        if index.isValid():
            # 실제 파일 시스템 경로 가져오기
            file_path = self.model.filePath(self.proxy_model.mapToSource(index))
            # DRS에 따라 디렉토리인 경우에만 컨텍스트 메뉴를 요청
            if self.model.isDir(self.proxy_model.mapToSource(index)):
                self.directory_context_menu_requested.emit(file_path, self.tree_view.mapToGlobal(position))