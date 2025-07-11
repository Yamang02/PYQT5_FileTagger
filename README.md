# FileTagger 프로젝트

## 소개
FileTagger는 파일에 태그를 부여하고 관리할 수 있는 데스크탑 애플리케이션입니다. PyQt5 기반의 GUI와 MongoDB를 활용한 태그 관리 기능을 제공합니다.

## 주요 기능
- **파일 태그 관리**:
    - **태그 추가**: 새로운 태그를 텍스트 입력 후 `Enter` 키로 추가하거나, 기존 태그 목록에서 선택하여 파일에 추가할 수 있습니다. 디렉토리별 일괄 태그 추가 기능도 지원합니다.
    - **태그 수정/삭제**: 초기에는 태그 삭제만 가능하며, 여러 파일에 부여된 태그를 일괄 삭제하는 기능이 포함될 예정입니다.
    - **태그 표시**: 파일에 부여된 태그는 "태그 칩" 형태로 시각적으로 표시됩니다.
- **태그 검색**: 부여된 태그를 기반으로 파일을 효율적으로 검색할 수 있습니다.
- **직관적인 GUI 환경**: 사용자 친화적인 그래픽 사용자 인터페이스를 통해 쉽게 파일을 관리하고 태그를 조작할 수 있습니다.
- **MongoDB 연동**: 모든 태그 및 파일 정보는 MongoDB에 저장되어 데이터의 영속성과 안정성을 보장합니다.

## 프로젝트 문서

### 📋 기능 명세서 (Feature Specifications)
- **FS-20250711-002**: [파일 태그 수정/삭제 기능](docs/specifications/FS-20250711-002_file_tag_modification_deletion.md)
- **FS-20250711-003**: [작업 공간 설정 기능](docs/specifications/FS-20250711-003_workspace_setting.md)
- **FS-20250711-004**: [디렉토리 탐색 및 파일 목록 표시 기능](docs/specifications/FS-20250711-004_directory_exploration_file_listing.md)
- **FS-20250711-005**: [파일 상세 정보 및 태그 제어 기능](docs/specifications/FS-20250711-005_file_detail_preview_tag_control.md)
- **FS-20250711-006**: [전역 파일 검색 기능](docs/specifications/FS-20250711-006_global_file_search.md)
- **FS-20250711-007**: [사용자 정의 태그 관리 기능](docs/specifications/FS-20250711-007_custom_tag_management.md)
- **FS-20250711-008**: [일괄 태그 제거 기능](docs/specifications/FS-20250711-008_batch_tag_removal.md)

### 🔧 기술 스펙 정의서 (Technical Specifications)
- **TS-20250711-001**: [태그 관리 시스템](docs/specifications/technical/TS-20250711-001_tag_management_system.md)
- **TS-20250711-002**: [UI 컴포넌트 시스템](docs/specifications/technical/TS-20250711-002_ui_component_system.md)
- **TS-20250711-003**: [파일 시스템 및 미리보기 시스템](docs/specifications/technical/TS-20250711-003_file_system_preview_system.md)

### 📚 개발자 가이드 (Developer Guide)
- [코딩 컨벤션](docs/developer_guide/coding_conventions.md)
- [태깅 기능 상세 명세](docs/developer_guide/tagging_feature_spec.md)
- [UI 위젯 및 시그널 참조](docs/developer_guide/ui_widgets_signals_reference.md)
- [개발 요청 명세](docs/developer_guide/development_request_spec.md)
- [개발 노트](docs/developer_guide/dev_notes.md)
- [에러 처리 가이드](docs/developer_guide/errors.md)

### 👥 사용자 가이드 (User Guide)
- [태그 추가하기](docs/user_guide/adding_tags.md)

### 📊 프로젝트 관리
- [프로젝트 개요](docs/portfolio/project_overview.md)
- [개발 이슈](docs/issues.md)
- [대화 로그](docs/conversation_log.md)
- [테스트 리포트](docs/test_report_20250705.md)

## 개발 환경 설정
1. **Python 및 Conda 설치**
2. **필수 패키지 설치**
   ```bash
   pip install -r requirements.txt
   pip install pymongo
   ```
3. **애플리케이션 실행**
   ```bash
   python main.py
   ```

## 기타
- MongoDB가 로컬에서 실행 중이어야 합니다.
- 테스트 데이터 생성을 위해 `tests/test_data_generator.py` 스크립트를 사용할 수 있습니다.
