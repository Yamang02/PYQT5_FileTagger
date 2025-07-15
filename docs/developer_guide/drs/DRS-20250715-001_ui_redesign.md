## 개발 요청 명세 (Development Request Specification)

*   **문서 ID**: `DRS-20250715-001`
*   **작성일**: `2025년 7월 15일`
*   **작성자**: `PM (Gemini)`
*   **관련 기능/모듈**: `애플리케이션 전역 UI`, `모든 위젯`
*   **관련 이슈**: 없음

---

### 1. 개요 (Overview)

*   이 개발 요청의 목적은 현재 기능적인 UI를 보다 **심미적이고 현대적인 디자인으로 개선**하는 것입니다.
*   일관된 디자인 시스템을 적용하여 사용자에게 더 나은 시각적 경험과 직관적인 사용성을 제공하고자 합니다.
*   UI와 로직이 분리된 현 아키텍처의 장점을 활용하여, 기능 변경 없이 순수하게 디자인 품질을 높이는 것을 목표로 합니다.

### 2. 요구사항 (Requirements)

*   **2.1. 기능 요구사항 (Functional Requirements)**
    *   기존의 모든 기능은 변경 없이 동일하게 작동해야 합니다.
    *   사용자는 새로운 디자인 시스템이 적용된 UI를 통해 기존의 모든 작업을 수행할 수 있어야 합니다.

*   **2.2. 비기능 요구사항 (Non-Functional Requirements)**
    *   **사용성**: 구글의 Material Design 원칙을 참고하여 일관되고 직관적인 UI를 제공해야 합니다. 사용자가 각 UI 요소의 기능을 쉽게 예측하고 사용할 수 있어야 합니다.
    *   **확장성**: 새로운 위젯이나 기능이 추가될 때 쉽게 적용할 수 있도록, 전역 스타일시트(QSS)를 기반으로 한 확장 가능한 디자인 시스템을 구축해야 합니다.
    *   **호환성**: Windows, macOS 등 다양한 운영체제에서 UI가 깨지지 않고 일관된 모습을 보여야 합니다.

### 3. UI/UX 설계 (User Interface / User Experience Design)

#### 3.1. 디자인 원칙: Material Design

구글의 Material Design 원칙을 차용하여 깔끔하고 정돈된 UI를 구현합니다. 그림자, 깊이, 표면과 같은 물리적 세계의 은유를 사용하여 사용자가 UI 구조를 직관적으로 이해하도록 돕습니다.

#### 3.2. 전역 스타일 시스템 (QSS)

-   **파일 위치**: 프로젝트 루트에 `assets` 디렉토리를 생성하고, 내부에 `style.qss` 파일을 위치시킵니다. (**확정 경로**: `C:\GIT\FileTagger\assets\style.qss`)
-   **적용**: `main.py`에서 애플리케이션 시작 시 해당 QSS 파일을 로드하여 전역 스타일을 적용합니다.
-   **주요 색상 팔레트**:
    *   Primary (주 색상): `#2196f3` (Blue)
    *   Light Primary (밝은 주 색상): `#e3f2fd` (Light Blue)
    *   Accent (강조 색상): `#ffc107` (Amber)
    *   Primary Text: `#212121` (Black)
    *   Secondary Text: `#757575` (Gray)
    *   Window Background: `#f5f5f5`
-   **폰트 시스템**:
    *   기본 폰트: `맑은 고딕` (Windows), `Apple SD Gothic Neo` (macOS), `Noto Sans KR` (Linux) - 시스템에 따라 폴백(fallback) 적용
    *   **폰트 위계**:
| 레벨 | 사용처 예시 | 폰트 크기 | 굵기 |
| :--- | :--- | :--- | :--- |
| **Level 1 (타이틀)** | 위젯 그룹의 제목 (예: '태그 컨트롤', '모든 태그') | 11pt | Bold |
| **Level 2 (부제목/중요 정보)** | 선택된 파일/디렉토리 경로, 검색 결과 요약 | 10pt | Normal |
| **Level 3 (기본 텍스트)** | `QListView`, `QTreeView` 아이템, `QLabel`, `QPushButton` | 9pt | Normal |
| **Level 4 (보조 텍스트)** | 파일 메타데이터, 상태 표시줄 메시지, 태그 칩 | 8pt | Normal |

#### 3.3. 컴포넌트별 디자인 가이드

-   **버튼 (QPushButton)**:
    *   기본 상태: 평평한(flat) 디자인, 4px의 둥근 모서리, 투명 또는 밝은 회색 배경.
    *   Hover 상태: 배경색이 약간 어두워짐.
    *   Pressed 상태: **물결 효과(Ripple Effect) 대신 더 어두운 배경색으로 변경하여 통일합니다.**
    *   Primary 버튼 (예: '적용'): 주 색상(`Primary`)을 배경으로 사용.
-   **입력 필드 (QLineEdit)**:
    *   하단에만 1px의 실선 테두리 적용.
    *   Focus 상태: 하단 테두리가 `Primary` 색상으로 변경되고 두께가 2px로 두꺼워짐.
-   **카드 (Card) / 패널 (Panel)**:
    *   `QFrame` 등을 사용하여 각 위젯 영역을 논리적인 '카드'로 묶습니다.
    *   **그림자 효과**: `QGraphicsDropShadowEffect`를 적용하여 깊이감을 표현합니다.
        *   `blurRadius`: 15
        *   `xOffset`: 0
        *   `yOffset`: 2
        *   `color`: `#d0d0d0`
-   **아이콘**:
    *   **아이콘 라이브러리**: **Google Material Symbols**를 표준으로 사용합니다. ([https://fonts.google.com/icons](https://fonts.google.com/icons))
    *   **사용 방식**: 필요한 아이콘을 SVG 형식으로 다운로드하여 `assets/icons/` 디렉토리에 저장 후 사용합니다.
    *   **크기 및 색상**: 기본 `20x20` 픽셀, `Primary Text` 색상(`#212121`)을 사용합니다.
    *   **적용 예시**: 검색(search), 초기화(close), 고급 검색 토글(expand_more/expand_less) 등.

### 4. 기술적 고려사항 (Technical Considerations)

*   **QSS 적용**: `main.py`에서 애플리케이션 시작 시 `assets/style.qss` 파일을 읽어 `app.setStyleSheet()`를 통해 적용해야 합니다.
*   **.ui 파일 수정**: **프로젝트 내 모든 .ui 파일**의 위젯 `styleSheet` 속성에 직접 작성된 인라인 스타일은 모두 제거하고, 전역 QSS에서 스타일을 통합 관리하는 것을 원칙으로 합니다.
*   **리팩토링**: 디자인 적용을 용이하게 하기 위해 일부 위젯의 구조 리팩토링이 필요할 수 있습니다.

### 5. 테스트 시나리오 (Test Scenarios)

*   애플리케이션 실행 시 전역 스타일이 모든 위젯에 올바르게 적용되는지 확인.
*   각 위젯(버튼, 입력 필드 등)이 Hover, Pressed, Focus 등 각 상태에 따라 디자인 가이드에 맞게 표시되는지 확인.
*   창 크기를 조절하거나 다른 OS 환경에서도 UI 레이아웃이 깨지지 않는지 확인.

### 6. 기타 (Miscellaneous)

*   이 작업은 기능 변경을 포함하지 않으므로, 기존 로직의 안정성을 해치지 않는 선에서 진행되어야 합니다.
*   개발자는 디자인 가이드라인을 최대한 준수하되, 기술적 제약이 있을 경우 PM과 협의하여 대안을 찾습니다.

---