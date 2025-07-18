import logging
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, 
                             QPushButton, QLabel, QFrame, QSizePolicy, QSpacerItem, QCompleter, QMessageBox, QComboBox)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QStringListModel, QSize
from PyQt5.QtGui import QIcon, QFont

from viewmodels.search_viewmodel import SearchViewModel

logger = logging.getLogger(__name__)

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
        
        # 태그 자동완성 초기화
        self._initialize_tag_completer()

    def setup_ui(self):
        # Material Design 스타일 적용
        self.setObjectName("searchPanel")
        
        # SearchWidget 자체의 높이 정책 설정
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(60)  # 메인 레이아웃 마진(8*2) + QLineEdit 높이(44) = 60px
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 8, 16, 8)  # 상하 마진을 늘려서 여유 공간 확보
        main_layout.setSpacing(12)

        # 필드 컨테이너 (전체창 너비의 50% 차지)
        main_fields_container = QWidget()
        main_fields_container.setObjectName("mainFieldsContainer")
        main_fields_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        main_fields_layout = QHBoxLayout(main_fields_container)
        main_fields_layout.setContentsMargins(0, 0, 0, 0)
        main_fields_layout.setSpacing(12)

        # 파일명 입력 (20%)
        self.filename_input = QLineEdit()
        self.filename_input.setPlaceholderText("파일명 검색...")
        self.filename_input.setFixedHeight(36)
        self.filename_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        main_fields_layout.addWidget(self.filename_input, 2)

        # 확장자 필터 콤보박스 (고정폭)
        self.extension_filter_combo = QComboBox()
        self.extension_filter_combo.addItems([
            "모든 파일",
            "이미지 파일", 
            "문서 파일",
            "사용자 정의"
        ])
        self.extension_filter_combo.setFixedHeight(20)
        self.extension_filter_combo.setFixedWidth(120)
        self.extension_filter_combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.extension_filter_combo.currentTextChanged.connect(self._on_extension_filter_changed)
        main_fields_layout.addWidget(self.extension_filter_combo)

        # 태그 입력 (30%)
        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("태그 검색 (예: 중요,문서|긴급)")
        self.tag_input.setFixedHeight(36)
        self.tag_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.tag_input.setToolTip("쉼표(,)는 AND, 파이프(|)는 OR, 별표(*)는 NOT 조건입니다.")
        main_fields_layout.addWidget(self.tag_input, 3)

        main_layout.addWidget(main_fields_container, 65)  # stretch=65로 65% 차지
        
        # 자동완성 설정
        self._tag_completer_model = QStringListModel()
        self._tag_completer = QCompleter(self._tag_completer_model, self.tag_input)
        self._tag_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self._tag_completer.setFilterMode(Qt.MatchContains)
        self._tag_completer.setCompletionMode(QCompleter.PopupCompletion)
        self._tag_completer.setMaxVisibleItems(6)  # 표시 항목 수 조정 (높이 제한)
        self._tag_completer.setWrapAround(False)
        
        # QCompleter 팝업 뷰의 높이 직접 설정
        popup = self._tag_completer.popup()
        popup.setMinimumHeight(200)  # 최소 높이 설정
        popup.setMaximumHeight(300)  # 최대 높이 설정
        
        self.tag_input.setCompleter(self._tag_completer)
        


        # 아이콘 버튼들을 별도 컨테이너에 배치하여 정렬 개선
        button_container = QWidget()
        button_container.setFixedHeight(40)  # QLineEdit의 실제 높이에 맞춤 (36 + 테두리 4px)
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 2, 0, 2)  # 상하 패딩 추가하여 버튼 중앙 정렬
        button_layout.setSpacing(8)

        # 검색 버튼 (정사각형, QLineEdit의 실제 높이에 맞춤)
        self.search_button = QPushButton()
        self.search_button.setIcon(QIcon("assets/icons/search.svg"))
        self.search_button.setFixedSize(36, 36)  # 정사각형 유지
        self.search_button.setToolTip("검색 실행")
        self.search_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # 크기 정책 고정
        self.search_button.setProperty("class", "search-button")  # CSS 클래스 설정
        button_layout.addWidget(self.search_button)

        # 초기화 버튼 (정사각형, QLineEdit의 실제 높이에 맞춤)
        self.clear_button = QPushButton()
        self.clear_button.setIcon(QIcon("assets/icons/close.svg"))
        self.clear_button.setFixedSize(36, 36)  # 정사각형 유지
        self.clear_button.setToolTip("검색 조건 초기화")
        self.clear_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # 크기 정책 고정
        self.clear_button.setProperty("class", "search-button")  # CSS 클래스 설정
        button_layout.addWidget(self.clear_button)

        # 고급 검색 토글 버튼 (정사각형, QLineEdit의 실제 높이에 맞춤)
        self.advanced_toggle = QPushButton()
        self.advanced_toggle.setIcon(QIcon("assets/icons/expand_more.svg"))
        self.advanced_toggle.setFixedSize(36, 36)  # 정사각형 유지
        self.advanced_toggle.setToolTip("고급 검색 옵션")
        self.advanced_toggle.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # 크기 정책 고정
        self.advanced_toggle.setProperty("class", "search-button")  # CSS 클래스 설정
        button_layout.addWidget(self.advanced_toggle)

        # 버튼 컨테이너 (고정 크기)
        button_container.setFixedWidth(135)  # 3개 버튼(36px) + 간격(8px*2) + 여유공간 = 135px

        main_layout.addWidget(button_container)

        # 결과 표시 영역 (반응형 - 나머지 공간 차지)
        result_container = QWidget()
        result_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        result_container.setFixedHeight(44)  # QLineEdit의 실제 높이에 맞춤 (36 + 테두리 4px)
        result_layout = QVBoxLayout(result_container)
        result_layout.setContentsMargins(0, 4, 0, 4)  # 상하 패딩 추가
        result_layout.setSpacing(2)

        self.result_count_label = QLabel("검색 결과")
        self.result_count_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.result_count_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        result_layout.addWidget(self.result_count_label)

        self.search_conditions_label = QLabel()
        self.search_conditions_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.search_conditions_label.setWordWrap(False)  # 줄바꿈 비활성화
        self.search_conditions_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.search_conditions_label.setProperty("class", "search-conditions")
        result_layout.addWidget(self.search_conditions_label)

        main_layout.addWidget(result_container, 35)  # stretch=35로 나머지 35% 차지

        # 고급 검색 패널 설정
        self.setup_advanced_panel()

    def setup_advanced_panel(self):
        """고급 검색 패널을 설정합니다."""
        self.advanced_panel = QWidget()
        self.advanced_panel.setVisible(False)
        
        advanced_layout = QHBoxLayout(self.advanced_panel)
        advanced_layout.setContentsMargins(16, 8, 16, 8)
        advanced_layout.setSpacing(12)

        # 고급 필드 컨테이너 (전체창 너비의 50% 차지)
        advanced_fields_container = QWidget()
        advanced_fields_container.setObjectName("advancedFieldsContainer")
        advanced_fields_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        advanced_fields_layout = QHBoxLayout(advanced_fields_container)
        advanced_fields_layout.setContentsMargins(0, 0, 0, 0)
        advanced_fields_layout.setSpacing(12)

        # 부분일치 파일명 입력 (메인과 동일한 비율: stretch=2)
        self.partial_filename_input = QLineEdit()
        self.partial_filename_input.setPlaceholderText("파일명 부분일치 검색...")
        self.partial_filename_input.setFixedHeight(36)
        self.partial_filename_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        advanced_fields_layout.addWidget(self.partial_filename_input, 2)

        # 부분일치 확장자 입력 (QLineEdit, 메인과 시각적으로 동일한 너비)
        self.partial_extensions_input = QLineEdit()
        self.partial_extensions_input.setPlaceholderText("확장자 부분일치 (예: jpg, png, pdf)")
        self.partial_extensions_input.setFixedHeight(36)  # 메인과 동일한 높이
        self.partial_extensions_input.setFixedWidth(120)  # 메인과 정확히 동일한 너비
        self.partial_extensions_input.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.partial_extensions_input.textChanged.connect(self._on_input_changed)
        advanced_fields_layout.addWidget(self.partial_extensions_input)

        # 부분일치 태그 입력 (메인과 동일한 비율: stretch=3)
        self.partial_tag_input = QLineEdit()
        self.partial_tag_input.setPlaceholderText("태그 부분일치 검색...")
        self.partial_tag_input.setFixedHeight(36)
        self.partial_tag_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        advanced_fields_layout.addWidget(self.partial_tag_input, 3)
        
        # 부분일치 검색 필드들에 자동완성 설정
        self._setup_partial_search_completers()

        advanced_layout.addWidget(advanced_fields_container, 65)  # stretch=65로 65% 차지

        # 부분일치 검색 옵션 영역 (메인의 버튼 + 검색결과 영역과 동일한 구조)
        # 버튼 컨테이너 (메인과 동일한 높이: 40px, 설명 라벨 포함)
        advanced_button_container = QWidget()
        advanced_button_container.setFixedHeight(40)  # 메인과 동일한 높이
        advanced_button_layout = QHBoxLayout(advanced_button_container)
        advanced_button_layout.setContentsMargins(0, 2, 0, 2)  # 메인과 동일한 마진
        advanced_button_layout.setSpacing(8)  # 메인과 동일한 간격

        # 부분일치 검색 설명 라벨
        partial_search_label = QLabel("부분일치 검색 (우선 적용)")
        partial_search_label.setStyleSheet("color: #666; font-size: 11px;")
        partial_search_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        advanced_button_layout.addWidget(partial_search_label)

        # 고급 버튼 컨테이너 (메인과 동일한 고정 크기)
        advanced_button_container.setFixedWidth(135)  # 메인과 동일한 고정 크기
        advanced_layout.addWidget(advanced_button_container)

        # 부분일치 검색 결과 영역 (메인과 동일한 구조, 비어있음)
        advanced_result_container = QWidget()
        advanced_result_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        advanced_result_container.setFixedHeight(44)  # 메인과 동일한 높이
        advanced_result_layout = QVBoxLayout(advanced_result_container)
        advanced_result_layout.setContentsMargins(0, 4, 0, 4)  # 메인과 동일한 패딩
        advanced_result_layout.setSpacing(2)

        advanced_layout.addWidget(advanced_result_container, 35)  # stretch=35로 나머지 35% 차지

    def setup_connections(self):
        """시그널-슬롯 연결"""
        # 검색 버튼 연결
        self.search_button.clicked.connect(self._on_search_requested)
        self.clear_button.clicked.connect(self.viewmodel.clear_search)
        self.advanced_toggle.clicked.connect(self._toggle_advanced_panel)
        
        # 입력 필드 연결 (디바운싱 적용)
        self.filename_input.textChanged.connect(self._on_input_changed)
        self.tag_input.textChanged.connect(self._on_input_changed)
        
        # 부분일치 검색 필드 연결 (디바운싱 적용)
        self.partial_filename_input.textChanged.connect(self._on_input_changed)
        self.partial_extensions_input.textChanged.connect(self._on_input_changed)
        self.partial_tag_input.textChanged.connect(self._on_input_changed)
        
        # 태그 입력 필드 포커스 이벤트 연결
        self.tag_input.focusInEvent = self._on_tag_input_focus_in
        
        # 부분일치 태그 입력 필드 포커스 이벤트 연결
        self.partial_tag_input.focusInEvent = self._on_partial_tag_input_focus_in
        
        # Enter 키 연결
        self.filename_input.returnPressed.connect(self._on_search_requested)
        self.tag_input.returnPressed.connect(self._on_tag_input_return_pressed)
        
        # 부분일치 검색 패널 Enter 키 연결
        self.partial_filename_input.returnPressed.connect(self._on_search_requested)
        self.partial_extensions_input.returnPressed.connect(self._on_search_requested)
        self.partial_tag_input.returnPressed.connect(self._on_search_requested)
        


    def _on_extension_filter_changed(self):
        """확장자 필터 콤보박스 변경 시 호출됩니다."""
        current_text = self.extension_filter_combo.currentText()
        self.custom_extension_input.setVisible(current_text == "사용자 정의")
        self._on_input_changed()

    def _get_extension_filter_extensions(self):
        """현재 선택된 확장자 필터에 해당하는 확장자 목록을 반환합니다."""
        current_text = self.extension_filter_combo.currentText()
        if current_text == "모든 파일":
            return []
        elif current_text == "이미지 파일":
            return [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".svg"]
        elif current_text == "문서 파일":
            return [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".xls", ".xlsx", ".ppt", ".pptx", ".md"]
        elif current_text == "사용자 정의":
            custom_text = self.custom_extension_input.text().strip()
            if custom_text:
                extensions = [ext.strip() for ext in custom_text.split(",")]
                extensions = [ext if ext.startswith(".") else f".{ext}" for ext in extensions if ext]
                return extensions
            return []
        return []

    def _on_input_changed(self):
        """입력 변경 시 디바운싱 적용"""
        self._debounce_timer.start(300)  # 300ms 디바운싱
        
    def _on_debounce_timeout(self):
        """디바운싱 타임아웃 시 실시간 검색"""
        if (self.filename_input.text().strip() or 
            self.tag_input.text().strip() or 
            self.extension_filter_combo.currentText() != "모든 파일" or
            self.partial_filename_input.text().strip() or
            self.partial_extensions_input.text().strip() or
            self.partial_tag_input.text().strip()):
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
        
        # 기본 검색 조건 (완전일치)
        basic_conditions = {}
        
        # 파일명 검색 조건
        filename = self.filename_input.text().strip()
        extension_filter_extensions = self._get_extension_filter_extensions()
        
        if filename or extension_filter_extensions:
            basic_conditions['filename'] = {
                'name': filename,
                'extensions': extension_filter_extensions
            }
            
        # 태그 검색 조건
        tag_query = self.tag_input.text().strip()
        if tag_query:
            basic_conditions['tags'] = {
                'query': tag_query
            }
            
        # 부분일치 검색 조건
        partial_conditions = {}
        
        # 고급 검색 패널이 보이거나 부분일치 검색 필드에 입력이 있으면 처리
        partial_filename = self.partial_filename_input.text().strip()
        partial_extensions = self.partial_extensions_input.text().strip()
        partial_tags = self.partial_tag_input.text().strip()
        
        if partial_filename or partial_extensions or partial_tags:
            # 파일명 부분일치 검색
            if partial_filename:
                partial_conditions['filename'] = {
                    'partial': partial_filename
                }
                
            # 확장자 부분일치 검색
            if partial_extensions:
                partial_conditions['extensions'] = {
                    'partial': [ext.strip() for ext in partial_extensions.split(',') if ext.strip()]
                }
                
            # 태그 부분일치 검색
            if partial_tags:
                partial_conditions['tags'] = {
                    'partial': [tag.strip() for tag in partial_tags.split(',') if tag.strip()]
                }
        
        # 우선순위 결정: 부분일치 검색이 있으면 우선 처리
        if partial_conditions:
            conditions['partial'] = partial_conditions
            # 부분일치 검색이 있을 때는 기본 검색 조건을 무시하고 사용자에게 알림
            if basic_conditions:
                self._show_search_mode_notification("부분일치 검색이 우선 적용됩니다.")
        else:
            # 부분일치 검색이 없으면 기본 검색 조건 사용
            conditions.update(basic_conditions)
                
        return conditions
        
    def set_search_conditions(self, conditions: dict):
        """검색 조건 설정"""
        # 파일명 검색 조건
        if 'filename' in conditions:
            filename_cond = conditions['filename']
            self.filename_input.setText(filename_cond.get('name', ''))
            extensions = filename_cond.get('extensions', [])
            # 기본 검색에는 확장자 입력 필드가 없으므로 무시
            

            
        # 태그 검색 조건
        if 'tags' in conditions:
            tag_cond = conditions['tags']
            self.tag_input.setText(tag_cond.get('query', ''))
            
        # 부분일치 검색 조건
        if 'partial' in conditions:
            partial_cond = conditions['partial']
            
            # 파일명 부분일치 검색
            if 'filename' in partial_cond:
                filename_partial = partial_cond['filename']
                self.partial_filename_input.setText(filename_partial.get('partial', ''))
                
            # 확장자 부분일치 검색
            if 'extensions' in partial_cond:
                extensions_partial = partial_cond['extensions']
                self.partial_extensions_input.setText(', '.join(extensions_partial.get('partial', [])))
                
            # 태그 부분일치 검색
            if 'tags' in partial_cond:
                tags_partial = partial_cond['tags']
                self.partial_tag_input.setText(', '.join(tags_partial.get('partial', [])))
                
    def clear_search(self):
        """검색 조건 초기화"""
        self.filename_input.clear()
        self.tag_input.clear()
        self.partial_filename_input.clear()
        self.partial_extensions_input.clear()
        self.extension_filter_combo.setCurrentText("모든 파일")
        self.custom_extension_input.clear()
        self.custom_extension_input.setVisible(False)
        self.partial_tag_input.clear()
        

        
        self.result_count_label.setText("검색 결과")
        self.search_conditions_label.clear()
        
    def update_search_results(self, count: int, conditions_summary: str = ""):
        """검색 결과 업데이트"""
        self.result_count_label.setText(f"{count}개 검색됨")
        
        # 사용자가 입력한 검색값들만 조건표시창에 표시
        display_conditions = []
        
        # 파일명 검색 조건
        filename = self.filename_input.text().strip()
        extension_filter = self.extension_filter_combo.currentText()
        
        if filename:
            display_conditions.append(f"파일명: '{filename}'")
        if extension_filter != "모든 파일":
            display_conditions.append(f"필터: {extension_filter}")
        

                
        # 태그 검색 조건
        tag_query = self.tag_input.text().strip()
        if tag_query:
            display_conditions.append(f"태그: '{tag_query}'")
                
        # 부분일치 검색 조건
        partial_filename = self.partial_filename_input.text().strip()
        partial_extensions = self.partial_extensions_input.text().strip()
        partial_tags = self.partial_tag_input.text().strip()
        
        if partial_filename or partial_extensions or partial_tags:
            if partial_filename:
                display_conditions.append(f"부분 파일명: '{partial_filename}'")
            if partial_extensions:
                display_conditions.append(f"부분 확장자: {partial_extensions}")
            if partial_tags:
                display_conditions.append(f"부분 태그: '{partial_tags}'")
                    
        if display_conditions:
            # 모든 조건을 하나의 줄로 표시
            combined_text = " | ".join(display_conditions)
            
            # 라벨의 너비에 맞춰 전체 텍스트를 말줄임표 처리
            max_width = 180  # 라벨의 고정 너비
            font_metrics = self.search_conditions_label.fontMetrics()
            
            # 텍스트가 너무 길면 말줄임표 처리
            if font_metrics.width(combined_text) > max_width:
                # 말줄임표를 포함한 최대 길이 계산
                ellipsis_width = font_metrics.width("...")
                available_width = max_width - ellipsis_width
                
                # 사용 가능한 너비에 맞는 텍스트 길이 계산
                truncated_text = ""
                for char in combined_text:
                    if font_metrics.width(truncated_text + char) <= available_width:
                        truncated_text += char
                    else:
                        break
                
                combined_text = truncated_text + "..."
            
            self.search_conditions_label.setText(combined_text)
        else:
            self.search_conditions_label.clear()

    def show_advanced_panel(self, show: bool):
        """고급 검색 패널 표시/숨김"""
        self.advanced_panel.setVisible(show)
        self.advanced_search_requested.emit({'show': show})

    def get_advanced_panel(self):
        """고급 검색 패널 위젯을 반환합니다."""
        return self.advanced_panel

    def _initialize_tag_completer(self):
        """태그 자동완성을 초기화합니다."""
        # 즉시 초기화 시도
        self._load_tag_completer_data()
        
        # 애플리케이션 시작 후 태그 데이터가 로드될 시간을 주고 다시 시도
        QTimer.singleShot(2000, self._load_tag_completer_data)
    
    def _load_tag_completer_data(self):
        """태그 자동완성 데이터를 로드합니다."""
        try:
            all_tags = self.viewmodel.get_all_tags()
            self._tag_completer_model.setStringList(all_tags)
        except Exception as e:
            # 자동완성 실패 시 빈 리스트로 설정
            self._tag_completer_model.setStringList([])
    
    def update_tag_completer(self, tags: list):
        """태그 자동완성 목록을 업데이트합니다."""
        self._tag_completer_model.setStringList(tags)
        # 부분일치 검색의 태그 자동완성도 함께 업데이트
        if hasattr(self, '_partial_tag_completer_model'):
            self._partial_tag_completer_model.setStringList(tags)
    
    def _on_tag_input_focus_in(self, event):
        """태그 입력 필드에 포커스가 들어올 때 호출됩니다."""
        # 원래 focusInEvent를 먼저 호출하여 기본 동작(커서 깜빡임 등) 보장
        QLineEdit.focusInEvent(self.tag_input, event)
        # 포커스 인 시 자동완성 데이터 다시 로드
        self._load_tag_completer_data()
    
    def _on_tag_input_return_pressed(self):
        """태그 입력 필드에서 엔터 키가 눌렸을 때 호출됩니다."""
        # 자동완성 팝업이 열려있고 선택된 항목이 있으면 검색하지 않음
        if self._tag_completer.popup().isVisible():
            return
        
        # 자동완성 팝업이 닫혀있을 때만 검색 실행
        self._on_search_requested()
    
    def _on_partial_tag_input_focus_in(self, event):
        """부분일치 태그 입력 필드에 포커스가 들어올 때 호출됩니다."""
        # 원래 focusInEvent를 먼저 호출하여 기본 동작(커서 깜빡임 등) 보장
        QLineEdit.focusInEvent(self.partial_tag_input, event)
        # 포커스 인 시 자동완성 데이터 다시 로드
        self._load_tag_completer_data()
    
    def _show_search_mode_notification(self, message: str):
        """검색 모드 알림을 표시합니다."""
        # 상태바나 알림 영역에 메시지 표시
        # 현재는 간단히 print로 출력 (나중에 UI 알림으로 개선 가능)
        print(f"검색 알림: {message}")
    
    def _setup_partial_search_completers(self):
        """부분일치 검색 필드들에 자동완성을 설정합니다."""
        # 태그 부분일치 자동완성
        self._partial_tag_completer_model = QStringListModel()
        self._partial_tag_completer = QCompleter(self._partial_tag_completer_model, self.partial_tag_input)
        self._partial_tag_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self._partial_tag_completer.setFilterMode(Qt.MatchContains)
        self._partial_tag_completer.setCompletionMode(QCompleter.PopupCompletion)
        self._partial_tag_completer.setMaxVisibleItems(6)
        self._partial_tag_completer.setWrapAround(False)
        
        # QCompleter 팝업 뷰의 높이 설정
        partial_popup = self._partial_tag_completer.popup()
        partial_popup.setMinimumHeight(200)
        partial_popup.setMaximumHeight(300)
        
        self.partial_tag_input.setCompleter(self._partial_tag_completer)
        
        # 확장자 부분일치 자동완성
        common_extensions = [
            "jpg", "jpeg", "png", "gif", "bmp", "tiff", "svg",
            "pdf", "doc", "docx", "txt", "rtf", "odt", "xls", "xlsx", "ppt", "pptx", "md",
            "mp3", "mp4", "avi", "mov", "wmv", "flv", "mkv",
            "zip", "rar", "7z", "tar", "gz"
        ]
        self._partial_extension_completer_model = QStringListModel(common_extensions)
        self._partial_extension_completer = QCompleter(self._partial_extension_completer_model, self.partial_extensions_input)
        self._partial_extension_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self._partial_extension_completer.setFilterMode(Qt.MatchContains)
        self._partial_extension_completer.setCompletionMode(QCompleter.PopupCompletion)
        self._partial_extension_completer.setMaxVisibleItems(8)
        
        partial_ext_popup = self._partial_extension_completer.popup()
        partial_ext_popup.setMinimumHeight(200)
        partial_ext_popup.setMaximumHeight(300)
        
        self.partial_extensions_input.setCompleter(self._partial_extension_completer) 