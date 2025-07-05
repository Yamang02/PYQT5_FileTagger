from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QTableView, 
    QMessageBox, QHeaderView, QVBoxLayout, QLabel
)
from PyQt5.QtCore import (
    pyqtSignal, QModelIndex, QTimer, QDir, QAbstractTableModel, 
    Qt, QVariant
)
from PyQt5.QtGui import QFont
import os


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


class FileSelectionAndPreviewWidget(QWidget):
    """
    파일 목록 테이블뷰 및 미리보기 위젯
    DRS 요구사항: 파일 목록 테이블뷰와 파일 미리보기 기능만 담당
    """
    
    file_selected = pyqtSignal(str, list)  # 파일 경로, 태그 목록
    directory_selected = pyqtSignal(str)

    def __init__(self, state_manager, tag_manager, parent=None):
        super().__init__(parent)
        self.state_manager = state_manager
        self.tag_manager = tag_manager
        
        self.setup_ui()
        self.setup_models()
        self.connect_signals()

    def setup_ui(self):
        """UI 구성 요소 설정"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        # 제목
        title_label = QLabel("📋 파일 목록 및 미리보기")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        title_label.setStyleSheet("color: #34495e; padding: 4px;")
        
        # 파일 테이블 뷰
        self.table_view = QTableView()
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        self.table_view.setSelectionMode(QTableView.SingleSelection)
        self.table_view.setStyleSheet("""
            QTableView {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
                gridline-color: #ecf0f1;
                alternate-background-color: #f8f9fa;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 6px;
                border: none;
                font-weight: bold;
            }
            QTableView::item:selected {
                background-color: #3498db;
                color: white;
            }
        """)
        
        main_layout.addWidget(title_label)
        main_layout.addWidget(self.table_view)

    def setup_models(self):
        """모델 설정"""
        # 파일 테이블 모델 (커스텀 모델 사용)
        self.file_model = FileTableModel(self.tag_manager)
        self.table_view.setModel(self.file_model)
        
        # 테이블 헤더 설정
        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 파일명
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # 경로
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # 태그
        
        # 초기 디렉토리 설정 (MainWindow에서 설정될 예정)
        # self.set_directory(os.path.expanduser("~"))

    def connect_signals(self):
        """시그널 연결"""
        self.table_view.clicked.connect(self._on_table_clicked)

    def set_directory(self, path: str):
        if not os.path.exists(path) or not os.path.isdir(path):
            print(f"[FSPW] set_directory - 경로 오류: {path}")
            QMessageBox.critical(self, "경로 오류", f"지정한 경로가 존재하지 않거나 디렉토리가 아닙니다: {path}")
            return
            
        def update_views():
            try:
                if not self.file_model:
                    return
                self.file_model.set_directory(path)
                self.directory_selected.emit(path)
                if self.state_manager:
                    self.state_manager.set_selected_directory(path)
            except RuntimeError as e:
                if "wrapped C/C++ object" in str(e):
                    return
                else:
                    raise
            except Exception as e:
                try:
                    QMessageBox.critical(self, "디렉토리 접근 오류", str(e))
                except RuntimeError:
                    pass
                
        # UI 블로킹 방지를 위한 지연 실행
        QTimer.singleShot(0, update_views)

    def get_selected_files(self) -> list:
        """현재 선택된 파일 목록 반환"""
        selection = self.table_view.selectionModel().selectedRows()
        files = []
        for index in selection:
            file_path = self.file_model.get_file_path(index)
            if file_path:
                files.append(file_path)
        return files

    def _on_table_clicked(self, index: QModelIndex):
        """테이블 뷰 클릭 시 파일 선택"""
        file_path = self.file_model.get_file_path(index)
        if file_path:
            # 파일의 태그 가져오기
            tags = []
            try:
                tags = self.tag_manager.get_tags_for_file(file_path)
            except Exception as e:
                print(f"[FileSelectionAndPreviewWidget] 태그 조회 오류: {e}")
                
            self.file_selected.emit(file_path, tags)
            
            # 상태 관리자 업데이트
            if self.state_manager:
                self.state_manager.set_selected_files([file_path])

    def set_state_manager(self, manager):
        """상태 관리자 설정"""
        self.state_manager = manager
        
        # 상태 변경 시그널 연결
        if hasattr(manager, 'state_changed'):
            manager.state_changed.connect(self._on_state_changed)
            
    def _on_state_changed(self, state: dict):
        """상태 관리자 상태 변경 시 UI 업데이트"""
        # 선택된 디렉토리 업데이트
        directory = state.get('selected_directory', '')
        if directory and directory != self.file_model.current_directory:
            self.set_directory(directory)
            
    def refresh_file_tags(self, file_path):
        """특정 파일의 태그 정보 새로고침"""
        self.file_model.refresh_file_tags(file_path)
        
    def get_current_directory(self):
        """현재 디렉토리 반환"""
        return self.file_model.current_directory

    def update_file_details(self, file_path: str):
        """선택된 파일의 상세 정보 및 미리보기를 업데이트합니다."""
        if not file_path or not os.path.exists(file_path):
            self.file_details_browser.clear()
            self.image_preview.clear()
            self.image_preview.setText("미리보기를 사용할 수 없습니다.")
            return

        # 파일 상세 정보
        file_info = f"<b>파일 이름:</b> {os.path.basename(file_path)}<br>"
        file_info += f"<b>경로:</b> {file_path}<br>"
        try:
            file_size = os.path.getsize(file_path)
            file_info += f"<b>크기:</b> {file_size / (1024*1024):.2f} MB<br>"
            mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
            file_info += f"<b>수정일:</b> {mod_time.strftime('%Y-%m-%d %H:%M:%S')}<br>"
        except Exception as e:
            file_info += f"<b>정보 로드 오류:</b> {e}<br>"
        self.file_details_browser.setHtml(file_info)

        # 이미지 미리보기 (간단한 이미지 파일만 지원)
        self.image_preview.clear()
        self.image_preview.setText("미리보기를 사용할 수 없습니다.")
        
        # 이미지 파일 확장자 목록
        image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']
        file_ext = os.path.splitext(file_path)[1].lower()

        if file_ext in image_extensions:
            try:
                pixmap = QPixmap(file_path)
                if not pixmap.isNull():
                    # QLabel 크기에 맞춰 이미지 스케일링
                    scaled_pixmap = pixmap.scaled(
                        self.image_preview.size(),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                    self.image_preview.setPixmap(scaled_pixmap)
                    self.image_preview.setText("") # 이미지 로드 성공 시 텍스트 제거
                else:
                    self.image_preview.setText("이미지 로드 실패")
            except Exception as e:
                self.image_preview.setText(f"이미지 미리보기 오류: {e}")
        else:
            self.image_preview.setText("이미지 파일이 아닙니다.")

    # 대용량 디렉토리 대응(비동기/지연 로딩, QThread 구조 확장 가능성)
    # QFileSystemModel은 기본적으로 비동기 로딩을 지원하지만, 추가로 QThread를 활용한 커스텀 파일 목록 로딩,
    # 페이징/캐싱 등은 실제 대용량 환경에서 필요시 확장 가능

    # 대용량 디렉토리 대응(비동기/지연 로딩) 구조 설계 주석
    # TODO: QFileSystemModel의 비동기 특성을 활용하되, 대규모 파일 시스템에서 UI 응답성 저하가 발생할 경우
    #       QThread, QTimer, 또는 별도의 파일 목록 캐싱/페이징 기법 적용을 고려할 것

    # 대용량 디렉토리 대응(비동기/지연 로딩, QThread 구조 확장 가능성)
    # QFileSystemModel은 기본적으로 비동기 로딩을 지원하지만, 추가로 QThread를 활용한 커스텀 파일 목록 로딩,
    # 페이징/캐싱 등은 실제 대용량 환경에서 필요시 확장 가능

    # 대용량 디렉토리 대응(비동기/지연 로딩) 구조 설계 주석
    # TODO: QFileSystemModel의 비동기 특성을 활용하되, 대규모 파일 시스템에서 UI 응답성 저하가 발생할 경우
    #       QThread, QTimer, 또는 별도의 파일 목록 캐싱/페이징 기법 적용을 고려할 것