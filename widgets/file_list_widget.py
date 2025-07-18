from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableView, QHeaderView, QAbstractItemView
from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt, QVariant, pyqtSignal
import os
from core.path_utils import normalize_path
from viewmodels.file_list_viewmodel import FileListViewModel # FileListViewModel 임포트

# 백업에서 가져온 FileTableModel 정의
class FileTableModel(QAbstractTableModel):
    """
    파일 정보와 태그 정보를 함께 표시하는 커스텀 테이블 모델
    DRS 요구사항: 파일명, 상대 경로, 현재 적용된 태그를 표시
    """
    
    def __init__(self, file_list_viewmodel: FileListViewModel, parent=None):
        super().__init__(parent)
        self.viewmodel = file_list_viewmodel
        
    def set_directory(self, directory_path, recursive=False, file_extensions=None):
        self.beginResetModel()
        self.viewmodel.set_directory(directory_path, recursive, file_extensions)
        self.endResetModel()

    def set_tag_filter(self, tag_text):
        self.beginResetModel()
        self.viewmodel.set_tag_filter(tag_text)
        self.endResetModel()

    def set_search_results(self, file_paths):
        self.beginResetModel()
        self.viewmodel.set_search_results(file_paths)
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return len(self.viewmodel.get_current_display_files())
        
    def columnCount(self, parent=QModelIndex()):
        return 3  # 파일명, 태그, 경로
        
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
            
        current_files = self.viewmodel.get_current_display_files()
        if index.row() >= len(current_files):
            return QVariant()
        
        file_path = current_files[index.row()]
        
        if role == Qt.DisplayRole:
            if index.column() == 0:  # 파일명
                return os.path.basename(file_path)
            elif index.column() == 1:  # 태그
                try:
                    tags = self.viewmodel.get_tags_for_file(file_path)
                    return ", ".join(tags) if tags else ""
                except Exception:
                    return ""
            elif index.column() == 2:  # 경로
                if self.viewmodel.is_search_mode():
                    return file_path
                elif self.viewmodel.get_current_directory():
                    try:
                        return os.path.relpath(file_path, self.viewmodel.get_current_directory())
                    except ValueError:
                        return file_path
                return file_path
                    
        elif role == Qt.UserRole:  # 전체 파일 경로 반환
            return file_path
            
        return QVariant()
        
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            headers = ["파일명", "태그", "경로"]
            if section < len(headers):
                return headers[section]
        return QVariant()
        
    def get_file_path(self, index):
        """인덱스에 해당하는 파일 경로 반환"""
        return self.viewmodel.get_file_path_at_index(index.row())
        
    def refresh_tags_for_current_files(self):
        """현재 표시된 모든 파일의 태그 정보를 새로고침합니다.
        파일 목록 자체는 변경되지 않고, 태그 컬럼만 업데이트됩니다.
        """
        current_display_files = self.viewmodel.get_current_display_files()
        
        if not current_display_files:
            return

        # 태그 컬럼 (인덱스 1)에 대해서만 dataChanged 시그널 발생
        top_left = self.index(0, 1)
        bottom_right = self.index(len(current_display_files) - 1, 1)
        self.dataChanged.emit(top_left, bottom_right)


class FileListWidget(QWidget):
    file_selection_changed = pyqtSignal(list)

    def __init__(self, file_list_viewmodel: FileListViewModel, parent=None):
        super().__init__(parent)
        self.viewmodel = file_list_viewmodel
        self.user_has_resized = False  # 사용자가 수동으로 조정했는지 추적
        
        # 레이아웃 설정
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 파일 테이블 모델 생성
        self.model = FileTableModel(self.viewmodel) # FileListViewModel 인스턴스 전달
        
        # 테이블 뷰 생성 및 모델 설정
        self.list_view = QTableView() # QListView 대신 QTableView 사용
        self.list_view.setModel(self.model)
        
        # 다중 선택 허용
        self.list_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list_view.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.list_view.selectionModel().selectionChanged.connect(self._on_selection_changed)

        # 테이블 헤더 설정 - 사용자 조정 가능하도록 Interactive 모드 사용
        header = self.list_view.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Interactive)  # 파일명 - 사용자 조정 가능
        header.setSectionResizeMode(1, QHeaderView.Interactive)  # 태그 - 사용자 조정 가능
        header.setSectionResizeMode(2, QHeaderView.Interactive)  # 경로 - 사용자 조정 가능
        
        # 최소 컬럼 너비 설정
        header.setMinimumSectionSize(80)
        
        # 헤더 섹션 크기 변경 시그널 연결
        header.sectionResized.connect(self._on_section_resized)
        
        layout.addWidget(self.list_view)
        self.setLayout(layout)

        # 위젯이 표시된 후 컬럼 크기 설정
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(100, self._setup_column_sizes)

        self.connect_viewmodel_signals()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 창 크기 변경 시 컬럼 크기를 자동으로 조정합니다.
        if not self.user_has_resized:
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(50, self._setup_column_sizes)

    def _on_section_resized(self, logical_index, old_size, new_size):
        """사용자가 헤더 섹션을 수동으로 조정했을 때 호출됩니다."""
        self.user_has_resized = True

    def _setup_column_sizes(self):
        """컬럼 크기를 비율에 맞게 설정합니다."""
        if self.user_has_resized:
            return  # 사용자가 수동으로 조정했다면 자동 조정하지 않음
            
        header = self.list_view.horizontalHeader()
        total_width = self.list_view.width()
        
        if total_width > 0:
            # 스크롤바 너비를 고려하여 실제 사용 가능한 너비 계산
            scrollbar_width = 20  # 스크롤바 너비
            available_width = total_width - scrollbar_width
            
            # 최소 너비 보장
            min_width = 80
            file_name_width = max(int(available_width * 0.4), min_width)  # 40%
            tag_width = max(int(available_width * 0.4), min_width)  # 40%
            path_width = max(int(available_width * 0.2), min_width)  # 20%
            # 컬럼 크기 설정
            header.resizeSection(0, file_name_width)
            header.resizeSection(1, tag_width)
            header.resizeSection(2, path_width)

    def reset_column_sizes(self):
        """컬럼 크기를 기본 비율로 리셋하고 자동 조정을 다시 활성화합니다."""
        self.user_has_resized = False
        self._setup_column_sizes()

    def connect_viewmodel_signals(self):
        self.viewmodel.files_updated.connect(self.on_viewmodel_files_updated)

    def on_viewmodel_files_updated(self, file_paths: list):
        # ViewModel에서 파일 목록이 업데이트되었음을 알리면 모델을 리셋하여 뷰를 갱신
        self.model.beginResetModel()
        self.model.endResetModel()

    def set_path(self, path, recursive=False, file_extensions=None):
        """지정된 경로의 파일 목록을 표시합니다."""
        self.viewmodel.set_directory(path, recursive, file_extensions)

    def set_tag_filter(self, tag_text):
        """파일 목록을 태그로 필터링합니다."""
        self.viewmodel.set_tag_filter(tag_text)

    def set_search_results(self, file_paths):
        """전역 검색 결과를 파일 목록에 표시합니다."""
        self.viewmodel.set_search_results(file_paths)

    def get_selected_file_paths(self):
        """현재 선택된 모든 파일의 경로 목록을 반환합니다."""
        selected_paths = []
        for index in self.list_view.selectionModel().selectedRows():
            file_path = self.model.get_file_path(index)
            if file_path:
                selected_paths.append(file_path)
        return selected_paths

    def refresh_tags_for_current_files(self):
        """모델의 태그 정보를 새로고침하도록 요청합니다."""
        self.model.refresh_tags_for_current_files()

    def index_from_path(self, file_path):
        """주어진 파일 경로에 해당하는 QModelIndex를 반환합니다."""
        current_files = self.viewmodel.get_current_display_files()
        try:
            row = current_files.index(file_path)
            return self.model.index(row, 0) # 첫 번째 컬럼의 인덱스 반환
        except ValueError:
            return QModelIndex() # 파일을 찾지 못하면 유효하지 않은 인덱스 반환

    def _on_selection_changed(self, selected, deselected):
        selected_paths = self.get_selected_file_paths()
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[FILE_LIST] 파일 선택 변경: {len(selected_paths)}개 파일")
        if selected_paths:
            logger.info(f"[FILE_LIST] 첫 번째 선택 파일: {selected_paths[0]}")
        self.file_selection_changed.emit(selected_paths)

