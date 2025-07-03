# feat/tag-autocomplete 브랜치 개발 회고

- **날짜:** 2025-07-04
- **관련 시스템/모듈:** TagInputWidget, QuickTagsWidget, TagUIStateManager, main_window.py 등

## 문제 상황
- 파일이 선택되지 않은 상태에서 자주 사용하는 태그(QuickTagsWidget) 버튼이 비활성화되지 않고 클릭되는 현상 발생
- TagInputWidget, QuickTagsWidget 등 태그 관련 UI의 상태가 일관되게 관리되지 않아 UX 혼란 및 데이터 불일치 가능성

## 증상
- 파일 미선택 시에도 태그 버튼이 활성화되어 태그칩이 생성됨
- UI와 논리 상태가 불일치하여 사용자 혼란 유발

## 원인 분석
- PyQt5 위젯 계층 및 setEnabled 동작에 대한 이해 부족
- 상태 관리 로직이 각 위젯에 분산되어 있어 중앙 집중적 관리의 부재
- 시그널 연결 및 UI 상태 동기화 타이밍 문제

## 해결 방법
- TagUIStateManager(상태 관리 클래스) 도입으로 태그 관련 UI의 상태를 중앙에서 일괄 관리
- main_window.py에서 TagInputWidget, QuickTagsWidget, 태그 저장 버튼 등을 state_manager에 등록
- 최초 로드시 state_manager.set_file_selected(False) 호출로 모든 태그 관련 UI가 비활성화된 상태로 시작하도록 개선
- 기획팀과의 논의 및 issues.md, dev_notes.md 등 문서화 병행

## 재발 방지
- 상태 관리 클래스(TagUIStateManager) 도입으로 UI 상태 불일치 문제 구조적으로 예방
- UI/UX 정책을 명확히 문서화하고, 정책 변경 시 코드와 문서 동기화
- 코드 리뷰 및 테스트 강화, dev_notes.md 등 내부 기록 적극 활용

## 회고
- **배운 점:**
    - UI 상태 관리는 반드시 중앙 집중적으로 설계해야 예외 상황과 확장에 강하다.
    - 기획팀과의 긴밀한 논의와 문서화가 정책 일관성 유지에 매우 중요함을 체감
- **개선할 점:**
    - PyQt5 등 프레임워크의 동작 원리를 더 깊이 이해하고, UI/상태 관리 구조를 미리 설계할 필요
    - 테스트 자동화 및 예외 케이스에 대한 QA를 더 체계적으로 준비
- **좋았던 점:**
    - 문제 발생 시 신속하게 원인 분석 및 구조 개선(상태 관리 클래스 도입)으로 이어진 점
    - dev_notes.md, issues.md 등 문서화와 커뮤니케이션이 잘 이루어짐 