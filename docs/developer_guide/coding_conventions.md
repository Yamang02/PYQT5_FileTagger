# 개발 가이드라인

## 1. 주석 및 문서화 정책

개발팀은 코드의 가독성과 유지보수성을 높이기 위해 다음과 같은 주석 및 문서화 정책을 따릅니다.

-   **Google style docstring**: 모든 주요 함수, 클래스, 메서드에는 Google style docstring을 사용하여 '무엇을 하는지', '어떻게 사용하는지', '어떤 매개변수를 받는지', '무엇을 반환하는지' 등을 명확하게 기술합니다.
    -   Docstring은 코드의 '왜'와 '어떻게'에 집중하여 작성하며, 기획 문서와 연동하여 사용자 및 기획자도 참고할 수 있도록 작성합니다.
    -   예시:
        ```python
        def example_function(param1: str, param2: int) -> bool:
            """
            이 함수는 param1과 param2를 사용하여 특정 작업을 수행합니다.

            Args:
                param1 (str): 첫 번째 매개변수로, 문자열 형태여야 합니다.
                param2 (int): 두 번째 매개변수로, 정수 형태여야 합니다.

            Returns:
                bool: 작업 성공 여부를 반환합니다. True는 성공, False는 실패를 의미합니다.
            """
            # 함수 로직
            pass
        ```

-   **인라인 주석**: 복잡한 로직, 특정 결정의 배경, 또는 코드의 특정 부분이 왜 그렇게 작성되었는지에 대한 설명을 위해 인라인 주석을 사용합니다.
    -   인라인 주석은 코드의 '왜'에 집중하며, '무엇'을 하는지는 코드를 통해 명확히 드러나도록 작성합니다.
    -   예시:
        ```python
        # 이 부분은 사용자 인증을 위해 JWT 토큰을 검증하는 로직입니다.
        if not validate_jwt_token(token):
            raise UnauthorizedError("유효하지 않은 토큰입니다.")
        ```

## 2. 파일 분리 (모듈화) 정책

코드의 유지보수성, 확장성 및 협업 효율성을 극대화하기 위해 기능 단위 및 관심사별로 파일을 명확하게 분리합니다.

-   **UI (User Interface)**: 사용자 인터페이스와 관련된 코드는 `ui/` 디렉토리 또는 `widgets/` 디렉토리 내에 위치시킵니다. (예: `main_window.py`, `tag_input_widget.py`)
-   **비즈니스 로직 (Business Logic)**: 핵심 비즈니스 규칙 및 애플리케이션의 주요 기능을 담당하는 코드는 `core/` 디렉토리 내에 위치시킵니다. (예: `tag_manager.py`)
-   **데이터 모델 (Data Models)**: 데이터 구조 및 데이터베이스와의 상호작용을 정의하는 코드는 `models/` 디렉토리 내에 위치시킵니다. (예: `tagged_file.py`)
-   **API (Application Programming Interface)**: 외부 서비스와의 연동 또는 내부 API 정의 코드는 `api/` 디렉토리 내에 위치시킵니다.
-   **테스트 코드**: 모든 테스트 코드는 원본 코드와 동일한 디렉토리 구조를 가지는 `tests/` 디렉토리 내에 위치시킵니다. (예: `tests/core/test_tag_manager.py`)

이러한 모듈화 정책을 통해 각 파일의 책임이 명확해지고, 코드 변경 시 영향을 받는 범위를 최소화할 수 있습니다.

## AI Agent Role Clarification (project_mandatory)

- **GEMINI**: The AI agent representing the planning team. Responsible for managing official documents (such as `docs/conversation_log.md`), project policies, decision records, and official issue tracking.
- **Cursor**: The AI agent representing the development team. Responsible for code implementation, debugging, experiments, internal technical discussions, code reviews, and temporary decisions. Manages the development team's internal log (`docs/developer_guide/dev_notes.md`).
- When a discussion or decision needs to be formalized, Cursor summarizes it in `dev_notes.md` and GEMINI migrates the summary to the official document (`docs/conversation_log.md`).

## 개발팀 내부 기록 및 역할(CURSOR)

- Cursor(개발팀 에이전트)는 개발팀의 일원으로서, 내부 기술 논의, 디버깅, 실험, 코드 리뷰, 임시 결정사항 등을 `docs/developer_guide/dev_notes.md`에 기록·관리한다.
- 공식화가 필요한 논의나 결정은 요약하여 GEMINI(기획팀) 측 공식 문서(`docs/conversation_log.md`)로 이관한다.
- 세션이 바뀌어도 dev_notes.md의 기록을 참고하여 일관된 개발 맥락을 유지한다.
- 개발팀의 실무적 히스토리, 온보딩, 회고 등에 dev_notes.md를 적극 활용한다.

## 3. 효과적인 커밋 전략

개발 과정 중 커밋은 단순히 변경 사항을 저장하는 것을 넘어, 작업의 논리적 단위를 기록하고 협업을 용이하게 하는 중요한 도구입니다. 작업 효율을 저해하지 않으면서도 코드 관리의 이점을 극대화하기 위한 커밋 전략을 제안합니다.

### 3.1. 커밋의 목적 이해
- **논리적 단위**: 각 커밋은 하나의 독립적인 논리적 변경 단위를 나타내야 합니다. (예: 버그 수정, 특정 기능 추가, 리팩토링 등)
- **히스토리 기록**: 커밋 히스토리는 프로젝트의 변경 이력을 명확하게 보여주는 문서입니다.

### 3.2. 적절한 커밋 단위 및 시점
- **작고 빈번하게 커밋**:
    - **"작동하는 최소 단위"**: 코드가 특정 기능을 수행하기 시작하거나, 버그가 수정되는 등 의미 있는 변화가 있을 때마다 커밋합니다.
    - **"테스트 통과 시점"**: 새로운 코드를 추가하거나 수정하여 테스트가 다시 통과하는 시점은 좋은 커밋 시점입니다.
    - **"작업 전환 전"**: 다른 작업으로 전환하기 전에 현재까지의 변경 사항을 커밋하여 작업 내용을 보존합니다.
    - **"점심시간/퇴근 전"**: 작업 내용을 잃지 않도록 주기적으로 커밋합니다.
- **단일 책임 원칙 (Single Responsibility Principle) 적용**:
    - 하나의 커밋은 하나의 논리적 변경에만 집중합니다. 예를 들어, 버그 수정과 새로운 기능 추가를 한 커밋에 섞지 않습니다.
    - UI 변경, 비즈니스 로직 변경, 데이터 모델 변경 등 관심사별로 분리하여 커밋하는 것을 고려합니다.
- **커밋 메시지 명확화**:
    - **제목 (Subject)**: 변경 사항을 한 줄로 요약합니다. (예: `feat: 사용자 프로필 업데이트 기능 추가`, `fix: 로그인 시 비밀번호 오류 수정`)
    - **본문 (Body)**: 변경의 `이유(Why)`와 `무엇을(What)` 변경했는지 상세히 설명합니다. `어떻게(How)` 변경했는지는 코드 자체로 설명되도록 합니다.

### 3.3. 효율성을 위한 Git 활용 팁
- **`git add -p` (patch add)**: 변경된 파일 내에서 특정 부분만 선택적으로 스테이징하여 커밋 단위를 세밀하게 조절할 수 있습니다.
- **`git commit --amend`**: 직전 커밋에 변경 사항을 추가하거나 커밋 메시지를 수정할 때 사용합니다.
- **`git rebase -i` (interactive rebase)**: PR을 올리기 전, 브랜치 내의 여러 작은 커밋들을 하나의 논리적 커밋으로 `squash`하거나, 커밋 순서를 변경하여 히스토리를 깔끔하게 정리할 수 있습니다. (단, 이미 공유된 커밋에는 사용하지 않도록 주의)

### 3.4. 기대 효과
- **쉬운 코드 리뷰**: 작은 단위의 커밋은 리뷰어가 변경 사항을 이해하고 검토하기 쉽게 만듭니다.
- **빠른 디버깅**: 문제가 발생했을 때 `git bisect` 등을 활용하여 문제 발생 지점을 빠르게 찾아낼 수 있습니다.
- **안전한 되돌리기**: 특정 변경 사항만 안전하게 되돌리거나 제거하기 용이합니다.
- **협업 용이성**: 다른 개발자와의 충돌을 줄이고, 병합(merge) 과정을 더 원활하게 만듭니다.

## 4. 브랜치 전략: Feature Branch Workflow

우리 프로젝트는 **Feature Branch Workflow (기능 브랜치 워크플로우)**를 사용합니다. 이는 새로운 기능 개발이나 주요 작업마다 별도의 브랜치를 생성하여 `main` 브랜치(또는 `develop` 브랜치)의 안정성을 유지하는 전략입니다.

### 4.1. `main` 브랜치
- 항상 안정적이고 배포 가능한 상태를 유지합니다.
- 새로운 기능 브랜치나 핫픽스 브랜치가 완료되면 `main` 브랜치로 머지됩니다.
- 직접 커밋은 지양합니다.

### 4.2. `feature/<기능-이름>` 브랜치
- 새로운 기능 개발, 큰 개선 사항, 또는 독립적인 작업 단위마다 `main` 브랜치에서 분기하여 생성합니다.
- 브랜치 이름은 `feature/` 접두사 뒤에 기능의 목적을 명확히 나타내는 이름을 붙입니다 (예: `feature/file-search`, `feature/batch-tagging`).
- 작업이 완료되고 충분히 테스트되면 `main` 브랜치로 머지됩니다.
- 머지 후에는 해당 `feature` 브랜치를 삭제합니다.

### 4.3. `hotfix/<핫픽스-이름>` 브랜치 (필요시)
- `main` 브랜치에서 발생한 긴급 버그를 수정할 때 `main` 브랜치에서 분기하여 생성합니다.
- 수정 완료 후 `main` 브랜치로 머지하고, 필요시 `develop` 브랜치(만약 사용한다면)에도 머지합니다.

## 5. 문서 명명 규칙 (Document Naming Conventions)

프로젝트 문서의 일관성과 가독성을 높이기 위해 다음과 같은 명명 규칙을 따릅니다.

### 5.1. 개발 요청 명세 (Development Request Specification, DRS)
- **목적**: 기획팀이 개발팀에게 특정 기능이나 개선 사항을 요청할 때 사용하는 문서.
- **형식**: `DRS-YYYYMMDD-XXX_기능명.md`
    - `DRS`: Development Request Specification의 약자.
    - `YYYYMMDD`: 문서 작성 연월일.
    - `XXX`: 해당 날짜의 순번 (예: 001, 002).
    - `기능명`: 기능의 핵심 내용을 요약한 영문명 (띄어쓰기 대신 언더스코어 `_` 사용).
- **저장 위치**: `docs/developer_guide/drs/`
- **예시**: `docs/developer_guide/drs/DRS-20250704-001_Batch_Tagging_Feature.md`

### 5.2. 기타 문서
- 다른 문서들도 목적과 내용을 명확히 나타낼 수 있도록 직관적인 이름을 사용합니다.
- 필요에 따라 접두사(예: `SPEC-`, `GUIDE-`)를 활용할 수 있습니다.