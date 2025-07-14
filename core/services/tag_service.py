from core.repositories.tag_repository import TagRepository
from core.events import EventBus

class TagService:
    def __init__(self, tag_repository: TagRepository, event_bus: EventBus):
        self._repository = tag_repository
        self._event_bus = event_bus

    def add_tag_to_file(self, file_path: str, tag: str) -> bool:
        result = self._repository.add_tag(file_path, tag)
        if result:
            self._event_bus.publish_tag_added(file_path, tag)
        return result

    def remove_tag_from_file(self, file_path: str, tag: str) -> bool:
        result = self._repository.remove_tag(file_path, tag)
        if result:
            self._event_bus.publish_tag_removed(file_path, tag)
        return result

    def get_tags_for_file(self, file_path: str) -> list:
        return self._repository.get_tags_for_file(file_path)

    def get_all_tags(self) -> list:
        return self._repository.get_all_tags()

    def get_files_by_tags(self, tags: list) -> list:
        return self._repository.get_files_by_tags(tags)

    def delete_file_entry(self, file_path: str) -> bool:
        return self._repository.delete_file_entry(file_path)