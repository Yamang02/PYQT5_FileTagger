from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableView, QHeaderView, QAbstractItemView
from PyQt5.QtCore import QDir, QAbstractTableModel, QModelIndex, Qt, QVariant
import os
from core.path_utils import normalize_path # path_utils 모듈 임포트

# 백업에서 가져온 FileTableModel 정의
class FileTableModel(QAbstractTableModel):
    """
    파일 정보와 태그 정보를 함께 표시하는 커스텀 테이블 모델
    DRS 요구사항: 파일명, 상대 경로, 현재 적용된 태그를 표시
    """
    
    def __init__(self, tag_manager, parent=None):
        super().__init__(parent)
        self.tag_manager = tag_manager
        self.all_files = [] # 필터링되지 않은 모든 파일 목록 (디렉토리 모드)
        self.filtered_files = [] # 필터링된 파일 목록 (디렉토리 모드)
        self.search_results = [] # 검색 결과 파일 목록 (검색 모드)
        self.current_directory = ""
        self._tag_filter = "" # 현재 적용된 태그 필터
        self._is_search_mode = False # 검색 모드 여부
        
    def set_directory(self, directory_path, recursive=False, file_extensions=None):
        self.beginResetModel()
        self.current_directory = directory_path
        self.all_files = []
        self.filtered_files = []
        self.search_results = []
        self._tag_filter = "" # 디렉토리 변경 시 태그 필터 초기화
        self._is_search_mode = False # 디렉토리 선택 시 검색 모드 해제
        
        # TagManager의 헬퍼 메서드를 사용하여 파일 목록을 가져옵니다.
        self.all_files = self.tag_manager._get_files_in_directory(directory_path, recursive, file_extensions)
        self.all_files.sort(key=lambda x: os.path.basename(x).lower())
            
        self._apply_filter()
        self.endResetModel()

    def set_tag_filter(self, tag_text):
        self.beginResetModel()
        self._tag_filter = tag_text.strip()
        self._apply_filter()
        self.endResetModel()

    def set_search_results(self, file_paths):
        self.beginResetModel()
        self.search_results = sorted(file_paths, key=lambda x: os.path.basename(x).lower())
        self._is_search_mode = True
        self.endResetModel()

    def _apply_filter(self):
        if not self._tag_filter:
            self.filtered_files = list(self.all_files)
        else:
            self.filtered_files = []
            for file_path in self.all_files:
                tags = self.tag_manager.get_tags_for_file(file_path)
                if self._tag_filter.lower() in [tag.lower() for tag in tags]:
                    self.filtered_files.append(file_path)
        
    def rowCount(self, parent=QModelIndex()):
        if self._is_search_mode:
            return len(self.search_results)
        else:
            return len(self.filtered_files)
        
    def columnCount(self, parent=QModelIndex()):
        return 3  # 파일명, 상대 경로, 태그
        
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
            
        if self._is_search_mode:
            if index.row() >= len(self.search_results):
                return QVariant()
            file_path = self.search_results[index.row()]
        else:
            if index.row() >= len(self.filtered_files):
                return QVariant()
            file_path = self.filtered_files[index.row()]
        
        if role == Qt.DisplayRole:
            if index.column() == 0:  # 파일명
                return os.path.basename(file_path)
            elif index.column() == 1:  # 상대 경로
                # 검색 모드에서는 전체 경로 표시
                if self._is_search_mode:
                    return file_path
                # 디렉토리 모드에서는 상대 경로 표시
                elif self.current_directory:
                    try:
                        return os.path.relpath(file_path, self.current_directory)
                    except ValueError:
                        return file_path
                return file_path
            elif index.column() == 2:  # 태그
                try:
                    # 태그를 요청하기 전에 파일 경로를 정규화
                    normalized_file_path = normalize_path(file_path)
                    tags = self.tag_manager.get_tags_for_file(normalized_file_path)
                    
                    return ", ".join(tags) if tags else ""
                except Exception:
                    return ""
                    
        elif role == Qt.UserRole:  # 전체 파일 경로 반환
            return file_path
            
        return QVariant()
        
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            headers = ["파일명", "경로", "태그"]
            if section < len(headers):
                return headers[section]
        return QVariant()
        
    def get_file_path(self, index):
        """인덱스에 해당하는 파일 경로 반환"""
        if self._is_search_mode:
            if index.isValid() and index.row() < len(self.search_results):
                return self.search_results[index.row()]
        else:
            if index.isValid() and index.row() < len(self.filtered_files):
                return self.filtered_files[index.row()]
        return ""
        
    def refresh_file_tags(self, file_path):
        """특정 파일의 태그 정보를 새로고침"""
        # 태그 정보가 변경되었을 수 있으므로 필터를 다시 적용
        self._apply_filter()
        # 필터링된 파일 목록에서 해당 파일의 새 인덱스를 찾아 업데이트 시그널 발생
        if file_path in self.filtered_files:
            new_file_index = self.filtered_files.index(file_path)
            top_left = self.index(new_file_index, 2)
            bottom_right = self.index(new_file_index, 2)
            self.dataChanged.emit(top_left, bottom_right)
        elif file_path in self.search_results:
            # 검색 결과에 있는 경우에도 업데이트
            new_file_index = self.search_results.index(file_path)
            top_left = self.index(new_file_index, 2)
            bottom_right = self.index(new_file_index, 2)
            self.dataChanged.emit(top_left, bottom_right)
        else:
            # 필터링으로 인해 파일이 사라지거나 나타날 수 있으므로 전체 리셋
            self.layoutChanged.emit()


class FileListWidget(QWidget):
    def __init__(self, tag_manager, parent=None):
        super().__init__(parent)
        
        # 레이아웃 설정
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 파일 테이블 모델 생성
        self.model = FileTableModel(tag_manager) # TagManager 인스턴스 전달
        
        # 테이블 뷰 생성 및 모델 설정
        self.list_view = QTableView() # QListView 대신 QTableView 사용
        self.list_view.setModel(self.model)
        
        # 다중 선택 허용
        self.list_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list_view.setSelectionBehavior(QAbstractItemView.SelectRows)

        # 테이블 헤더 설정
        header = self.list_view.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 파일명
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # 경로
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # 태그
        
        layout.addWidget(self.list_view)
        self.setLayout(layout)

        # 디버깅용 시그널 연결
        self.list_view.selectionModel().selectionChanged.connect(lambda selected, deselected: print(f"DEBUG: selectionChanged signal emitted. Selected: {len(selected.indexes())}, Deselected: {len(deselected.indexes())}"))

    def set_path(self, path, recursive=False, file_extensions=None):
        """지정된 경로의 파일 목록을 표시합니다."""
        self.model.set_directory(path, recursive, file_extensions)

    def set_tag_filter(self, tag_text):
        """파일 목록을 태그로 필터링합니다."""
        self.model.set_tag_filter(tag_text)

    def set_search_results(self, file_paths):
        """전역 검색 결과를 파일 목록에 표시합니다."""
        self.model.set_search_results(file_paths)

    def get_selected_file_paths(self):
        """현재 선택된 모든 파일의 경로 목록을 반환합니다."""
        selected_paths = []
        for index in self.list_view.selectionModel().selectedRows():
            file_path = self.model.get_file_path(index)
            if file_path:
                selected_paths.append(file_path)
        return selected_paths
