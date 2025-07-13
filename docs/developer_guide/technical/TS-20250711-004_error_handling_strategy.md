# TS-20250711-004: FileTagger 아키텍처 에러 핸들링 전략

> 작성일: 2025-07-11  
> 작성자: Gemini (PM)

---

## 1. 개요
FileTagger의 Clean Architecture + MVVM + 플러그인 구조에서 일관되고 견고한 에러 핸들링을 보장하기 위한 계층별 정책, 예외 클래스, 전파/로깅/피드백 원칙을 정의한다.

---

## 2. 계층별 에러 처리 원칙

### 2.1 Repository Layer
- 모든 I/O 예외를 커스텀 예외(RepositoryError, FileIOError 등)로 래핑
- logger.error()로 상세 기록, 불가피한 경우 Service로 예외 전파

### 2.2 Service Layer
- Repository 계층 예외를 ServiceError로 변환/래핑
- ValidationError 등 도메인 검증 실패는 별도 예외로 구분
- 주요 비즈니스 실패는 logger.warning()/error()로 기록, 필요시 재시도/롤백

### 2.3 ViewModel Layer
- Service 계층 예외를 사용자 친화적 메시지로 변환
- 상태 플래그(is_error, error_message 등)로 UI에 전달
- 예상치 못한 예외는 logger.error()로 기록

### 2.4 UI Layer (View)
- ViewModel에서 전달된 에러 메시지, 예외 상황을 사용자에게 안내(QMessageBox, 상태바 등)
- 복구 옵션(재시도, 무시, 상세보기 등) 제공, 치명적 오류 시 graceful shutdown

### 2.5 이벤트 버스/플러그인
- 이벤트 객체에 에러 타입/메시지/스택트레이스 포함
- 구독자(플러그인 등)에서 개별적으로 처리, 필요시 UI에 전파

---

## 3. 에러 타입 및 예외 클래스 설계

```python
# domain/errors.py
class DomainError(Exception): pass
class ValidationError(DomainError): pass

# repository/errors.py
class RepositoryError(Exception): pass
class FileIOError(RepositoryError): pass
class DatabaseError(RepositoryError): pass

# service/errors.py
class ServiceError(Exception): pass

# viewmodel/errors.py
class ViewModelError(Exception): pass

# 플러그인/이벤트
class PluginError(Exception): pass
class EventBusError(Exception): pass
```

---

## 4. 에러 전파 및 사용자 피드백 흐름

1. Repository에서 DB 연결 실패 → DatabaseError 발생 → ServiceError로 래핑 → ViewModel에서 사용자 메시지로 변환 → UI에서 안내
2. 비즈니스 검증 실패 → ValidationError 발생 → ViewModel에서 사용자 메시지로 변환
3. 플러그인 에러 → EventBusError 발생 시 구독자별 개별 처리, 필요시 UI에 알림

---

## 5. 로깅/모니터링/테스트
- 각 계층별 logger 사용, 에러 레벨 구분(logging.ERROR, WARNING 등)
- 치명적 오류는 파일/원격 서버로 리포트(옵션: Sentry 등)
- 에러 발생 시 정상적으로 예외가 처리되는지 단위/통합 테스트 필수

---

## 6. 배포/운영 단계의 안전장치
- 각 Phase별 롤백 포인트, 치명적 에러 발생 시 즉시 롤백
- 사용자에게 에러 리포트 전송 옵션 제공
- 에러 처리 플로우도 CI에서 자동화 테스트

---

## 7. 참고
- 본 전략은 DRS-20250711-010 및 전체 프로젝트 확장 로드맵의 아키텍처를 전제로 함
- 실제 예외 클래스/핸들러 구현은 각 계층별 Python 모듈에 위치 