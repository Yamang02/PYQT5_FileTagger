---
status: Approved
---
# DRS-20250711-010: Phase 1 아키텍처 리팩터링 - Clean Architecture & MVVM 도입 (v1.1)

> **작성자**: Gemini (PM)  
> **작성일**: 2025-07-11  
> **수정일**: 2025-07-11 (개발팀 피드백 반영)  
> **우선순위**: Critical  
> **예상 공수**: 2.5주 (Phase 0 포함)  

---

## 🔄 개발팀 피드백 반영 사항

1. **EventBus 시스템 개선**: 타입 안전한 dataclass 기반 이벤트 + PyQt Signal 하이브리드 방식
2. **마이그레이션 순서 조정**: MainWindow 분리 우선 → 개별 위젯 리팩터링
3. **테스트 커버리지 단계적 목표**: 50% → 70% → 80%
4. **Phase 0 추가**: 사전 분석 및 위험도 평가 (3일)
5. **롤백 계획 수립**: 각 Phase별 안전장치 마련
6. **구체적 구현 가이드 보완**: Adapter 패턴 활용 점진적 전환

---

## 1. 개요

FileTagger 프로젝트의 확장성과 유지보수성을 확보하기 위해 Clean Architecture + MVVM 패턴을 도입하고, UI-로직 완전 분리를 통한 아키텍처 리팩터링을 수행한다.

### 1.1 프로젝트 전체 맥락
본 DRS는 **2025-07-11 확장 로드맵**의 Phase 1에 해당하며, 기존 기능의 안정화 및 배포 가능한 앱 형태로의 전환을 위한 기반이 된다:
- **Phase 2-6**: 기존 기능 정비, QA, 스탠드얼론 패키징, 릴리스

**목표**: 기존 기능의 안정화 및 배포 가능한 앱 형태로의 전환을 위한 견고한 아키텍처 기반 마련

---

## 2. 현재 상태 분석

### 2.1 주요 문제점
1. **UI-로직 강결합**: `TagControlWidget`에서 태그 추가 시 즉시 DB 저장 로직 실행
2. **단일 책임 원칙 위반**: `MainWindow` 293라인에 레이아웃/시그널/상태관리 모두 집중
3. **테스트 어려움**: UI 없이 비즈니스 로직 단독 테스트 불가
4. **확장성 부족**: 신규 창 추가 시 기존 코드 대폭 수정 필요
5. **상태 관리 분산**: 각 위젯이 개별적으로 상태 관리

### 2.2 현재 구조
```
main_window.py (293 lines)
├── widgets/
│   ├── tag_control_widget.py (414 lines)
│   ├── file_detail_widget.py (319 lines)
│   └── [기타 위젯들]
└── core/
    ├── tag_manager.py
    ├── search_manager.py
    └── tag_ui_state_manager.py
```

---

## 3. 목표 아키텍처

### 3.1 Clean Architecture 계층
```
┌─────────────────────────────────────────┐
│                UI Layer                 │
│  ┌─────────────────┐ ┌─────────────────┐│
│  │    View         │ │   ViewModel     ││
│  │ (QWidget)       │ │ (상태+시그널)    ││
│  └─────────────────┘ └─────────────────┘│
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│              Service Layer              │
│  ┌─────────────────┐ ┌─────────────────┐│
│  │   TagService    │ │ FileQueryService││
│  │ (비즈니스 로직)   │ │   (검색 로직)    ││
│  └─────────────────┘ └─────────────────┘│
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│            Repository Layer             │
│  ┌─────────────────┐ ┌─────────────────┐│
│  │  TagRepository  │ │ FileRepository  ││
│  │  (MongoDB I/O)  │ │ (파일시스템 I/O) ││
│  └─────────────────┘ └─────────────────┘│
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│               Domain Layer              │
│  ┌─────────────────┐ ┌─────────────────┐│
│  │      Tag        │ │   TaggedFile    ││
│  │ (엔티티/모델)     │ │   (엔티티)       ││
│  └─────────────────┘ └─────────────────┘│
└─────────────────────────────────────────┘
```

### 3.2 개선된 이벤트 시스템 (PyQt Signal + 타입 안전한 이벤트)
```python
# core/events.py
from dataclasses import dataclass
from typing import List
from PyQt5.QtCore import QObject, pyqtSignal

@dataclass
class TagAddedEvent:
    file_path: str
    tag: str
    timestamp: float

@dataclass  
class TagRemovedEvent:
    file_path: str
    tag: str
    timestamp: float

class EventBus(QObject):
    # 타입 안전한 시그널 정의
    tag_added = pyqtSignal(TagAddedEvent)
    tag_removed = pyqtSignal(TagRemovedEvent)
    
    def publish_tag_added(self, file_path: str, tag: str):
        event = TagAddedEvent(file_path, tag, time.time())
        self.tag_added.emit(event)
    
    def subscribe_tag_added(self, callback):
        self.tag_added.connect(callback)
```

---

## 4. 단계별 구현 계획

### 4.0 Phase 0: 사전 분석 및 위험도 평가 (3일)

#### 4.0.1 현재 코드 구조 완전 분석
- [ ] Signal/Slot 연결 매핑 테이블 작성
- [ ] 순환 의존성 식별 및 해결 방안 수립
- [ ] 각 위젯 간 데이터 흐름 다이어그램 작성

#### 4.0.2 리팩터링 위험도 평가
- [ ] 각 모듈별 변경 영향도 매트릭스 작성
- [ ] 회귀 테스트 필수 시나리오 정의
- [ ] 롤백 포인트 및 브랜치 전략 수립

#### 4.0.3 즉시 결정 필요 사항
- [ ] **Signal/Slot vs EventBus**: 기존 PyQt Signal 유지 + 타입 안전한 이벤트 추가
- [ ] **MongoDB 연결**: 기존 방식 유지 (Connection Pool은 Phase 2 이후 검토)
- [ ] **UI 테스트**: 수동 테스트 유지 (자동화는 Phase 3 이후)

### 4.1 Phase 1-A: MainWindow 분리 우선 (1주)

#### 4.1.1 MainWindow 3단계 분리
```python
# main_window.py (목표: 100라인 이하)
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui_setup = UISetupManager(self)
        self.signal_manager = SignalConnectionManager(self)
        self.data_loader = DataLoadingManager(self)
        
        self.ui_setup.setup_ui()
        self.signal_manager.connect_signals()
        self.data_loader.load_initial_data()

# ui/ui_setup_manager.py
class UISetupManager:
    def setup_ui(self):
        # 레이아웃 설정만 담당
        
# core/signal_connection_manager.py  
class SignalConnectionManager:
    def connect_signals(self):
        # 시그널 연결만 담당
        
# core/data_loading_manager.py
class DataLoadingManager:
    def load_initial_data(self):
        # 초기 데이터 로딩만 담당
```

#### 4.1.2 Adapter 패턴 활용 점진적 전환
```python
# core/adapters/tag_manager_adapter.py
class TagManagerAdapter:
    """기존 TagManager 인터페이스 유지하면서 새로운 TagService 연결"""
    def __init__(self, tag_service: TagService):
        self._tag_service = tag_service
    
    def update_tags(self, file_path: str, tags: List[str]):
        # 기존 메서드 시그니처 유지
        return self._tag_service.update_file_tags(file_path, tags)
```

### 4.2 Phase 1-B: Service/Repository 계층 구축 (0.5주)

#### 4.2.1 Service Layer 구축
```python
# core/services/tag_service.py
class TagService:
    def __init__(self, tag_repository: TagRepository, event_bus: EventBus):
        self._repository = tag_repository
        self._event_bus = event_bus
    
    def add_tag_to_file(self, file_path: str, tag: str) -> bool:
        """파일에 태그 추가 (비즈니스 로직만 처리)"""
        result = self._repository.add_tag(file_path, tag)
        if result:
            self._event_bus.publish_tag_added(file_path, tag)
        return result
```

#### 4.2.2 Repository Layer 구축
```python
# core/repositories/tag_repository.py
class TagRepository:
    def __init__(self, mongo_client):
        self._client = mongo_client
    
    def add_tag(self, file_path: str, tag: str) -> bool:
        """MongoDB I/O만 처리"""
        # 실제 DB 저장 로직
```

### 4.3 Phase 1-C: ViewModel 구축 및 위젯 리팩터링 (1주)

#### 4.3.1 ViewModel 구축
```python
# viewmodels/tag_control_viewmodel.py
class TagControlViewModel(QObject):
    tags_changed = pyqtSignal(list)
    target_changed = pyqtSignal(str, bool)
    
    def __init__(self, tag_service: TagService, event_bus: EventBus):
        super().__init__()
        self._tag_service = tag_service
        self._event_bus = event_bus
        self._current_tags = []
        self._current_target = None
    
    def add_tag(self, tag: str):
        """UI에서 호출하는 태그 추가 메서드"""
        if self._tag_service.add_tag_to_file(self._current_target, tag):
            self._current_tags.append(tag)
            self.tags_changed.emit(self._current_tags)
```

#### 4.3.2 위젯 리팩터링 (TagControlWidget 우선)
```python
# widgets/tag_control_widget.py (목표: 200라인 이하)
class TagControlWidget(QWidget):
    def __init__(self, viewmodel: TagControlViewModel):
        super().__init__()
        self._viewmodel = viewmodel
        self.setup_ui()
        self.connect_viewmodel()
    
    def connect_viewmodel(self):
        self._viewmodel.tags_changed.connect(self.update_tags_display)
        # UI 이벤트 → ViewModel 메서드 호출만
```

---

## 5. 테스트 전략 (단계적 커버리지 목표)

### 5.1 1단계: 50% 커버리지 (핵심 Service 계층)
```python
# tests/services/test_tag_service.py
def test_add_tag_to_file_success():
    # Given
    mock_repository = Mock()
    mock_event_bus = Mock()
    service = TagService(mock_repository, mock_event_bus)
    
    # When
    result = service.add_tag_to_file("/path/to/file", "test_tag")
    
    # Then
    assert result is True
    mock_repository.add_tag.assert_called_once()
    mock_event_bus.publish_tag_added.assert_called_once()
```

### 5.2 2단계: 70% 커버리지 (ViewModel 포함)
- ViewModel 단위 테스트 추가
- Service ↔ Repository 통합 테스트

### 5.3 3단계: 80% 커버리지 (완전 분리 후)
- UI 없는 전체 플로우 테스트
- 이벤트 버스 메시지 전달 테스트

---

## 6. 롤백 계획

### 6.1 브랜치 전략
```
main
├── feat/phase0-analysis (Phase 0 완료 후 merge)
├── feat/phase1a-mainwindow (Phase 1-A 완료 후 merge)
├── feat/phase1b-service-layer (Phase 1-B 완료 후 merge)
└── feat/phase1c-viewmodel (Phase 1-C 완료 후 merge)
```

### 6.2 각 Phase별 롤백 포인트
- **Phase 0**: 분석 문서만 생성, 코드 변경 없음
- **Phase 1-A**: MainWindow 분리 후 기존 기능 100% 동작 확인
- **Phase 1-B**: Service/Repository 추가 후 기존 TagManager와 병존
- **Phase 1-C**: ViewModel 추가 후 기존 위젯과 병존

### 6.3 롤백 트리거 조건
- 주요 기능 회귀 발생 시
- 테스트 커버리지 목표 미달 시
- 메모리 사용량 +20% 초과 시

---

## 7. 완료 기준 (수정)

### 7.1 기능적 요구사항
- [ ] 기존 태그 기능 100% 동일하게 동작
- [ ] UI 없이 Service 계층 단독 테스트 가능
- [ ] 타입 안전한 이벤트 시스템 동작

### 7.2 품질 요구사항 (단계적)
- [ ] **Phase 1-A**: MainWindow 100라인 이하 분리
- [ ] **Phase 1-B**: Service 계층 50% 테스트 커버리지
- [ ] **Phase 1-C**: 전체 70% 테스트 커버리지
- [ ] 메모리 사용량 기존 대비 +15% 이내

### 7.3 문서화 요구사항
- [ ] 아키텍처 다이어그램 업데이트
- [ ] Adapter 패턴 활용 가이드
- [ ] 마이그레이션 체크리스트

---

## 8. 리스크 및 대응방안 (업데이트)

| 리스크 | 확률 | 영향도 | 대응방안 |
|--------|------|--------|----------|
| MainWindow 분리 시 Signal 연결 오류 | 높음 | 높음 | Phase 0 분석 + 단계별 검증 |
| 대규모 리팩터링으로 인한 회귀 버그 | 중간 | 높음 | 각 Phase별 롤백 포인트 |
| 개발 일정 지연 | 중간 | 높음 | 핵심 기능 우선, 점진적 개선 |
| EventBus 디버깅 복잡성 | 중간 | 중간 | PyQt Signal 기반 하이브리드 방식 |

---

## 📎 에러 핸들링 정책 참고
- 아키텍처 수준의 에러 처리 정책 및 예외 클래스 설계는 [TS-20250711-004_error_handling_strategy.md](../technical/TS-20250711-004_error_handling_strategy.md) 문서를 참조할 것.

---

## 9. 구체적 구현 가이드

### 9.1 기존 TagManager → TagService 마이그레이션
```python
# 1단계: Adapter 패턴으로 병존
tag_service = TagService(tag_repository, event_bus)
tag_manager_adapter = TagManagerAdapter(tag_service)

# 2단계: 기존 코드에서 점진적 교체
# Before
self.tag_manager.update_tags(file_path, tags)

# After  
self.tag_manager_adapter.update_tags(file_path, tags)

# 3단계: 직접 Service 호출로 전환
self.tag_service.update_file_tags(file_path, tags)
```

### 9.2 기존 테스트 코드 수정 범위
- **최소 수정**: Adapter 패턴 활용으로 기존 테스트 대부분 유지
- **추가 필요**: Service/Repository 계층 단위 테스트
- **통합 테스트**: ViewModel ↔ Service 연동 테스트

---

## 10. 승인 요청

개발팀 피드백을 반영하여 **더 안전하고 실현 가능한 계획**으로 수정했습니다:

✅ **Phase 0 추가**로 사전 위험 분석  
✅ **MainWindow 분리 우선**으로 의존성 관리  
✅ **단계적 테스트 커버리지** 목표  
✅ **타입 안전한 EventBus** + PyQt Signal 하이브리드  
✅ **롤백 계획** 및 안전장치 마련  

**승인 여부**: [ ] 승인 / [ ] 수정 요청 / [ ] 거부  
**검토자**: ________________  
**승인일**: ________________ 