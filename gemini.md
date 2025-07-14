# FileTagger 프로젝트 (Gemini)

## 소개
FileTagger는 파일에 태그를 부여하고 관리할 수 있는 데스크탑 애플리케이션입니다. PyQt5 기반의 GUI와 MongoDB를 활용한 태그 관리 기능을 제공합니다.

## 주요 기능
- 파일에 태그 추가, 삭제, 검색
- 직관적인 GUI 환경
- MongoDB 연동을 통한 데이터 영속성

## 개발 환경 설정
1. **Python 및 Conda 설치**
2. **가상환경 생성 및 활성화**
   ```bash
   conda create -n env_filetagger_dev python=3.10
   conda activate env_filetagger_dev
   ```
3. **필수 패키지 설치**
   ```bash
   pip install -r requirements.txt
   pip install pymongo
   ```
4. **애플리케이션 실행**
   ```bash
   python main.py
   ```

## 문서 구조
프로젝트 문서는 `docs` 디렉토리 아래에 체계적으로 관리됩니다.
- `docs/introduction`: 프로젝트 소개, 목표 등 전반적인 내용을 담습니다.
- `docs/user_guide`: 사용자 매뉴얼, 기능 설명 등 사용자 관련 문서를 포함합니다.
- `docs/developer_guide`: 개발 환경 설정, 코드 컨벤션, 아키텍처 등 개발자 관련 문서를 포함합니다.
- `docs/api`: API 명세서 등 기술적인 상세 문서를 포함합니다.
- `docs/developer_guide/dev_notes.md`: 개발팀 내부의 기술적 논의, 디버깅 과정, 실험 결과 등을 자유롭게 기록하는 문서입니다. 주요 결정사항은 `docs/conversation_log.md`로 요약 이관됩니다.
- `docs/developer_guide/drs/`: 개발 요청 명세(DRS) 문서들을 저장하는 디렉토리입니다.
- `docs/developer_guide/development_request_spec.md`: 기획팀이 개발팀에게 특정 기능이나 개선 사항을 요청할 때 사용하는 개발 요청 명세 양식입니다.

## 기능 명세
FileTagger의 모든 기능 명세는 `docs/specifications` 디렉토리에 문서 ID(`FS-YYYYMMDD-XXX`) 형태로 관리됩니다. 각 기능의 상세한 요구사항은 해당 문서를 참조하십시오.

## 기타
- MongoDB가 로컬에서 실행 중이어야 합니다.
- 테스트 데이터 생성을 위해 `tests/test_data_generator.py` 스크립트를 사용할 수 있습니다.
- 추가 문의는 README 또는 개발자에게 연락 바랍니다.

**모든 AI 에이전트는 한국어로 응답해야 합니다.**

**`docs/conversation_log.md` 파일은 PM 역할을 맡은 AI만 수정할 수 있습니다. 다른 AI 역할은 해당 파일을 참고만 해야 합니다.**

---
**참고**: 본 AI 에이전트(Gemini)의 역할 및 작업 워크플로우에 대한 상세 내용은 `FileTagger_Roles/PM.md` 파일을 참조하십시오.
