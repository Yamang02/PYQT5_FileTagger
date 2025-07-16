import os
from pymongo import UpdateOne
from typing import List, Dict
from core.repositories.tag_repository import TagRepository
from core.events import EventBus, TagAddedEvent, TagRemovedEvent
from core.path_utils import normalize_path

class TagService:
    def __init__(self, tag_repository: TagRepository, event_bus: EventBus):
        self._repository = tag_repository
        self._event_bus = event_bus
        # 캐시 추가
        self._file_tags_cache: Dict[str, List[str]] = {}
        self._all_tags_cache: List[str] = None

    def add_tag_to_file(self, file_path: str, tag: str) -> bool:
        result = self._repository.add_tag(file_path, tag)
        if result:
            # 캐시 업데이트
            if file_path in self._file_tags_cache:
                if tag not in self._file_tags_cache[file_path]:
                    self._file_tags_cache[file_path].append(tag)
            else:
                self._file_tags_cache[file_path] = [tag]
            
            # 전체 태그 캐시 무효화
            self._all_tags_cache = None
            
            self._event_bus.publish_tag_added(file_path, tag)
        return result

    def remove_tag_from_file(self, file_path: str, tag: str) -> bool:
        result = self._repository.remove_tag(file_path, tag)
        if result:
            # 캐시 업데이트
            if file_path in self._file_tags_cache:
                if tag in self._file_tags_cache[file_path]:
                    self._file_tags_cache[file_path].remove(tag)
            
            # 전체 태그 캐시 무효화
            self._all_tags_cache = None
            
            self._event_bus.publish_tag_removed(file_path, tag)
        return result

    def get_tags_for_file(self, file_path: str) -> list:
        # 캐시에서 먼저 확인
        if file_path in self._file_tags_cache:
            return self._file_tags_cache[file_path].copy()
        
        # 캐시에 없으면 데이터베이스에서 조회
        tags = self._repository.get_tags_for_file(file_path)
        self._file_tags_cache[file_path] = tags.copy()
        return tags

    def get_all_tags(self) -> list:
        # 캐시에서 먼저 확인
        if self._all_tags_cache is not None:
            return self._all_tags_cache.copy()
        
        # 캐시에 없으면 데이터베이스에서 조회
        tags = self._repository.get_all_tags()
        self._all_tags_cache = tags.copy()
        return tags

    def get_files_by_tags(self, tags: list) -> list:
        return self._repository.get_files_by_tags(tags)

    def delete_file_entry(self, file_path: str) -> bool:
        result = self._repository.delete_file_entry(file_path)
        if result:
            # 캐시에서 제거
            if file_path in self._file_tags_cache:
                del self._file_tags_cache[file_path]
        return result

    def add_tags_to_files(self, file_paths: List[str], tags_to_add: List[str]) -> dict:
        if not isinstance(file_paths, list) or not file_paths:
            return {"success": False, "error": "잘못된 파일 경로 리스트"}

        bulk_operations = []
        for file_path in file_paths:
            normalized_path = normalize_path(file_path)
            existing_tags = self._repository.get_tags_for_file(normalized_path)
            new_tags = list(set(existing_tags + tags_to_add))
            bulk_operations.append(
                UpdateOne({"file_path": normalized_path}, {"$set": {"tags": new_tags}}, upsert=True)
            )
        
        result = self._repository.bulk_update_tags(bulk_operations)
        if result.get("modified", 0) > 0 or result.get("upserted", 0) > 0:
            # 캐시 무효화
            for file_path in file_paths:
                if file_path in self._file_tags_cache:
                    del self._file_tags_cache[file_path]
            self._all_tags_cache = None
            
            for file_path in file_paths:
                for tag in tags_to_add:
                    self._event_bus.publish_tag_added(file_path, tag)
        return {"success": True, "processed": len(file_paths), "successful": result.get("modified", 0) + result.get("upserted", 0)}

    def remove_tags_from_files(self, file_paths: List[str], tags_to_remove: List[str]) -> dict:
        if not isinstance(file_paths, list) or not file_paths:
            return {"success": False, "error": "잘못된 파일 경로 리스트"}

        bulk_operations = []
        for file_path in file_paths:
            normalized_path = normalize_path(file_path)
            existing_tags = set(self._repository.get_tags_for_file(normalized_path))
            updated_tags = list(existing_tags - set(tags_to_remove))
            bulk_operations.append(
                UpdateOne({"file_path": normalized_path}, {"$set": {"tags": updated_tags}}, upsert=True)
            )

        result = self._repository.bulk_update_tags(bulk_operations)
        if result.get("modified", 0) > 0:
            # 캐시 무효화
            for file_path in file_paths:
                if file_path in self._file_tags_cache:
                    del self._file_tags_cache[file_path]
            self._all_tags_cache = None
            
            for file_path in file_paths:
                for tag in tags_to_remove:
                    self._event_bus.publish_tag_removed(file_path, tag)
        return {"success": True, "processed": len(file_paths), "successful": result.get("modified", 0) + result.get("upserted", 0)}

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

    def clear_cache(self):
        """캐시를 초기화합니다."""
        self._file_tags_cache.clear()
        self._all_tags_cache = None
