# FileTagger 아키텍처 가이드

이 문서는 FileTagger 프로젝트의 아키텍처, 설계 원칙, 주요 컴포넌트의 역할과 상호작용을 설명합니다.

## 1. 설계 목표

FileTagger는 다음과 같은 설계 목표를 가지고 개발되었습니다.

*   **유지보수성 (Maintainability):** 코드의 각 부분이 명확한 책임을 가지도록 분리하여, 기능 변경 및 버그 수정이 용이하도록 합니다.
*   **확장성 (Scalability):** 새로운 기능을 추가하거나 기존 기능을 변경할 때, 다른 부분에 미치는 영향을 최소화할 수 있는 유연한 구조를 지향합니다.
*   **테스트 용이성 (Testability):** UI와 비즈니스 로직을 분리하여 각 부분을 독립적으로 테스트할 수 있도록 합니다.
*   **안정성 (Stability):** 복잡한 의존성을 제거하고 데이터 흐름을 단순화하여 예측 가능하고 안정적인 애플리케이션을 구축합니다.

## 2. 핵심 아키텍처: MVVM (Model-View-ViewModel)

FileTagger는 UI 코드와 비즈니스 로직을 효과적으로 분리하기 위해 **MVVM (Model-View-ViewModel)** 패턴을 핵심 아키텍처로 채택했습니다.

*(이미지: 간단한 MVVM 구조 다이어그램)*

*   **Model**: 애플리케이션의 핵심 데이터와 비즈니스 로직을 담당합니다.
    *   **Services (`core/services/`):** `TagService`와 같이 특정 도메인의 비즈니스 로직을 처리합니다.
    *   **Repositories (`core/repositories/`):** `TagRepository`와 같이 MongoDB와의 데이터 I/O를 담당하며, 데이터 영속성을 관리합니다.
    *   **Data Models**: 데이터 구조를 정의합니다.

*   **View**: 사용자에게 보여지는 UI를 담당합니다.
    *   **Widgets (`widgets/`):** `FileListWidget`, `TagControlWidget` 등 사용자와 직접 상호작용하는 커스텀 위젯들로 구성됩니다.
    *   **UI Files (`ui/`):** Qt Designer로 생성된 `.ui` 파일들로, 위젯의 레이아웃을 정의합니다.
    *   View는 오직 ViewModel에만 의존하며, Model에 직접 접근하지 않습니다.

*   **ViewModel**: View와 Model 사이의 중재자 역할을 합니다.
    *   **ViewModels (`viewmodels/`):** `FileDetailViewModel`, `TagControlViewModel` 등이 있으며, View에 표시될 데이터를 Model로부터 가져와 가공합니다.
    - View의 사용자 입력을 받아 Model의 비즈니스 로직을 호출하고, 그 결과를 다시 View에 전달(시그널-슬롯 메커니즘 사용)합니다.

## 3. 주요 컴포넌트 및 책임

### 3.1. `MainWindow`와 UI 관리자

`MainWindow`는 애플리케이션의 메인 창이지만, 모든 로직을 담고 있지 않습니다. 대신, 여러 관리자(Manager) 클래스에 책임을 위임하여 단일 책임 원칙을 준수합니다.

*   **`UISetupManager` (`core/ui/`):**
    *   모든 UI 위젯의 생성, 초기화, 레이아웃 배치를 담당합니다.
    *   위젯에 그림자 효과 등을 주기 위해 `QFrame`으로 래핑하는 로직을 포함하며, 외부에서는 `get_widget('widget_name')` 메서드를 통해서만 래핑되지 않은 **실제 위젯 인스턴스**에 접근하도록 하여 `AttributeError` 발생을 원천적으로 차단하고 캡슐화를 강화했습니다.

*   **`SignalConnectionManager` (`core/ui/`):**
    *   애플리케이션 내의 모든 시그널-슬롯 연결을 담당합니다.
    *   ViewModel과 View, 또는 View와 View 간의 상호작용을 정의하여 코드의 응집도를 높입니다.

### 3.2. 위젯 구조 단순화 원칙

프로젝트 초기에는 일부 위젯이 복잡한 내부 로직과 상태를 가지고 있었습니다. 하지만 유지보수성과 안정성을 높이기 위해 다음과 같은 **"데이터 → 뷰모델 → UI"**의 단순하고 일관된 데이터 흐름 원칙을 적용하여 리팩토링을 진행했습니다.

*   **상태는 ViewModel이 관리:** 위젯 자체는 상태를 가지지 않으며, 모든 상태 변경은 ViewModel을 통해 이루어집니다.
*   **UI 갱신은 데이터 바인딩으로:** ViewModel의 데이터가 변경되면, 시그널을 통해 View에 알리고 View는 해당 데이터를 기반으로 UI를 다시 그립니다. 불필요한 강제 새로고침 로직을 제거하여 성능과 안정성을 높였습니다.
*   **복잡한 레이아웃 조작 지양:** `FileDetailWidget`의 사례처럼, `QStackedWidget`과 같은 복잡한 구조 대신 위젯을 직접 `hide()`/`show()` 하는 단순한 방식으로 변경하여 예측 가능성을 높이고 잠재적인 오류를 줄였습니다.

## 4. 데이터 흐름 예시: 태그 추가

1.  **View (`TagControlWidget`):** 사용자가 태그 입력창에 텍스트를 입력하고 Enter 키를 누릅니다.
2.  **View:** `tag_added` 시그널을 발생시킵니다.
3.  **ViewModel (`TagControlViewModel`):** 해당 시그널을 받아, 입력된 태그 정보와 현재 선택된 파일 경로를 `TagService`에 전달합니다.
4.  **Model (`TagService`):** 비즈니스 로직(e.g., 태그 유효성 검사)을 수행한 후, `TagRepository`를 호출하여 데이터베이스에 태그를 저장합니다.
5.  **Model (`TagRepository`):** MongoDB에 해당 파일의 태그 정보를 업데이트합니다.
6.  **EventBus/Signal:** 태그 변경이 완료되면 `EventBus`나 시그널을 통해 시스템 전체에 `tags_updated`와 같은 이벤트를 알립니다.
7.  **ViewModels:** `FileDetailViewModel`, `FileListViewModel` 등 관련된 다른 ViewModel들이 이 이벤트를 수신하고, 자신의 데이터를 갱신한 후 View에 변경을 알립니다.
8.  **Views:** 각 위젯들은 ViewModel로부터 받은 최신 데이터로 화면을 다시 그려 사용자에게 변경된 내용을 보여줍니다.

이러한 구조를 통해 각 컴포넌트는 자신의 책임에만 집중할 수 있으며, 전체 시스템은 유연하고 확장 가능한 형태로 유지됩니다.
