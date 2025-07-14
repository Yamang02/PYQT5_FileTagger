from typing import List
from core.services.tag_service import TagService

class TagManagerAdapter:
    """기존 TagManager 인터페이스를 유지하면서 새로운 TagService에 연결하는 어댑터"""
    def __init__(self, tag_service: TagService):
        self._tag_service = tag_service

    def add_tag(self, file_path: str, tag: str) -> bool:
        return self._tag_service.add_tag_to_file(file_path, tag)

    def remove_tag(self, file_path: str, tag: str) -> bool:
        return self._tag_service.remove_tag_from_file(file_path, tag)

    def get_tags_for_file(self, file_path: str) -> list:
        return self._tag_service.get_tags_for_file(file_path)

    def get_all_tags(self) -> list:
        return self._tag_service.get_all_tags()

    def get_files_by_tags(self, tags: list) -> list:
        return self._tag_service.get_files_by_tags(tags)

    def delete_file_entry(self, file_path: str) -> bool:
        return self._tag_service.delete_file_entry(file_path)

    def update_tags(self, file_path: str, tags: List[str]):
        current_tags = self._tag_service.get_tags_for_file(file_path)
        for tag in current_tags:
            if tag not in tags:
                self._tag_service.remove_tag_from_file(file_path, tag)
        for tag in tags:
            if tag not in current_tags:
                self._tag_service.add_tag_to_file(file_path, tag)

    def get_files_with_tags(self, tags: List[str], match_all: bool = False) -> List[str]:
        if match_all:
            # TODO: Implement logic for matching all tags
            pass
        else:
            return self._tag_service.get_files_by_tags(tags)

    def get_all_tagged_files(self) -> List[str]:
        # TODO: Implement this in TagService or TagRepository
        return []

    def get_tag_counts(self) -> dict:
        # TODO: Implement this in TagService or TagRepository
        return {}

    def remove_tags_from_files(self, file_paths: List[str], tags_to_remove: List[str]) -> dict:
        return self._tag_service.remove_tags_from_files(file_paths, tags_to_remove)

    def add_tags_to_files(self, file_paths: List[str], tags_to_add: List[str]) -> dict:
        return self._tag_service.add_tags_to_files(file_paths, tags_to_add)

    def add_tags_to_directory(self, directory_path, tags, recursive=False, file_extensions=None):
        return self._tag_service.add_tags_to_directory(directory_path, tags, recursive, file_extensions)

    def get_files_in_directory(self, directory_path, recursive=False, file_extensions=None):
        return self._tag_service.get_files_in_directory(directory_path, recursive, file_extensions)
