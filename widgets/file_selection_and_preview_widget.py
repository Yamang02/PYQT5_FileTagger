from PyQt5.QtWidgets import QWidget, QHBoxLayout, QTreeView, QTableView, QFileSystemModel, QMessageBox
from PyQt5.QtCore import pyqtSignal, QModelIndex, QTimer, QDir
import os

class FileSelectionAndPreviewWidget(QWidget):
    file_selected = pyqtSignal(str)
    directory_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.tree_view = QTreeView(self)   # 디렉토리 트리
        self.table_view = QTableView(self) # 파일 목록/미리보기
        self.layout.addWidget(self.tree_view)
        self.layout.addWidget(self.table_view)
        self.setLayout(self.layout)

        # 파일 시스템 모델 연결 (QFileSystemModel은 기본적으로 비동기)
        self.dir_model = QFileSystemModel()
        self.dir_model.setRootPath("")
        self.dir_model.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot)
        self.tree_view.setModel(self.dir_model)
        self.tree_view.setRootIndex(self.dir_model.index(os.path.expanduser("~")))
        self.tree_view.clicked.connect(self._on_tree_clicked)

        self.file_model = QFileSystemModel()
        self.file_model.setRootPath("")
        self.file_model.setFilter(QDir.Files | QDir.NoDotAndDotDot)
        self.table_view.setModel(self.file_model)
        self.table_view.setRootIndex(self.file_model.index(os.path.expanduser("~")))
        self.table_view.clicked.connect(self._on_table_clicked)

        # TODO: TagUIStateManager와의 연동(상태 동기화)
        self.state_manager = None

    def set_directory(self, path: str):
        """트리뷰/테이블뷰의 루트 디렉토리 설정, 예외 처리 및 사용자 피드백 포함
        대용량 디렉토리의 경우 QTimer.singleShot을 활용한 지연 로딩으로 UI 블로킹 방지"""
        if not os.path.exists(path) or not os.path.isdir(path):
            QMessageBox.critical(self, "경로 오류", f"지정한 경로가 존재하지 않거나 디렉토리가 아닙니다: {path}")
            return
        def update_views():
            try:
                self.tree_view.setRootIndex(self.dir_model.index(path))
                self.table_view.setRootIndex(self.file_model.index(path))
                self.directory_selected.emit(path)
                if self.state_manager:
                    self.state_manager.set_selected_directory(path)
            except Exception as e:
                QMessageBox.critical(self, "디렉토리 접근 오류", str(e))
        # QTimer.singleShot(0, ...)을 사용해 이벤트 루프에 등록하여 UI 블로킹 최소화
        QTimer.singleShot(0, update_views)

    def get_selected_files(self) -> list:
        """현재 선택된 파일 목록 반환"""
        selection = self.table_view.selectionModel().selectedRows()
        files = []
        for index in selection:
            file_path = self.file_model.filePath(index)
            files.append(file_path)
        return files

    def _on_tree_clicked(self, index: QModelIndex):
        path = self.dir_model.filePath(index)
        self.set_directory(path)

    def _on_table_clicked(self, index: QModelIndex):
        file_path = self.file_model.filePath(index)
        self.file_selected.emit(file_path)
        if self.state_manager:
            self.state_manager.set_selected_files(self.get_selected_files())

    def set_state_manager(self, manager):
        self.state_manager = manager
        # TODO: 상태 매니저의 state_changed 시그널과 연동하여 UI 업데이트

    # 대용량 디렉토리 대응(비동기/지연 로딩, QThread 구조 확장 가능성)
    # QFileSystemModel은 기본적으로 비동기 로딩을 지원하지만, 추가로 QThread를 활용한 커스텀 파일 목록 로딩,
    # 페이징/캐싱 등은 실제 대용량 환경에서 필요시 확장 가능

    # 대용량 디렉토리 대응(비동기/지연 로딩) 구조 설계 주석
    # TODO: QFileSystemModel의 비동기 특성을 활용하되, 대규모 파일 시스템에서 UI 응답성 저하가 발생할 경우
    #       QThread, QTimer, 또는 별도의 파일 목록 캐싱/페이징 기법 적용을 고려할 것 