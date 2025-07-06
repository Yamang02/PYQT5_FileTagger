from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTreeView, QFileSystemModel
from PyQt5.QtCore import QDir

class DirectoryTreeWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 레이아웃 설정
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0) # 여백 최소화
        
        # 파일 시스템 모델 생성
        self.model = QFileSystemModel()
        self.model.setRootPath(QDir.homePath()) # 시작 경로를 홈 디렉토리로 설정
        self.model.setFilter(QDir.NoDotAndDotDot | QDir.AllDirs) # 디렉토리만 표시
        
        # 트리 뷰 생성 및 모델 설정
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.model)
        self.tree_view.setRootIndex(self.model.index(QDir.homePath()))
        
        # 최소 너비 설정 (예: 150 픽셀)
        self.tree_view.setMinimumWidth(150)

        # 불필요한 컬럼 숨기기 (이름만 표시)
        self.tree_view.hideColumn(1) # Size
        self.tree_view.hideColumn(2) # Type
        self.tree_view.hideColumn(3) # Date Modified
        
        # 레이아웃에 트리 뷰 추가
        layout.addWidget(self.tree_view)
        self.setLayout(layout)
