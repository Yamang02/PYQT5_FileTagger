# 개발 요청 명세 (DRS): 통합 UI 리팩토링 (3-Column)

**문서 ID:** DRS-20250706-001
**버전:** 2.0
**작성일:** 2025년 7월 6일
**요청자:** 사용자
**담당자:** Gemini (PM)

---
status: Approved
---
## 개발 요청 명세 (Development Request Specification)

*   **문서 ID**: `DRS-20250706-001`
*   **작성일**: `2025년 7월 6일`
*   **작성자**: `Gemini (기획팀)`
*   **관련 기능/모듈**: `UI/UX, 리팩토링`

## 2. 배경
초기 4열 레이아웃 구성안에 대해 사용자 피드백을 반영하여, 공간 활용도를 높이고 시선 분산을 줄이는 3열 구조로 설계를 변경한다.

## 3. 요구사항: 3-Column 메인 윈도우 레이아웃
메인 윈도우는 다음의 3개 주요 세로 열로 구성된다.

### 3.1. 1열: 디렉토리 트리 뷰 (Directory Tree View)
- **기능**: 시스템의 디렉토리 구조를 트리 형태로 표시한다.
- **상호작용**: 사용자가 특정 디렉토리를 선택하면 '2열 하단: 파일 리스트 뷰'가 해당 디렉토리의 내용으로 갱신된다.

### 3.2. 2열: 파일 정보 뷰 (File Information View)
- **구성**: 상하로 분할된 `QSplitter`를 사용하여 두 개의 위젯을 배치한다.
- **상단: 파일 상세 정보 뷰 (File Detail View)**
    - **기능**: '파일 리스트 뷰'에서 선택된 파일의 상세 정보나 미리보기를 표시한다.
    - **지원 포맷**: 이미지 파일(jpg, png 등) 미리보기, 텍스트 파일 내용 일부 표시 등.
- **하단: 파일 리스트 뷰 (File List View)**
    - **기능**: '1열: 디렉토리 트리 뷰'에서 선택된 디렉토리 내의 파일 목록을 표시한다.
    - **상호작용**: 사용자가 특정 파일을 선택하면 '2열 상단: 파일 상세 정보 뷰'와 '3열: 태그 컨트롤 컨테이너'가 해당 파일의 정보로 갱신된다.

### 3.3. 3열: 태그 컨트롤 컨테이너 (Tag Control Container)
- **기능**: 선택된 파일의 태그를 관리(추가, 삭제, 조회)하는 모든 UI 요소를 포함한다.
- **포함 위젯**:
    - 태그 입력 및 추가 (`tag_input_widget`)
    - 적용된 태그 목록 표시 (`tag_chip` 형태)
    - 빠른 태그 제안/선택 (`quick_tags_widget`)
    - 일괄 태깅 옵션 (`batch_tagging_options_widget`) - (디렉토리 선택 시 활성화 고려)

## 4. 기대 효과
- 연관성이 높은 파일 목록과 상세 정보를 한 열에 배치하여 시선의 흐름을 자연스럽게 유도.
- 전체적인 레이아웃을 단순화하여 사용자가 핵심 기능에 더 집중할 수 있도록 함.
- `QSplitter`를 통해 사용자가 필요에 따라 정보 표시 영역의 크기를 조절할 수 있어 유연성 증대.

## 5. 참고 자료
- 기존 UI 백업: `_backup_ui_refactoring/`
- 관련 문서: `docs/developer_guide/tagging_feature_spec.md`
