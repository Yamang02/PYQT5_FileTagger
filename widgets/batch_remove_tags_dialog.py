from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QDialogButtonBox, QLabel, QScrollArea, QWidget, QGridLayout
from widgets.tag_chip import TagChip

class BatchRemoveTagsDialog(QDialog):
    def __init__(self, tag_manager, target_path, parent=None):
        super().__init__(parent)
        self.tag_manager = tag_manager
        self.target_path = target_path
        self.setWindowTitle("일괄 태그 제거")
        self.setMinimumWidth(400)

        self.all_tags = []
        self.tag_chips = []

        self.setup_ui()
        self.load_tags()

    def setup_ui(self):
        """UI를 설정합니다."""
        layout = QVBoxLayout(self)

        # 대상 정보 표시
        self.target_label = QLabel()
        self.target_label.setWordWrap(True)
        layout.addWidget(self.target_label)

        # 태그 검색 입력
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("제거할 태그 검색...")
        self.search_input.textChanged.connect(self.filter_tags)
        layout.addWidget(self.search_input)

        # 태그 칩 스크롤 영역
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        container = QWidget()
        self.chip_layout = QGridLayout(container)
        scroll_area.setWidget(container)
        layout.addWidget(scroll_area)

        # 버튼 박스
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self._update_target_label()

    def _update_target_label(self):
        """대상 정보 레이블을 업데이트합니다."""
        if isinstance(self.target_path, list):
            self.target_label.setText(f"<b>대상 파일:</b><br>{'<br>'.join(self.target_path[:5])}")
            if len(self.target_path) > 5:
                self.target_label.setText(self.target_label.text() + "...")
        elif isinstance(self.target_path, str):
            self.target_label.setText(f"<b>대상 디렉토리:</b><br>{self.target_path}")

    def load_tags(self):
        """대상 파일들의 모든 태그를 로드합니다."""
        files = self._get_target_files()
        if not files:
            return

        # 모든 태그 수집
        all_tags_set = set()
        for file_path in files:
            tags = self.tag_manager.get_tags_for_file(file_path)
            all_tags_set.update(tags)

        self.all_tags = sorted(list(all_tags_set))
        self.create_tag_chips(self.all_tags)

    def _get_target_files(self):
        """대상 파일 목록을 반환합니다."""
        if isinstance(self.target_path, list):
            return self.target_path
        elif isinstance(self.target_path, str):
            return self.tag_manager.get_files_in_directory(self.target_path, recursive=True)
        return []

    def filter_tags(self, text):
        """태그를 필터링합니다."""
        if not text:
            self.create_tag_chips(self.all_tags)
            return

        filtered_tags = [tag for tag in self.all_tags if text.lower() in tag.lower()]
        self.create_tag_chips(filtered_tags)

    def create_tag_chips(self, tags):
        """태그 칩들을 생성합니다."""
        # 기존 칩들 제거
        self._clear_chips()
        
        # 새 칩들 생성
        row, col = 0, 0
        max_cols = 3

        for tag in tags:
            chip = TagChip(tag)
            chip.tag_removed.connect(lambda tag_text, chip_widget=chip: self.on_tag_removed(tag_text, chip_widget))
            self.tag_chips.append(chip)
            self.chip_layout.addWidget(chip, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def _clear_chips(self):
        """모든 태그 칩을 제거합니다."""
        for chip in self.tag_chips:
            chip.setParent(None)
            chip.deleteLater()
        self.tag_chips.clear()

    def on_tag_removed(self, tag, chip_widget):
        """태그가 제거되었을 때 처리합니다."""
        files = self._get_target_files()
        if not files:
            return
            
        # 태그 매니저를 통해 일괄 삭제
        self.tag_manager.remove_tags_from_files(files, [tag])
        
        # UI에서 칩 제거
        chip_widget.setParent(None)
        chip_widget.deleteLater()
        if chip_widget in self.tag_chips:
            self.tag_chips.remove(chip_widget)

    def get_tags_to_remove(self):
        """제거할 태그 목록을 반환합니다."""
        return [chip.tag_text for chip in self.tag_chips if chip.is_checked()]