from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableView, QHeaderView
from PyQt5.QtCore import QDir, QAbstractTableModel, QModelIndex, Qt, QVariant
import os

# 백업에서 가져온 FileTableModel 정의
class FileTableModel(QAbstractTableModel):
    """
    파일 정보와 태그 정보를 함께 표시하는 커스텀 테이블 모델
    DRS 요구사항: 파일명, 상대 경로, 현재 적용된 태그를 표시
    """
    
    def __init__(self, tag_manager, parent=None):
        super().__init__(parent)
        self.tag_manager = tag_manager
        self.files = []
        self.current_directory = ""
        
    def set_directory(self, directory_path):
        self.beginResetModel()
        self.current_directory = directory_path
        self.files = []
        
        if os.path.exists(directory_path) and os.path.isdir(directory_path):
            for item in os.listdir(directory_path):
                item_path = os.path.join(directory_path, item)
                if os.path.isfile(item_path):
                    self.files.append(item_path)
                    
            self.files.sort(key=lambda x: os.path.basename(x).lower())
            
        self.endResetModel()
        
    def rowCount(self, parent=QModelIndex()):
        return len(self.files)
        
    def columnCount(self, parent=QModelIndex()):
        return 3  # 파일명, 상대 경로, 태그
        
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self.files):
            return QVariant()
            
        file_path = self.files[index.row()]
        
        if role == Qt.DisplayRole:
            if index.column() == 0:  # 파일명
                return os.path.basename(file_path)
            elif index.column() == 1:  # 상대 경로
                if self.current_directory:
                    try:
                        return os.path.relpath(file_path, self.current_directory)
                    except ValueError:
                        return file_path
                return file_path
            elif index.column() == 2:  # 태그
                try:
                    tags = self.tag_manager.get_tags_for_file(file_path)
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
        if index.isValid() and index.row() < len(self.files):
            return self.files[index.row()]
        return ""
        
    def refresh_file_tags(self, file_path):
        """특정 파일의 태그 정보를 새로고침"""
        try:
            file_index = self.files.index(file_path)
            # 태그 열만 업데이트
            top_left = self.index(file_index, 2)
            bottom_right = self.index(file_index, 2)
            self.dataChanged.emit(top_left, bottom_right)
        except ValueError:
            # 파일이 목록에 없는 경우 무시
            pass


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
        
        # 테이블 헤더 설정
        header = self.list_view.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 파일명
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # 경로
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # 태그
        
        layout.addWidget(self.list_view)
        self.setLayout(layout)

    def set_path(self, path):
        """지정된 경로의 파일 목록을 표시합니다."""
        self.model.set_directory(path)