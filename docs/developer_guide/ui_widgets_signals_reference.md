# UI 위젯 및 시그널-슬롯 참조 가이드

이 문서는 FileTagger 애플리케이션의 현재 아키텍처, 주요 UI 위젯, 그리고 이들 간의 시그널-슬롯 연결 구조를 설명합니다. 코드를 수정하거나 새로운 기능을 추가할 때 반드시 이 문서를 참조하고 최신 상태로 유지해야 합니다.

## 1. 아키텍처 개요: 컴포넌트 기반 UI

FileTagger는 각 위젯이 명확하게 정의된 단일 책임(Single Responsibility)을 갖는 **컴포넌트 기반 아키텍처**를 따릅니다. `MainWindow`가 중앙 컨트롤 타워 역할을 하며, 각 독립적인 위젯들을 조합하고 이들 간의 상호작용을 시그널-슬롯 메커니즘을 통해 조율합니다.

### 아키텍처 결정 배경 (UnifiedTaggingPanel 계획 취소)

> 초기에는 개별/일괄 태깅 기능을 `UnifiedTaggingPanel`이라는 단일 위젯으로 통합하려는 시도가 있었습니다. (`_backup_ui_refactoring` 디렉토리 참조) 하지만 개발 과정에서 해당 패널의 복잡성이 과도하게 증가하고 위젯 간의 의존성이 높아지는 문제가 발생했습니다. 
> 
> 그 결과, 각 위젯의 역할을 명확히 분리하고 `MainWindow`에서 이를 제어하는 현재의 컴포Nᅥᆫ트 기반 아키텍처가 유지보수성, 확장성, 안정성 측면에서 더 유리하다고 판단하여 **`UnifiedTaggingPanel` 계획은 공식적으로 취소되었습니다.**

## 2. 핵심 위젯 및 역할

애플리케이션의 UI는 다음과 같은 핵심 위젯들로 구성됩니다.

| 위젯 클래스 | 파일 경로 | 역할 |
| :--- | :--- | :--- |
| `MainWindow` | `main_window.py` | 모든 위젯을 포함하고 배치하는 메인 컨테이너. 위젯 간 시그널-슬롯 연결을 총괄. |
| `DirectoryTreeWidget` | `widgets/directory_tree_widget.py` | 파일 시스템의 디렉토리 구조를 트리 형태로 제공하고, 디렉토리 선택 및 검색 이벤트를 발생시킴. |
| `FileListWidget` | `widgets/file_list_widget.py` | 선택된 디렉토리의 파일 목록 또는 검색 결과를 테이블 형태로 표시. 태그 기반 필터링 기능 포함. |
| `FileDetailWidget` | `widgets/file_detail_widget.py` | 단일 파일 선택 시, 파일의 썸네일, 메타데이터, 현재 태그 목록을 표시. |
| `TagControlWidget` | `widgets/tag_control_widget.py` | **태그 편집의 핵심 UI.** "개별 태깅"과 "일괄 태깅" 탭을 통해 상황에 맞는 태그 편집 기능을 제공. |
| `BatchTaggingPanel` | `widgets/batch_tagging_panel.py` | **독립 실행 가능한 일괄 태깅 패널.** 디렉토리 단위의 상세한 일괄 태깅 옵션과 백그라운드 처리 기능을 제공. |

## 3. 시그널-슬롯 연결 (`MainWindow.setup_connections`)

`MainWindow`는 다음과 같이 위젯 간의 상호작용을 정의합니다.

- **디렉토리 선택 → 파일 목록 업데이트**
    - **시그널**: `DirectoryTreeWidget.tree_view.clicked`
    - **슬롯**: `MainWindow.on_directory_selected`
    - **동작**: 선택된 디렉토리 경로를 `FileListWidget.set_path()`에 전달하여 파일 목록을 갱신하고, `TagControlWidget`을 해당 디렉토리 타겟으로 설정합니다.

- **파일 선택 → 상세 정보 및 태그 편집기 업데이트**
    - **시그널**: `FileListWidget.list_view.selectionModel().selectionChanged`
    - **슬롯**: `MainWindow.on_file_selection_changed`
    - **동작**:
        - **단일 파일 선택 시**: `FileDetailWidget.update_preview()`를 호출하여 상세 정보를 표시하고, `TagControlWidget`을 해당 파일 타겟 ("개별 태깅" 모드)으로 설정합니다.
        - **다중 파일 선택 시**: `FileDetailWidget`을 초기화하고, `TagControlWidget`을 선택된 파일 목록 타겟 ("일괄 태깅" 모드)으로 설정합니다.

- **태그 필터링**
    - **시그널**: `DirectoryTreeWidget.tag_filter_changed`
    - **슬롯**: `FileListWidget.set_tag_filter`
    - **동작**: 태그 검색어에 따라 `FileListWidget`의 파일 목록을 실시간으로 필터링합니다.

- **전역 파일 검색**
    - **시그널**: `DirectoryTreeWidget.global_file_search_requested`
    - **슬롯**: `MainWindow.on_global_file_search_requested`
    - **동작**: 작업 공간 전체에서 파일을 검색하여 `FileListWidget.set_search_results()`를 통해 결과를 표시합니다.

- **일괄 태깅 다이얼로그 실행 (향후 연결 예정)**
    - **시그널**: `MainWindow.actionBatchTagging.triggered`
    - **슬롯**: `MainWindow.open_batch_tagging_dialog`
    - **현재 상태**: 기능이 호출되었다는 로그만 출력합니다. 향후 이 슬롯에서 `BatchTaggingPanel`을 포함하는 별도의 다이얼로그를 생성하고 실행하는 로직이 구현될 예정입니다.

## 4. 데이터 흐름 요약

1.  사용자가 `DirectoryTreeWidget`에서 디렉토리를 선택합니다.
2.  `MainWindow`가 이 시그널을 받아 `FileListWidget`에 파일 목록 표시를 지시합니다.
3.  사용자가 `FileListWidget`에서 하나 또는 여러 파일을 선택합니다.
4.  `MainWindow`가 선택 상태를 감지하여 `FileDetailWidget`과 `TagControlWidget`에 필요한 정보를 전달하고 UI를 업데이트하도록 지시합니다.
5.  사용자는 `TagControlWidget`을 통해 태그를 편집하고, `TagControlWidget`은 내부적으로 `TagManager`를 호출하여 변경 사항을 데이터베이스에 저장합니다.

이러한 구조는 각 컴포넌트의 독립성을 보장하고, 기능 변경 및 확장이 용이하도록 설계되었습니다.
