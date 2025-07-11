# 기능 명세 (Feature Specification)

*   **문서 ID**: `FS-20250711-002`
*   **작성일**: `2025년 7월 11일`
*   **작성자**: `Gemini`
*   **기능명**: `파일 태그 수정/삭제 기능`

---

### 1. 개요 (Overview)

이 기능은 사용자가 FileTagger 애플리케이션 내에서 파일 또는 디렉토리에 부여된 태그를 수정하거나 삭제할 수 있도록 합니다. 이를 통해 잘못 부여된 태그를 정리하거나, 더 이상 필요 없는 태그를 제거하여 파일 관리의 정확성과 효율성을 유지할 수 있습니다.

### 2. 주요 기능 상세 (Detailed Functional Description)

*   **2.1. 기능 설명**:
    *   **단일 파일 태그 수정**: 사용자가 파일 목록에서 단일 파일을 선택한 후, 해당 파일에 부여된 태그를 추가하거나 제거하여 태그 목록을 수정할 수 있습니다. 수정된 태그 목록은 "저장" 버튼을 통해 반영됩니다.
    *   **단일 파일 태그 개별 삭제**: 파일에 부여된 태그 칩 옆의 삭제 버튼을 클릭하여 해당 태그를 즉시 제거할 수 있습니다.
    *   **다중 파일 태그 일괄 삭제**: 사용자가 파일 목록에서 여러 파일을 선택하거나 특정 디렉토리를 선택한 후, 해당 파일들에 부여된 태그 중 특정 태그들을 일괄적으로 제거할 수 있습니다.
    *   **모든 태그 삭제 (개별 파일)**: 단일 파일에 부여된 모든 태그를 한 번에 제거할 수 있습니다. (현재 UI에서는 직접적인 버튼은 없으나, 모든 태그 칩을 삭제 후 저장하는 방식으로 가능)

*   **2.2. 입력/출력**:
    *   **입력**:
        *   대상 파일 경로 (단일 파일, 다중 파일 리스트, 디렉토리 경로)
        *   수정/삭제할 태그 (텍스트 입력 또는 선택)
    *   **출력**:
        *   성공/실패 메시지
        *   업데이트된 태그가 UI에 즉시 반영
        *   MongoDB에 태그 정보 업데이트

*   **2.3. 정상 흐름**:
    1.  사용자가 FileTagger 애플리케이션을 실행합니다.
    2.  **단일 파일 태그 수정**:
        *   사용자가 디렉토리 트리 또는 파일 목록에서 단일 파일을 선택합니다.
        *   `TagControlWidget`의 "개별 태깅" 탭에 해당 파일의 현재 태그가 태그 칩 형태로 표시됩니다.
        *   사용자가 태그 칩의 삭제 버튼을 클릭하여 태그를 제거하거나, 태그 입력 필드를 통해 새로운 태그를 추가합니다.
        *   "저장" 버튼을 클릭하면 `TagManager.update_tags` 메서드가 호출되어 파일의 태그 목록이 업데이트됩니다.
        *   저장 성공 메시지가 표시되고 UI가 업데이트됩니다.
    3.  **다중 파일 태그 일괄 삭제**:
        *   사용자가 파일 목록에서 여러 파일을 선택하거나 디렉토리 트리에서 디렉토리를 선택합니다.
        *   `TagControlWidget`의 "일괄 태깅" 탭에서 "일괄 태그 제거" 버튼을 클릭합니다.
        *   `BatchRemoveTagsDialog`가 열리고, 선택된 대상 파일들에 존재하는 모든 태그 목록이 표시됩니다.
        *   사용자가 제거하고자 하는 태그들을 선택하고 "확인" 버튼을 클릭합니다.
        *   `TagManager.remove_tags_from_files` 메서드가 호출되어 선택된 파일들에서 해당 태그들이 제거됩니다.
        *   제거 성공 메시지가 표시되고 UI가 업데이트됩니다.

*   **2.4. 예외 처리**:
    *   **데이터베이스 연결 실패**: MongoDB 연결에 실패할 경우 사용자에게 오류 메시지를 표시하고 태그 작업이 불가능함을 알립니다.
    *   **파일/디렉토리 접근 오류**: 파일 또는 디렉토리에 접근할 수 없는 경우(권한 문제 등) 오류 메시지를 표시합니다.
    *   **대상 없음**: 태그를 수정/삭제할 파일이나 디렉토리가 선택되지 않은 경우 경고 메시지를 표시합니다.
    *   **제거할 태그 없음**: 일괄 태그 제거 시 선택된 태그가 없는 경우 경고 메시지를 표시합니다.

### 3. UI/UX 요소 (UI/UX Elements)

*   **TagControlWidget**:
    *   **태그 칩**: 각 태그 칩에 포함된 삭제 버튼을 통해 개별 태그를 제거할 수 있습니다.
    *   **저장 버튼**: 개별 태깅 탭에서 수정된 태그 목록을 저장합니다.
    *   **일괄 태그 제거 버튼**: 일괄 태깅 탭에서 `BatchRemoveTagsDialog`를 엽니다.
*   **BatchRemoveTagsDialog**:
    *   **대상 표시**: 현재 태그를 제거할 파일 또는 디렉토리 대상을 표시합니다.
    *   **태그 검색 필드**: 제거할 태그를 검색할 수 있는 입력 필드.
    *   **태그 목록**: 대상 파일들에 존재하는 모든 태그를 체크박스 형태로 표시하여 사용자가 선택할 수 있도록 합니다.
    *   **확인/취소 버튼**: 태그 제거 작업을 확정하거나 취소합니다.

### 4. 기술적 구현 (Technical Implementation)

*   **TagManager**:
    *   `TagManager.update_tags(file_path, tags)`: 단일 파일의 태그를 새로운 리스트로 덮어씁니다. (수정)
    *   `TagManager.remove_tags_from_file(file_path, tags_to_remove)`: 단일 파일에서 특정 태그들을 제거합니다.
    *   `TagManager.clear_all_tags_from_file(file_path)`: 단일 파일의 모든 태그를 제거합니다.
    *   `TagManager.remove_tags_from_files(file_paths, tags_to_remove)`: 여러 파일에서 특정 태그들을 일괄 제거합니다.
    *   `TagManager.get_tags_for_file(file_path)`: 파일의 현재 태그를 조회합니다.
    *   `TagManager.get_files_in_directory(directory_path, recursive, file_extensions)`: 일괄 제거 대상 파일 목록을 가져옵니다.
*   **TagControlWidget**:
    *   `remove_tag(tag_text, mode)`: UI에서 태그 칩을 제거하고 내부 태그 리스트를 업데이트합니다.
    *   `save_individual_tags()`: `TagManager.update_tags`를 호출하여 개별 파일 태그를 저장합니다.
    *   `_on_batch_remove_tags_clicked()`: `BatchRemoveTagsDialog`를 생성하고 실행합니다.
*   **BatchRemoveTagsDialog**:
    *   `populate_tags()`: 대상 파일들로부터 모든 고유 태그를 수집하여 UI에 표시합니다.
    *   `get_tags_to_remove()`: 사용자가 선택한 태그 목록을 반환합니다.
*   **MongoDB**: `update_one` 및 `bulk_write` 연산을 사용하여 태그 데이터를 수정/삭제합니다.

### 5. 테스트 케이스 (Test Cases)

*   **TC-FS-012**: 단일 파일에서 특정 태그 삭제 (태그 칩 삭제 버튼 이용)
*   **TC-FS-013**: 단일 파일의 모든 태그 삭제 (모든 태그 칩 삭제 후 저장)
*   **TC-FS-014**: 여러 파일에서 특정 태그 일괄 삭제 (BatchRemoveTagsDialog 이용)
*   **TC-FS-015**: 디렉토리 내 파일에서 특정 태그 일괄 삭제 (BatchRemoveTagsDialog 이용)
*   **TC-FS-016**: 존재하지 않는 태그 삭제 시도 (오류 없이 처리되는지 확인)
*   **TC-FS-017**: 태그 삭제 후 UI 및 DB에 올바르게 반영되는지 확인
*   **TC-FS-018**: 일괄 태그 제거 시 제거할 태그를 선택하지 않았을 때 경고 메시지 확인

### 6. 관련 파일/모듈 (Related Files/Modules)

*   `main_window.py`: 메인 UI 및 위젯 연결
*   `core/tag_manager.py`: 태그 데이터베이스 로직
*   `widgets/tag_control_widget.py`: 태그 입력 및 표시 UI
*   `widgets/tag_chip.py`: 개별 태그 칩 UI
*   `widgets/batch_remove_tags_dialog.py`: 일괄 태그 제거 다이얼로그
*   `config.py`: MongoDB 연결 설정
*   `ui/tag_control_widget.ui`: 태그 제어 위젯 UI 정의

---
