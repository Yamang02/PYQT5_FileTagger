# 개발 이슈 (Development Issues)

## [이슈] 파일 미선택 상태에서 태그 입력 및 등록 UI 동작 정책 논의 (2024-06-13)

- **이슈 유형**: 질문/기능 개선 논의
- **제출 팀**: 기획팀
- **제출 팀**: 기획팀
- **제목**: 파일 미선택 상태에서 태그 입력 및 등록 UI 동작 정책 논의
- **설명**:
    - **문제/요청 내용**: 현재 TagInputWidget(태그 입력 UI)은 파일이 선택되지 않은 상태에서도 태그 칩을 추가할 수 있습니다. 하지만 이 상태에서 태그를 등록해도 실제로는 어떤 파일에도 태그가 저장되지 않습니다. 사용자는 태그가 등록된 것처럼 보이지만, 실제로는 데이터에 반영되지 않아 혼란을 줄 수 있습니다.
    - **재현 단계 (버그의 경우)**:
        1. 파일을 선택하지 않은 상태에서 태그 입력 필드에 태그를 입력하고 Enter를 누른다.
        2. 태그 칩이 UI에 추가된다.
        3. [태그 저장] 버튼을 눌러도 DB에는 반영되지 않는다.
    - **현재 동작**:
        - 파일 미선택 상태에서도 태그 칩 추가 및 입력 가능
        - 저장 시 실제로는 아무 파일에도 태그가 저장되지 않음
    - **기대 동작**: 파일이 선택되지 않은 상태에서는 태그 입력/등록이 불가능하거나, 또는 명확한 안내 메시지(예: "파일을 먼저 선택하세요")가 제공되어야 함
    - **영향**:
        - 사용자 혼란 유발
        - 태그 관리 기능의 신뢰성 저하
    - **관련 파일/모듈**:
        - main_window.py
        - widgets/tag_input_widget.py
    - **스크린샷/로그 (선택 사항)**: (필요시 첨부)

- **해결 상태**: [해결 완료]
- **해결 내용**: 파일 미선택 시 태그 입력 필드를 비활성화하여 사용자의 혼란을 방지하고, 태그 관리의 명확성을 높이기로 결정.
- **해결 일자**: 2025년 7월 3일
- **관련 커밋**: (개발자가 커밋 후 추가 예정)

## [이슈] 파일 미선택 시 자주 사용하는 태그(QuickTagsWidget) 버튼 비활성화 동작 미흡 (2024-07-03)

- **이슈 유형**: 버그/기획 논의
- **제출 팀**: 개발팀
- **제출 팀**: 개발팀
- **제목**: 파일 미선택 시 자주 사용하는 태그(QuickTagsWidget) 버튼이 비활성화되지 않고 클릭 동작이 발생함
- **설명**:
    - **문제/요청 내용**: 파일이 선택되지 않은 상태에서도 QuickTagsWidget(자주 사용하는 태그) 버튼이 활성화되어 클릭 시 태그가 TagInputWidget에 추가/제거된다. 기획 의도상 파일이 선택되지 않은 경우에는 해당 버튼들이 비활성화되어야 하며, 클릭해도 아무 동작이 없어야 한다.
    - **재현 단계 (버그의 경우)**:
        1. 애플리케이션 실행
        2. 파일을 선택하지 않은 상태에서 자주 사용하는 태그 버튼을 클릭
        3. 태그가 TagInputWidget에 추가/제거됨
    - **현재 동작**: 파일 미선택 상태에서도 자주 사용하는 태그 버튼이 클릭 가능하며, 태그가 추가/제거된다.
    - **기대 동작**: 파일이 선택되지 않은 경우 QuickTagsWidget 전체가 비활성화되어 버튼 클릭이 불가능해야 한다.
    - **영향**: 사용자가 파일을 선택하지 않은 상태에서 태그를 잘못 추가/제거할 수 있어 UX 혼란 및 데이터 불일치 가능성이 있다.
    - **관련 파일/모듈**:
        - widgets/quick_tags_widget.py
        - main_window.py
    - **스크린샷/로그 (선택 사항)**: (생략)

- **해결 상태**: [Closed]
- **해결 내용**: MainWindow 초기화 시 모든 태그 관련 위젯 등록 후 TagUIStateManager의 set_file_selected(False)를 호출하여, 최초 로드시 태그 관련 UI가 비활성화된 상태로 시작하도록 개선. 파일이 선택되기 전까지 태그 입력/버튼 등 모든 태그 관련 UI가 비활성화되어 정책 일관성 및 UX 신뢰성 확보. `feat/tag-autocomplete` 브랜치가 `main`에 성공적으로 머지됨.
- **해결 일자**: 2025년 7월 4일
- **관련 커밋**: (머지된 커밋 해시 추가 예정)

## [이슈] 일괄 태그 추가 기능 QA 테스트 요청 (2025-07-05)

## [이슈] 일괄 태그 적용 시 UI 상태 업데이트 미흡 (2025-07-05)

## [이슈] 일괄 태그 적용 오류 메시지 상세화 필요 (2025-07-05)

## [이슈] `test_batch_tagging_ui.py`의 `TagManager` 모의 객체 `bulk_write` 동작 불일치 (2025-07-05)

- **이슈 유형**: 버그 (테스트 코드 수정 필요)
- **제출 팀**: QA팀
- **제목**: `test_batch_tagging_ui.py`에서 `TagManager` 모의 객체의 `bulk_write` 동작이 실제와 달라 테스트 실패 유발
- **설명**:
    - **문제/요청 내용**: `test_batch_tagging_ui.py` 테스트에서 `TagManager`를 모의(mock)할 때, `add_tags_to_directory` 메서드 내부에서 호출되는 `bulk_write`의 동작이 실제 `TagManager`의 `bulk_write` 동작과 일치하지 않아 테스트 실패를 유발합니다. 특히 `bulk_write`에 전달되는 요청 형식이 유효하지 않다는 오류 로그가 발생합니다.
    - **재현 단계 (버그의 경우)**:
        1. `test_batch_tagging_ui.py` 테스트 실행.
        2. `ERROR core.tag_manager:tag_manager.py:327 [TagManager] : {'updateOne': ...} is not a valid request`와 같은 로그가 발생하며 테스트가 실패함.
    - **현재 동작**: `TagManager` 모의 객체의 `bulk_write`가 실제 `TagManager`의 `bulk_write`와 다른 방식으로 동작하여 테스트가 실패함.
    - **기대 동작**: `test_batch_tagging_ui.py`에서 `TagManager`를 모의할 때, `bulk_write`의 동작을 실제 `TagManager`의 `bulk_write`와 동일하게 모의하여 테스트가 정확하게 동작하도록 해야 함.
    - **영향**: `test_batch_tagging_ui.py`의 `test_batch_tagging_panel_apply_tags` 및 `test_batch_tagging_panel_apply_tags_error_handling` 테스트 실패의 근본 원인 중 하나로 추정됨.
    - **관련 파일/모듈**:
        - `tests/test_batch_tagging_ui.py` (특히 `mock_tag_manager` fixture)
        - `core/tag_manager.py` (실제 `bulk_write` 구현)
    - **추정 원인**: `test_batch_tagging_ui.py`의 `mock_tag_manager` fixture에서 `bulk_write`를 적절히 모의하지 못했거나, `TagManager`의 `add_tags_to_directory` 메서드 내부에서 `bulk_write`를 호출하는 방식이 `test_tag_manager.py`의 모의 방식과 달라 발생.
- **해결 상태**: [New Issue]
- **담당자**: 개발팀 (테스트 코드 수정)
- **우선순위**: 높음
- **예상 완료일**: 2025년 7월 8일



- **이슈 유형**: 버그/기능 개선
- **제출 팀**: QA팀
- **제목**: `test_batch_tagging_panel_apply_tags_error_handling` 테스트 실패 - 오류 메시지 박스 내용 불충분
- **설명**:
    - **문제/요청 내용**: 일괄 태그 적용 중 오류 발생 시 표시되는 메시지 박스의 내용이 너무 간략하여 사용자에게 충분한 정보를 제공하지 못합니다. 테스트에서는 "일괄 태그 추가 중 오류 발생"과 같은 상세 메시지를 기대했지만, 실제로는 "❌ 오류"와 같은 간략한 메시지만 표시됩니다.
    - **재현 단계 (버그의 경우)**:
        1. `test_batch_tagging_ui.py`의 `test_batch_tagging_panel_apply_tags_error_handling` 테스트 실행.
        2. 테스트가 `assert "일괄 태그 추가 중 오류 발생" in args[1]` 부분에서 실패함.
    - **현재 동작**: 오류 발생 시 간략한 메시지만 표시됨.
    - **기대 동작**: 오류 발생 시 상세한 오류 내용(예: 오류 유형, 실패한 파일 목록, 해결 방안 등)이 메시지 박스에 포함되어야 함.
    - **영향**: 사용자에게 오류 상황에 대한 명확한 정보 제공 불가, 문제 해결 어려움.
    - **관련 파일/모듈**:
        - `widgets/batch_tagging_panel.py` (오류 메시지 처리 로직)
        - `tests/test_batch_tagging_ui.py`
    - **추정 원인**: 오류 메시지 구성 로직의 문제 또는 메시지 박스에 전달되는 정보의 부족.
- **해결 상태**: [New Issue]
- **담당자**: 개발팀
- **우선순위**: 중간
- **예상 완료일**: 2025년 7월 8일



- **이슈 유형**: 버그
- **제출 팀**: QA팀
- **제목**: `test_batch_tagging_panel_apply_tags` 테스트 실패 - 일괄 태그 적용 시 `apply_button`이 숨겨지지 않음
- **설명**:
    - **문제/요청 내용**: 일괄 태그 적용(`apply_button` 클릭) 작업이 시작될 때, `apply_button`이 숨겨지고 `cancel_button`과 `progress_bar`가 표시되어야 하지만, `apply_button`이 계속 보이는 문제가 발생합니다. 이로 인해 사용자는 작업이 진행 중임을 명확히 인지하기 어렵습니다.
    - **재현 단계 (버그의 경우)**:
        1. `test_batch_tagging_ui.py`의 `test_batch_tagging_panel_apply_tags` 테스트 실행.
        2. 테스트가 `assert not batch_tagging_panel.apply_button.isVisible()` 부분에서 실패함.
    - **현재 동작**: 일괄 태그 적용 시작 시 `apply_button`이 계속 표시됨.
    - **기대 동작**: 일괄 태그 적용 시작 시 `apply_button`이 숨겨지고, `cancel_button`과 `progress_bar`가 표시되어야 함.
    - **영향**: 사용자 경험 저하, 작업 진행 상태에 대한 혼란.
    - **관련 파일/모듈**:
        - `widgets/batch_tagging_panel.py` (UI 상태 업데이트 로직)
        - `tests/test_batch_tagging_ui.py`
    - **추정 원인**: UI 업데이트 로직의 누락 또는 지연, 혹은 `TagManager` 모의 객체의 `bulk_write` 동작이 실제와 달라 발생하는 문제일 수 있음.
- **해결 상태**: [New Issue]
- **담당자**: 개발팀
- **우선순위**: 높음
- **예상 완료일**: 2025년 7월 8일



- **이슈 유형**: QA 테스트 요청
- **제출 팀**: 개발팀
- **제출 팀**: 개발팀
- **제목**: 일괄 태그 추가 기능에 대한 종합 테스트 수행 요청
- **설명**:
    - **문제/요청 내용**: 7월 3일에 구현된 일괄 태그 추가 기능의 개선사항(UI/UX 개선, 에러 처리 강화, 사용자 피드백 개선)이 완료되었습니다. QA팀에서 해당 기능에 대한 종합적인 테스트를 수행하여 기능의 안정성과 사용성을 검증해주시기 바랍니다.
    - **테스트 대상 기능**:
        1. **기본 기능**: 디렉토리 선택, 파일 미리보기, 태그 입력, 일괄 적용
        2. **필터링 기능**: 재귀 옵션, 파일 확장자 필터링 (이미지/문서/사용자 정의)
        3. **UI/UX**: 스타일링, 상태 표시, 진행률 표시, 반응성
        4. **에러 처리**: 잘못된 입력, 네트워크 오류, 권한 오류 등
        5. **사용자 피드백**: 성공/실패 메시지, 상세 결과 표시
    - **테스트 기준**: DRS-20250704-001_Batch_Tagging_Feature.md 명세서 및 tagging_feature_spec.md
    - **현재 동작**: 
        - File 메뉴 → "일괄 태그 추가" 클릭 시 BatchTaggingPanel 표시
        - 디렉토리 선택 및 파일 미리보기 기능
        - 백그라운드 처리로 UI 블로킹 방지
        - 상세한 결과 표시 및 오류 처리
    - **기대 동작**: 명세서에 명시된 모든 기능이 안정적으로 동작하며, 사용자 경험이 향상되어야 함
    - **영향**: 
        - 사용자 생산성 향상
        - 대량 파일 태그 관리 효율성 증대
        - 프로젝트 품질 보증
    - **관련 파일/모듈**:
        - widgets/batch_tagging_panel.py
        - core/tag_manager.py (add_tags_to_directory 메서드)
        - main_window.py (일괄 태그 메뉴 연동)
        - docs/developer_guide/tagging_feature_spec.md
        - docs/developer_guide/drs/DRS-20250704-001_Batch_Tagging_Feature.md
    - **개선사항 요약**:
        - UI/UX: 모던한 디자인, 상태 표시, 파일 수 표시
        - 에러 처리: 로깅 시스템, 재시도 메커니즘, 상세 오류 메시지
        - 사용자 피드백: 상세 결과, 실패 파일 목록, 해결 방법 안내

- **해결 상태**: [New Issue]
- **담당자**: QA팀
- **우선순위**: 높음
- **예상 완료일**: 2025년 7월 7일

---

## [이슈] `core/tag_manager.py` 내 `add_tags_to_directory` 메서드 로컬 `os` 변수 참조 오류 (2025-07-05)

- **이슈 유형**: 버그 (개발팀 수정 필요) / 기획팀 평가 요청
- **제출 팀**: QA팀
- **제목**: `add_tags_to_directory` 메서드 내 불필요한 `os` 모듈 재임포트로 인한 `local variable 'os' referenced before assignment` 오류 발생
- **설명**:
    - **문제/요청 내용**: `core/tag_manager.py` 파일의 `add_tags_to_directory` 메서드 내부에서 `os` 및 `pathlib` 모듈을 불필요하게 재임포트하고 있었습니다. 이로 인해 메서드 내에서 `os.path.exists()`와 같은 함수를 호출할 때, 전역 `os` 모듈이 아닌 지역 변수 `os`를 참조하려 하여 `local variable 'os' referenced before assignment` 오류가 발생했습니다. 이 오류는 `add_tags_to_directory`를 사용하는 모든 기능(예: 일괄 태깅)의 정상적인 동작을 방해합니다.
    - **재현 단계 (버그의 경우)**:
        1. `core/tag_manager.py`의 `add_tags_to_directory` 메서드 내부에 `import os` 또는 `from pathlib import Path` 라인이 존재하는 상태에서 해당 메서드를 호출한다.
        2. `os.path.exists()` 또는 `os.walk()` 등 `os` 모듈의 함수를 호출하는 지점에서 오류가 발생한다.
    - **현재 동작**: `add_tags_to_directory` 메서드 호출 시 `local variable 'os' referenced before assignment` 오류로 인해 기능이 정상 작동하지 않음.
    - **기대 동작**: `add_tags_to_directory` 메서드가 오류 없이 정상적으로 파일들을 처리하고 태그를 추가해야 함.
    - **영향**:
        - '일괄 태깅' 기능 등 `add_tags_to_directory`를 사용하는 모든 기능이 동작하지 않음.
        - 애플리케이션의 안정성 저하.
    - **관련 파일/모듈**:
        - `core/tag_manager.py` (특히 `add_tags_to_directory` 메서드)
    - **QA팀의 임시 조치**:
        - QA 테스트 진행을 위해 `core/tag_manager.py` 파일의 `add_tags_to_directory` 메서드 내부에 있던 `import os` 및 `from pathlib import Path` 라인을 제거했습니다. 이 수정으로 현재 `TagManager`의 단위 테스트는 모두 통과하는 상태입니다.
    - **기획팀 평가 요청**:
        - 이 문제는 개발팀의 코드 수정이 필요한 버그입니다. QA팀에서 임시 조치했지만, 개발팀에서 정식으로 수정하고 코드 리뷰를 통해 재발 방지 대책을 마련해야 합니다.
        - 기획팀에서는 이러한 유형의 코드 품질 이슈에 대해 어떤 프로세스로 관리하고 평가할지 검토해주시기 바랍니다. (예: 코드 컨벤션 강화, 정적 분석 도구 도입 등)

- **해결 상태**: [New Issue] (QA팀 임시 조치 완료, 개발팀 정식 수정 및 기획팀 평가 필요)
- **담당자**: 개발팀 (수정), 기획팀 (평가)
- **우선순위**: Critical (핵심 기능 블로커)
- **예상 완료일**: 2025년 7월 8일 (개발팀 수정 완료 기준)

---