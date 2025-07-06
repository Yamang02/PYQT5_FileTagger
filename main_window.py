import sys
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.uic import loadUi

# 위젯 임포트
from widgets.directory_tree_widget import DirectoryTreeWidget
from widgets.file_list_widget import FileListWidget
from widgets.file_detail_widget import FileDetailWidget
from widgets.tag_control_widget import TagControlWidget

# 코어 로직 임포트
from core.tag_manager import TagManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        loadUi('ui/main_window.ui', self)

        # --- 코어 로직 초기화 ---
        self.tag_manager = TagManager()

        # --- 위젯 인스턴스 생성 ---
        self.directory_tree = DirectoryTreeWidget() # setMinimumWidth는 여기서 설정
        self.file_list = FileListWidget(self.tag_manager)
        self.file_detail = FileDetailWidget(self.tag_manager)
        self.tag_control = TagControlWidget(self.tag_manager)

        # --- 3열 레이아웃 구성 (QSplitter 사용) ---
        # .ui 파일에서 로드된 mainSplitter에 위젯들을 추가합니다.
        self.mainSplitter.insertWidget(0, self.directory_tree)
        self.mainSplitter.insertWidget(1, self.splitter) # 기존 수직 splitter를 2번째 열에 삽입
        self.mainSplitter.insertWidget(2, self.tag_control)

        # .ui 파일의 placeholder 위젯 삭제 (mainSplitter에 추가된 후)
        self.directoryTreeWidget.deleteLater()
        self.tagControlWidget.deleteLater()

        # 2열: 파일 상세 정보(상)와 파일 목록(하)을 담는 Splitter
        self.splitter.insertWidget(0, self.file_detail)
        self.splitter.insertWidget(1, self.file_list)
        self.fileDetailWidget.deleteLater()
        self.fileListWidget.deleteLater()

        # 초기 크기 설정 (픽셀 단위)
        # 1열: 150px, 2열: 800px (나머지), 3열: 150px
        self.mainSplitter.setSizes([150, self.width() - 300, 150])
        self.splitter.setSizes([self.height() // 2, self.height() // 2])

        # --- 연결 설정 ---
        self.setup_connections()
        self.statusbar.showMessage("준비 완료")

        self.show()

    def setup_connections(self):
        """위젯 및 메뉴 액션의 시그널-슬롯을 연결합니다."""
        # 메뉴 액션
        self.actionExit.triggered.connect(self.close)
        self.actionBatchTagging.triggered.connect(self.open_batch_tagging_dialog)

        # 위젯 간 연결
        self.directory_tree.tree_view.clicked.connect(self.on_directory_selected)
        self.file_list.list_view.clicked.connect(self.on_file_selected)

    def on_directory_selected(self, index):
        """디렉토리 트리에서 항목 선택 시 파일 목록 및 태그 뷰를 업데이트합니다."""
        path = self.directory_tree.model.filePath(index)
        self.file_list.set_path(path)
        self.file_detail.clear_preview()
        self.tag_control.clear_view()
        self.statusbar.showMessage(f"'{path}' 디렉토리를 보고 있습니다.")

    def on_file_selected(self, index):
        """파일 리스트에서 항목 선택 시 상세 정보 및 태그 컨트롤을 업데이트합니다."""
        file_path = self.file_list.model.get_file_path(index) # get_file_path 사용
        self.file_detail.update_preview(file_path)
        self.tag_control.update_for_file(file_path)
        self.statusbar.showMessage(f"'{file_path}' 파일을 선택했습니다.")

    def open_batch_tagging_dialog(self):
        """일괄 태깅 다이얼로그를 엽니다. (구현 예정)"""
        self.statusbar.showMessage("일괄 태깅 기능이 실행되었습니다.")
        print("일괄 태깅 기능 실행")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())