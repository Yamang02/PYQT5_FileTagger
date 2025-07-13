# 2025-07-11 확장 로드맵: Tag Graph Editor & Tag-Based File Browser 및 스탠드얼론 배포

> 작성자: Gemini (PM)  
> 작성일: 2025-07-11  
> 최신 수정: 2025-07-11  

---

## 1. 개요 및 목표

본 로드맵은 FileTagger 프로젝트에 두 개의 신규 창(① **Tag Graph Editor**: 태그 관계·범주·레이팅 편집, ② **Tag-Based File Browser**: 태그 기반 파일 탐색)을 추가하고, 이후 **스탠드얼론 배포**까지 확장하기 위한 단계별 계획을 제시한다. 목표는 다음과 같다:

1. 태그 관리 기능 고도화를 통해 사용자 경험(UX) 극대화
2. 모듈화·계층화된 아키텍처로 유지보수성과 확장성 확보
3. 문서·테스트·CI/CD 강화를 통한 품질 및 배포 효율 증대

---

## 2. 범위

| 구분 | 세부 내용 |
|------|-----------|
| 창 ① | **Tag Graph Editor**<br/>• 태그 간 관계(부모-자식, 연관, 유사) 시각화/편집<br/>• 범주(Category) 지정, 레이팅(1–5) 부여<br/>• 그래프 UI (`QGraphicsView` + networkx) |
| 창 ② | **Tag-Based File Browser**<br/>• 태그·범주·레이팅 필터 → 파일 리스트 & 썸네일/미리보기<br/>• 멀티 선택·일괄 태그 작업 지원 |
| 공통 | • 이벤트 버스(Pub/Sub)로 실시간 동기화<br/>• Clean Architecture + MVVM 적용: Domain / Service / Repository / UI 계층 구분<br/>• 플러그인(모듈) 로드 방식으로 신규 창 지속 확장 |
| 배포 | • PyInstaller 기반 스탠드얼론 EXE 빌드<br/>• GitHub Actions 릴리스 파이프라인 구축 |

---

## 3. 단계별 일정 (안)

| Phase | 기간(예상) | 주요 산출물 | 비고 |
|-------|-----------|-------------|------|
| 0. Kick-off | 07-11 ~ 07-15 | • 본 로드맵 승인<br/>• DRS 초안 작성 | PM • PL |
| 1. 아키텍처 리팩터링 | 07-16 ~ 07-28 | • `TagService`, `FileQueryService` 등 Service/Repository 계층 분리<br/>• `core/event_bus.py` 구현 | Dev 팀 |
| 2. Tag Graph Editor | 07-29 ~ 08-11 | • Tag Graph Editor UI/VM/Service<br/>• 단위·통합 테스트 | Dev + UX |
| 3. File Browser | 08-12 ~ 08-25 | • Tag-Based File Browser UI/VM/Service<br/>• 단위·통합 테스트 | Dev + UX |
| 4. QA & Hardening | 08-26 ~ 09-02 | • 회귀/성능/사용성 테스트<br/>• Bug Fix | QA |
| 5. 스탠드얼론 패키징 | 09-03 ~ 09-06 | • PyInstaller spec 파일<br/>• GH Actions 빌드 파이프라인 | DevOps |
| 6. 릴리스 & 회고 | 09-07 | • 릴리스 태그 v1.5<br/>• 회고(Retrospective) | All |

> **※** 일정은 초기 추정치이며, 상세 WBS는 Sprint Planning 시 확정한다.

---

## 4. 아키텍처 개선 항목

1. **계층 분리**: Domain → Service → Repository → UI
2. **MVVM 패턴**: ViewModel에서 상태·로직 처리, Test 용이성 확보
3. **이벤트 버스**: 창 간 Pub/Sub; blinker 또는 custom Signal 구현
4. **플러그인 시스템**: 신규 창을 `plugins/` 하위 모듈로 로드
5. **DI(Container) 도입**: Service 의존성 주입으로 테스트 격리
6. **Docstring & Mermaid**: AI Agent 친화적 문서화

---

## 5. 리스크 및 의존성

| 리스크 | 영향 | 대응 방안 |
|---------|-------|-----------|
| 대규모 리팩터링에 따른 회귀 버그 | 기능 불안정 | 단계별 PR + 광범위 테스트 |
| 그래프 시각화 성능 | 대용량 태그 시 렌더링 지연 | Level-of-Detail, 네트워크 축소 모드 |
| 스탠드얼론 빌드 용량 | 배포 파일 크기 ↑ | Qt 커스텀 빌드, 필요 모듈만 포함 |

---

## 6. 담당자 및 완료 기준

| 역할 | 담당자(예시) | 완료 기준 |
|------|--------------|-----------|
| PM/PL | Gemini | 일정·범위·품질 달성, 문서 업데이트 |
| Dev | Alice, Bob | 기능 구현, 90% 이상 테스트 커버리지 |
| QA | Carol | 주요 시나리오 100% 통과, P1 버그 0건 |
| DevOps | Dan | 자동 빌드·배포 파이프라인 성공 |

---

## 7. 변경 이력

| 버전 | 일자 | 작성자 | 내용 |
|-------|------|--------|------|
| v0.1 | 2025-07-11 | Gemini | 최초 작성 | 