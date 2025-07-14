import logging

from PyQt5.QtWidgets import QWidget, QCompleter, QMessageBox, QSizePolicy
from PyQt5.uic import loadUi
from PyQt5.QtCore import Qt, QStringListModel, pyqtSignal

from widgets.tag_chip import TagChip
from widgets.quick_tags_widget import QuickTagsWidget
from widgets.batch_tagging_options_widget import BatchTaggingOptionsWidget
from core.custom_tag_manager import CustomTagManager
from widgets.batch_remove_tags_dialog import BatchRemoveTagsDialog
from viewmodels.tag_control_viewmodel import TagControlViewModel # ViewModel 임포트

logger = logging.getLogger(__name__)

class TagControlWidget(QWidget):
    tags_updated = pyqtSignal() # 외부(MainWindow)로 태그 변경 알림

    def __init__(self, viewmodel: TagControlViewModel, custom_tag_manager: CustomTagManager, parent=None):
        super().__init__(parent)
        self.viewmodel = viewmodel
        self.custom_tag_manager = custom_tag_manager

        self.setup_ui()
        self.setup_completer()
        self.connect_signals()
        self.connect_viewmodel_signals()
        self.update_all_tags_list() # 모든 태그 목록 초기화

    def setup_ui(self):
        loadUi('ui/tag_control_widget.ui', self)

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
        self.individual_quick_tags.tags_changed.connect(self.on_individual_quick_tags_changed)

        # 일괄 태깅 탭 시그널
        self.batch_tag_input.returnPressed.connect(lambda: self.add_tag_from_input(mode='batch'))
        self.batch_apply_button.clicked.connect(self.apply_batch_tags)
        self.batch_quick_tags.tags_changed.connect(self.on_batch_quick_tags_changed)
        self.batch_remove_tags_button.clicked.connect(self._on_batch_remove_tags_clicked)

        # 모든 태그 검색 시그널
        self.all_tags_search_input.textChanged.connect(self.filter_all_tags_list)
        self.all_tags_list_view.clicked.connect(self.on_all_tags_list_clicked)

    def connect_viewmodel_signals(self):
        self.viewmodel.tags_updated.connect(self.on_viewmodel_tags_updated)
        self.viewmodel.target_info_updated.connect(self.on_viewmodel_target_info_updated)
        self.viewmodel.enable_ui.connect(self.set_enabled)
        self.viewmodel.show_message.connect(lambda msg, duration: QMessageBox.information(self, "정보", msg) if duration == 0 else self.parent().statusbar.showMessage(msg, duration))

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
        all_tags = self.viewmodel.get_all_tags()
        self.completer_model.setStringList(all_tags)

    def update_all_tags_list(self):
        all_tags = self.viewmodel.get_all_tags()
        self.all_tags_model.setStringList(all_tags)

    def filter_all_tags_list(self, text):
        all_tags = self.viewmodel.get_all_tags()
        filtered_tags = [tag for tag in all_tags if text.lower() in tag.lower()]
        self.all_tags_model.setStringList(filtered_tags)

    def on_all_tags_list_clicked(self, index):
        selected_tag = self.all_tags_model.data(index, Qt.DisplayRole)
        current_tab_index = self.tagging_tab_widget.currentIndex()

        if current_tab_index == 0: # 개별 태깅 탭
            self.viewmodel.add_tag_to_individual(selected_tag)
        elif current_tab_index == 1: # 일괄 태깅 탭
            self._add_tag_to_list(selected_tag, self.viewmodel.get_current_batch_tags(), self.batch_chip_layout, self.batch_tag_input)

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
        self.viewmodel.update_for_target(target, is_dir)

    def on_viewmodel_tags_updated(self, tags):
        current_tab_index = self.tagging_tab_widget.currentIndex()
        if current_tab_index == 0: # 개별 태깅 탭
            self._refresh_chip_layout(tags, self.individual_chip_layout, self.individual_tag_input)
        elif current_tab_index == 1: # 일괄 태깅 탭
            self._refresh_chip_layout(tags, self.batch_chip_layout, self.batch_tag_input)
        self.tags_updated.emit() # MainWindow에 태그 변경 알림

    def on_viewmodel_target_info_updated(self, label_text: str, is_dir: bool):
        if is_dir:
            self.tagging_tab_widget.setTabEnabled(0, False) # 개별 태깅 탭 비활성화
            self.tagging_tab_widget.setTabEnabled(1, True)  # 일괄 태깅 탭 활성화
            self.tagging_tab_widget.setCurrentIndex(1) # 일괄 태깅 탭으로 전환
            self.individual_target_label.setText("파일을 선택하세요.")
            self.batch_target_label.setText(label_text)
        else:
            self.tagging_tab_widget.setTabEnabled(0, True)  # 개별 태깅 탭 활성화
            self.tagging_tab_widget.setTabEnabled(1, False) # 일괄 태깅 탭 비활성화
            self.tagging_tab_widget.setCurrentIndex(0) # 개별 태깅 탭으로 전환
            self.individual_target_label.setText(label_text)
            self.batch_target_label.setText("디렉토리를 선택하세요.")

    def set_tags_for_mode(self, mode, tags):
        # 이 메서드는 ViewModel에서 데이터를 가져와 UI를 업데이트하는 방식으로 변경됨
        # 직접 태그 리스트를 설정하지 않고, ViewModel의 시그널을 통해 업데이트
        pass

    def add_tag_from_input(self, mode):
        if mode == 'individual':
            tag_text = self.individual_tag_input.text().strip()
            if tag_text:
                self.viewmodel.add_tag_to_individual(tag_text)
                self.individual_tag_input.clear()
        elif mode == 'batch':
            tag_text = self.batch_tag_input.text().strip()
            if tag_text:
                self._add_tag_to_list(tag_text, self.viewmodel.get_current_batch_tags(), self.batch_chip_layout, self.batch_tag_input)
                self.batch_tag_input.clear()

    def remove_tag(self, tag_text, mode):
        if mode == 'individual':
            self.viewmodel.remove_tag_from_individual(tag_text)
        elif mode == 'batch':
            # ViewModel에 일괄 태깅 탭의 태그 제거 로직 추가 필요
            batch_tags = self.viewmodel.get_current_batch_tags()
            if tag_text in batch_tags:
                batch_tags.remove(tag_text)
                self._refresh_chip_layout(batch_tags, self.batch_chip_layout, self.batch_tag_input)

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
        pass  # 더 이상 사용하지 않음, 버튼도 UI에서 제거 필요

    def apply_batch_tags(self):
        tags_to_add = self.viewmodel.get_current_batch_tags()
        recursive = self.batch_options.recursive_checkbox.isChecked()
        file_extensions = self.batch_options._get_file_extensions()
        self.viewmodel.apply_batch_tags(tags_to_add, recursive, file_extensions)

    def set_enabled(self, enabled):
        # 탭 위젯 자체의 활성화/비활성화는 여기서 제어하지 않고, update_for_target에서 탭별로 제어
        self.individual_tag_input.setEnabled(enabled)
        self.individual_quick_tags.set_enabled(enabled)

        self.batch_tag_input.setEnabled(enabled)
        self.batch_apply_button.setEnabled(enabled)
        self.batch_quick_tags.set_enabled(enabled)
        self.batch_options.setEnabled(enabled)

        self.all_tags_search_input.setEnabled(enabled)
        self.all_tags_list_view.setEnabled(enabled)

        # 칩들도 활성화/비활성화
        for i in range(self.individual_chip_layout.count() - 1):
            item = self.individual_chip_layout.itemAt(i)
            if item and item.widget():
                item.widget().setEnabled(enabled)
        for i in range(self.batch_chip_layout.count() - 1):
            item = self.batch_chip_layout.itemAt(i)
            if item and item.widget():
                item.widget().setEnabled(enabled)

    def on_individual_quick_tags_changed(self, tags):
        # 빠른 태그 변경 시 개별 태깅 탭의 태그 목록 업데이트
        # ViewModel의 add_tag_to_individual을 호출하도록 변경
        for tag in tags:
            self.viewmodel.add_tag_to_individual(tag)

    def on_batch_quick_tags_changed(self, tags):
        # 빠른 태그 변경 시 일괄 태깅 탭의 태그 목록 업데이트
        # ViewModel의 get_current_batch_tags를 통해 태그 목록을 가져와 업데이트
        batch_tags = self.viewmodel.get_current_batch_tags()
        for tag in tags:
            if tag not in batch_tags:
                batch_tags.append(tag)
        self._refresh_chip_layout(batch_tags, self.batch_chip_layout, self.batch_tag_input)

    def _on_batch_remove_tags_clicked(self):
        current_target_path = self.viewmodel.get_current_target_path()
        current_target_paths = self.viewmodel.get_current_target_paths()
        is_current_target_dir = self.viewmodel.is_current_target_dir()

        if not current_target_path and not current_target_paths:
            QMessageBox.warning(self, "대상 없음", "태그를 제거할 파일 또는 디렉토리를 선택해주세요.")
            return

        target = current_target_paths if current_target_paths else current_target_path
        dialog = BatchRemoveTagsDialog(self.viewmodel._tag_service, target, self) # ViewModel의 tag_service 전달
        if dialog.exec_():
            tags_to_remove = dialog.get_tags_to_remove()
            if not tags_to_remove:
                return

            target_files = []
            if current_target_paths: # 다중 파일 선택
                target_files = current_target_paths
            elif current_target_path and is_current_target_dir: # 단일 디렉토리 선택
                target_files = self.viewmodel._tag_service.get_files_in_directory(current_target_path, recursive=True, file_extensions=None)
            
            if not target_files:
                QMessageBox.information(self, "정보", "선택된 대상 내에 태그를 제거할 파일이 없습니다.")
                return

            result = self.viewmodel._tag_service.remove_tags_from_files(target_files, tags_to_remove)
            if result and result.get("success"):
                QMessageBox.information(self, "일괄 태그 제거 완료", f"{result.get('successful', 0)}개 항목에서 태그가 성공적으로 제거되었습니다.")
                self.tags_updated.emit() # UI 업데이트
            else:
                error_msg = result.get("error") if result else "알 수 없는 오류"
                QMessageBox.critical(self, "일괄 태그 제거 실패", f"오류: {error_msg}")

    def clear_view(self):
        self.viewmodel.update_for_target(None, False)
        self.individual_target_label.setText("선택된 파일 없음")
        self.batch_target_label.setText("선택된 디렉토리 없음")
        self.set_enabled(False)

    def open_custom_tag_dialog(self):
        """커스텀 태그 관리 다이얼로그를 엽니다."""
        dialog = CustomTagDialog(self.custom_tag_manager, self)
        if dialog.exec_() == CustomTagDialog.Accepted:
            self.tags_updated.emit()

    def open_batch_remove_tags_dialog(self, directory_path):
        """일괄 태그 제거 다이얼로그를 엽니다."""
        dialog = BatchRemoveTagsDialog(self.viewmodel._tag_service, directory_path, self)
        if dialog.exec_():
            self.tags_updated.emit()
