# 개발팀 내부 기록 (Development Notes)

## 2025년 7월 14일

### DRS-20250711-010 Phase 1-A, 1-B, 1-C 완료 (아키텍처 리팩터링)

#### 배경
- PM에서 Clean Architecture + MVVM 도입을 위한 DRS-20250711-010 승인
- Phase 1 아키텍처 리팩터링의 1-A, 1-B, 1-C 단계 완료 확인

#### Phase 1-A: MainWindow 분리 우선
- **목표**: MainWindow의 책임 분리 및 Adapter 패턴 도입
- **진행 상황**:
    - `main_window.py`에서 `UISetupManager`, `SignalConnectionManager`, `DataLoadingManager`를 사용하여 UI 설정, 시그널 연결, 초기 데이터 로딩 로직 분리 완료.
    - `core/ui/ui_setup_manager.py`, `core/ui/signal_connection_manager.py`, `core/ui/data_loading_manager.py` 파일들이 DRS에 명시된 역할을 수행하며 존재함.
    - `core/adapters/tag_manager_adapter.py` 파일이 존재하며 `TagService`를 사용하는 어댑터 역할을 수행함.
- **결론**: 완료

#### Phase 1-B: Service/Repository 계층 구축
- **목표**: 비즈니스 로직과 데이터 접근 로직 분리
- **진행 상황**:
    - `core/services/tag_service.py` 파일이 존재하며 `TagRepository`와 `EventBus`를 주입받아 비즈니스 로직을 수행함.
    - `core/repositories/tag_repository.py` 파일이 존재하며 `MongoClient`를 주입받아 MongoDB I/O 작업을 수행함.
- **결론**: 완료

#### Phase 1-C: ViewModel 구축 및 위젯 리팩터링
- **목표**: UI와 비즈니스 로직 간의 중재자 역할 수행 및 위젯의 ViewModel 사용 전환
- **진행 상황**:
    - `viewmodels/tag_control_viewmodel.py` 파일이 존재하며 `TagService`와 `EventBus`를 주입받아 UI와 비즈니스 로직 사이의 중재자 역할을 수행함.
    - `widgets/tag_control_widget.py`가 `TagControlViewModel`을 주입받아 사용하고 있으며, ViewModel의 시그널을 구독하고 ViewModel의 메서드를 호출하여 UI와 비즈니스 로직을 분리함.
- **결론**: 완료

#### 다음 단계
- DRS-20250711-010의 다음 Phase 진행 (Phase 2-6) 또는 추가적인 리팩터링 및 기능 개발.

## 2025년 7월 13일

### DRS-20250711-010 Phase 0 분석 완료 (아키텍처 리팩터링)

#### 배경
- PM에서 Clean Architecture + MVVM 도입을 위한 DRS-20250711-010 승인
- Phase 1 아키텍처 리팩터링 시작 전 사전 분석 수행
- 현재 코드 구조 완전 분석 및 위험도 평가 완료

#### 주요 분석 결과
1. **Signal/Slot 연결 매핑**: MainWindow에서 12개 시그널 연결 구조 분석
2. **순환 의존성 검토**: ✅ 순환 의존성 없음 확인 (안전한 리팩터링 환경)
3. **위험도 평가**: MainWindow(293라인), TagControlWidget(409라인) 높은 위험도 식별
4. **데이터 흐름 분석**: 위젯 간 명확한 단방향 데이터 흐름 확인

#### 기술적 결정사항
- **Signal/Slot 방식**: 기존 PyQt Signal 유지 + 타입 안전한 이벤트 추가
- **MongoDB 연결**: 기존 방식 유지 (Connection Pool은 Phase 2 이후)
- **마이그레이션 순서**: MainWindow 분리 → Service/Repository → ViewModel

#### 위험 완화 조치
- 각 Phase별 롤백 조건 설정
- 단계적 테스트 커버리지 목표 (50% → 70% → 80%)
- 브랜치 전략 수립 (feat/phase0-analysis → feat/phase1a-mainwindow-split)

#### 다음 단계
- Phase 1-A: MainWindow 분리 (UISetupManager, SignalConnectionManager, DataLoadingManager)
- 상세 분석 결과: `docs/developer_guide/architecture_refactoring/phase0_analysis_report.md`

## 2025년 7월 13일

### 일괄태깅 기능 개선 (공통 태그 표시)

#### 문제점
- 여러 파일을 선택하여 일괄태깅할 때 기존 파일들의 태그가 UI에 표시되지 않음
- 사용자가 새 태그만 입력하면 기존 태그가 사라질 것으로 오해할 수 있음
- 실제로는 `add_tags_to_files()` 메서드가 기존 태그에 추가하지만, UI에서 명확하지 않음

#### 해결 방안
1. **공통 태그 표시 기능 추가**
   - `_get_common_tags_for_files()` 메서드 구현
   - 선택된 파일들의 교집합 태그를 계산하여 표시
   - 모든 파일에 공통으로 있는 태그만 표시

2. **UI 개선**
   - 일괄태깅 탭의 대상 라벨에 공통 태그 개수 표시
   - "선택된 파일: 3개 (공통 태그: 2개)" 형태로 정보 제공
   - 공통 태그가 없는 경우 "공통 태그 없음" 표시

#### 구현 세부사항
```python
def _get_common_tags_for_files(self, file_paths):
    """선택된 파일들의 공통 태그를 찾아 반환"""
    if not file_paths:
        return []
    
    # 첫 번째 파일의 태그를 기준으로 시작
    common_tags = set(self.tag_manager.get_tags_for_file(file_paths[0]))
    
    # 나머지 파일들과 교집합 계산
    for file_path in file_paths[1:]:
        file_tags = set(self.tag_manager.get_tags_for_file(file_path))
        common_tags = common_tags.intersection(file_tags)
    
    return list(common_tags)
```

#### 변경된 파일
- `widgets/tag_control_widget.py`: 공통 태그 표시 기능 추가

#### 테스트 결과
- 기본 태그 관리 기능은 정상 동작
- 일부 디렉토리 일괄태깅 테스트에서 `UpdateOne` 관련 오류 발생 (별도 수정 필요)

#### 향후 개선사항
1. 공통 태그가 아닌 개별 파일 태그도 표시할 수 있는 옵션 추가
2. 태그 적용 시 "추가" vs "덮어쓰기" 모드 선택 기능
3. 일괄태깅 시 미리보기 기능 추가

## 2025년 7월 12일

### 태그 관리/일괄삭제/동기화 UI/UX 개선 및 코드 정비

- 태그 저장 버튼(개별 태깅 패널) 완전 제거: 태그 입력/엔터/목록/퀵태그 클릭 시 즉시 저장 및 UI 반영.
- 파일 상세 정보 패널의 '모든 태그 삭제' 버튼 완전 제거: 태그칩(x) 또는 일괄삭제 다이얼로그만 사용.
- TagControlWidget <-> FileDetailWidget 태그칩 동기화: 태그 변경 시 양방향 시그널 구조로 항상 최신 상태 유지.
- 일괄삭제 다이얼로그 내 TagChip x버튼 클릭 시, 선택 파일 전체에서 해당 태그 즉시 삭제 및 UI 반영.
- DRS/기능명세/이슈 문서에 따라 관련 내용 업데이트 및 완료 처리.

### 태그 기반 검색 1단계 구현 결과 및 DRS 요구사항 비교

#### 1. 1단계 구현 범위 및 완료 여부 점검
- **1단계 목표:**
    - 기존 DirectoryTreeWidget의 분산된 검색 입력란(파일명, 태그, 확장자) → SearchWidget으로 통합
    - MainWindow에 통합 검색 툴바(SearchWidget) 추가 및 시그널 연결
    - 단일 태그 검색 및 태그 자동완성 기능 구현
    - 기본 검색 결과 표시(파일 목록, 개수, 조건 요약)
    - UI/UX 일관성 확보(툴바, 고급 검색 패널 구조)
- **실제 구현 내용:**
    - SearchWidget에 파일명, 확장자, 태그 입력란 및 검색/초기화/고급검색 버튼 구현
    - MainWindow에 QVBoxLayout 구조로 툴바-고급검색-메인 splitter 배치
    - 태그 입력란(QLineEdit)에 QCompleter 기반 자동완성 구현(포커스 시 전체 태그, 입력 시 필터링, 최대 5개)
    - 태그 자동완성은 TagManager에서 직접 태그 목록을 받아와 항상 최신 상태 유지
    - 검색 실행 시 파일 목록, 결과 개수, 조건 요약 표시
    - 고급 검색 패널 UI/레이아웃 개선(입력란 높이, spacing 등)
    - 검색 히스토리/드롭다운 기능은 1단계에서 제외(추후 별도 브라우저 창에서 구현 예정)
- **미완료/보류 사항:**
    - SearchManager, SearchHistory 등 별도 검색 로직/DB 연동 구조는 2단계 이후로 이관
    - 복합 검색(AND/OR/NOT), 고급 검색 패널의 실제 검색 로직은 2단계에서 본격 구현 예정
    - 검색 결과 하이라이트, 실시간 검색, 성능 최적화 등은 2~3단계에서 추가 예정

#### 2. DRS-20250711-009 요구사항과의 비교 및 변경점
- **DRS 주요 요구사항:**
    - 단일 태그 검색, 태그 자동완성, 대소문자 구분 없는 검색
    - 복합(AND/OR/NOT) 검색, 고급 검색 패널, 검색 결과 표시/개수/조건 요약
    - 검색 히스토리(최근 검색어, 즐겨찾기)
    - 성능(500ms/1초/300ms), 실시간 검색, 하이라이트 등
- **실제 구현/변경점:**
    - [완료] 단일 태그 검색, 태그 자동완성(QCompleter, 5개 제한, 실시간 갱신)
    - [완료] UI 구조(툴바, 고급 검색 패널, 결과 표시 등)
    - [보류] 복합 검색(AND/OR/NOT), 고급 검색 패널의 실제 검색 로직(2단계 예정)
    - [보류] 검색 히스토리/즐겨찾기(별도 브라우저 창에서 구현, 3단계 예정)
    - [보류] 실시간 검색, 성능 최적화, 결과 하이라이트(2~3단계 예정)
    - [변경] 검색 히스토리 버튼/로직은 1단계에서 제거, UI 단순화

#### 3. 추가 논의/결정 사항
- 태그 자동완성은 parent/window 의존성 제거, tag_manager 직접 주입 방식으로 구조 개선
- 고급 검색 패널의 입력란 높이, spacing 등 UI/UX 개선
- 일괄 태그 삭제 버튼 미동작 이슈 docs/issues.md에 사전 등록
- 1단계 범위 내에서 DRS 요구사항의 핵심(통합 검색 UI, 단일 태그 검색, 자동완성, 결과 표시)은 모두 충족
- 2단계부터 복합 검색, 고급 검색, 성능/UX 고도화, 히스토리 등 확장 예정

## 2025년 7월 11일

### DRS-20250711-009 태그 기반 검색 기능 개발 시작

#### **코드베이스 검토 결과**
- **현재 검색 관련 기능 현황**:
  - `DirectoryTreeWidget`에 분산된 검색 기능들:
    - `global_file_search_input`: 전역 파일 검색
    - `tag_search_input`: 태그 검색 (단순 필터링)
    - `extensions_input`: 확장자 필터링
  - `MainWindow`의 검색 처리:
    - `on_global_file_search_requested()`: 전역 파일 검색 처리
    - `FileListWidget`의 `set_search_results()`: 검색 결과 표시
  - `FileListWidget`의 검색 모드:
    - `_is_search_mode`: 검색 모드와 디렉토리 모드 구분
    - `set_search_results()`: 검색 결과 설정
    - `set_tag_filter()`: 태그 필터링

#### **DRS 변경사항과의 호환성 분석**
- **긍정적 측면**:
  - `TagManager`의 `get_files_by_tag()` 메서드 활용 가능
  - `FileListWidget`의 검색 모드 구조 재사용 가능
  - MongoDB 연결 및 태그 관리 시스템 그대로 활용
  - 기존 3분할 레이아웃 유지하면서 검색 툴바 추가 가능

- **주요 변경 필요사항**:
  1. **UI 구조 대폭 변경**: 분산된 검색 기능들을 통합 검색 툴바로 통합
  2. **검색 로직 확장**: 단순 필터링에서 복합 검색(AND/OR/NOT)으로 확장
  3. **새로운 컴포넌트 필요**: `SearchWidget`, `SearchManager`, `SearchHistory`, `AdvancedSearchPanel`

#### **단계별 개발 계획**

**1단계: 기존 기능 마이그레이션 (1-2주)**
- `DirectoryTreeWidget`에서 제거할 요소들:
  - `global_file_search_input` → `SearchWidget`로 이동
  - `tag_search_input` → `SearchWidget`로 이동  
  - `extensions_input` → `SearchWidget` 파일명 영역으로 이동
- 유지할 요소들:
  - `show_files_checkbox` (체크박스 형태로 유지)
  - `recursive_checkbox` (체크박스 형태로 유지)
  - 파일 시스템 트리 뷰
  - 컨텍스트 메뉴 기능

**2단계: 통합 검색 툴바 구현 (2-3주)**
- `SearchWidget` 클래스 구현:
  - 파일명 검색 영역 (25%)
  - 태그 검색 영역 (25%)
  - 검색 제어 버튼들
  - 검색 결과 표시 (우측)
- `MainWindow`에 통합 검색 툴바 추가

**3단계: 검색 로직 확장 (2-3주)**
- `SearchManager` 클래스 구현:
  - 복합 검색 조건 처리
  - 검색 쿼리 파싱 로직
  - MongoDB 인덱스 최적화
- `SearchHistory` 클래스 구현

**4단계: 고급 기능 (1-2주)**
- 고급 검색 패널 구현
- 검색 히스토리 UI
- 성능 최적화
- 실시간 검색

#### **기술적 고려사항**
- **기존 코드와의 호환성**: `MainWindow`의 시그널 연결 구조 변경 필요
- **성능 최적화**: MongoDB 인덱스 추가, 검색 결과 캐싱, 디바운싱 구현
- **UI/UX 일관성**: 기존 PyQt5 스타일 가이드라인 준수, 키보드 단축키 구현

#### **개발 시작**
- **현재 상태**: DRS 검토 완료, 개발 계획 수립 완료
- **다음 단계**: 1단계 기존 기능 마이그레이션 시작
- **예상 완료일**: 2025년 8월 말 (총 8-10주)

---

### PDF 미리보기 기능 구현 완료
- **목표**: PDF 파일에 대한 미리보기 기능 추가.
- **구현 내용**:
    - `widgets/file_detail_widget.py` 수정:
        - `fitz` (PyMuPDF) 라이브러리 임포트.
        - `PDF_EXTENSIONS` 및 `MAX_PDF_PAGES_TO_PREVIEW` 상수 정의.
        - `setup_ui`에 PDF 미리보기를 위한 `pdf_preview_label` 및 관련 레이아웃 추가.
        - `update_preview` 메서드에서 PDF 파일 감지 시 `_render_pdf_thumbnail` 호출.
        - `_render_pdf_thumbnail` 메서드 구현: PDF 페이지를 이미지로 렌더링하여 `pdf_preview_label`에 표시 (최대 페이지 수 제한).
        - `PyQt5.QtGui`에서 `QImage` 임포트 추가.
- **개선점**: 현재는 PDF의 첫 페이지만 렌더링하여 표시하고 있음. 향후 여러 페이지를 스크롤하여 볼 수 있는 기능 또는 페이지 이동 기능 추가 고려.

### 로컬 파일 서버 제거
- **목표**: 더 이상 사용되지 않는 로컬 파일 서버 관련 코드 및 파일을 제거하여 애플리케이션을 간소화하고 불필요한 리소스 사용을 줄임.
- **구현 내용**:
    - `main.py`에서 `LocalFileServer` import 문 및 인스턴스 생성/시작/중지 관련 코드를 제거.
    - `core/local_server.py` 파일을 삭제.
- **기대 효과**: 애플리케이션 시작 시 불필요한 서버 시작 방지 및 종료 시 관련 로그 제거. 코드베이스 정리 및 유지보수성 향상.

### DRS 구현 완료 및 디버그 로그 제거 (DRS-20250711-001: 디렉토리 뷰에 파일 표시)
- **DRS ID**: `DRS-20250711-001_display_files_in_directory_view.md`
- **목표**: 디렉토리 뷰(좌측 트리 뷰)에 폴더와 함께 파일을 표시하여 사용성을 향상시키고, 워크스페이스(루트) 선택 기능을 추가하며, UI 레이아웃을 조정.
- **구현 내용**:
    - `widgets/directory_tree_widget.py` 수정:
        - 디렉토리 뷰에 파일 표시 기능 추가 (`QFileSystemModel` 필터링 로직 변경).
        - "디렉토리 뷰에 파일 표시" 체크박스 추가 및 `extensions_input` 필드 위치 조정.
        - 워크스페이스(루트) 선택 기능 활성화.
    - `main_window.py` 수정:
        - `on_directory_selected` 함수 로직을 업데이트하여 디렉토리 트리에서 파일/디렉토리 선택 시 중앙 파일 목록 및 상세 정보가 올바르게 업데이트되도록 함.
        - `_on_directory_tree_filter_options_changed` 함수를 추가하여 `directory_tree.filter_options_changed` 시그널을 처리.
    - `widgets/file_list_widget.py` 수정:
        - `index_from_path` 메서드를 추가하여 파일 경로로부터 `QModelIndex`를 얻을 수 있도록 함.
- **디버그 로그 제거**: `widgets/file_list_widget.py`에 있던 디버깅 로그 (`DEBUG: selectionChanged signal emitted...`)를 제거하여 코드 정리.
- **검토 결과**: 기능 요구사항이 모두 구현되었으며, 성능 측면의 고려사항은 향후 최적화 단계에서 추가 검토 예정.

### 동영상 섬네일 표시 오류 수정 및 개선점
- **목표**: 동영상 섬네일 영역에 동영상이 표시되지 않는 오류 해결 및 관련 기능 개선점 도출.
- **해결**: `widgets/file_detail_widget.py`에서 `video_page_layout.addStretch(1)`을 제거하여 `QVideoWidget`이 공간을 제대로 확보하도록 수정.
- **개선점**:
    - 동영상 재생 시 `QVideoWidget`이 충분한 공간을 확보하도록 크기 정책 명시적 설정 고려.
    - 동영상 재생 컨트롤 (재생/일시정지, 정지, 볼륨, 진행률 슬라이더)의 UI/UX 개선.
    - 동영상 로딩 속도 최적화 및 대용량 파일 처리 방안 마련.

## 2025년 7월 10일

### 미해결 이슈 해결 (이슈 5, 6, 7, 8)
- **목표**: `dev_notes.md`에 기록된 미해결 이슈 4건을 모두 해결하여 애플리케이션의 안정성을 확보.

- **이슈 5: 파일 상세 탭에서 태그 삭제 미동작 (해결 완료)**
    - **원인**: `FileDetailWidget`에서 `TagChip`의 `tag_removed` 시그널을 사용하지 않고, 내부 `delete_button`의 `clicked` 시그널에 직접 연결하여 `TagChip`의 캡슐화를 위반하고 있었음.
    - **해결**: `file_detail_widget.py`의 `_refresh_tag_chips` 메서드에서 `chip.tag_removed.connect(self._on_tag_chip_removed)`를 사용하도록 수정하여 `TagChip`의 `tag_removed` 시그널을 정상적으로 처리하도록 변경.

- **이슈 6: 태그 저장 시 파일 목록 사라짐 (해결 완료)**
    - **원인**: `main_window.py`의 `on_tags_updated` 메서드에서 `self.file_list.refresh_tags_for_current_files()`를 호출하여 파일 목록을 새로고침하는 방식이 선택 상태 및 스크롤 위치를 초기화하는 문제 발생.
    - **해결**: `self.file_list.refresh_tags_for_current_files()` 대신 `self.file_list.model.layoutChanged.emit()`를 호출하여 뷰만 강제로 다시 그리도록 수정. 이로써 선택 상태와 스크롤 위치를 유지하면서 태그 정보만 업데이트.

- **이슈 7: 일괄 태그 제거 기능 미동작 (컨텍스트 메뉴) (해결 완료)**
    - **원인**: `main_window.py`의 `setup_connections` 메서드에서 `directory_tree.directory_context_menu_requested` 시그널과 `on_directory_tree_context_menu` 슬롯의 연결이 누락되어 있었음.
    - **해결**: `setup_connections` 메서드에 `self.directory_tree.directory_context_menu_requested.connect(self.on_directory_tree_context_menu)` 코드를 추가하여 시그널-슬롯 연결.

- **이슈 8: 일괄 태그 제거 기능 미동작 (버튼) (해결 완료)**
    - **원인**: `TagControlWidget`의 `connect_signals` 메서드에서 `batch_remove_tags_button`의 `clicked` 시그널과 `_on_batch_remove_tags_clicked` 슬롯의 연결이 누락되어 있었음.
    - **해결**: `connect_signals` 메서드에 `self.batch_remove_tags_button.clicked.connect(self._on_batch_remove_tags_clicked)` 코드를 추가하여 시그널-슬롯 연결.

- **추가 조치: 파일 상세 정보 태그 삭제 시 파일 목록 즉시 반영**
    - **요구사항**: 파일 상세 정보(`FileDetailWidget`)에서 태그 삭제 시, 변경 사항이 파일 목록(`FileListWidget`)에 즉시 반영되어야 함.
    - **해결**: `main_window.py`의 `setup_connections` 메서드에 `self.file_detail.file_tags_changed.connect(self.on_tags_updated)` 코드를 추가하여, `FileDetailWidget`의 `file_tags_changed` 시그널을 `on_tags_updated` 슬롯에 연결. 이로써 데이터 변경 시 UI가 일관성 있게 업데이트됨.

## 2025년 7월 8일

### DRS 검토 결과 (태그 관리 기능 강화)
- **DRS-20250708-003_Tag_Management_Enhancements.md**:
    - **목표**: 태그 삭제 일관성 확보 및 커스텀 태그 버튼 기능 도입.
    - **최종 결정 사항 (기획팀 협의)**:
        1.  **태그 삭제 기능 구현**:
            - `core/tag_manager.py`에 `remove_tags_from_file`, `clear_all_tags_from_file`, `remove_tags_from_files` 메서드 추가.
            - `widgets/tag_chip.py`에 삭제 버튼 추가 및 기능 연동 (팝업 없이 즉시 삭제).
            - `widgets/file_detail_widget.py`에 모든 태그 삭제 버튼 추가 및 기능 연동 (팝업 없이 즉시 삭제).
            - **일괄 태그 제거 UI**: 디렉토리 뷰의 디렉토리 우클릭 컨텍스트 메뉴와 일괄 태그 탭 내부의 버튼을 통해 독립적인 다이얼로그로 진입.
        2.  **커스텀 태그 관리 기능 구현**:
            - **커스텀 태그 영속성**: 별도의 JSON 파일을 통해 저장/로드.
            - `TagManager` 또는 별도의 클래스에 `save_custom_quick_tags` 및 `load_custom_quick_tags` 메서드 추가.
            - **커스텀 태그 관리 UI 진입점**: 메인 윈도우 메뉴바를 통해서만 진입.
            - 커스텀 태그를 편집할 수 있는 새로운 다이얼로그/패널 구현 (세부 사항은 개발 중 논의).
            - `QuickTagsWidget`이 이 커스텀 태그 목록을 로드하고 표시하도록 수정.

### 개발 진행 상황 (2025년 7월 8일)
- **태그 삭제 백엔드 로직 구현 완료**:
    - `core/tag_manager.py`에 `remove_tags_from_file`, `clear_all_tags_from_file`, `remove_tags_from_files` 메서드 추가.
    - `core/tag_manager.py`에 `get_files_in_directory` 공개 메서드 추가.
- **커스텀 태그 저장/로드 로직 구현 완료**:
    - `config.py`에 `CUSTOM_TAGS_FILE` 경로 추가.
    - `core/custom_tag_manager.py` 파일 생성 및 `CustomTagManager` 클래스 구현 (JSON 파일 기반).
- **개별 태그 삭제 UI 구현 완료**:
    - `widgets/tag_chip.py`에 `tag_removed` 시그널 추가 및 `_on_delete_button_clicked` 메서드 구현.
    - `ui/file_detail_content_widget.ui`에 '모든 태그 삭제' 버튼 추가.
    - `widgets/file_detail_widget.py`에 `_on_clear_all_tags_clicked` 및 `_on_tag_chip_removed` 메서드 구현, `file_tags_changed` 시그널 추가.
- **커스텀 태그 관리 UI 구현 완료**:
    - `ui/main_window.ui`에 '빠른 태그 관리' 메뉴 항목 추가.
    - `ui/custom_tag_dialog.ui` 파일 생성.
    - `widgets/custom_tag_dialog.py` 파일 생성 및 `CustomTagDialog` 클래스 구현.
    - `main_window.py`에 `CustomTagManager` 및 `CustomTagDialog` 임포트, `open_custom_tag_dialog` 메서드 구현 및 메뉴 연결.
    - `widgets/quick_tags_widget.py`가 `CustomTagManager`를 통해 태그를 로드하도록 수정.
    - `widgets/tag_control_widget.py`에서 `QuickTagsWidget` 초기화 시 `CustomTagManager` 인스턴스 전달.
- **일괄 태그 제거 기능 UI 구현 완료**:
    - `ui/batch_remove_tags_dialog.ui` 파일 생성.
    - `widgets/batch_remove_tags_dialog.py` 파일 생성 및 `BatchRemoveTagsDialog` 클래스 구현.
    - `widgets/directory_tree_widget.py`에 `directory_context_menu_requested` 시그널 추가 및 컨텍스트 메뉴 로직 구현.
    - `main_window.py`에 `on_directory_tree_context_menu` 메서드 구현 및 `_open_batch_remove_tags_dialog` 호출.
    - `ui/tag_control_widget.ui`에 '일괄 태그 제거' 버튼 추가.
    - `widgets/tag_control_widget.py`에 `_on_batch_remove_tags_clicked` 메서드 구현 및 `BatchRemoveTagsDialog` 호출.

### 발생한 이슈 및 해결 (2025년 7월 8일)
- **이슈 1: `AttributeError: 'MainWindow' object has no attribute 'custom_tag_manager'`**
    - **원인**: `MainWindow`의 `__init__` 메서드에서 `self.custom_tag_manager`가 `self.tag_control`에 전달되기 전에 초기화되지 않아 발생.
    - **해결**: `main_window.py`에서 `self.custom_tag_manager = CustomTagManager()` 초기화 순서를 `self.tag_control` 생성보다 앞으로 이동하여 해결.
- **이슈 2: `TypeError: QWidget(parent: Optional[QWidget] = None, flags: Union[Qt.WindowFlags, Qt.WindowType] = Qt.WindowFlags()): argument 1 has unexpected type 'CustomTagManager'`**
    - **원인**: `widgets/tag_control_widget.py`에서 `QuickTagsWidget`을 초기화할 때 `CustomTagManager` 객체가 `parent` 인자로 잘못 전달되었기 때문에 발생.
    - **해결**: `widgets/tag_control_widget.py`에서 `QuickTagsWidget` 생성 시 `CustomTagManager` 인스턴스를 첫 번째 인자로, `self` (부모 위젯)를 두 번째 인자로 명시적으로 전달하도록 수정.
- **이슈 3: `AttributeError: 'TagControlWidget' object has no attribute 'custom_tag_manager'` (재발)**
    - **원인**: `widgets/tag_control_widget.py`의 `__init__` 메서드에 `self.custom_tag_manager = custom_tag_manager` 할당 라인이 누락되어 발생.
    - **해결**: `widgets/tag_control_widget.py`의 `__init__` 메서드에 `self.custom_tag_manager = custom_tag_manager` 할당을 추가하여 해결.
- **이슈 4: `AttributeError: 'TagControlWidget' object has no attribute 'quick_tags_widget'`**
    - **원인**: `main_window.py`에서 `self.tag_control.quick_tags_widget.load_quick_tags()`를 호출할 때, `TagControlWidget` 내에 `quick_tags_widget`이라는 직접적인 속성이 없었기 때문. `individual_quick_tags`와 `batch_quick_tags` 두 개의 인스턴스가 존재.
    - **해결**: `main_window.py`의 `open_custom_tag_dialog` 메서드에서 `self.tag_control.individual_quick_tags.load_quick_tags()`와 `self.tag_control.batch_quick_tags.load_quick_tags()`를 모두 호출하도록 수정.

### 현재 미해결 이슈 (2025년 7월 8일)
- **이슈 5: 파일 상세 탭에서 태그 삭제 미동작**
    - **증상**: 개별 태그 칩의 'X' 버튼 및 '모든 태그 삭제' 버튼이 파일 상세 탭에서 동작하지 않음. (개별 태깅 탭에서는 'X' 버튼 동작 확인됨)
    - **진단**: `widgets/file_detail_widget.py`의 `_on_tag_chip_removed` 및 `_on_clear_all_tags_clicked` 메서드 호출 여부 및 `tag_manager`의 태그 삭제 메서드 성공 여부 확인 필요. `FileDetailWidget`의 `current_file_path` 값 확인 필요.
- **이슈 6: 태그 저장 시 파일 목록 사라짐**
    - **증상**: 태그를 저장한 후 파일 목록이 사라지거나 초기화됨.
    - **진단**: `main_window.py`의 `on_tags_updated` 메서드에서 파일 목록을 새로고침하는 방식(`self.file_list.set_path(current_path)`)이 문제의 원인으로 추정됨. 기존 선택 상태나 스크롤 위치를 잃게 만듦.
- **이슈 7: 일괄 태그 제거 기능 미동작 (컨텍스트 메뉴)**
    - **증상**: 디렉토리 뷰에서 디렉토리를 우클릭했을 때 '일괄 태그 제거...' 컨텍스트 메뉴가 나타나지 않음.
    - **진단**: `widgets/directory_tree_widget.py`의 컨텍스트 메뉴 관련 설정 및 `main_window.py`의 시그널 연결 확인 필요.
- **이슈 8: 일괄 태그 제거 기능 미동작 (버튼)**
    - **증상**: 일괄 태깅 탭 내의 '일괄 태그 제거' 버튼 클릭 시 다이얼로그가 나타나지 않음.
    - **진단**: `widgets/tag_control_widget.py`의 `_on_batch_remove_tags_clicked` 메서드 호출 여부 및 `BatchRemoveTagsDialog` 생성 및 실행 로직 확인 필요.

---

### DRS 검토 결과 (일괄/멀티 태깅)
- **DRS-20250704-001_Batch_Tagging_Feature.md (일괄 태깅 기능)**:
    - 대부분의 기능 및 비기능 요구사항이 충족됨.
    - UI/UX 설계 부분에서 일부 개선의 여지 있음:
        - 메뉴바를 통해 일괄 태깅 모드 진입 시, 사용자가 직접 대상 디렉토리를 선택하는 기능 부재.
        - 일괄 태깅 작업 완료 후 패널이 사라지는 기능 부재 (현재는 탭 전환 방식).
- **DRS-20250705-002_Tagging_UI_UX_Integration.md (UI/UX 통합)**:
    - 이 DRS의 주요 목표인 UI/UX 통합 아키텍처 변경 계획은 복잡성 증가로 인해 취소되었으므로, 해당 요구사항은 충족되지 않음.
    - 다만, 이 DRS에서 언급된 일부 버그(예: `add_tags_to_directory` 메서드 오류, `test_batch_tagging_ui.py`의 `bulk_write` 모의 객체 불일치)는 이미 해결되었음.

### 로그 레벨 조정 및 디버깅용 출력 제거
- **목표**: 애플리케이션의 로그 출력 수준을 최적화하고, 개발 과정에서 사용된 디버깅용 `print` 문을 제거하여 코드 가독성 및 성능 향상.
- **변경 사항**:
    - `core/tag_manager.py`: 파일 태그 조회, 업데이트 성공, 전체 태그/파일 검색, 파일 탐색 시작/완료, 일괄 태그 추가 시작/완료 등 상세한 정보성 `INFO` 로그들을 `DEBUG` 레벨로 조정.
    - `widgets/tag_control_widget.py`: UI 상태 변화, 탭 전환 시도 등 상세한 `INFO` 로그들을 `DEBUG` 레벨로 조정.
    - `main_window.py`: 초기화 상태, 디렉토리/파일 선택 이벤트 등 상세한 `INFO` 로그들을 `DEBUG` 레벨로 조정.
    - `main_window.py` 및 `widgets/file_list_widget.py`에 남아있던 디버깅용 `print` 문들을 모두 제거.
- **기대 효과**: 운영 환경에서 불필요한 로그 출력 감소 및 필요한 경우 상세한 디버깅 정보 확인 가능. 코드베이스의 정리 및 유지보수성 향상.

### 파일 경로 정규화 및 모듈화
- **문제**: 디렉토리 일괄 태깅 후 하위 디렉토리 파일의 태그가 파일 목록에 표시되지 않는 문제 발생. `TagManager`와 `FileTableModel` 간의 파일 경로 문자열 불일치(슬래시/역슬래시 혼용, 대소문자 등)가 원인으로 파악됨.
- **해결**:
    - `core/path_utils.py` 모듈을 신규 생성하여 `normalize_path` 함수를 정의. 이 함수는 `os.path.normpath`를 사용하여 운영체제에 맞는 경로를 생성하고, Windows 환경에 맞게 모든 슬래시를 역슬래시로 통일하도록 구현.
    - `TagManager` (core/tag_manager.py)의 모든 파일 경로 처리 메서드(`get_tags_for_file`, `update_tags`, `add_tags_to_files`, `add_tags_to_directory`)에 `normalize_path` 함수를 적용하여 MongoDB에 저장 및 조회 시 경로의 일관성을 확보.
    - `FileTableModel` (widgets/file_list_widget.py)에서도 `TagManager`에 태그 조회를 요청하기 전에 `normalize_path` 함수를 사용하여 파일 경로를 정규화하도록 수정.
- **기대 효과**: 파일 경로 불일치로 인한 태그 조회 실패 문제 해결 및 경로 처리 로직의 중앙 집중화로 유지보수성 향상.

---

## 2025년 7월 7일 (업데이트)

### UI 리팩토링 방향 전환 및 문서 재정비
- **결정**: 복잡성 증가로 인해 `UnifiedTaggingPanel`을 중심으로 한 UI 통합 리팩토링 계획을 **취소**하기로 결정.
- **근거**: 기존의 각 위젯(`DirectoryTreeWidget`, `FileListWidget`, `FileDetailWidget`, `TagControlWidget`, `BatchTaggingPanel`)이 명확한 단일 책임을 가지는 현재 아키텍처가 더 안정적이고 유지보수성이 높다고 판단.
- **조치**:
    - `_backup_ui_refactoring` 디렉토리에 관련 실험 코드를 백업하고, 현재 코드베이스에서 `UnifiedTaggingPanel` 관련 코드를 모두 제거.
    - 이에 따라, 현재 안정적으로 동작하는 코드 아키텍처를 기준으로 모든 관련 문서를 재정비하는 작업을 시작함.
- **향후 계획**:
    1. 현재 코드베이스(`main_window.py` 및 각 `widgets` 모듈)를 재분석하여 기능 명세를 명확히 함.
    2. 사용자 가이드(`docs/user_guide`)를 현재 UI/UX에 맞게 업데이트.
    3. 개발자 가이드(`docs/developer_guide`)에 현재 아키텍처, 위젯 간 상호작용, `UnifiedTaggingPanel` 계획 취소 배경 등을 상세히 기술.

---

## 2025년 7월 3일

### QuickTagsWidget 비활성화 문제 논의
- `setEnabled(False)`가 예상대로 동작하지 않는 원인 분석 필요.
- 시그널 연결 및 위젯 계층 구조 재검토.
- `TagUIStateManager` 도입 전, 단기적으로 디버깅 로그를 통해 실제 UI 상태 추적 예정.

## 2025년 7월 4일

### 최초 로드시 태그 관련 UI 비활성화 개선
- 문제: 애플리케이션 최초 로드시 파일이 선택되지 않았음에도 자주 사용하는 태그(QuickTagsWidget) 버튼이 활성화되어 있었음.
- 원인: state_manager.set_file_selected(False)가 초기화 시점에 호출되지 않아, 위젯이 기본적으로 활성화(True) 상태로 남아 있었음.
- 조치: MainWindow 초기화 시 모든 위젯 등록 후 state_manager.set_file_selected(False)를 호출하여, 최초 로드시 태그 관련 UI가 비활성화된 상태로 시작하도록 개선.
- 기대 효과: 파일이 선택되기 전까지 태그 입력/버튼 등 모든 태그 관련 UI가 비활성화되어 UX 혼란 방지 및 정책 일관성 확보.

## 2025년 7월 3일

### 디렉토리별 일괄 태그 추가 기능 개발 시작
- DRS-20250704-001_Batch_Tagging_Feature.md 명세에 따른 개발 시작
- 통합 패널 방식의 UI/UX 설계 채택
- BatchTaggingPanel 위젯 구현 예정
- 백그라운드 처리 및 파일 미리보기 기능 포함

### 일괄 태그 기능 1차 구현 완료
- TagManager에 add_tags_to_directory 메서드 구현
  - 벌크 업데이트를 통한 성능 최적화
  - 재귀 옵션 및 파일 확장자 필터링 지원
  - 중복 태그 제거 로직 포함
- BatchTaggingPanel 위젯 구현
  - 디렉토리 선택 및 파일 미리보기 기능
  - 실시간 필터링 옵션 (재귀, 확장자)
  - 백그라운드 워커 스레드로 UI 블로킹 방지
  - 진행률 표시 및 취소 기능
- MainWindow에 일괄 태그 메뉴 및 패널 통합
  - File 메뉴에 "일괄 태그 추가" 항목 추가
  - 현재 선택된 디렉토리로 패널 자동 설정
- 다음 단계: UI 레이아웃 개선 및 테스트

### 일괄 태그 기능 1차 커밋 완료 (2025-07-03)
- 커밋 해시: fb544b2
- 구현된 기능:
  - TagManager.add_tags_to_directory: 벌크 업데이트 기반 일괄 태그 추가
  - BatchTaggingPanel: 전용 UI 패널 (파일 미리보기, 필터링, 백그라운드 처리)
  - MainWindow 통합: 별도 공간에 패널 배치, 메뉴 연동
- 남은 개선사항:
  - UI/UX 세부 조정 (크기, 색상, 레이아웃)
  - 에러 처리 강화
  - 사용자 피드백 개선
  - 테스트 케이스 작성

## 2025년 7월 5일

### 일괄 태그 기능 개선사항 완료
- **UI/UX 세부 조정 완료**:
  - BatchTaggingPanel 전체적인 디자인 개선
  - 모던한 스타일시트 적용 (색상, 폰트, 간격, 아이콘)
  - 상태 표시 라벨 추가 (대기 중, 진행 중, 완료, 오류)
  - 파일 수 표시 및 실시간 업데이트
  - 버튼 스타일 개선 (호버 효과, 비활성화 상태)
  - 테이블 스타일 개선 (교대 행 색상, 헤더 스타일)
  - 진행률 바 스타일 개선

- **에러 처리 강화 완료**:
  - TagManager에 상세한 로깅 시스템 도입
  - 커스텀 예외 클래스 (TagManagerError) 추가
  - 연결 재시도 메커니즘 구현 (최대 3회)
  - 태그 유효성 검사 로직 추가
  - 상세한 오류 메시지 및 해결 방법 제시
  - 벌크 업데이트 시 개별 파일 오류 추적
  - 연결 상태 확인 메서드 추가

- **사용자 피드백 개선 완료**:
  - 상세한 처리 결과 표시 (성공/실패/수정/생성 파일 수)
  - 실패한 파일 목록 표시 (최대 5개)
  - 오류 발생 시 해결 방법 안내
  - 성공/실패에 따른 다른 아이콘 사용
  - 실시간 상태 업데이트

- **다음 단계**:
  - QA팀에 테스트 요청 (테스트 케이스 설계 및 실행)
  - 사용자 피드백 수집 및 추가 개선
  - 성능 최적화 검토

### File Information 표시 문제 발견
- **문제**: 일부 파일에서 File Information이 표시되지 않는 현상 발생
- **원인 분석**:
  - File Information은 DB 메타 정보가 아닌 실시간 파일 시스템 정보 (os.stat 사용)
  - 파일 접근 권한, 파일 존재 여부, 경로 문제 등으로 인해 TaggedFile 생성 시 FileNotFoundError 발생
  - 현재는 예외만 출력하고 UI에는 아무것도 표시하지 않음
- **영향**: 사용자 경험 저하 (파일 정보가 보이지 않아 혼란)
- **해결 방안**:
  - 파일 접근 오류 시 사용자에게 명확한 메시지 표시
  - 파일 정보를 가져올 수 없는 경우에도 기본 정보 표시
  - 권한 문제나 파일 시스템 문제에 대한 상세한 오류 처리
- **처리 계획**: QA팀 테스트 완료 후 발견된 이슈들과 함께 docs/issues.md에 등록하여 처리

## 2025년 7월 6일

### QA 이슈 대응 개발 내역
- **일괄 태그 적용 UI 버튼 상태 오류**
  - 태그 적용 작업 시작 시 apply_button이 숨겨지지 않는 문제를 해결
  - start_batch_tagging, reset_ui_state 등에서 버튼 상태를 명확히 제어하도록 개선
- **오류 메시지 상세화 부족**
  - 태그 적용 중 오류 발생 시 메시지 박스에 실패 파일명, 에러 원인 등 상세 정보를 포함하도록 개선
  - on_batch_tagging_finished에서 errors 리스트, 실패 원인, 전체 처리 결과를 메시지에 반영
- **TagManager mock 객체 bulk_write 동작 불일치**
  - mock_tag_manager의 add_tags_to_directory 반환값 구조를 실제 TagManager 반환 구조와 일치하도록 개선
  - 테스트 함수 내에서 성공/실패/에러 상황별로 다양한 반환값을 세팅
- **TagManager add_tags_to_directory import 오류**
  - core/tag_manager.py에서 os import 중복 문제를 해결(파일 상단에만 import)

### 도커 환경에서의 MongoDB 인증/연결 문제 및 최근 개발 이슈 정리
- **문제 상황**: 도커 컴포즈(docker-compose)로 새로운 환경에서 어플리케이션을 실행할 때 MongoDB 인증 오류(`Authentication failed`)로 인해 DB 연결이 되지 않는 현상 발생
- **원인 분석**:
  - docker-compose.yml에서 `MONGO_INITDB_ROOT_USERNAME: root`, `MONGO_INITDB_ROOT_PASSWORD: password`로 설정되어 있으나, 실제 컨테이너 볼륨이 남아 있으면 비밀번호가 변경되지 않음
  - TagManager는 항상 root/password로 접속을 시도하며, URI에 인증 DB(`authSource=admin`)가 명시되어 있지 않음
  - config.py에는 사용자명/비밀번호가 직접 명시되어 있지 않고, DB/컬렉션 정보만 있음
- **해결 방안**:
  1. 컨테이너 볼륨을 완전히 삭제 후 재생성(docker-compose down -v && docker-compose up -d)
  2. mongo shell로 직접 접속하여 root 계정이 정상인지 확인(mongo -u root -p password --authenticationDatabase admin)
  3. TagManager의 MongoDB URI에 `?authSource=admin`을 명시적으로 추가
  4. 필요시 file_tagger DB에 별도 계정 생성 후 해당 계정으로 접속
- **참고**: 운영/테스트 환경별로 계정/비밀번호를 분리 관리하는 것이 보안상 안전함

- **최근 개발 이슈 요약**:
  - mock 객체 반환값 구조를 실제 TagManager와 일치하도록 개선
  - BatchTaggingPanel의 버튼 상태 및 오류 메시지 상세화 개선
  - core/tag_manager.py의 os import 중복 제거
  - QA팀 피드백 기반 UI/UX, 에러 처리, 사용자 피드백 강화

### [DRS-20250705-002] 1단계: 기존 구조 분석 및 영향 범위 도출 (2025-07-05) - (취소됨)
- **주요 파일/모듈**: main_window.py, widgets/batch_tagging_panel.py, widgets/tag_input_widget.py, widgets/quick_tags_widget.py, core/tag_ui_state_manager.py, core/tag_manager.py, tests/test_batch_tagging_ui.py
- **중복/통합 대상 기능**: 파일/디렉토리 선택, 파일 목록/미리보기, 태그 입력/표시, 상태 관리 등
- **영향 범위**:
    - UI 구조 전면 개편(개별/일괄 태깅 통합)
    - 공통 컴포넌트 신설(파일/디렉토리 선택 및 미리보기, 태그 입력 등)
    - 상태 관리 구조 확장(TagUIStateManager 역할 확대)
    - 테스트 코드 전면 리팩토링(구조 변경 반영)
- **다음 단계**: 상위 구조/공통 컴포넌트/상태 관리 설계

### [DRS-20250705-002] 2단계: 상위 구조/공통 컴포넌트/상태 관리 설계 (2025-07-05) - (취소됨)
- **UnifiedTaggingPanel(통합 태깅 패널)**: 탭(Tab) 방식으로 "개별 태깅"과 "일괄 태깅" 모드 전환, 각 탭별로 필요한 서브 컴포넌트 배치
    - Tab: 개별 태깅
        - FileSelectionAndPreviewWidget
        - TagInputWidget
        - QuickTagsWidget
    - Tab: 일괄 태깅
        - FileSelectionAndPreviewWidget(디렉토리/파일 일괄 선택)
        - TagInputWidget
        - QuickTagsWidget
- **FileSelectionAndPreviewWidget(공통 컴포넌트)**: 좌측 디렉토리 트리(TreeView), 우측 파일 목록(TableView, 파일명/경로/태그 표시), 선택 이벤트를 상태 관리에 반영
- **TagInputWidget, QuickTagsWidget**: 기존 위젯 재사용, 필요시 기능 확장(자동완성 등)
- **TagUIStateManager(상태 관리 구조)**: 현재 모드(개별/일괄), 선택 파일/디렉토리, 태그 적용 가능 여부, 각 위젯 활성화/비활성화 등 중앙 관리(시그널/슬롯 구조)
- **요약**: 통합 패널에서 탭 전환으로 두 모드 지원, 파일/디렉토리 선택/미리보기는 공통 위젯으로 일원화, 상태 관리는 TagUIStateManager가 중앙에서 담당, 기존 태그 입력/빠른 태그 위젯은 그대로 재사용
- **다음 단계**: 구체적인 클래스/파일 구조 설계(클래스 다이어그램, 주요 메서드 시그니처 등)

### [DRS-20250705-002] 3단계: 구체적인 클래스/파일 구조 설계 (2025-07-05) - (취소됨)
- **파일 구조(신규/변경 예상)**
    - widgets/unified_tagging_panel.py: 통합 태깅 패널(메인 위젯)
    - widgets/file_selection_and_preview_widget.py: 파일/디렉토리 선택 및 미리보기 공통 위젯
    - widgets/batch_tagging_panel.py: (기존) 일괄 태깅 관련 서브 컴포넌트로 리팩토링
    - widgets/tag_input_widget.py, widgets/quick_tags_widget.py: (기존) 태그 입력/빠른 태그 위젯
    - core/tag_ui_state_manager.py: 상태 관리 확장
    - core/tag_manager.py: 태그 적용 로직(버그 수정 포함)
    - main_window.py: 통합 패널 포함, 역할 분산
- **클래스 관계(다이어그램 요약)**
    - MainWindow → UnifiedTaggingPanel → (FileSelectionAndPreviewWidget, TagInputWidget, QuickTagsWidget, BatchTaggingPanel, TagUIStateManager)
    - 각 위젯은 TagUIStateManager와 연동(시그널/슬롯)
- **주요 클래스/메서드 시그니처 예시**
    - UnifiedTaggingPanel(QWidget): switch_mode(mode), set_state_manager(manager)
    - FileSelectionAndPreviewWidget(QWidget): set_directory(path), get_selected_files(), file_selected(str), directory_selected(str)
    - TagUIStateManager(QObject): set_mode(mode), set_selected_files(files), set_tag_input_enabled(enabled), state_changed(dict)
- **설계 요약**: 통합 패널이 모든 태깅 관련 위젯을 포함, 공통 파일/디렉토리 선택 위젯 재사용, TagUIStateManager가 상태 중앙 관리, 시그널/슬롯 연동
- **다음 단계**: 실제 코드 뼈대(클래스/파일 생성) 및 UI/로직 구현

### [DRS-20250705-002] 4단계: 코드 뼈대 생성 및 구조 반영 (2025-07-05) - (취소됨)
- **widgets/unified_tagging_panel.py**: 통합 태깅 패널 클래스 뼈대(탭 기반, 상태 매니저 연동, 서브 컴포넌트 배치 구조)
- **widgets/file_selection_and_preview_widget.py**: 파일/디렉토리 선택 및 미리보기 공통 위젯 뼈대(트리뷰+테이블뷰, 시그널/슬롯 구조)
- **core/tag_ui_state_manager.py**: 통합 패널 상태 중앙 관리 클래스 뼈대(모드, 선택 파일/디렉토리, 각 위젯 활성화 등)
- **main_window.py**: 통합 패널 및 상태 매니저를 포함하는 메인 윈도우 뼈대(기존 구조와의 연결 고려)
- 각 파일별로 클래스/메서드 시그니처, 시그널/슬롯 구조 등 기본 골격만 우선 구현
- **다음 단계**: PL 컨펌 후 각 위젯/로직의 구체 구현, 기존 기능 통합, 테스트 코드 리팩토링 등 세부 구현 단계로 진행 예정

### [DRS-20250705-002] 5단계: PL 구조 평가 및 피드백 반영 (2025-07-05) - (취소됨)
- **PL 평가 요약**:
    - 개발팀의 구조 설계 및 뼈대 구축 방식이 DRS의 목표와 제안 아키텍처에 매우 잘 부합하며, 체계적이고 단계적인 접근이 강점으로 평가됨.
    - 탭 기반 UI, 공통 파일 선택 컴포넌트, 중앙 집중식 상태 관리 등 DRS의 핵심 요구사항이 모두 반영됨.
    - 관심사 분리, 모듈화, 테스트 용이성, 선제적 버그 해결, 점진적 구현 방식 등에서 높은 평가를 받음.
- **PL 피드백 주요 포인트**:
    1. 컴포넌트 간 통신(시그널/슬롯) 흐름을 명확히 설계·문서화할 것
    2. 새로운 컴포넌트의 오류 처리 및 사용자 피드백 일관성 강화
    3. 포괄적 테스트(특히 모드 전환/공통 컴포넌트 상호작용) 필수
    4. 대용량 디렉토리 등 성능 최적화 고려
- **결론**: 위 사항을 반영하여 세부 구현 단계로 진행 예정
- **다음 단계**: 각 컴포넌트별 세부 구현, 통신 구조 설계, 오류 처리/테스트/성능 최적화 방안 구체화

### [DRS-20250705-002] 6단계: 컴포넌트 간 통신(시그널/슬롯) 구조 설계 (2025-07-05) - (취소됨)
- 각 위젯/컴포넌트와 TagUIStateManager 간의 시그널/슬롯 구조를 명확히 정의
    - FileSelectionAndPreviewWidget: file_selected(str), directory_selected(str) → TagUIStateManager로 전달
    - TagInputWidget/QuickTagsWidget: tags_changed(list) → TagUIStateManager로 전달
    - UnifiedTaggingPanel: mode_changed(str) → TagUIStateManager로 전달
    - TagUIStateManager: state_changed(dict) → 각 위젯/패널로 상태 동기화
- 주요 이벤트 흐름(파일/디렉토리 선택, 모드 전환, 태그 입력/수정 등)에 따른 상태 동기화 및 UI 반영 방식 설계
- 다음 단계: 각 위젯별 세부 구현(시그널/슬롯 연결, 오류 처리, 사용자 피드백 등)

### [DRS-20250705-002] 7단계: TagInputWidget/QuickTagsWidget 및 통합 패널-상태매니저 통신 구조 구현 (2025-07-05) - (취소됨)
- TagInputWidget/QuickTagsWidget: 태그 입력/수정 시 시그널 emit, 입력값 유효성 검사 및 사용자 피드백(QMessageBox), 외부 상태에 따른 활성/비활성 동기화 구현
- UnifiedTaggingPanel: 각 서브 컴포넌트 시그널을 TagUIStateManager에 연결, 상태 매니저의 state_changed 시그널을 받아 UI 동기화
- 주요 통신 흐름(모드 전환, 파일/디렉토리 선택, 태그 입력 등)에 대한 시그널/슬롯 구조 구현 완료
- 다음 단계: BatchTaggingPanel 리팩토링 및 통합, 테스트 코드 리팩토링, 성능 최적화 등

### [DRS-20250705-002] 8단계: BatchTaggingPanel 리팩토링 및 통합 (2025-07-05) - (취소됨)
- BatchTaggingPanel을 통합 패널(UnifiedTaggingPanel)의 일괄 태깅 탭 서브 컴포넌트로 리팩토링
- 파일/디렉토리 선택/미리보기는 FileSelectionAndPreviewWidget으로 대체, 태그 입력/빠른 태그 위젯도 기존 컴포넌트 재사용
- TagUIStateManager와의 상태 연동(적용 버튼 활성화, 진행 상태 등) 구조로 변경
- 일괄 태깅 실행 시 오류 처리 및 사용자 피드백(QMessageBox 등) 일관성 강화
- 다음 단계: 테스트 코드 리팩토링 및 통합, 성능 최적화

### [DRS-20250705-002] 9단계: 테스트 코드 리팩토링 및 통합 (2025-07-05) - (취소됨)
- 기존 테스트(test_batch_tagging_ui.py 등)를 통합 구조에 맞게 전면 수정
- 모드 전환, 파일/디렉토리 선택, 태그 입력/적용 등 주요 시나리오별 통합 테스트 추가
- 기존 버그 재현 및 해결 검증 테스트 강화
- 신규 컴포넌트 단위/통합 테스트 작성
- 다음 단계: 성능 최적화(대용량 디렉토리, UI 응답성 등)

## 2025년 7월 6일

### UI 레이아웃 재구성 및 개선
- **목표**: 사용자 경험 개선을 위한 메인 윈도우 UI 레이아웃 재구성 및 세부 조정.
- **변경 사항**:
    - **4열에서 3열 구조로 전환**: 기존 4열 구조에서 2열(파일 상세/목록)을 수직 분할하여 3열 구조로 변경.
    - **메인 윈도우 QSplitter 적용**: 최상위 레이아웃에 `QSplitter`를 도입하여 사용자가 각 열의 너비를 동적으로 조절할 수 있도록 함. 초기 너비는 1열:150px, 3열:150px, 2열:나머지 공간으로 설정.
    - **파일 상세 정보 영역 개선**: 2열 상단의 `FileDetailWidget`을 재설계.
        - `ui/file_detail_content_widget.ui`를 새로 생성하여 썸네일, 파일 메타데이터, 태그 칩 영역을 포함.
        - 썸네일 영역(`QLabel`)에 200x200px의 고정 크기를 부여하여 일관된 UI 유지.
        - 파일 메타데이터(`QTextBrowser`)와 태그 칩 영역(`QScrollArea` 내 `QHBoxLayout`)을 2:1 비율로 배치.
    - **`FileTableModel` 통합**: `widgets/file_list_widget.py`를 `QTableView` 기반으로 변경하고, `FileTableModel`을 사용하여 파일 목록에 태그 정보를 직접 표시하도록 개선.
    - **오류 수정**:
        - `widgets/tag_control_widget.py`에서 `QStringListModel`의 잘못된 import 경로 (`PyQt5.QtWidgets` -> `PyQt5.QtCore`) 수정.
        - `widgets/file_detail_widget.py`에 `clear_preview()` 메서드 추가 및 `main_window.py`에서 호출하여 디렉토리 변경 시 파일 상세 정보 초기화.
- **기대 효과**:
    - 사용자에게 더 직관적이고 효율적인 작업 환경 제공.
    - 유연한 레이아웃 조절로 다양한 사용 환경에 대응.
    - 파일 정보와 태그 정보의 시각적 일관성 및 가독성 향상.
- **다음 단계**: 일괄 태깅 다이얼로그 구현 또는 `QuickTagsWidget` 통합 등 기능 구현.

## 2025년 7월 7일

### 파일 상세 정보 및 자동 탭 전환 기능 복구
- **문제**: 최근 UI 레이아웃 재구성 및 통합 태깅 패널 도입 과정에서 파일 선택 시 파일 상세 정보가 표시되지 않고, 단일 파일 선택 시 개별 태깅 탭으로 자동 전환되지 않는 문제 발생.
- **원인 분석**:
    - `main_window.py`의 `on_file_selection_changed` 함수에서 `self.file_list.get_selected_file_paths()`가 `QTableView`의 `selectedRows()` 메서드 동작 방식의 오해로 인해 빈 리스트를 반환하고 있었음.
    - `UnifiedTaggingPanel`이 아직 구현되지 않아 자동 탭 전환 기능이 부재했음.
- **해결**:
    - `main_window.py`의 `on_file_selection_changed` 함수 로직을 수정하여 `self.file_list.list_view.selectionModel().selectedIndexes()`를 직접 순회하며 선택된 파일 경로를 추출하도록 개선. 이 과정에서 중복 파일 경로 처리를 위해 `processed_rows` 집합을 사용.
    - `widgets/file_detail_widget.py`의 `update_preview` 메서드에 예외 처리 로직을 추가하여 파일 정보 로딩 중 발생할 수 있는 오류에 대비.
    - 디버깅 과정에서 추가했던 불필요한 `print` 문 제거.
- **결과**: 파일 선택 시 파일 상세 정보가 정상적으로 표시되며, 단일 파일 선택 시 개별 태깅 탭으로의 자동 전환도 정상 동작 확인.

### 고급 파일 추적 기능 (이동/수정된 파일) 논의
- **배경**: 파일의 디렉토리 이동 또는 내용 변경 시에도 애플리케이션이 동일한 파일로 인식하고 추적할 수 있는 기능에 대한 필요성 논의.
- **고려 사항**:
    - **파일 내용이 변경되지 않는 경우**: 파일의 내용을 기반으로 하는 해시 값(예: SHA256)을 고유 식별자로 사용하여 파일 이동을 추적.
    - **파일 내용이 변경될 수 있는 경우**: 데이터베이스 기반의 고유 ID(UUID 등)를 논리적 파일 식별자로 사용하고, 파일 경로, 파일명, 크기, 마지막 수정 시간 등의 메타데이터를 보조 식별자로 활용하는 휴리스틱 기반의 재연결 로직 도입. 사용자 명시적 확인을 통한 데이터 무결성 확보.
- **구현 로직 위치 (제안)**:
    - `models/tagged_file.py`: 고유 ID 필드 추가.
    - `core/tag_manager.py`: 고유 ID 기반의 파일 저장, 조회, 업데이트 로직 추가.
    - `core/file_tracker.py` (신규): 파일 내용이 변경되지 않는 경우의 파일 시스템 스캔, 해시 계산, 이동된 파일 식별 로직.
    - `core/file_reconciler.py` (신규): 파일 내용이 변경될 수 있는 경우의 파일 시스템 스캔, 사라진/새로운 파일 식별, 휴리스틱 기반 재연결 시도 로직.
    - `main_window.py` 또는 별도의 UI 서비스: 해당 기능들을 트리거하는 UI 요소 및 백그라운드 작업 관리.
- **다음 단계**: 향후 개발 로드맵에 포함하여 구체적인 설계 및 구현 진행 예정.