import os
import logging
import config
from PyQt5.QtWidgets import (
    QMainWindow,
    QFileDialog,
    QMessageBox,
    QMenu,
    QAbstractItemView,
    QVBoxLayout,
    QSpacerItem,
    QSizePolicy,
)
from PyQt5.uic import loadUi
from PyQt5.QtCore import QDir, QModelIndex, QEvent, QItemSelectionModel

from widgets.directory_tree_widget import DirectoryTreeWidget
from widgets.file_list_widget import FileListWidget
from widgets.file_detail_widget import FileDetailWidget
from widgets.tag_control_widget import TagControlWidget
from widgets.search_widget import SearchWidget
from core.custom_tag_manager import CustomTagManager
from widgets.custom_tag_dialog import CustomTagDialog
from widgets.batch_remove_tags_dialog import BatchRemoveTagsDialog
from core.search_manager import SearchManager
from core.ui.ui_setup_manager import UISetupManager
from core.ui.signal_connection_manager import SignalConnectionManager
from core.ui.data_loading_manager import DataLoadingManager

# 새로 추가된 모듈 임포트
from core.events import EventBus
from core.repositories.tag_repository import TagRepository
from core.services.tag_service import TagService
from core.adapters.tag_manager_adapter import TagManagerAdapter
from viewmodels.tag_control_viewmodel import TagControlViewModel
from viewmodels.file_detail_viewmodel import FileDetailViewModel
from viewmodels.file_list_viewmodel import FileListViewModel
from viewmodels.search_viewmodel import SearchViewModel

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self, mongo_client):
        super().__init__()

        # 고정 크기 정의
        self.DEFAULT_WIDTH = 1400
        self.DEFAULT_HEIGHT = 900
        self.is_fixed_size_mode = False  # 최대화 허용으로 변경

        # --- 코어 로직 초기화 ---
        self.mongo_client = mongo_client

        # 새로운 아키텍처 컴포넌트 초기화
        self.event_bus = EventBus()
        self.tag_repository = TagRepository(mongo_client)
        self.tag_service = TagService(self.tag_repository, self.event_bus)
        self.tag_manager = TagManagerAdapter(self.tag_service)  # TagManagerAdapter 사용

        self.custom_tag_manager = CustomTagManager()
        self.search_manager = SearchManager(
            self.tag_manager
        )  # SearchManager는 TagManagerAdapter를 사용하도록 변경

        # ViewModel 초기화
        self.search_viewmodel = SearchViewModel(self.tag_service, self.search_manager)
        self.tag_control_viewmodel = TagControlViewModel(
            self.tag_service, self.event_bus
        )
        self.file_detail_viewmodel = FileDetailViewModel(
            self.tag_service, self.event_bus
        )
        self.file_list_viewmodel = FileListViewModel(
            self.tag_service, self.event_bus, self.search_viewmodel
        )

        # --- 분리된 관리자 클래스 활용 ---
        self.ui_setup = UISetupManager(self)
        self.ui_setup.setup_ui()

        self.signal_manager = SignalConnectionManager(self)
        self.signal_manager.connect_signals()

        self.data_loader = DataLoadingManager(self)
        self.data_loader.load_initial_data()

        self.statusbar.showMessage("준비 완료")

        # 윈도우 크기 설정 및 제한
        self.setup_window_size_constraints()

        self.show()

    def setup_window_size_constraints(self):
        """윈도우 크기 제한을 설정합니다."""
        # 기본 크기로 설정
        self.resize(self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)

        # 최소 크기만 설정 (최대화 허용)
        self.setMinimumSize(self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)
        # 최대 크기 제한 제거 - 최대화 허용
        self.setMaximumSize(16777215, 16777215)

        # 윈도우를 화면 중앙에 배치
        self.center_on_screen()

    def center_on_screen(self):
        """윈도우를 화면 중앙에 배치합니다."""
        from PyQt5.QtWidgets import QDesktopWidget

        screen = QDesktopWidget().screenGeometry()
        window = self.geometry()
        x = (screen.width() - window.width()) // 2
        y = (screen.height() - window.height()) // 2
        self.move(x, y)

    def changeEvent(self, event):
        """창 상태 변경 이벤트를 처리하여 전체 화면 시 레이아웃을 조정합니다."""
        if event.type() == QEvent.WindowStateChange:
            logger.info(f"[WINDOW] 상태 변경: 최대화={self.isMaximized()}")

            if self.isMaximized() or self.isFullScreen():
                # 전체 화면: 크기 제한 해제
                self.setMaximumSize(16777215, 16777215)  # 최대값 해제
                self.setMinimumSize(0, 0)  # 최소값도 해제
            else:
                # 기본 화면: 크기 제한 재적용
                self.setup_window_size_constraints()

            # 여러 번의 지연된 레이아웃 조정 시도
            from PyQt5.QtCore import QTimer

            QTimer.singleShot(50, self._adjust_layout)  # 첫 번째 시도
            QTimer.singleShot(150, self._adjust_layout)  # 두 번째 시도
            QTimer.singleShot(300, self._adjust_layout)  # 세 번째 시도

        super().changeEvent(event)

    def _adjust_layout(self):
        """창 상태에 따라 레이아웃을 조정합니다."""
        if hasattr(self, "ui_setup") and self.ui_setup:
            self.ui_setup.adjust_layout()

    def resizeEvent(self, event):
        """창 크기 변경 시 레이아웃을 안정화합니다."""
        super().resizeEvent(event)

        # 최대화/전체화면 상태에서는 레이아웃 재조정
        if self.isMaximized() or self.isFullScreen():
            from PyQt5.QtCore import QTimer

            QTimer.singleShot(10, self._adjust_layout)  # 빠른 재조정

        # 모든 자식 위젯의 레이아웃을 강제로 업데이트
        if hasattr(self, "file_detail_widget"):
            self.file_detail_widget.update()
            self.file_detail_widget.repaint()
        if hasattr(self, "file_list_widget"):
            self.file_list_widget.update()
        if hasattr(self, "search_widget"):
            self.search_widget.update()

    # setup_connections 메서드는 더 이상 사용되지 않지만, 기존 함수를 참조하는 코드 호환을 위해 남겨둡니다.
    def setup_connections(self):
        """호환성 유지용 래퍼: SignalConnectionManager가 시그널 연결을 담당합니다."""
        if not hasattr(self, "signal_manager"):
            self.signal_manager = SignalConnectionManager(self)
        self.signal_manager.connect_signals()

    def set_workspace(self):
        current_workspace = (
            config.DEFAULT_WORKSPACE_PATH
            if config.DEFAULT_WORKSPACE_PATH
            and os.path.isdir(config.DEFAULT_WORKSPACE_PATH)
            else QDir.homePath()
        )
        new_workspace = QFileDialog.getExistingDirectory(
            self, "작업 공간 선택", current_workspace
        )
        if new_workspace:
            try:
                with open("config.py", "r", encoding="utf-8") as f:
                    lines = f.readlines()
                with open("config.py", "w", encoding="utf-8") as f:
                    for line in lines:
                        if line.startswith("DEFAULT_WORKSPACE_PATH ="):
                            cleaned_path = new_workspace.replace("\\", "/")
                            f.write(f'DEFAULT_WORKSPACE_PATH = "{cleaned_path}"\n')
                        else:
                            f.write(line)
                config.DEFAULT_WORKSPACE_PATH = new_workspace
                self.ui_setup.get_widget("directory_tree").set_root_path(new_workspace)
                self.file_list_viewmodel.set_directory(new_workspace)
                self.ui_setup.get_widget("file_detail").clear_preview()
                self.tag_control_viewmodel.update_for_target(None, False)
                self.statusbar.showMessage(
                    f"작업 공간이 '{new_workspace}'로 설정되었습니다.", 5000
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "오류", f"작업 공간 설정 중 오류가 발생했습니다: {e}"
                )
                self.statusbar.showMessage("작업 공간 설정 실패", 3000)

    def on_directory_selected(self, file_path: str, is_dir: bool):
        recursive = self.ui_setup.get_widget(
            "directory_tree"
        ).recursive_checkbox.isChecked()
        # extensions_input이 제거되었으므로 빈 리스트로 설정
        file_extensions = []

        if is_dir:
            # If a directory is selected, update the file list with its contents
            self.file_list_viewmodel.set_directory(
                file_path, recursive, file_extensions
            )
            self.ui_setup.get_widget("file_detail").clear_preview()
            self.tag_control_viewmodel.update_for_target(file_path, True)
            self.statusbar.showMessage(f"'{file_path}' 디렉토리를 보고 있습니다.")
        else:
            # If a file is selected, update file detail and select it in the file list
            self.ui_setup.get_widget("file_detail").update_preview(file_path)
            self.ui_setup.get_widget("tag_control").update_for_target(file_path, False)
            self.statusbar.showMessage(f"'{file_path}' 파일을 선택했습니다.")

            # Select the file in the file_list
            file_list_index = self.ui_setup.get_widget("file_list").index_from_path(
                file_path
            )
            if file_list_index.isValid():
                self.ui_setup.get_widget("file_list").list_view.selectionModel().select(
                    file_list_index, QItemSelectionModel.ClearAndSelect
                )
            else:
                # If the file is not in the current file_list view (e.g., due to filters),
                # update the file_list to show the directory containing the file
                parent_dir = os.path.dirname(file_path)
                self.file_list_viewmodel.set_directory(
                    parent_dir, recursive, file_extensions
                )
                # Try selecting again after updating the path
                file_list_index = self.ui_setup.get_widget("file_list").index_from_path(
                    file_path
                )
                if file_list_index.isValid():
                    self.ui_setup.get_widget(
                        "file_list"
                    ).list_view.selectionModel().select(
                        file_list_index, QItemSelectionModel.ClearAndSelect
                    )

    def _on_directory_tree_filter_options_changed(
        self, recursive: bool, file_extensions: list
    ):
        # Get the currently selected directory in the directory tree
        # If no directory is selected, use the current file_list directory or default workspace
        selected_index = self.ui_setup.get_widget(
            "directory_tree"
        ).tree_view.currentIndex()
        if selected_index.isValid():
            current_path = self.ui_setup.get_widget("directory_tree").model.filePath(
                self.ui_setup.get_widget("directory_tree").proxy_model.mapToSource(
                    selected_index
                )
            )
            # If the selected item is a file, use its parent directory
            if not self.ui_setup.get_widget("directory_tree").model.isDir(
                self.ui_setup.get_widget("directory_tree").proxy_model.mapToSource(
                    selected_index
                )
            ):
                current_path = os.path.dirname(current_path)
        else:
            current_path = self.ui_setup.get_widget(
                "file_list"
            ).model.viewmodel.get_current_directory()
            if not current_path:
                current_path = (
                    config.DEFAULT_WORKSPACE_PATH
                    if config.DEFAULT_WORKSPACE_PATH
                    and os.path.isdir(config.DEFAULT_WORKSPACE_PATH)
                    else QDir.homePath()
                )

        self.file_list_viewmodel.set_directory(current_path, recursive, file_extensions)
        self.ui_setup.get_widget(
            "file_detail"
        ).clear_preview()  # Clear preview as the file list content might change
        self.tag_control_viewmodel.update_for_target(
            None, False
        )  # Clear tag control as the file list content might change
        self.statusbar.showMessage(
            f"필터 옵션 변경: 재귀={recursive}, 확장자={', '.join(file_extensions) if file_extensions else '모두'}"
        )

    def on_file_selection_changed(self, selected_file_paths: list):
        logger.info(f"[MAIN] 파일 선택 변경: {len(selected_file_paths)}개 파일")

        if len(selected_file_paths) == 1:
            file_path = selected_file_paths[0]
            logger.info(f"[MAIN] 단일 파일 선택: {os.path.basename(file_path)}")
            self.ui_setup.get_widget("file_detail").update_preview(file_path)
            self.tag_control_viewmodel.update_for_target(file_path, False)
            self.statusbar.showMessage(f"'{file_path}' 파일을 선택했습니다.")
        elif len(selected_file_paths) > 1:
            logger.info(f"[MAIN] 다중 파일 선택: {len(selected_file_paths)}개")
            self.ui_setup.get_widget("file_detail").clear_preview()
            self.tag_control_viewmodel.update_for_target(selected_file_paths, False)
            self.statusbar.showMessage(
                f"{len(selected_file_paths)}개 파일을 선택했습니다."
            )
        else:
            logger.info(f"[MAIN] 파일 선택 해제")
            self.ui_setup.get_widget("file_detail").clear_preview()
            self.tag_control_viewmodel.update_for_target(None, False)
            self.statusbar.showMessage("파일 선택이 해제되었습니다.")

    def on_tags_updated(self):
        """태그가 변경될 때 관련 위젯들을 업데이트합니다."""
        try:
            logger.debug("[MAIN] 태그 업데이트 시그널 받음")

            # 파일 목록 업데이트 (태그 표시 새로고침)
            if hasattr(self.file_list_viewmodel, "refresh_current_files"):
                self.file_list_viewmodel.refresh_current_files()

            # EventBus를 통해 이미 ViewModel들이 자동 업데이트되므로
            # 여기서는 추가적인 ViewModel 업데이트를 하지 않음
            # (무한 루프 방지)

            logger.debug("[MAIN] 태그 업데이트 완료")

        except Exception as e:
            logger.error(f"[MAIN] 태그 업데이트 중 오류: {e}")
