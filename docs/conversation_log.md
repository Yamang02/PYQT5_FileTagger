
## 2025년 7월 15일 화요일

### UI 위젯 래핑으로 인한 AttributeError 해결 방안 결정
- **이슈**: `UISetupManager`에서 위젯을 `QFrame`으로 래핑하면서 `AttributeError` 반복 발생.
- **논의**: 개발팀의 제안 중 `UISetupManager`가 위젯을 래핑한 후, 래핑된 위젯의 실제 위젯을 반환하는 헬퍼 메서드를 제공하여 일관된 접근 방식을 강제하는 방안을 선택.
- **결정**: `UISetupManager`의 `_create_widgets` 메서드에서 위젯을 생성하고 래핑한 후, `self.widgets` 딕셔너리에는 **실제 위젯 인스턴스**를 저장하도록 변경. `MainWindow` 및 `SignalConnectionManager`는 `self.ui_setup_manager.get_widget('widget_name')`을 통해 실제 위젯에 접근하도록 수정. 이 방식은 캡슐화 강화, 단일 책임 원칙 준수, 일관된 위젯 접근 방식 제공, 유연성 및 확장성 증대 등 아키텍처에 긍정적인 영향을 미침.
- **조치**: `docs/issues.md`의 해당 이슈에 의견 추가 후 마감.
