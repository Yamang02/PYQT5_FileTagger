---
status: Approved
---
# 기능 명세 (Feature Specification)

*   **문서 ID**: `FS-20250711-003`
*   **작성일**: `2025년 07월 14일`
*   **작성자**: `Gemini (PM)`
*   **기능명**: `작업 공간 설정`

---

### 1. 개요 (Overview)

이 기능은 사용자가 FileTagger 애플리케이션에서 작업할 기본 디렉토리를 설정할 수 있도록 합니다. 설정된 작업 공간은 애플리케이션의 모든 파일 탐색 및 태깅 작업의 기준점이 되며, 전역 파일 검색의 범위를 결정합니다. 사용자는 필요에 따라 작업 공간을 변경하여 다른 디렉토리에서 파일 관리 작업을 수행할 수 있습니다.

### 2. 주요 기능 상세 (Detailed Functional Description)

*   **2.1. 기능 설명**:
    *   **작업 공간 선택**: 사용자가 메뉴바의 "파일 > 작업 공간 설정"을 통해 새로운 작업 디렉토리를 선택할 수 있습니다. 파일 탐색 다이얼로그를 통해 원하는 디렉토리를 선택하면 해당 경로가 새로운 작업 공간으로 설정됩니다.
    *   **설정 영속성**: 선택된 작업 공간 경로는 `config.py` 파일에 `DEFAULT_WORKSPACE_PATH` 변수로 저장되어 애플리케이션 재시작 시에도 유지됩니다.
    *   **UI 업데이트**: 작업 공간이 변경되면 디렉토리 트리, 파일 목록, 파일 상세 정보 등 모든 관련 UI 요소가 새로운 작업 공간을 기준으로 업데이트됩니다.
    *   **상태 표시**: 작업 공간 변경 시 상태바에 성공 메시지가 표시되어 사용자에게 변경 사항을 알립니다.

*   **2.2. 입력/출력**:
    *   **입력**:
        *   사용자가 선택한 디렉토리 경로
        *   현재 설정된 작업 공간 경로 (기본값으로 사용)
    *   **출력**:
        *   성공/실패 메시지 (상태바 및 메시지 박스)
        *   업데이트된 UI (디렉토리 트리, 파일 목록 등)
        *   `config.py` 파일의 `DEFAULT_WORKSPACE_PATH` 값 업데이트

*   **2.3. 정상 흐름**:
    1.  사용자가 메뉴바에서 "파일 > 작업 공간 설정"을 클릭합니다.
    2.  `QFileDialog.getExistingDirectory`를 통해 디렉토리 선택 다이얼로그가 열립니다.
    3.  사용자가 새로운 작업 디렉토리를 선택하고 "확인"을 클릭합니다.
    4.  선택된 경로가 유효한 디렉토리인지 확인합니다.
    5.  `config.py` 파일을 읽어 `DEFAULT_WORKSPACE_PATH` 값을 새로운 경로로 업데이트합니다.
    6.  메모리상의 `config.DEFAULT_WORKSPACE_PATH` 값을 업데이트합니다.
    7.  `DirectoryTreeWidget.set_root_path()`를 호출하여 디렉토리 트리의 루트를 변경합니다.
    8.  `FileListWidget.set_path()`를 호출하여 파일 목록을 새로운 작업 공간으로 초기화합니다.
    9.  `FileDetailWidget.clear_preview()`를 호출하여 파일 상세 정보를 초기화합니다.
    10. `TagControlWidget.clear_view()`를 호출하여 태그 제어 위젯을 초기화합니다.
    11. 상태바에 성공 메시지를 표시합니다.

*   **2.4. 예외 처리**:
    *   **사용자 취소**: 사용자가 디렉토리 선택 다이얼로그에서 "취소"를 클릭한 경우 아무 동작도 수행하지 않습니다.
    *   **파일 접근 오류**: `config.py` 파일을 읽거나 쓰는 과정에서 오류가 발생할 경우 오류 메시지 박스를 표시하고 작업을 중단합니다.
    *   **잘못된 경로**: 선택된 경로가 유효한 디렉토리가 아닌 경우 오류 메시지를 표시합니다.
    *   **권한 부족**: 선택된 디렉토리에 접근 권한이 없는 경우 오류 메시지를 표시합니다.

### 3. UI/UX 요소 (UI/UX Elements)

*   **메뉴바**: "파일" 메뉴 아래 "작업 공간 설정(&W)..." 항목을 통해 기능에 접근할 수 있습니다.
*   **디렉토리 선택 다이얼로그**: 표준 파일 탐색 다이얼로그를 통해 사용자가 원하는 디렉토리를 선택할 수 있습니다.
*   **상태바**: 작업 공간 변경 성공 시 "작업 공간이 '[경로]'로 설정되었습니다." 메시지가 5초간 표시됩니다.
*   **오류 메시지 박스**: 설정 과정에서 오류가 발생할 경우 상세한 오류 메시지를 포함한 경고 창이 표시됩니다.

### 4. 기술적 구현 (Technical Implementation)

*   **MainWindow**:
    *   `set_workspace()`: 메뉴 액션에 연결된 메인 메서드로, 전체 작업 공간 설정 프로세스를 관리합니다.
    *   `QFileDialog.getExistingDirectory()`: 사용자가 디렉토리를 선택할 수 있는 표준 다이얼로그를 제공합니다.
*   **Config 파일 관리**:
    *   `config.py` 파일을 직접 읽고 쓰는 방식으로 `DEFAULT_WORKSPACE_PATH` 값을 업데이트합니다.
    *   경로 구분자를 통일하기 위해 백슬래시를 슬래시로 변환합니다.
*   **위젯 업데이트**:
    *   `DirectoryTreeWidget.set_root_path()`: 디렉토리 트리의 루트 경로를 새로운 작업 공간으로 설정합니다.
    *   `FileListWidget.set_path()`: 파일 목록을 새로운 작업 공간으로 초기화합니다.
    *   `FileDetailWidget.clear_preview()`: 파일 상세 정보를 초기화합니다.
    *   `TagControlWidget.clear_view()`: 태그 제어 위젯을 초기화합니다.
*   **초기화 로직**: 애플리케이션 시작 시 `config.DEFAULT_WORKSPACE_PATH`가 유효한 디렉토리인지 확인하고, 유효하지 않으면 사용자의 홈 디렉토리를 기본값으로 사용합니다.

### 5. 테스트 케이스 (Test Cases)

*   **TC-FS-019**: 유효한 디렉토리를 작업 공간으로 설정하고 UI가 올바르게 업데이트되는지 확인
*   **TC-FS-020**: 작업 공간 설정 후 `config.py` 파일에 경로가 올바르게 저장되는지 확인
*   **TC-FS-021**: 애플리케이션 재시작 후 설정된 작업 공간이 유지되는지 확인
*   **TC-FS-022**: 디렉토리 선택 다이얼로그에서 "취소"를 클릭했을 때 아무 동작도 하지 않는지 확인
*   **TC-FS-023**: 존재하지 않는 디렉토리를 선택했을 때 적절한 오류 메시지가 표시되는지 확인
*   **TC-FS-024**: 권한이 없는 디렉토리를 선택했을 때 적절한 오류 메시지가 표시되는지 확인
*   **TC-FS-025**: `config.py` 파일 접근 오류 시 적절한 오류 메시지가 표시되는지 확인

### 6. 관련 파일/모듈 (Related Files/Modules)

*   `main_window.py`: 메인 UI 및 `set_workspace` 메서드 구현
*   `config.py`: 작업 공간 경로 설정 및 관리
*   `widgets/directory_tree_widget.py`: 디렉토리 트리 루트 경로 설정
*   `widgets/file_list_widget.py`: 파일 목록 초기화
*   `widgets/file_detail_widget.py`: 파일 상세 정보 초기화
*   `widgets/tag_control_widget.py`: 태그 제어 위젯 초기화
*   `ui/main_window.ui`: 메뉴바 UI 정의

--- 