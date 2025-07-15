---
status: Approved
---
# 기능 명세 (Feature Specification)

*   **문서 ID**: `FS-20250711-008`
*   **작성일**: `2025년 07월 14일`
*   **작성자**: `Gemini (PM)`
*   **기능명**: `일괄 태그 제거`

---

### 1. 개요 (Overview)

이 기능은 사용자가 FileTagger 애플리케이션에서 선택된 디렉토리 내의 파일들 또는 다중 선택된 파일들에서 특정 태그들을 일괄적으로 제거할 수 있도록 합니다. 일괄 태그 제거는 대량의 파일에서 불필요한 태그를 효율적으로 정리할 때 유용하며, 디렉토리 컨텍스트 메뉴와 태그 제어 위젯의 버튼을 통해 두 가지 진입점을 제공합니다.

### 2. 주요 기능 상세 (Detailed Functional Description)

*   **2.1. 기능 설명**:
    *   **일괄 태그 제거**: 선택된 디렉토리 내의 모든 파일 또는 다중 선택된 파일들에서 지정된 태그들을 일괄적으로 제거합니다.
    *   **다중 진입점**: 디렉토리 트리의 컨텍스트 메뉴와 태그 제어 위젯의 "일괄 태그 제거" 버튼을 통해 기능에 접근할 수 있습니다.
    *   **태그 선택 다이얼로그**: 제거할 태그들을 선택할 수 있는 전용 다이얼로그를 제공합니다.
    *   **실시간 태그 수집**: 대상 파일들에 존재하는 모든 고유 태그를 자동으로 수집하여 선택 옵션으로 제공합니다.
    *   **태그 검색**: 다이얼로그 내에서 제거할 태그를 검색할 수 있는 기능을 제공합니다.
    *   **결과 피드백**: 일괄 제거 작업의 성공/실패 결과를 사용자에게 명확히 알립니다.

*   **2.2. 입력/출력**:
    *   **입력**:
        *   대상 디렉토리 경로 또는 다중 선택된 파일 경로들
        *   제거할 태그 목록 (사용자가 다이얼로그에서 선택)
    *   **출력**:
        *   일괄 제거 작업 결과 (성공/실패, 처리된 파일 수)
        *   성공/실패 메시지
        *   업데이트된 파일 목록 및 태그 정보

*   **2.3. 정상 흐름**:
    1.  **진입점 1 - 디렉토리 컨텍스트 메뉴**:
        *   사용자가 디렉토리 트리에서 디렉토리를 우클릭합니다.
        *   컨텍스트 메뉴에서 "일괄 태그 제거..."를 선택합니다.
        *   `MainWindow.on_directory_tree_context_menu()` 메서드가 호출됩니다.
        *   `MainWindow._open_batch_remove_tags_dialog()` 메서드가 호출되어 다이얼로그를 생성합니다.
    2.  **진입점 2 - 태그 제어 위젯 버튼**:
        *   사용자가 태그 제어 위젯의 "일괄 태그 제거" 버튼을 클릭합니다.
        *   `TagControlWidget._on_batch_remove_tags_clicked()` 메서드가 호출됩니다.
        *   현재 선택된 대상(디렉토리 또는 다중 파일)을 확인합니다.
        *   대상이 없으면 경고 메시지를 표시하고 종료합니다.
        *   `BatchRemoveTagsDialog`를 생성하여 다이얼로그를 표시합니다.
    3.  **다이얼로그 초기화**:
        *   `BatchRemoveTagsDialog`가 생성되면서 대상 파일들의 모든 고유 태그를 수집합니다.
        *   `BatchRemoveTagsDialog.populate_tags()` 메서드가 호출되어 태그 목록을 생성합니다.
        *   수집된 태그들이 체크박스 형태의 태그 칩으로 다이얼로그에 표시됩니다.
    4.  **태그 선택**:
        *   사용자가 제거하고자 하는 태그들을 체크박스로 선택합니다.
        *   필요시 다이얼로그의 검색 필드를 사용하여 특정 태그를 찾을 수 있습니다.
        *   `BatchRemoveTagsDialog.filter_tags()` 메서드를 통해 실시간 검색이 지원됩니다.
    5.  **일괄 제거 실행**:
        *   사용자가 "확인" 버튼을 클릭합니다.
        *   `BatchRemoveTagsDialog.get_tags_to_remove()` 메서드가 호출되어 선택된 태그 목록을 반환합니다.
        *   선택된 태그가 없으면 정보 메시지를 표시하고 종료합니다.
        *   대상 파일 목록을 생성합니다:
            *   다중 파일 선택의 경우: 선택된 파일 경로들
            *   디렉토리 선택의 경우: `TagManager.get_files_in_directory()`를 통해 디렉토리 내 모든 파일 경로들
        *   `TagManager.remove_tags_from_files()` 메서드를 호출하여 일괄 제거를 실행합니다.
    6.  **결과 처리**:
        *   일괄 제거 작업의 결과를 확인합니다.
        *   성공 시: 성공 메시지와 함께 처리된 파일 수를 표시합니다.
        *   실패 시: 오류 메시지를 표시합니다.
        *   성공한 경우 `TagControlWidget.tags_updated.emit()`을 호출하여 UI를 업데이트합니다.

*   **2.4. 예외 처리**:
    *   **대상 없음**: 태그를 제거할 파일이나 디렉토리가 선택되지 않은 경우 "대상 없음" 경고 메시지를 표시합니다.
    *   **태그 미선택**: 제거할 태그를 선택하지 않은 경우 "제거할 태그가 선택되지 않았습니다." 정보 메시지를 표시합니다.
    *   **파일 없음**: 선택된 디렉토리 내에 태그를 제거할 파일이 없는 경우 "선택된 디렉토리 내에 태그를 제거할 파일이 없습니다." 정보 메시지를 표시합니다.
    *   **데이터베이스 오류**: MongoDB 연결 또는 쿼리 오류 시 상세한 오류 메시지를 표시합니다.
    *   **권한 오류**: 파일 접근 권한이 없는 경우 해당 파일은 처리에서 제외하고 계속 진행합니다.

### 3. UI/UX 요소 (UI/UX Elements)

*   **BatchRemoveTagsDialog**:
    *   **대상 표시 라벨**: 현재 태그를 제거할 파일 또는 디렉토리 대상을 표시하는 `QLabel`
    *   **태그 검색 필드**: 제거할 태그를 검색할 수 있는 `QLineEdit` 위젯
    *   **태그 목록 영역**: 대상 파일들에 존재하는 모든 태그를 체크박스 형태로 표시하는 `QScrollArea`
    *   **태그 칩**: 각 태그를 체크박스 형태로 표시하는 `TagChip` 위젯들
    *   **확인/취소 버튼**: 작업을 확정하거나 취소하는 표준 다이얼로그 버튼
*   **디렉토리 컨텍스트 메뉴**: 디렉토리 우클릭 시 나타나는 "일괄 태그 제거..." 메뉴 항목
*   **태그 제어 위젯**: "일괄 태그 제거" 버튼이 포함된 일괄 태깅 탭
*   **메시지 박스**: 작업 결과 및 오류 메시지를 표시하는 `QMessageBox`

### 4. 기술적 구현 (Technical Implementation)

*   **MainWindow**:
    *   `on_directory_tree_context_menu(directory_path, global_pos)`: 디렉토리 컨텍스트 메뉴 이벤트 처리
    *   `_open_batch_remove_tags_dialog(target_path)`: 일괄 태그 제거 다이얼로그를 열고 결과를 처리하는 메서드
*   **TagControlWidget**:
    *   `_on_batch_remove_tags_clicked()`: 일괄 태그 제거 버튼 클릭 이벤트 처리
    *   `tags_updated`: 태그 업데이트 시그널 (`pyqtSignal()`)
*   **BatchRemoveTagsDialog**:
    *   `__init__(tag_manager, target_path, parent)`: 다이얼로그 초기화 및 UI 설정
    *   `setup_ui()`: 다이얼로그 UI 구성
    *   `populate_tags()`: 대상 파일들로부터 모든 고유 태그를 수집하여 UI에 표시
    *   `filter_tags(text)`: 태그 검색 필터링 기능
    *   `update_chip_layout(tags)`: 태그 칩 레이아웃 업데이트
    *   `get_tags_to_remove() -> list[str]`: 사용자가 선택한 태그 목록을 반환
*   **TagManager**:
    *   `get_files_in_directory(directory_path, recursive, file_extensions)`: 디렉토리 내 파일 목록 조회
    *   `get_tags_for_file(file_path)`: 특정 파일의 태그 조회
    *   `remove_tags_from_files(file_paths, tags_to_remove) -> dict`: 여러 파일에서 태그 일괄 제거
*   **DirectoryTreeWidget**:
    *   `directory_context_menu_requested`: 디렉토리 컨텍스트 메뉴 요청 시그널 (`pyqtSignal(str, object)`)

### 5. 테스트 케이스 (Test Cases)

*   **TC-FS-072**: 디렉토리 컨텍스트 메뉴를 통해 일괄 태그 제거 다이얼로그가 열리는지 확인
*   **TC-FS-073**: 태그 제어 위젯의 버튼을 통해 일괄 태그 제거 다이얼로그가 열리는지 확인
*   **TC-FS-074**: 대상 파일들이 올바르게 표시되는지 확인
*   **TC-FS-075**: 대상 파일들의 모든 고유 태그가 다이얼로그에 표시되는지 확인
*   **TC-FS-076**: 태그 검색 기능이 올바르게 동작하는지 확인
*   **TC-FS-077**: 체크박스를 통해 태그를 선택할 수 있는지 확인
*   **TC-FS-078**: 선택된 태그들이 올바르게 제거되는지 확인
*   **TC-FS-079**: 태그 미선택 시 적절한 메시지가 표시되는지 확인
*   **TC-FS-080**: 대상 없음 시 적절한 경고 메시지가 표시되는지 확인
*   **TC-FS-081**: 일괄 제거 성공 시 적절한 성공 메시지가 표시되는지 확인
*   **TC-FS-082**: 일괄 제거 실패 시 적절한 오류 메시지가 표시되는지 확인
*   **TC-FS-083**: 일괄 제거 후 UI가 올바르게 업데이트되는지 확인
*   **TC-FS-084**: 대용량 디렉토리에서 일괄 제거 성능이 적절한지 확인

### 6. 관련 파일/모듈 (Related Files/Modules)

*   `main_window.py`: 메인 UI 및 디렉토리 컨텍스트 메뉴 처리
*   `widgets/batch_remove_tags_dialog.py`: 일괄 태그 제거 다이얼로그 구현
*   `widgets/tag_control_widget.py`: 태그 제어 위젯 및 일괄 태그 제거 버튼
*   `widgets/directory_tree_widget.py`: 디렉토리 트리 및 컨텍스트 메뉴
*   `core/tag_manager.py`: 태그 데이터베이스 관리 및 일괄 제거 로직
*   `widgets/tag_chip.py`: 체크박스 형태의 태그 칩 위젯
*   `ui/batch_remove_tags_dialog.ui`: 일괄 태그 제거 다이얼로그 UI 정의
*   `ui/tag_control_widget.ui`: 태그 제어 위젯 UI 정의

--- 