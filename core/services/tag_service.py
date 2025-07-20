import os
from pymongo import UpdateOne
from typing import List, Dict, Optional
from core.repositories.tag_repository import TagRepository
from core.events import EventBus, TagAddedEvent, TagRemovedEvent
from core.path_utils import normalize_path
from models.tag_model import validate_tag_name, normalize_tag_name


class TagService:
    """
    태그 서비스
    
    태그 관련 비즈니스 로직을 처리하고, 캐싱과 이벤트 발행을 담당합니다.
    """
    
    def __init__(self, tag_repository: TagRepository, event_bus: EventBus):
        self._repository = tag_repository
        self._event_bus = event_bus
        # 캐시 추가
        self._file_tags_cache: Dict[str, List[str]] = {}
        self._all_tags_cache: Optional[List[str]] = None

    def add_tag_to_file(self, file_path: str, tag: str) -> bool:
        """
        파일에 태그를 추가합니다.
        
        Args:
            file_path: 파일 경로
            tag: 태그 이름
            
        Returns:
            bool: 성공 여부
        """
        try:
            # 태그 이름 검증
            normalized_tag = normalize_tag_name(tag)
            if not validate_tag_name(normalized_tag):
                return False
            
            # 파일 경로 정규화
            normalized_path = normalize_path(file_path)
            
            result = self._repository.add_tag(normalized_path, normalized_tag)
            if result:
                # 캐시 업데이트
                if normalized_path in self._file_tags_cache:
                    if normalized_tag not in self._file_tags_cache[normalized_path]:
                        self._file_tags_cache[normalized_path].append(normalized_tag)
                else:
                    self._file_tags_cache[normalized_path] = [normalized_tag]
                
                # 전체 태그 캐시 무효화
                self._all_tags_cache = None
                
                # 이벤트 발행
                self._event_bus.publish_tag_added(normalized_path, normalized_tag)
            
            return result
            
        except Exception as e:
            print(f"[ERROR] TagService.add_tag_to_file 실패: {e}")
            return False

    def remove_tag_from_file(self, file_path: str, tag: str) -> bool:
        """
        파일에서 태그를 제거합니다.
        
        Args:
            file_path: 파일 경로
            tag: 태그 이름
            
        Returns:
            bool: 성공 여부
        """
        try:
            # 태그 이름 정규화
            normalized_tag = normalize_tag_name(tag)
            
            # 파일 경로 정규화
            normalized_path = normalize_path(file_path)
            
            result = self._repository.remove_tag(normalized_path, normalized_tag)
            if result:
                # 캐시 업데이트
                if normalized_path in self._file_tags_cache:
                    if normalized_tag in self._file_tags_cache[normalized_path]:
                        self._file_tags_cache[normalized_path].remove(normalized_tag)
                
                # 전체 태그 캐시 무효화
                self._all_tags_cache = None
                
                # 이벤트 발행
                self._event_bus.publish_tag_removed(normalized_path, normalized_tag)
            
            return result
            
        except Exception as e:
            print(f"[ERROR] TagService.remove_tag_from_file 실패: {e}")
            return False

    def get_tags_for_file(self, file_path: str) -> List[str]:
        """
        파일의 태그 목록을 반환합니다.
        
        Args:
            file_path: 파일 경로
            
        Returns:
            List[str]: 태그 이름 목록
        """
        try:
            # 파일 경로 정규화
            normalized_path = normalize_path(file_path)
            
            # 캐시에서 먼저 확인
            if normalized_path in self._file_tags_cache:
                cached_tags = self._file_tags_cache[normalized_path].copy()
                return cached_tags
            
            # 캐시에 없으면 데이터베이스에서 조회
            tags = self._repository.get_tags_for_file(normalized_path)
            self._file_tags_cache[normalized_path] = tags.copy()
            return tags
            
        except Exception as e:
            print(f"[ERROR] TagService.get_tags_for_file 실패: {e}")
            return []

    def get_all_tags(self) -> List[str]:
        """
        모든 태그 목록을 반환합니다.
        
        Returns:
            List[str]: 태그 이름 목록
        """
        try:
            # 캐시에서 먼저 확인
            if self._all_tags_cache is not None:
                return self._all_tags_cache.copy()
            
            # 캐시에 없으면 데이터베이스에서 조회
            tags = self._repository.get_all_tags()
            self._all_tags_cache = tags.copy()
            return tags
            
        except Exception as e:
            print(f"[ERROR] TagService.get_all_tags 실패: {e}")
            return []

    def get_files_by_tags(self, tags: List[str]) -> List[str]:
        """
        지정된 태그를 가진 파일 목록을 반환합니다.
        
        Args:
            tags: 태그 이름 목록
            
        Returns:
            List[str]: 파일 경로 목록
        """
        try:
            return self._repository.get_files_by_tags(tags)
        except Exception as e:
            print(f"[ERROR] TagService.get_files_by_tags 실패: {e}")
            return []

    def delete_file_entry(self, file_path: str) -> bool:
        """
        파일의 태그 정보를 삭제합니다.
        
        Args:
            file_path: 파일 경로
            
        Returns:
            bool: 성공 여부
        """
        try:
            # 파일 경로 정규화
            normalized_path = normalize_path(file_path)
            
            result = self._repository.delete_file_entry(normalized_path)
            if result:
                # 캐시에서 제거
                if normalized_path in self._file_tags_cache:
                    del self._file_tags_cache[normalized_path]
            
            return result
            
        except Exception as e:
            print(f"[ERROR] TagService.delete_file_entry 실패: {e}")
            return False

    def add_tags_to_files(self, file_paths: List[str], tags_to_add: List[str]) -> Dict:
        """
        여러 파일에 태그를 일괄 추가합니다.
        
        Args:
            file_paths: 파일 경로 목록
            tags_to_add: 추가할 태그 목록
            
        Returns:
            Dict: 결과 정보
        """
        try:
            if not isinstance(file_paths, list) or not file_paths:
                return {"success": False, "error": "잘못된 파일 경로 리스트"}

            # 태그 이름 검증 및 정규화
            normalized_tags = []
            for tag in tags_to_add:
                normalized_tag = normalize_tag_name(tag)
                if validate_tag_name(normalized_tag):
                    normalized_tags.append(normalized_tag)
            
            if not normalized_tags:
                return {"success": False, "error": "유효한 태그가 없습니다"}

            # 각 파일에 태그 추가
            success_count = 0
            for file_path in file_paths:
                normalized_path = normalize_path(file_path)
                for tag in normalized_tags:
                    if self._repository.add_tag(normalized_path, tag):
                        success_count += 1
                        # 이벤트 발행
                        self._event_bus.publish_tag_added(normalized_path, tag)
            
            # 캐시 무효화
            for file_path in file_paths:
                normalized_path = normalize_path(file_path)
                if normalized_path in self._file_tags_cache:
                    del self._file_tags_cache[normalized_path]
            self._all_tags_cache = None
            
            return {
                "success": True, 
                "processed": len(file_paths), 
                "successful": success_count
            }
            
        except Exception as e:
            print(f"[ERROR] TagService.add_tags_to_files 실패: {e}")
            return {"success": False, "error": str(e)}

    def remove_tags_from_files(self, file_paths: List[str], tags_to_remove: List[str]) -> Dict:
        """
        여러 파일에서 태그를 일괄 제거합니다.
        
        Args:
            file_paths: 파일 경로 목록
            tags_to_remove: 제거할 태그 목록
            
        Returns:
            Dict: 결과 정보
        """
        try:
            if not isinstance(file_paths, list) or not file_paths:
                return {"success": False, "error": "잘못된 파일 경로 리스트"}

            # 태그 이름 정규화
            normalized_tags = [normalize_tag_name(tag) for tag in tags_to_remove]

            # 각 파일에서 태그 제거
            success_count = 0
            for file_path in file_paths:
                normalized_path = normalize_path(file_path)
                for tag in normalized_tags:
                    if self._repository.remove_tag(normalized_path, tag):
                        success_count += 1
                        # 이벤트 발행
                        self._event_bus.publish_tag_removed(normalized_path, tag)
            
            # 캐시 무효화
            for file_path in file_paths:
                normalized_path = normalize_path(file_path)
                if normalized_path in self._file_tags_cache:
                    del self._file_tags_cache[normalized_path]
            self._all_tags_cache = None
            
            return {
                "success": True, 
                "processed": len(file_paths), 
                "successful": success_count
            }
            
        except Exception as e:
            print(f"[ERROR] TagService.remove_tags_from_files 실패: {e}")
            return {"success": False, "error": str(e)}

    def add_tags_to_directory(self, directory_path: str, tags: List[str], 
                            recursive: bool = False, file_extensions: Optional[List[str]] = None) -> Dict:
        """
        디렉토리의 파일들에 태그를 일괄 추가합니다.
        
        Args:
            directory_path: 디렉토리 경로
            tags: 추가할 태그 목록
            recursive: 하위 디렉토리 포함 여부
            file_extensions: 대상 파일 확장자 목록
            
        Returns:
            Dict: 결과 정보
        """
        try:
            target_files = self._get_files_in_directory(directory_path, recursive, file_extensions)
            
            if not target_files:
                return {"success": True, "message": "조건에 맞는 파일이 없습니다", "processed": 0}
            
            return self.add_tags_to_files(target_files, tags)
            
        except Exception as e:
            print(f"[ERROR] TagService.add_tags_to_directory 실패: {e}")
            return {"success": False, "error": str(e)}

    def _get_files_in_directory(self, directory_path: str, recursive: bool = False, 
                               file_extensions: Optional[List[str]] = None) -> List[str]:
        """
        디렉토리에서 파일 목록을 가져옵니다.
        
        Args:
            directory_path: 디렉토리 경로
            recursive: 하위 디렉토리 포함 여부
            file_extensions: 대상 파일 확장자 목록
            
        Returns:
            List[str]: 파일 경로 목록
        """
        try:
            if not directory_path or not os.path.isdir(directory_path):
                return []

            target_files = []
            # 확장자 필터 정규화 (점 제거하고 소문자로)
            normalized_extensions = []
            if file_extensions:
                for ext in file_extensions:
                    normalized_ext = ext.lower().lstrip('.')
                    normalized_extensions.append(normalized_ext)

            if recursive:
                for root, _, files in os.walk(directory_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        file_ext = os.path.splitext(file_path)[1].lower().lstrip('.')
                        
                        # 확장자 필터 적용
                        if not normalized_extensions or file_ext in normalized_extensions:
                            target_files.append(normalize_path(file_path))
            else:
                for file in os.listdir(directory_path):
                    file_path = os.path.join(directory_path, file)
                    if os.path.isfile(file_path):
                        file_ext = os.path.splitext(file_path)[1].lower().lstrip('.')
                        
                        # 확장자 필터 적용
                        if not normalized_extensions or file_ext in normalized_extensions:
                            target_files.append(normalize_path(file_path))
            
            return target_files
            
        except Exception as e:
            print(f"[ERROR] TagService._get_files_in_directory 실패: {e}")
            return []

    def get_files_in_directory(self, directory_path: str, recursive: bool = False, 
                              file_extensions: Optional[List[str]] = None) -> List[str]:
        """
        디렉토리의 파일 목록을 반환합니다.
        
        Args:
            directory_path: 디렉토리 경로
            recursive: 하위 디렉토리 포함 여부
            file_extensions: 대상 파일 확장자 목록
            
        Returns:
            List[str]: 파일 경로 목록
        """
        return self._get_files_in_directory(directory_path, recursive, file_extensions)

    def clear_cache(self):
        """캐시를 초기화합니다."""
        self._file_tags_cache.clear()
        self._all_tags_cache = None
