import os
from typing import List
from core.services.tag_service import TagService
from core.path_utils import normalize_path

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
        successful_removes = 0
        for file_path in file_paths:
            for tag in tags_to_remove:
                if self._tag_service.remove_tag_from_file(file_path, tag):
                    successful_removes += 1
        return {"success": True, "processed": len(file_paths), "successful": successful_removes}

    def add_tags_to_files(self, file_paths: List[str], tags_to_add: List[str]) -> dict:
        successful_adds = 0
        for file_path in file_paths:
            for tag in tags_to_add:
                if self._tag_service.add_tag_to_file(file_path, tag):
                    successful_adds += 1
        return {"success": True, "processed": len(file_paths), "successful": successful_adds}

    def add_tags_to_directory(self, directory_path, tags, recursive=False, file_extensions=None):
        target_files = self._get_files_in_directory(directory_path, recursive, file_extensions)
        if not target_files:
            return {"success": True, "message": "조건에 맞는 파일이 없습니다", "processed": 0}
        
        return self.add_tags_to_files(target_files, tags)

    def _get_files_in_directory(self, directory_path, recursive=False, file_extensions=None):
        if not directory_path or not os.path.isdir(directory_path):
            return []

        target_files = []
        file_extensions = [ext.lower().lstrip('.') for ext in file_extensions] if file_extensions else []

        if recursive:
            for root, _, files in os.walk(directory_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if not file_extensions or os.path.splitext(file_path)[1].lower().lstrip('.') in file_extensions:
                        target_files.append(normalize_path(file_path))
        else:
            for file in os.listdir(directory_path):
                file_path = os.path.join(directory_path, file)
                if os.path.isfile(file_path):
                    if not file_extensions or os.path.splitext(file_path)[1].lower().lstrip('.') in file_extensions:
                        target_files.append(normalize_path(file_path))
        return target_files

    def get_files_in_directory(self, directory_path, recursive=False, file_extensions=None):
        return self._get_files_in_directory(directory_path, recursive, file_extensions)
