import logging

from PyQt5.QtWidgets import QWidget, QCompleter, QMessageBox, QSizePolicy
from PyQt5.uic import loadUi
from PyQt5.QtCore import Qt, QStringListModel, pyqtSignal

from widgets.tag_chip import TagChip
from widgets.quick_tags_widget import QuickTagsWidget
from widgets.batch_tagging_options_widget import BatchTaggingOptionsWidget
from core.custom_tag_manager import CustomTagManager
from widgets.batch_remove_tags_dialog import BatchRemoveTagsDialog

logger = logging.getLogger(__name__)

class TagControlWidget(QWidget):
    tags_updated = pyqtSignal()

    def __init__(self, tag_manager, custom_tag_manager: CustomTagManager, parent=None):
        super().__init__(parent)
        self.tag_manager = tag_manager
        self.custom_tag_manager = custom_tag_manager
        self.current_target_path = None # 현재 선택된 파일 또는 디렉토리 경로 (단일 파일/디렉토리)
        self.current_target_paths: list[str] = [] # 현재 선택된 파일 목록 (다중 파일)
        self.is_current_target_dir = False # 현재 대상이 디렉토리인지 여부
        self.individual_tags: list[str] = [] # 개별 태깅 탭의 태그 목록
        self.batch_tags: list[str] = []      # 일괄 태깅 탭의 태그 목록

        self.setup_ui()
        self.setup_completer()
        self.connect_signals()
        self.update_all_tags_list() # 모든 태그 목록 초기화

    def setup_ui(self):
        loadUi('ui/tag_control_widget.ui', self)
        logger.debug(f"[TagControlWidget] setup_ui: tagging_tab_widget type: {type(self.tagging_tab_widget)}")

        # QuickTagsWidget 인스턴스 생성 및 배치
        self.individual_quick_tags = QuickTagsWidget(self.custom_tag_manager, self)
        self.individual_quick_tags.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.individual_verticalLayout.replaceWidget(self.individual_quick_tags_placeholder, self.individual_quick_tags)
        self.individual_quick_tags_placeholder.deleteLater()

        self.batch_quick_tags = QuickTagsWidget(self.custom_tag_manager, self)
        self.batch_quick_tags.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.batch_verticalLayout.replaceWidget(self.batch_quick_tags_placeholder, self.batch_quick_tags)
        self.batch_quick_tags_placeholder.deleteLater()

        # BatchTaggingOptionsWidget 인스턴스 생성 및 배치
        self.batch_options = BatchTaggingOptionsWidget()
        self.batch_verticalLayout.replaceWidget(self.batch_options_placeholder, self.batch_options)
        self.batch_options_placeholder.deleteLater()

        # 모든 태그 목록을 위한 모델
        self.all_tags_model = QStringListModel()
        self.all_tags_list_view.setModel(self.all_tags_model)

        self.set_enabled(False) # 초기에는 비활성화

    def connect_signals(self):
        # 탭 위젯 변경 시그널
        self.tagging_tab_widget.currentChanged.connect(self.on_tab_changed)

        # 개별 태깅 탭 시그널
        self.individual_tag_input.returnPressed.connect(lambda: self.add_tag_from_input(mode='individual'))
        self.individual_save_button.clicked.connect(self.save_individual_tags)
        self.individual_quick_tags.tags_changed.connect(self.on_individual_quick_tags_changed)

        # 일괄 태깅 탭 시그널
        self.batch_tag_input.returnPressed.connect(lambda: self.add_tag_from_input(mode='batch'))
        self.batch_apply_button.clicked.connect(self.apply_batch_tags)
        self.batch_quick_tags.tags_changed.connect(self.on_batch_quick_tags_changed)
        self.batch_remove_tags_button.clicked.connect(self._on_batch_remove_tags_clicked)

        # 모든 태그 검색 시그널
        self.all_tags_search_input.textChanged.connect(self.filter_all_tags_list)
        self.all_tags_list_view.clicked.connect(self.on_all_tags_list_clicked)

    def setup_completer(self):
        self.completer_model = QStringListModel()
        self.completer = QCompleter(self.completer_model, self)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        
        # 개별 태깅 입력 필드에 자동 완성 연결
        self.individual_tag_input.setCompleter(self.completer)
        # 일괄 태깅 입력 필드에 자동 완성 연결
        self.batch_tag_input.setCompleter(self.completer)

        self.update_completer_model()

    def update_completer_model(self):
        all_tags = self.tag_manager.get_all_tags()
        self.completer_model.setStringList(all_tags)

    def update_all_tags_list(self):
        all_tags = self.tag_manager.get_all_tags()
        self.all_tags_model.setStringList(all_tags)

    def filter_all_tags_list(self, text):
        all_tags = self.tag_manager.get_all_tags()
        filtered_tags = [tag for tag in all_tags if text.lower() in tag.lower()]
        self.all_tags_model.setStringList(filtered_tags)

    def on_all_tags_list_clicked(self, index):
        selected_tag = self.all_tags_model.data(index, Qt.DisplayRole)
        current_tab_index = self.tagging_tab_widget.currentIndex()

        if current_tab_index == 0: # 개별 태깅 탭
            self._add_tag_to_list(selected_tag, self.individual_tags, self.individual_chip_layout, self.individual_tag_input)
        elif current_tab_index == 1: # 일괄 태깅 탭
            self._add_tag_to_list(selected_tag, self.batch_tags, self.batch_chip_layout, self.batch_tag_input)

    def _add_tag_to_list(self, tag_text, tag_list, chip_layout, tag_input_field):
        if tag_text and tag_text not in tag_list:
            tag_list.append(tag_text)
            self._refresh_chip_layout(tag_list, chip_layout, tag_input_field)
            tag_input_field.clear()

    def on_tab_changed(self, index):
        # 탭 변경 시 현재 선택된 파일/디렉토리에 따라 UI 업데이트
        # 이 부분은 update_for_target에서 처리되므로 여기서는 특별한 로직이 필요 없을 수 있음
        pass

    def update_for_target(self, target, is_dir):
        logger.debug(f"[TagControlWidget] update_for_target 호출됨: target={target}, is_dir={is_dir}")
        # target은 단일 경로(str) 또는 여러 경로(list)가 될 수 있음
        self.current_target_path = None
        self.current_target_paths = []
        self.is_current_target_dir = is_dir

        if isinstance(target, list):
            self.current_target_paths = target
            # 다중 파일 선택 시 일괄 태깅 탭으로 강제 전환
            logger.debug("[TagControlWidget] 다중 파일 선택 감지. 일괄 태깅 탭으로 전환 시도.")
            self.tagging_tab_widget.setTabEnabled(0, False) # 개별 태깅 탭 비활성화
            self.tagging_tab_widget.setTabEnabled(1, True)  # 일괄 태깅 탭 활성화
            self.tagging_tab_widget.setCurrentIndex(1) # 일괄 태깅 탭으로 전환
            logger.debug(f"[TagControlWidget] 현재 탭 인덱스: {self.tagging_tab_widget.currentIndex()}")

            self.individual_target_label.setText("파일을 선택하세요.")
            self.batch_target_label.setText(f"선택된 파일: {len(target)}개")
            self.set_tags_for_mode('individual', [])
            self.set_tags_for_mode('batch', []) # 일괄 태깅 탭의 태그는 초기화
            self.set_enabled(True)

        elif isinstance(target, str):
            self.current_target_path = target
            if not target:
                self.set_enabled(False)
                self.individual_target_label.setText("선택된 파일 없음")
                self.batch_target_label.setText("선택된 디렉토리 없음")
                self.set_tags_for_mode('individual', [])
                self.set_tags_for_mode('batch', [])
                return

            self.set_enabled(True)

            if is_dir:
                # 디렉토리 선택 시 일괄 태깅 탭 활성화, 개별 태깅 탭 비활성화
                logger.debug("[TagControlWidget] 디렉토리 선택 감지. 일괄 태깅 탭으로 전환 시도.")
                self.tagging_tab_widget.setTabEnabled(0, False) # 개별 태깅 탭 비활성화
                self.tagging_tab_widget.setTabEnabled(1, True)  # 일괄 태깅 탭 활성화
                self.tagging_tab_widget.setCurrentIndex(1) # 일괄 태깅 탭으로 전환
                logger.debug(f"[TagControlWidget] 현재 탭 인덱스: {self.tagging_tab_widget.currentIndex()}")

                self.individual_target_label.setText("파일을 선택하세요.")
                self.batch_target_label.setText(f"대상 디렉토리: {target}")
                self.set_tags_for_mode('individual', [])
                self.set_tags_for_mode('batch', []) # 일괄 태깅 탭의 태그는 초기화

            else: # 파일 선택 시
                # 파일 선택 시 개별 태깅 탭 활성화, 일괄 태깅 탭 비활성화
                logger.debug("[TagControlWidget] 단일 파일 선택 감지. 개별 태깅 탭으로 전환 시도.")
                self.tagging_tab_widget.setTabEnabled(0, True)  # 개별 태깅 탭 활성화
                self.tagging_tab_widget.setTabEnabled(1, False) # 일괄 태깅 탭 비활성화
                self.tagging_tab_widget.setCurrentIndex(0) # 개별 태깅 탭으로 전환
                logger.debug(f"[TagControlWidget] 현재 탭 인덱스: {self.tagging_tab_widget.currentIndex()}")

                self.individual_target_label.setText(f"선택된 파일: {target}")
                self.batch_target_label.setText("디렉토리를 선택하세요.")
                
                # 파일의 기존 태그 로드
                tags = self.tag_manager.get_tags_for_file(target)
                self.set_tags_for_mode('individual', tags)
                self.set_tags_for_mode('batch', []) # 일괄 태깅 탭의 태그는 초기화

        else:
            # 유효하지 않은 대상
            self.set_enabled(False)
            self.individual_target_label.setText("선택된 파일 없음")
            self.batch_target_label.setText("선택된 디렉토리 없음")
            self.set_tags_for_mode('individual', [])
            self.set_tags_for_mode('batch', [])

    def set_tags_for_mode(self, mode, tags):
        if mode == 'individual':
            self.individual_tags = list(tags)
            self.individual_quick_tags.set_selected_tags(tags)
            self._refresh_chip_layout(self.individual_tags, self.individual_chip_layout, self.individual_tag_input)
        elif mode == 'batch':
            self.batch_tags = list(tags)
            self.batch_quick_tags.set_selected_tags(tags)
            self._refresh_chip_layout(self.batch_tags, self.batch_chip_layout, self.batch_tag_input)

    def add_tag_from_input(self, mode):
        if mode == 'individual':
            tag_text = self.individual_tag_input.text().strip()
            tag_list = self.individual_tags
            chip_layout = self.individual_chip_layout
            tag_input_field = self.individual_tag_input
        elif mode == 'batch':
            tag_text = self.batch_tag_input.text().strip()
            tag_list = self.batch_tags
            chip_layout = self.batch_chip_layout
            tag_input_field = self.batch_tag_input
        else:
            return

        if not tag_text:
            return
        
        if tag_text not in tag_list:
            tag_list.append(tag_text)
            self._refresh_chip_layout(tag_list, chip_layout, tag_input_field)
        tag_input_field.clear()

    def remove_tag(self, tag_text, mode):
        if mode == 'individual':
            tag_list = self.individual_tags
            chip_layout = self.individual_chip_layout
            tag_input_field = self.individual_tag_input
        elif mode == 'batch':
            tag_list = self.batch_tags
            chip_layout = self.batch_chip_layout
            tag_input_field = self.batch_tag_input
        else:
            return

        if tag_text in tag_list:
            tag_list.remove(tag_text)
            self._refresh_chip_layout(tag_list, chip_layout, tag_input_field)

    def _refresh_chip_layout(self, tags, chip_layout, tag_input_field):
        # 기존 칩 모두 제거 (스페이서 제외)
        while chip_layout.count() > 1:
            item = chip_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 현재 태그 목록으로 새 칩 생성 및 추가
        for tag in tags:
            chip = TagChip(tag)
            # 현재 활성화된 탭에 따라 remove_tag 호출 시 mode 인자 전달
            current_tab_index = self.tagging_tab_widget.currentIndex()
            if current_tab_index == 0: # 개별 태깅 탭
                chip.delete_button.clicked.connect(lambda _, t=tag: self.remove_tag(t, 'individual'))
            elif current_tab_index == 1: # 일괄 태깅 탭
                chip.delete_button.clicked.connect(lambda _, t=tag: self.remove_tag(t, 'batch'))
            chip_layout.insertWidget(chip_layout.count() - 1, chip)

    def save_individual_tags(self):
        if self.current_target_path and not self.is_current_target_dir:
            self.tag_manager.update_tags(self.current_target_path, self.individual_tags)
            self.update_completer_model() # 새 태그가 추가되었을 수 있으므로 자동완성 모델 업데이트
            self.update_all_tags_list() # 모든 태그 목록 업데이트
            self.tags_updated.emit()
            QMessageBox.information(self, "저장 완료", f"'{self.current_target_path}' 파일의 태그가 저장되었습니다.")
        else:
            QMessageBox.warning(self, "오류", "파일이 선택되지 않았거나 디렉토리입니다.")

    def apply_batch_tags(self):
        if not self.batch_tags:
            QMessageBox.warning(self, "태그 입력 필요", "적용할 태그를 입력해주세요.")
            return

        result = None
        # 1. 다중 파일 선택의 경우
        if self.current_target_paths:
            result = self.tag_manager.add_tags_to_files(
                self.current_target_paths, 
                self.batch_tags
            )

        # 2. 단일 디렉토리 선택의 경우
        elif self.current_target_path and self.is_current_target_dir:
            recursive = self.batch_options.recursive_checkbox.isChecked()
            file_extensions = self.batch_options._get_file_extensions()
            result = self.tag_manager.add_tags_to_directory(
                self.current_target_path, 
                self.batch_tags, 
                recursive=recursive, 
                file_extensions=file_extensions
            )
        
        # 3. 그 외 (대상이 선택되지 않은 경우 등)
        else:
            QMessageBox.warning(self, "오류", "태그를 적용할 대상(파일/디렉토리)이 선택되지 않았습니다.")
            return

        # 결과 처리 및 UI 업데이트
        if result and result.get("success"):
            QMessageBox.information(self, "일괄 태깅 완료", f"{result.get('successful', 0)}개 항목에 태그가 성공적으로 적용되었습니다.")
            self.update_completer_model()
            self.update_all_tags_list()
            self.tags_updated.emit()
        else:
            error_msg = result.get("error") if result else "알 수 없는 오류"
            QMessageBox.critical(self, "일괄 태깅 실패", f"오류: {error_msg}")

    def set_enabled(self, enabled):
        # 탭 위젯 자체의 활성화/비활성화는 여기서 제어하지 않고, update_for_target에서 탭별로 제어
        self.individual_tag_input.setEnabled(enabled)
        self.individual_save_button.setEnabled(enabled)
        self.individual_quick_tags.set_enabled(enabled)

        self.batch_tag_input.setEnabled(enabled)
        self.batch_apply_button.setEnabled(enabled)
        self.batch_quick_tags.set_enabled(enabled)
        self.batch_options.setEnabled(enabled)

        self.all_tags_search_input.setEnabled(enabled)
        self.all_tags_list_view.setEnabled(enabled)

        # 칩들도 활성화/비활성화
        for i in range(self.individual_chip_layout.count() - 1):
            widget = self.individual_chip_layout.itemAt(i).widget()
            if widget:
                widget.setEnabled(enabled)
        for i in range(self.batch_chip_layout.count() - 1):
            widget = self.batch_chip_layout.itemAt(i).widget()
            if widget:
                widget.setEnabled(enabled)

    def on_individual_quick_tags_changed(self, tags):
        # 빠른 태그 변경 시 개별 태깅 탭의 태그 목록 업데이트
        self.individual_tags = list(set(self.individual_tags + tags)) # 중복 제거
        self._refresh_chip_layout(self.individual_tags, self.individual_chip_layout, self.individual_tag_input)

    def on_batch_quick_tags_changed(self, tags):
        # 빠른 태그 변경 시 일괄 태깅 탭의 태그 목록 업데이트
        self.batch_tags = list(set(self.batch_tags + tags)) # 중복 제거
        self._refresh_chip_layout(self.batch_tags, self.batch_chip_layout, self.batch_tag_input)

    def _on_batch_remove_tags_clicked(self):
        print("DEBUG: _on_batch_remove_tags_clicked called.") # 진단용
        if not self.current_target_path and not self.current_target_paths:
            QMessageBox.warning(self, "대상 없음", "태그를 제거할 파일 또는 디렉토리를 선택해주세요.")
            return

        target = self.current_target_paths if self.current_target_paths else self.current_target_path
        dialog = BatchRemoveTagsDialog(self.tag_manager, target, self)
        print(f"DEBUG: BatchRemoveTagsDialog created: {dialog}") # 진단용
        if dialog.exec_():
            print("DEBUG: BatchRemoveTagsDialog accepted.") # 진단용
            tags_to_remove = dialog.get_tags_to_remove()
            if not tags_to_remove:
                QMessageBox.information(self, "정보", "제거할 태그가 선택되지 않았습니다.")
                return

            target_files = []
            if self.current_target_paths: # 다중 파일 선택
                target_files = self.current_target_paths
            elif self.current_target_path and self.is_current_target_dir: # 단일 디렉토리 선택
                # TagManager의 get_files_in_directory를 사용하여 파일 목록 가져오기
                target_files = self.tag_manager.get_files_in_directory(self.current_target_path, recursive=True, file_extensions=None)
            
            if not target_files:
                QMessageBox.information(self, "정보", "선택된 대상 내에 태그를 제거할 파일이 없습니다.")
                return

            result = self.tag_manager.remove_tags_from_files(target_files, tags_to_remove)
            print(f"DEBUG: tag_manager.remove_tags_from_files result: {result}") # 진단용
            if result and result.get("success"):
                QMessageBox.information(self, "일괄 태그 제거 완료", f"{result.get('successful', 0)}개 항목에서 태그가 성공적으로 제거되었습니다.")
                self.tags_updated.emit() # UI 업데이트
            else:
                error_msg = result.get("error") if result else "알 수 없는 오류"
                QMessageBox.critical(self, "일괄 태그 제거 실패", f"오류: {error_msg}")

    def clear_view(self):
        self.current_target_path = None
        self.current_target_paths = []
        self.is_current_target_dir = False
        self.individual_target_label.setText("선택된 파일 없음")
        self.batch_target_label.setText("선택된 디렉토리 없음")
        self.set_tags_for_mode('individual', [])
        self.set_tags_for_mode('batch', [])
        self.set_enabled(False)
