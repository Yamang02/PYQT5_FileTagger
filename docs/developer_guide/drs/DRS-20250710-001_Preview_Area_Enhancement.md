---
status: Approved
---
# 개발 요청 명세 (DRS)

## 문서 ID: DRS-20250710-001
## 제목: 미리보기(상세 정보) 영역 기능 강화
## 작성일: 2025년 7월 10일 목요일
## 버전: 1.0

---

### 1. 개요

본 문서는 FileTagger 애플리케이션의 파일 상세 정보 영역(현재 미리보기, 메타데이터, 태그 정보를 포함)의 기능을 강화하기 위한 개발 요구사항을 정의합니다. 현재 이미지 파일만 제한적으로 지원하는 미리보기 기능을 비디오, 문서 파일까지 확장하고, 전체 화면 모드에서 콘텐츠 가시성을 극대화하여 사용자 경험을 향상시키는 것을 목표로 합니다.

### 2. 목표

*   전체 화면 모드에서 미리보기 영역이 동적으로 확대되어 사용자가 콘텐츠에 집중할 수 있도록 UI를 개선합니다.
*   기존 이미지 미리보기 기능 외에 비디오 파일 재생 및 문서 파일 내용 표시 기능을 추가합니다.
*   다양한 파일 형식에 대한 미리보기 지원을 통해 파일 탐색 및 확인의 효율성을 높입니다.

### 3. 기능 요구사항

#### 3.1. 전체 화면 모드 레이아웃 최적화

*   **요구사항**: 사용자가 애플리케이션 창을 전체 화면으로 전환했을 때, 중앙 영역의 상단에 위치한 `FileDetailWidget`의 세로 크기가 동적으로 확대되어야 합니다.
*   **구현 방향**:
    *   `MainWindow` 클래스에서 창 상태 변경 이벤트(`changeEvent`)를 감지합니다.
    *   창이 `Qt.WindowMaximized` 상태가 되면, `mainSplitter`와 중앙 `splitter`의 `setSizes()` 메서드를 호출하여 `FileDetailWidget`이 차지하는 비율을 늘립니다. (예: `splitter.setSizes([self.height() * 0.8, self.height() * 0.2])`)
    *   창이 일반 크기로 돌아오면, `splitter`의 크기를 기본값(예: 50:50 비율)으로 복원합니다.

#### 3.2. 미리보기 기능 확장

*   **요구사항**: `FileDetailWidget`은 선택된 파일의 확장자를 감지하여 다음 형식에 맞는 미리보기를 제공해야 합니다.
*   **구현 방향 (`FileDetailWidget.update_preview` 메서드 수정)**:
    1.  파일 경로를 받으면, 파일 확장자를 소문자로 변환하여 분기 처리합니다.
    2.  기존 `thumbnail_label` (이미지용), 신규 `QVideoWidget` (비디오용), 신규 `QTextBrowser` (문서용) 위젯들을 담을 `QStackedWidget`을 사용하여, 파일 형식에 맞는 위젯만 표시하도록 관리합니다.

*   **3.2.1. 이미지 파일 미리보기 (기존 기능 유지)**
    *   **지원 확장자**: `.png`, `.jpg`, `.jpeg`, `.bmp`, `.gif` 등 `QPixmap`이 지원하는 표준 이미지 형식.
    *   **구현**: 기존과 동일하게 `QPixmap`을 사용하여 `thumbnail_label`에 이미지를 표시합니다.

*   **3.2.2. 비디오 파일 재생 기능 (신규)**
    *   **지원 확장자**: `.mp4`, `.avi`, `.mkv`, `.mov` 등 (시스템 코덱에 따라 지원 범위 상이)
    *   **구현**:
        *   `PyQt5.QtMultimedia` 및 `PyQt5.QtMultimediaWidgets` 모듈을 사용합니다.
        *   `QVideoWidget`을 `FileDetailWidget`의 `QStackedWidget`에 추가합니다.
        *   `QMediaPlayer` 인스턴스를 생성하고, `setMedia()`로 비디오 파일을 로드한 뒤 `setVideoOutput()`으로 `QVideoWidget`에 연결합니다.
        *   재생, 정지, 음소거 등 기본적인 제어를 위한 버튼들을 `QVideoWidget` 하단에 추가하는 것을 고려합니다. (초기 버전에서는 자동 재생만 구현 가능)

*   **3.2.3. 문서 파일 내용 표시 (신규)**
    *   **지원 확장자**: `.txt`, `.md`, `.py`, `.js`, `.html`, `.css` 등 텍스트 기반 파일.
    *   **구현**:
        *   `QTextBrowser`를 `FileDetailWidget`의 `QStackedWidget`에 추가합니다.
        *   파일을 `utf-8` 인코딩으로 읽어 `QTextBrowser`에 `setPlainText()` 또는 `setMarkdown()` (확장자가 .md인 경우)를 사용하여 내용을 표시합니다.
        *   대용량 파일의 경우, 성능 저하를 막기 위해 파일 내용의 일부(예: 상위 100줄)만 표시하는 것을 고려합니다.

### 4. 비기능 요구사항

*   **성능**: 대용량 비디오 또는 문서 파일 로드 시 UI가 멈추지 않아야 합니다. (필요시 비동기 로딩 고려)
*   **안정성**: 지원하지 않는 파일 형식이나 손상된 파일 선택 시 애플리케이션이 비정상 종료되지 않고, "미리보기 불가"와 같은 명확한 메시지를 표시해야 합니다.
*   **사용성**: 레이아웃 변경 및 미디어 제어는 직관적이고 부드럽게 동작해야 합니다.

### 5. 영향 범위

*   **`main_window.py`**: 전체 화면 상태 감지 및 `QSplitter` 크기 조절 로직 추가.
*   **`widgets/file_detail_widget.py`**: `update_preview` 메서드 대폭 수정, `QStackedWidget` 도입, `QVideoWidget`, `QMediaPlayer`, `QTextBrowser` 등 신규 위젯 및 로직 추가.
*   **`ui/file_detail_content_widget.ui`**: `QStackedWidget`을 포함하도록 UI 파일 수정 또는 코드 기반으로 동적 생성.
*   **`requirements.txt`**: `PyQt5.QtMultimedia` 및 `PyQt5.QtMultimediaWidgets`가 기본 설치에 포함되지 않는 경우, 관련 패키지 정보 추가 필요. (일반적으로 `PyQt5`에 포함됨)

### 6. 개발 및 테스트 고려사항

*   **단위 테스트**: 각 파일 형식(이미지, 비디오, 문서)에 대한 `update_preview`의 분기 처리 로직을 테스트합니다.
*   **통합 테스트**: `MainWindow`의 전체 화면 전환 시 `FileDetailWidget`의 크기가 올바르게 조절되는지 확인합니다.
*   **UI 테스트**: 비디오 재생/정지, 문서 스크롤 등 추가된 UI 요소들이 정상적으로 동작하는지 확인합니다.
*   **예외 처리**: 지원하지 않는 파일, 손상된 파일, 대용량 파일 등 다양한 예외 케이스에 대한 안정성을 테스트합니다.

---
