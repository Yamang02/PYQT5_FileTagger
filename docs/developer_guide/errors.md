# 에러 관리 및 조치 내역 (DRS-20250705-002)

| 발생 일시 | DRS/이슈 | 발생 위치 | 에러 메시지/현상 | 원인 | 조치/해결 방법 | 비고 |
|-----------|----------|-----------|------------------|------|----------------|------|
| 2025-07-05 | DRS-20250705-002 | QuickTagsWidget, main_window.py | AttributeError: 'QuickTagsWidget' object has no attribute 'set_quick_tags' | set_quick_tags 메서드 미구현 | set_quick_tags 메서드 추가 및 버튼 재생성 로직 구현 |  |
| 2025-07-05 | DRS-20250705-002 | FileSelectionAndPreviewWidget | AttributeError: 'QFileSystemModel' object has no attribute 'Dirs' | QFileSystemModel.Dirs → QDir.AllDirs 등으로 변경 필요 | QDir 상수 사용으로 코드 수정 |  |
| 2025-07-05 | DRS-20250705-002 | TagInputWidget | AttributeError: 'TagInputWidget' object has no attribute 'clear_tags' | clear_tags 메서드 미구현 | clear_tags 메서드 추가 |  |
| 2025-07-05 | DRS-20250705-002 | TagInputWidget | AttributeError: 'TagInputWidget' object has no attribute 'completer' | completer 속성 미초기화 | __init__에서 self.completer 및 관련 모델 초기화 예정 |  |
| 2025-07-05 | DRS-20250705-002 | QuickTagsWidget | AttributeError: 'QuickTagsWidget' object has no attribute 'clear_selection' | clear_selection 메서드 미구현 | clear_selection 메서드 추가 |  |
| 2025-07-05 | DRS-20250705-002 | QuickTagsWidget | AttributeError: 'QuickTagsWidget' object has no attribute 'set_selected_tags' | set_selected_tags 메서드 미구현 | set_selected_tags 메서드 추가 예정 |  |

---

## 에러 기록 양식(추가 시 복사하여 사용)

| 발생 일시 | DRS/이슈 | 발생 위치 | 에러 메시지/현상 | 원인 | 조치/해결 방법 | 비고 |
|-----------|----------|-----------|------------------|------|----------------|------|
|           |          |           |                  |      |                |      | 