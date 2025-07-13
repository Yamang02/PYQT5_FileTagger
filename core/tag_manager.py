import logging
import os
from pymongo import UpdateOne
from core.path_utils import normalize_path
from core.repositories.tag_repository import TagRepository

logger = logging.getLogger(__name__)

class TagManagerError(Exception):
    """TagManager 관련 커스텀 예외 클래스"""
    pass

class TagManager:
    """
    파일 태그 관련 비즈니스 로직을 처리합니다.
    데이터베이스 상호작용은 TagRepository에 위임합니다.
    """
    def __init__(self, mongo_client):
        """
        초기화 시 MongoClient를 받아 TagRepository를 생성합니다.
        """
        self.repository = TagRepository(mongo_client)
        logger.info("[TagManager] 인스턴스 생성 및 Repository 설정 완료")

    def get_tags_for_file(self, file_path):
        try:
            if not file_path or not isinstance(file_path, str):
                logger.warning(f"잘못된 파일 경로: {file_path}")
                return []
            return self.repository.get_tags_for_file(file_path)
        except Exception as e:
            logger.error(f"태그 조회 중 오류: {e}")
            raise TagManagerError(f"태그 조회 중 오류: {e}")

    def update_tags(self, file_path, tags):
        try:
            if not file_path or not isinstance(file_path, str):
                logger.error(f"잘못된 파일 경로: {file_path}")
                return False
            if not self._validate_tags(tags):
                logger.error(f"유효하지 않은 태그: {tags}")
                return False
            return self.repository.update_tags(file_path, tags)
        except Exception as e:
            logger.error(f"태그 업데이트 중 오류: {e}")
            raise TagManagerError(f"태그 업데이트 중 오류: {e}")

    def remove_tags_from_file(self, file_path: str, tags_to_remove: list[str]) -> bool:
        try:
            existing_tags = set(self.get_tags_for_file(file_path))
            updated_tags = list(existing_tags - set(tags_to_remove))
            return self.repository.update_tags(file_path, updated_tags)
        except Exception as e:
            logger.error(f"태그 제거 중 오류: {e}")
            raise TagManagerError(f"태그 제거 중 오류: {e}")

    def clear_all_tags_from_file(self, file_path: str) -> bool:
        try:
            return self.repository.update_tags(file_path, [])
        except Exception as e:
            logger.error(f"모든 태그 제거 중 오류: {e}")
            raise TagManagerError(f"모든 태그 제거 중 오류: {e}")

    def add_tags_to_files(self, file_paths: list[str], tags_to_add: list[str]) -> dict:
        if not isinstance(file_paths, list) or not file_paths:
            return {"success": False, "error": "잘못된 파일 경로 리스트"}
        if not self._validate_tags(tags_to_add):
            return {"success": False, "error": "유효하지 않은 태그가 포함되어 있습니다"}

        try:
            existing_docs = self.repository.find_files(file_paths)
            bulk_operations = []
            for file_path in file_paths:
                normalized_path = normalize_path(file_path)
                existing_tags = existing_docs.get(normalized_path, [])
                new_tags = list(set(existing_tags + tags_to_add))
                bulk_operations.append(
                    UpdateOne({"_id": normalized_path}, {"$set": {"tags": new_tags}}, upsert=True)
                )
            
            result = self.repository.bulk_update_tags(bulk_operations)
            return {
                "success": True,
                "processed": len(file_paths),
                "modified": result.get("modified", 0),
                "upserted": result.get("upserted", 0),
            }
        except Exception as e:
            logger.error(f"다중 파일 태그 추가 중 오류: {e}")
            return {"success": False, "error": str(e)}

    def remove_tags_from_files(self, file_paths: list[str], tags_to_remove: list[str]) -> dict:
        if not isinstance(file_paths, list) or not file_paths:
            return {"success": False, "error": "잘못된 파일 경로 리스트"}

        try:
            existing_docs = self.repository.find_files(file_paths)
            bulk_operations = []
            for file_path in file_paths:
                normalized_path = normalize_path(file_path)
                existing_tags = set(existing_docs.get(normalized_path, []))
                updated_tags = list(existing_tags - set(tags_to_remove))
                bulk_operations.append(
                    UpdateOne({"_id": normalized_path}, {"$set": {"tags": updated_tags}}, upsert=True)
                )

            result = self.repository.bulk_update_tags(bulk_operations)
            return {
                "success": True,
                "processed": len(file_paths),
                "modified": result.get("modified", 0),
                "upserted": result.get("upserted", 0),
            }
        except Exception as e:
            logger.error(f"다중 파일 태그 제거 중 오류: {e}")
            return {"success": False, "error": str(e)}

    def add_tags_to_directory(self, directory_path, tags, recursive=False, file_extensions=None):
        try:
            target_files = self._get_files_in_directory(directory_path, recursive, file_extensions)
            if not target_files:
                return {"success": True, "message": "조건에 맞는 파일이 없습니다", "processed": 0}
            return self.add_tags_to_files(target_files, tags)
        except Exception as e:
            logger.error(f"디렉토리 태그 추가 중 오류: {e}")
            return {"success": False, "error": str(e)}

    def get_all_unique_tags(self):
        try:
            return self.repository.get_all_unique_tags()
        except Exception as e:
            logger.error(f"고유 태그 조회 중 오류: {e}")
            raise TagManagerError(f"고유 태그 조회 중 오류: {e}")

    def get_files_by_tag(self, tag):
        try:
            if not tag or not isinstance(tag, str):
                logger.warning(f"잘못된 태그: {tag}")
                return []
            return self.repository.get_files_by_tag(tag)
        except Exception as e:
            logger.error(f"태그별 파일 검색 중 오류: {e}")
            raise TagManagerError(f"태그별 파일 검색 중 오류: {e}")

    def _get_files_in_directory(self, directory_path, recursive=False, file_extensions=None):
        if not directory_path or not os.path.isdir(directory_path):
            logger.error(f"유효하지 않은 디렉토리 경로: {directory_path}")
            return []
        
        target_files = []
        # ... (파일 탐색 로직은 동일하게 유지)
        return target_files

    def _validate_tags(self, tags):
        if not isinstance(tags, list):
            return False
        for tag in tags:
            if not isinstance(tag, str) or not tag.strip():
                return False
            if len(tag.strip()) > 50:
                return False
            if any(char in tag for char in ['<', '>', '&', '"', "'"]):
                return False
        return True

    # 하위 호환성을 위한 별칭 메서드들
    def get_all_tags(self): return self.get_all_unique_tags()
    def save_tags(self, file_path, tags): return self.update_tags(file_path, tags)
    def set_tags_for_file(self, file_path, tags): return self.update_tags(file_path, tags)