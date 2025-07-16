from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, 
                             QPushButton, QLabel, QFrame, QSizePolicy, QSpacerItem, QCompleter, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QStringListModel, QSize
from PyQt5.QtGui import QIcon, QFont

from viewmodels.search_viewmodel import SearchViewModel # SearchViewModel 임포트

class SearchWidget(QWidget):
    """
    통합 검색 툴바 위젯 (UI 개선 적용)
    """
    # search_requested = pyqtSignal(dict)  # ViewModel에서 처리
    # search_cleared = pyqtSignal()        # ViewModel에서 처리
    advanced_search_requested = pyqtSignal(dict)  # 고급 검색 요청

    MAX_HISTORY = 10  # 검색 히스토리 최대 개수

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
        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._on_debounce_timeout)
        self._advanced_panel_visible = False
        # self._search_history = []  # 검색 조건 히스토리 리스트

    def setup_ui(self):
        # Material Design 스타일 적용
        self.setObjectName("searchPanel")
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 8, 16, 8)
        main_layout.setSpacing(12)

        # 파일명 입력 (20%)
        self.filename_input = QLineEdit()
        self.filename_input.setPlaceholderText("파일명 검색...")
        self.filename_input.setFixedHeight(36)  # 고정 높이로 설정
        self.filename_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        main_layout.addWidget(self.filename_input, 2)

        # 확장자 입력 (고정폭)
        self.extensions_input = QLineEdit()
        self.extensions_input.setPlaceholderText(".jpg, .png")
        self.extensions_input.setFixedHeight(36)  # 고정 높이로 설정
        self.extensions_input.setFixedWidth(100)
        main_layout.addWidget(self.extensions_input)

        # 태그 입력 (30%)
        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("태그 검색 (예: 중요,문서|긴급)")
        self.tag_input.setFixedHeight(36)  # 고정 높이로 설정
        self.tag_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.tag_input.setToolTip("쉼표(,)는 AND, 파이프(|)는 OR, 별표(*)는 NOT 조건입니다.")
        main_layout.addWidget(self.tag_input, 3)
        # 자동완성 관련
        self._tag_completer_model = QStringListModel()
        self._tag_completer = QCompleter(self._tag_completer_model, self)
        self._tag_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self._tag_completer.setFilterMode(Qt.MatchContains)
        self.tag_input.setCompleter(self._tag_completer)
        self.tag_input.focusInEvent = self._on_tag_input_focus
        self.tag_input.textChanged.connect(self._on_tag_input_text_changed)

        # 아이콘 버튼들을 별도 컨테이너에 배치하여 정렬 개선
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(4)
        
        self.search_button = QPushButton()
        self.search_button.setIcon(QIcon("assets/icons/search.svg"))
        self.search_button.setIconSize(QSize(16, 16))  # 아이콘 크기 조정
        self.search_button.setFixedSize(36, 36)  # 입력 필드와 동일한 높이로 설정
        self.search_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # 크기 정책 명시
        self.search_button.setToolTip("검색 실행 (Enter)")
        self.search_button.setProperty("class", "icon-button")  # QSS 클래스 적용
        button_layout.addWidget(self.search_button)

        self.clear_button = QPushButton()
        self.clear_button.setIcon(QIcon("assets/icons/close.svg"))
        self.clear_button.setIconSize(QSize(16, 16))  # 아이콘 크기 조정
        self.clear_button.setFixedSize(36, 36)  # 입력 필드와 동일한 높이로 설정
        self.clear_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # 크기 정책 명시
        self.clear_button.setToolTip("검색 초기화")
        self.clear_button.setProperty("class", "icon-button")  # QSS 클래스 적용
        button_layout.addWidget(self.clear_button)

        self.advanced_toggle = QPushButton()
        self.advanced_toggle.setIcon(QIcon("assets/icons/expand_more.svg"))
        self.advanced_toggle.setIconSize(QSize(16, 16))  # 아이콘 크기 조정
        self.advanced_toggle.setFixedSize(36, 36)  # 입력 필드와 동일한 높이로 설정
        self.advanced_toggle.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # 크기 정책 명시
        self.advanced_toggle.setToolTip("고급 검색 패널 토글")
        self.advanced_toggle.setProperty("class", "icon-button")  # QSS 클래스 적용
        button_layout.addWidget(self.advanced_toggle)
        
        main_layout.addWidget(button_container)

        # 검색 조건 레이블 (고정폭, 우측 정렬)
        self.search_conditions_label = QLabel("")
        self.search_conditions_label.setFixedHeight(36)  # 입력 필드와 동일한 높이
        self.search_conditions_label.setFixedWidth(300)
        self.search_conditions_label.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        main_layout.addWidget(self.search_conditions_label)

        # 검색 결과 레이블 (고정폭, 우측 정렬)
        self.result_count_label = QLabel("검색 결과")
        self.result_count_label.setFixedHeight(36)  # 입력 필드와 동일한 높이
        self.result_count_label.setFixedWidth(120)
        self.result_count_label.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        main_layout.addWidget(self.result_count_label)

        self.setup_advanced_panel()
        
        # 폰트 위계 시스템 적용
        self._apply_font_hierarchy()

    def _show_tag_tooltip(self, event):
        QLineEdit.focusInEvent(self.tag_input, event)
        self.tag_input.setToolTip("쉼표(,)는 AND, 파이프(|)는 OR, 별표(*)는 NOT 조건입니다.")
        self.tag_input.setStatusTip("쉼표(,)는 AND, 파이프(|)는 OR, 별표(*)는 NOT 조건입니다.")

    def setup_advanced_panel(self):
        self.advanced_panel = QFrame()
        self.advanced_panel.setFrameStyle(QFrame.StyledPanel)
        self.advanced_panel.setVisible(False)
        # 고급 검색 패널 높이를 늘려서 모든 요소가 제대로 표시되도록 수정
        self.advanced_panel.setMinimumHeight(200)
        self.advanced_panel.setMaximumHeight(250)
        
        advanced_layout = QHBoxLayout(self.advanced_panel)
        advanced_layout.setContentsMargins(16, 16, 16, 16)  # 여백 증가
        advanced_layout.setSpacing(24)  # 간격 증가
        
        # 파일명 고급 검색 영역 (왼쪽 50%)
        filename_advanced_layout = QVBoxLayout()
        filename_advanced_layout.setSpacing(12)  # 간격 설정
        
        filename_title = QLabel("파일명 고급 검색")
        # 하드코딩된 스타일 제거 - 전역 QSS 사용
        filename_advanced_layout.addWidget(filename_title)
        
        # 정확한 파일명
        self.exact_filename_input = QLineEdit()
        self.exact_filename_input.setPlaceholderText("정확한 파일명")
        self.exact_filename_input.setMinimumHeight(36)
        # 하드코딩된 스타일 제거 - 전역 QSS 사용
        filename_advanced_layout.addWidget(self.exact_filename_input)
        
        # 부분 일치
        self.partial_filename_input = QLineEdit()
        self.partial_filename_input.setPlaceholderText("파일명에 포함된 텍스트")
        self.partial_filename_input.setMinimumHeight(36)
        # 하드코딩된 스타일 제거 - 전역 QSS 사용
        filename_advanced_layout.addWidget(self.partial_filename_input)
        
        # 정규식 체크박스
        from PyQt5.QtWidgets import QCheckBox
        self.regex_checkbox = QCheckBox("정규식 사용")
        # 하드코딩된 스타일 제거 - 전역 QSS 사용
        filename_advanced_layout.addWidget(self.regex_checkbox)
        
        # 남은 공간을 채우기 위한 스페이서 추가
        filename_advanced_layout.addStretch()
        
        advanced_layout.addLayout(filename_advanced_layout, 50)
        
        # 구분선
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        # 하드코딩된 스타일 제거 - 전역 QSS 사용
        advanced_layout.addWidget(separator)
        
        # 태그 고급 검색 영역 (오른쪽 50%)
        tag_advanced_layout = QVBoxLayout()
        tag_advanced_layout.setSpacing(12)  # 간격 설정
        
        tag_title = QLabel("태그 고급 검색")
        # 하드코딩된 스타일 제거 - 전역 QSS 사용
        tag_advanced_layout.addWidget(tag_title)
        
        # AND 검색
        self.and_tags_input = QLineEdit()
        self.and_tags_input.setPlaceholderText("AND 조건 태그들 (쉼표로 구분)")
        self.and_tags_input.setMinimumHeight(36)
        # 하드코딩된 스타일 제거 - 전역 QSS 사용
        tag_advanced_layout.addWidget(self.and_tags_input)
        
        # OR 검색
        self.or_tags_input = QLineEdit()
        self.or_tags_input.setPlaceholderText("OR 조건 태그들 (파이프로 구분)")
        self.or_tags_input.setMinimumHeight(36)
        # 하드코딩된 스타일 제거 - 전역 QSS 사용
        tag_advanced_layout.addWidget(self.or_tags_input)
        
        # NOT 검색
        self.not_tags_input = QLineEdit()
        self.not_tags_input.setPlaceholderText("제외할 태그들 (별표로 시작)")
        self.not_tags_input.setMinimumHeight(36)
        # 하드코딩된 스타일 제거 - 전역 QSS 사용
        tag_advanced_layout.addWidget(self.not_tags_input)
        
        # 남은 공간을 채우기 위한 스페이서 추가
        tag_advanced_layout.addStretch()
        
        advanced_layout.addLayout(tag_advanced_layout, 50)
        
        # 고급 검색 패널을 메인 레이아웃에 추가
        # (SearchWidget의 부모 위젯에서 관리)
        
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
            # self._add_to_history(search_conditions) # 히스토리 관련 코드 제거
            self.viewmodel.perform_search(search_conditions)
            
    def _toggle_advanced_panel(self):
        """고급 검색 패널 토글"""
        self._advanced_panel_visible = not self._advanced_panel_visible
        
        # 아이콘 변경 전에 기존 아이콘을 명시적으로 제거
        self.advanced_toggle.setIcon(QIcon())
        
        if self._advanced_panel_visible:
            self.advanced_toggle.setIcon(QIcon("assets/icons/expand_less.svg"))
        else:
            self.advanced_toggle.setIcon(QIcon("assets/icons/expand_more.svg"))
            
        self.show_advanced_panel(self._advanced_panel_visible)
        
    # self._search_history, MAX_HISTORY, _add_to_history, _on_history_requested, _history_summary 등 히스토리 관련 메서드/변수 전체 삭제
        
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
        
        # 사용자가 입력한 검색값들만 조건표시창에 표시하도록 수정
        if conditions_summary:
            # 실제 입력된 값들만 추출하여 표시
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
                    display_conditions.append(f"제외 태그: {not_tags}")
                    
            # 조건들을 쉼표로 구분하여 표시
            if display_conditions:
                self.search_conditions_label.setText(" | ".join(display_conditions))
            else:
                self.search_conditions_label.clear()
        else:
            self.search_conditions_label.clear()
            
    def show_advanced_panel(self, show: bool):
        """고급 검색 패널 표시/숨김"""
        self._advanced_panel_visible = show
        # 텍스트 설정 제거 - 아이콘만 사용
        self.advanced_panel.setVisible(show)
        
    def get_advanced_panel(self):
        """고급 검색 패널 반환"""
        return self.advanced_panel 

    def _on_tag_input_focus(self, event):
        # QLineEdit 기본 포커스 동작 유지
        QLineEdit.focusInEvent(self.tag_input, event)
        self._update_tag_completer()

    def _on_tag_input_text_changed(self, text):
        self._update_tag_completer()

    def _update_tag_completer(self):
        all_tags = self.viewmodel.get_all_tags()
        text = self.tag_input.text().strip()
        if not text:
            sorted_tags = sorted(all_tags, key=lambda x: x)
            self._tag_completer_model.setStringList(sorted_tags[:5])
        else:
            filtered = [tag for tag in all_tags if text.lower() in tag.lower()]
            self._tag_completer_model.setStringList(filtered)
            
    def _apply_font_hierarchy(self):
        """폰트 위계 시스템을 적용합니다."""
        # Level 2 (부제목/중요 정보) - 검색 조건 및 결과 요약
        self.search_conditions_label.setProperty("class", "level2-subtitle")
        self.result_count_label.setProperty("class", "level2-subtitle")
        
        # Level 4 (보조 텍스트) - 플레이스홀더 텍스트는 QLineEdit에서 처리 