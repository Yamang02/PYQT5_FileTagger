from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, 
                             QPushButton, QLabel, QFrame, QSizePolicy, QSpacerItem, QCompleter, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QStringListModel, QSize
from PyQt5.QtGui import QIcon, QFont

from viewmodels.search_viewmodel import SearchViewModel

class SearchWidget(QWidget):
    """
    통합 검색 툴바 위젯 (단순화된 구조)
    """
    advanced_search_requested = pyqtSignal(dict)  # 고급 검색 요청

    def __init__(self, viewmodel: SearchViewModel, parent=None):
        super().__init__(parent)
        self.viewmodel = viewmodel
        self.setup_ui()
        self.setup_connections()
        self.connect_viewmodel_signals()

    def connect_viewmodel_signals(self):
        """ViewModel의 시그널을 위젯의 슬롯에 연결합니다."""
        self.viewmodel.search_completed.connect(self.update_search_results)
        self.viewmodel.search_cleared.connect(self.clear_search)
        
        # 디바운싱 타이머 단순화
        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._on_debounce_timeout)
        
        self._advanced_panel_visible = False

    def setup_ui(self):
        # Material Design 스타일 적용
        self.setObjectName("searchPanel")
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 8, 16, 8)
        main_layout.setSpacing(12)

        # 파일명 입력 (20%)
        self.filename_input = QLineEdit()
        self.filename_input.setPlaceholderText("파일명 검색...")
        self.filename_input.setFixedHeight(36)
        self.filename_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        main_layout.addWidget(self.filename_input, 2)

        # 확장자 입력 (고정폭)
        self.extensions_input = QLineEdit()
        self.extensions_input.setPlaceholderText(".jpg, .png")
        self.extensions_input.setFixedHeight(36)
        self.extensions_input.setFixedWidth(100)
        main_layout.addWidget(self.extensions_input)

        # 태그 입력 (30%)
        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("태그 검색 (예: 중요,문서|긴급)")
        self.tag_input.setFixedHeight(36)
        self.tag_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.tag_input.setToolTip("쉼표(,)는 AND, 파이프(|)는 OR, 별표(*)는 NOT 조건입니다.")
        main_layout.addWidget(self.tag_input, 3)
        
        # 자동완성 단순화
        self._tag_completer_model = QStringListModel()
        self._tag_completer = QCompleter(self._tag_completer_model, self)
        self._tag_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self._tag_completer.setFilterMode(Qt.MatchContains)
        self.tag_input.setCompleter(self._tag_completer)

        # 아이콘 버튼들을 별도 컨테이너에 배치하여 정렬 개선
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(8)

        # 검색 버튼
        self.search_button = QPushButton()
        self.search_button.setIcon(QIcon("assets/icons/search.svg"))
        self.search_button.setFixedSize(36, 36)
        self.search_button.setToolTip("검색 실행")
        button_layout.addWidget(self.search_button)

        # 초기화 버튼
        self.clear_button = QPushButton()
        self.clear_button.setIcon(QIcon("assets/icons/close.svg"))
        self.clear_button.setFixedSize(36, 36)
        self.clear_button.setToolTip("검색 조건 초기화")
        button_layout.addWidget(self.clear_button)

        # 고급 검색 토글 버튼
        self.advanced_toggle = QPushButton()
        self.advanced_toggle.setIcon(QIcon("assets/icons/expand_more.svg"))
        self.advanced_toggle.setFixedSize(36, 36)
        self.advanced_toggle.setToolTip("고급 검색 옵션")
        button_layout.addWidget(self.advanced_toggle)

        main_layout.addWidget(button_container)

        # 결과 표시 영역
        result_container = QWidget()
        result_layout = QVBoxLayout(result_container)
        result_layout.setContentsMargins(0, 0, 0, 0)
        result_layout.setSpacing(4)

        self.result_count_label = QLabel("검색 결과")
        self.result_count_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        result_layout.addWidget(self.result_count_label)

        self.search_conditions_label = QLabel()
        self.search_conditions_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.search_conditions_label.setWordWrap(True)
        result_layout.addWidget(self.search_conditions_label)

        main_layout.addWidget(result_container)

        # 고급 검색 패널 설정
        self.setup_advanced_panel()

    def setup_advanced_panel(self):
        """고급 검색 패널을 설정합니다."""
        self.advanced_panel = QWidget()
        self.advanced_panel.setVisible(False)
        
        advanced_layout = QVBoxLayout(self.advanced_panel)
        advanced_layout.setContentsMargins(16, 8, 16, 8)
        advanced_layout.setSpacing(12)

        # 파일명 고급 검색
        filename_advanced_layout = QHBoxLayout()
        filename_advanced_layout.setSpacing(8)

        self.exact_filename_input = QLineEdit()
        self.exact_filename_input.setPlaceholderText("정확한 파일명")
        self.exact_filename_input.setMinimumHeight(36)
        filename_advanced_layout.addWidget(self.exact_filename_input)

        self.partial_filename_input = QLineEdit()
        self.partial_filename_input.setPlaceholderText("부분 파일명")
        self.partial_filename_input.setMinimumHeight(36)
        filename_advanced_layout.addWidget(self.partial_filename_input)

        from PyQt5.QtWidgets import QCheckBox
        self.regex_checkbox = QCheckBox("정규식 사용")
        filename_advanced_layout.addWidget(self.regex_checkbox)

        advanced_layout.addLayout(filename_advanced_layout)

        # 태그 고급 검색
        tag_advanced_layout = QHBoxLayout()
        tag_advanced_layout.setSpacing(8)

        self.and_tags_input = QLineEdit()
        self.and_tags_input.setPlaceholderText("AND 조건 태그들 (쉼표로 구분)")
        self.and_tags_input.setMinimumHeight(36)
        tag_advanced_layout.addWidget(self.and_tags_input)

        self.or_tags_input = QLineEdit()
        self.or_tags_input.setPlaceholderText("OR 조건 태그들 (파이프로 구분)")
        self.or_tags_input.setMinimumHeight(36)
        tag_advanced_layout.addWidget(self.or_tags_input)

        self.not_tags_input = QLineEdit()
        self.not_tags_input.setPlaceholderText("제외할 태그들 (별표로 시작)")
        self.not_tags_input.setMinimumHeight(36)
        tag_advanced_layout.addWidget(self.not_tags_input)

        advanced_layout.addLayout(tag_advanced_layout)

    def setup_connections(self):
        """시그널-슬롯 연결"""
        # 검색 버튼 연결
        self.search_button.clicked.connect(self._on_search_requested)
        self.clear_button.clicked.connect(self.viewmodel.clear_search)
        self.advanced_toggle.clicked.connect(self._toggle_advanced_panel)
        
        # 입력 필드 연결 (디바운싱 적용)
        self.filename_input.textChanged.connect(self._on_input_changed)
        self.tag_input.textChanged.connect(self._on_input_changed)
        self.extensions_input.textChanged.connect(self._on_input_changed)
        
        # Enter 키 연결
        self.filename_input.returnPressed.connect(self._on_search_requested)
        self.tag_input.returnPressed.connect(self._on_search_requested)

    def _on_input_changed(self):
        """입력 변경 시 디바운싱 적용"""
        self._debounce_timer.start(300)  # 300ms 디바운싱
        
    def _on_debounce_timeout(self):
        """디바운싱 타임아웃 시 실시간 검색"""
        if self.filename_input.text().strip() or self.tag_input.text().strip():
            self._on_search_requested()
            
    def _on_search_requested(self):
        """검색 요청 처리"""
        search_conditions = self.get_search_conditions()
        if search_conditions:
            self.viewmodel.perform_search(search_conditions)
            
    def _toggle_advanced_panel(self):
        """고급 검색 패널 토글"""
        self._advanced_panel_visible = not self._advanced_panel_visible
        
        # 아이콘 변경
        if self._advanced_panel_visible:
            self.advanced_toggle.setIcon(QIcon("assets/icons/expand_less.svg"))
        else:
            self.advanced_toggle.setIcon(QIcon("assets/icons/expand_more.svg"))
            
        self.show_advanced_panel(self._advanced_panel_visible)
        
    def get_search_conditions(self) -> dict:
        """현재 검색 조건을 딕셔너리로 반환"""
        conditions = {}
        
        # 파일명 검색 조건
        filename = self.filename_input.text().strip()
        extensions = self.extensions_input.text().strip()
        if filename or extensions:
            conditions['filename'] = {
                'name': filename,
                'extensions': [ext.strip() for ext in extensions.split(',') if ext.strip()]
            }
            
        # 태그 검색 조건
        tag_query = self.tag_input.text().strip()
        if tag_query:
            conditions['tags'] = {
                'query': tag_query
            }
            
        # 고급 검색 조건
        if self._advanced_panel_visible:
            advanced_conditions = {}
            
            # 파일명 고급 검색
            exact_filename = self.exact_filename_input.text().strip()
            partial_filename = self.partial_filename_input.text().strip()
            use_regex = self.regex_checkbox.isChecked()
            
            if exact_filename or partial_filename or use_regex:
                advanced_conditions['filename'] = {
                    'exact': exact_filename,
                    'partial': partial_filename,
                    'use_regex': use_regex
                }
                
            # 태그 고급 검색
            and_tags = self.and_tags_input.text().strip()
            or_tags = self.or_tags_input.text().strip()
            not_tags = self.not_tags_input.text().strip()
            
            if and_tags or or_tags or not_tags:
                advanced_conditions['tags'] = {
                    'and': [tag.strip() for tag in and_tags.split(',') if tag.strip()],
                    'or': [tag.strip() for tag in or_tags.split('|') if tag.strip()],
                    'not': [tag.strip() for tag in not_tags.split(',') if tag.strip()]
                }
                
            if advanced_conditions:
                conditions['advanced'] = advanced_conditions
                
        return conditions
        
    def set_search_conditions(self, conditions: dict):
        """검색 조건 설정"""
        # 파일명 검색 조건
        if 'filename' in conditions:
            filename_cond = conditions['filename']
            self.filename_input.setText(filename_cond.get('name', ''))
            extensions = filename_cond.get('extensions', [])
            self.extensions_input.setText(', '.join(extensions))
            
        # 태그 검색 조건
        if 'tags' in conditions:
            tag_cond = conditions['tags']
            self.tag_input.setText(tag_cond.get('query', ''))
            
        # 고급 검색 조건
        if 'advanced' in conditions:
            advanced_cond = conditions['advanced']
            
            # 파일명 고급 검색
            if 'filename' in advanced_cond:
                filename_adv = advanced_cond['filename']
                self.exact_filename_input.setText(filename_adv.get('exact', ''))
                self.partial_filename_input.setText(filename_adv.get('partial', ''))
                self.regex_checkbox.setChecked(filename_adv.get('use_regex', False))
                
            # 태그 고급 검색
            if 'tags' in advanced_cond:
                tags_adv = advanced_cond['tags']
                self.and_tags_input.setText(', '.join(tags_adv.get('and', [])))
                self.or_tags_input.setText('|'.join(tags_adv.get('or', [])))
                self.not_tags_input.setText(', '.join(tags_adv.get('not', [])))
                
    def clear_search(self):
        """검색 조건 초기화"""
        self.filename_input.clear()
        self.tag_input.clear()
        self.extensions_input.clear()
        self.exact_filename_input.clear()
        self.partial_filename_input.clear()
        self.regex_checkbox.setChecked(False)
        self.and_tags_input.clear()
        self.or_tags_input.clear()
        self.not_tags_input.clear()
        self.result_count_label.setText("검색 결과")
        self.search_conditions_label.clear()
        
    def update_search_results(self, count: int, conditions_summary: str = ""):
        """검색 결과 업데이트"""
        self.result_count_label.setText(f"{count}개 검색됨")
        
        # 사용자가 입력한 검색값들만 조건표시창에 표시
        if conditions_summary:
            display_conditions = []
            
            # 파일명 검색 조건
            filename = self.filename_input.text().strip()
            extensions = self.extensions_input.text().strip()
            if filename:
                display_conditions.append(f"파일명: '{filename}'")
            if extensions:
                display_conditions.append(f"확장자: {extensions}")
                
            # 태그 검색 조건
            tag_query = self.tag_input.text().strip()
            if tag_query:
                display_conditions.append(f"태그: '{tag_query}'")
                
            # 고급 검색 조건
            if self._advanced_panel_visible:
                exact_filename = self.exact_filename_input.text().strip()
                partial_filename = self.partial_filename_input.text().strip()
                and_tags = self.and_tags_input.text().strip()
                or_tags = self.or_tags_input.text().strip()
                not_tags = self.not_tags_input.text().strip()
                
                if exact_filename:
                    display_conditions.append(f"정확한 파일명: '{exact_filename}'")
                if partial_filename:
                    display_conditions.append(f"부분 파일명: '{partial_filename}'")
                if and_tags:
                    display_conditions.append(f"AND 태그: {and_tags}")
                if or_tags:
                    display_conditions.append(f"OR 태그: {or_tags}")
                if not_tags:
                    display_conditions.append(f"NOT 태그: {not_tags}")
                    
            if display_conditions:
                self.search_conditions_label.setText(" | ".join(display_conditions))
            else:
                self.search_conditions_label.clear()
        else:
            self.search_conditions_label.clear()

    def show_advanced_panel(self, show: bool):
        """고급 검색 패널 표시/숨김"""
        self.advanced_panel.setVisible(show)
        self.advanced_search_requested.emit({'show': show})

    def get_advanced_panel(self):
        """고급 검색 패널 위젯을 반환합니다."""
        return self.advanced_panel

    def update_tag_completer(self, tags: list):
        """태그 자동완성 목록을 업데이트합니다."""
        self._tag_completer_model.setStringList(tags) 