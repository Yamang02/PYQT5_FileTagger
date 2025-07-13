# core/services/tag_service.py
class TagService:
    def __init__(self, tag_repository, event_bus):
        self._repository = tag_repository
        self._event_bus = event_bus
    
    def add_tag_to_file(self, file_path: str, tag: str) -> bool:
        """파일에 태그 추가 (비즈니스 로직만 처리)"""
        result = self._repository.add_tag(file_path, tag)
        if result:
            # self._event_bus.publish_tag_added(file_path, tag) # EventBus는 나중에 구현
            pass
        return result
