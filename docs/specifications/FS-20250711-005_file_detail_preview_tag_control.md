# 기능 명세 (Feature Specification)

*   **문서 ID**: `FS-20250711-005`
*   **작성일**: `2025년 7월 11일`
*   **작성자**: `Gemini`
*   **기능명**: `파일 상세 정보 및 태그 제어 기능`

---

### 1. 개요 (Overview)

이 기능은 사용자가 FileTagger 애플리케이션에서 파일을 선택했을 때 해당 파일의 상세 정보를 미리보기로 표시하고, 태그를 추가/제거할 수 있는 UI를 제공합니다. 파일의 미리보기는 파일 형식에 따라 이미지, 비디오, 텍스트, PDF 등 다양한 형태로 제공되며, 태그 제어는 개별 파일에 대한 태그 관리와 일괄 태깅을 위한 두 가지 모드를 지원합니다.

### 2. 주요 기능 상세 (Detailed Functional Description)

*   **2.1. 기능 설명**:
    *   **파일 미리보기**: 선택된 파일의 형식에 따라 적절한 미리보기를 제공합니다. 이미지 파일은 썸네일로, 비디오 파일은 재생 가능한 형태로, 텍스트 파일은 내용 일부를, PDF 파일은 첫 페이지 썸네일을 표시합니다.
    *   **파일 메타데이터 표시**: 파일명, 경로, 크기, 수정일 등 파일의 기본 정보를 표시합니다.
    *   **현재 태그 표시**: 파일에 현재 적용된 태그들을 태그 칩 형태로 표시하고, 개별 태그 삭제 기능을 제공합니다.
    *   **태그 제어**: 개별 파일에 대한 태그 추가/제거 및 일괄 태깅을 위한 두 가지 모드를 지원합니다.
    *   **자동 모드 전환**: 단일 파일 선택 시 개별 태깅 모드로, 다중 파일 또는 디렉토리 선택 시 일괄 태깅 모드로 자동 전환됩니다.

*   **2.2. 입력/출력**:
    *   **입력**:
        *   선택된 파일 경로 (단일 또는 다중)
        *   태그 추가/제거 명령
        *   파일 형식별 미리보기 요청
    *   **출력**:
        *   파일 미리보기 (형식별)
        *   파일 메타데이터 정보
        *   현재 적용된 태그 목록
        *   태그 제어 UI (개별/일괄 모드)
        *   성공/실패 메시지

*   **2.3. 정상 흐름**:
    1.  사용자가 `FileListWidget`에서 파일을 선택합니다.
    2.  `MainWindow.on_file_selection_changed()` 메서드가 호출되어 선택된 파일들의 정보를 분석합니다.
    3.  **단일 파일 선택 시**:
        *   `FileDetailWidget.update_preview()`를 호출하여 파일 미리보기를 표시합니다.
        *   `TagControlWidget.update_for_target()`을 호출하여 개별 태깅 모드로 전환합니다.
        *   파일의 현재 태그를 로드하여 태그 칩으로 표시합니다.
        *   상태바에 파일 선택 메시지를 표시합니다.
    4.  **다중 파일 선택 시**:
        *   `FileDetailWidget.clear_preview()`를 호출하여 미리보기를 초기화합니다.
        *   `TagControlWidget.update_for_target()`을 호출하여 일괄 태깅 모드로 전환합니다.
        *   선택된 파일 수를 표시합니다.
        *   상태바에 다중 파일 선택 메시지를 표시합니다.
    5.  **파일 미리보기 처리**:
        *   파일 확장자를 확인하여 적절한 미리보기 방식을 결정합니다.
        *   이미지 파일: `QPixmap`을 사용하여 썸네일 생성 및 표시
        *   비디오 파일: `QMediaPlayer`와 `QVideoWidget`을 사용하여 재생 가능한 형태로 표시
        *   텍스트 파일: `QTextBrowser`를 사용하여 내용 일부 표시 (Markdown 지원)
        *   PDF 파일: PyMuPDF를 사용하여 첫 페이지 썸네일 생성 및 표시
        *   기타 파일: "미리보기를 지원하지 않는 형식" 메시지 표시
    6.  **태그 제어**:
        *   개별 태깅 모드: 파일의 현재 태그를 표시하고, 태그 추가/제거/저장 기능 제공
        *   일괄 태깅 모드: 선택된 파일들에 일괄적으로 태그를 적용하는 기능 제공

*   **2.4. 예외 처리**:
    *   **파일 접근 오류**: 파일을 읽을 수 없는 경우 "파일을 읽을 수 없습니다" 메시지를 표시합니다.
    *   **미지원 파일 형식**: 지원하지 않는 파일 형식의 경우 "미리보기를 지원하지 않는 형식" 메시지를 표시합니다.
    *   **대용량 파일**: 텍스트 파일이 너무 큰 경우 일부만 표시하고 경고 메시지를 표시합니다.
    *   **미디어 파일 오류**: 비디오 파일 재생 중 오류가 발생할 경우 재생을 중단하고 오류 메시지를 표시합니다.
    *   **태그 저장 실패**: 태그 저장 과정에서 오류가 발생할 경우 오류 메시지 박스를 표시합니다.

### 3. UI/UX 요소 (UI/UX Elements)

*   **FileDetailWidget**:
    *   **미리보기 영역**: `QStackedWidget`을 사용하여 파일 형식별 미리보기를 전환
    *   **이미지 미리보기**: `QLabel`을 사용하여 이미지 썸네일 표시
    *   **비디오 미리보기**: `QVideoWidget`과 재생 컨트롤 (재생/정지, 볼륨, 진행률)
    *   **텍스트 미리보기**: `QTextBrowser`를 사용하여 텍스트 내용 표시
    *   **PDF 미리보기**: `QLabel`을 사용하여 PDF 첫 페이지 썸네일 표시
    *   **메타데이터 영역**: 파일 정보를 HTML 형태로 표시하는 `QTextBrowser`
    *   **태그 영역**: 현재 파일의 태그들을 태그 칩으로 표시하는 `QGridLayout`
*   **TagControlWidget**:
    *   **탭 위젯**: "개별 태깅"과 "일괄 태깅" 탭으로 구성
    *   **개별 태깅 탭**: 단일 파일의 태그를 관리하는 UI
    *   **일괄 태깅 탭**: 다중 파일 또는 디렉토리에 태그를 일괄 적용하는 UI
    *   **태그 입력 필드**: 새로운 태그를 입력할 수 있는 `QLineEdit`
    *   **빠른 태그**: 자주 사용하는 태그를 버튼으로 제공하는 `QuickTagsWidget`
    *   **태그 칩**: 현재 적용된 태그를 표시하고 삭제할 수 있는 `TagChip` 위젯들
    *   **저장/적용 버튼**: 태그 변경사항을 저장하거나 적용하는 버튼들

### 4. 기술적 구현 (Technical Implementation)

*   **FileDetailWidget**:
    *   `update_preview(file_path)`: 파일 미리보기를 업데이트하는 메인 메서드
    *   `_update_metadata(file_path)`: 파일 메타데이터를 표시하는 메서드
    *   `_refresh_tag_chips(tags)`: 태그 칩들을 새로고침하는 메서드
    *   `_render_pdf_thumbnail(file_path)`: PDF 썸네일을 렌더링하는 메서드
    *   `_on_tag_chip_removed(tag_text)`: 개별 태그 삭제 이벤트 처리
    *   `_on_clear_all_tags_clicked()`: 모든 태그 삭제 이벤트 처리
    *   `toggle_play_pause()`: 비디오 재생/일시정지 토글
    *   `toggle_volume_slider()`: 볼륨 슬라이더 표시/숨김 토글
*   **TagControlWidget**:
    *   `update_for_target(target, is_dir)`: 대상에 따라 태그 제어 위젯을 업데이트
    *   `set_tags_for_mode(mode, tags)`: 특정 모드의 태그 목록을 설정
    *   `add_tag_from_input(mode)`: 입력 필드에서 태그를 추가
    *   `remove_tag(tag_text, mode)`: 특정 태그를 제거
    *   `save_individual_tags()`: 개별 파일의 태그를 저장
    *   `apply_batch_tags()`: 일괄 태깅을 적용
    *   `_on_batch_remove_tags_clicked()`: 일괄 태그 제거 다이얼로그 실행
*   **TagManager**:
    *   `get_tags_for_file(file_path)`: 파일의 현재 태그를 조회
    *   `update_tags(file_path, tags)`: 파일의 태그를 업데이트
    *   `remove_tags_from_file(file_path, tags_to_remove)`: 파일에서 특정 태그 제거
    *   `clear_all_tags_from_file(file_path)`: 파일의 모든 태그 제거
    *   `add_tags_to_files(file_paths, tags)`: 여러 파일에 태그 추가
    *   `add_tags_to_directory(directory_path, tags, recursive, file_extensions)`: 디렉토리에 일괄 태그 추가

### 5. 테스트 케이스 (Test Cases)

*   **TC-FS-035**: 이미지 파일 선택 시 썸네일 미리보기가 표시되는지 확인
*   **TC-FS-036**: 비디오 파일 선택 시 재생 가능한 미리보기가 표시되는지 확인
*   **TC-FS-037**: 텍스트 파일 선택 시 내용 미리보기가 표시되는지 확인
*   **TC-FS-038**: PDF 파일 선택 시 첫 페이지 썸네일이 표시되는지 확인
*   **TC-FS-039**: 단일 파일 선택 시 개별 태깅 모드로 자동 전환되는지 확인
*   **TC-FS-040**: 다중 파일 선택 시 일괄 태깅 모드로 자동 전환되는지 확인
*   **TC-FS-041**: 개별 태그 칩의 삭제 버튼이 올바르게 동작하는지 확인
*   **TC-FS-042**: 태그 입력 필드에서 새 태그를 추가할 수 있는지 확인
*   **TC-FS-043**: 빠른 태그 버튼을 통해 태그를 추가할 수 있는지 확인
*   **TC-FS-044**: 태그 저장 후 UI가 올바르게 업데이트되는지 확인
*   **TC-FS-045**: 일괄 태깅 적용이 올바르게 동작하는지 확인
*   **TC-FS-046**: 지원하지 않는 파일 형식에 대해 적절한 메시지가 표시되는지 확인
*   **TC-FS-047**: 대용량 파일 처리 시 성능이 적절한지 확인

### 6. 관련 파일/모듈 (Related Files/Modules)

*   `main_window.py`: 메인 UI 및 파일 선택 이벤트 처리
*   `widgets/file_detail_widget.py`: 파일 상세 정보 및 미리보기 위젯
*   `widgets/tag_control_widget.py`: 태그 제어 위젯
*   `widgets/tag_chip.py`: 개별 태그 칩 위젯
*   `widgets/quick_tags_widget.py`: 빠른 태그 선택 위젯
*   `core/tag_manager.py`: 태그 데이터베이스 관리
*   `ui/file_detail_content_widget.ui`: 파일 상세 정보 UI 정의
*   `ui/tag_control_widget.ui`: 태그 제어 위젯 UI 정의

--- 