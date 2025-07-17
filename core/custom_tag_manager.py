import json
import os
import logging
from core.config_manager import config_manager

logger = logging.getLogger(__name__)

class CustomTagManager:
    """
    사용자 정의 빠른 태그(Quick Tags)를 파일 시스템에 저장하고 로드하는 클래스입니다.
    """
    def __init__(self):
        self.file_path = os.path.join(os.getcwd(), config_manager.get_custom_tags_file())
        logger.info(f"[CustomTagManager] 커스텀 태그 파일 경로: {self.file_path}")

    def load_custom_quick_tags(self) -> list[str]:
        """
        저장된 커스텀 빠른 태그 목록을 로드합니다.
        파일이 없거나 읽기 오류 발생 시 빈 리스트를 반환합니다.
        """
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    tags = json.load(f)
                    if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
                        logger.warning("[CustomTagManager] 로드된 커스텀 태그 파일 형식이 올바르지 않습니다. 빈 리스트를 반환합니다.")
                        return []
                    logger.debug(f"[CustomTagManager] 커스텀 태그 로드 성공: {tags}")
                    return tags
            logger.info("[CustomTagManager] 커스텀 태그 파일이 존재하지 않습니다. 빈 리스트를 반환합니다.")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"[CustomTagManager] 커스텀 태그 파일 디코딩 오류: {e}")
            return []
        except Exception as e:
            logger.error(f"[CustomTagManager] 커스텀 태그 로드 중 예상치 못한 오류: {e}")
            return []

    def save_custom_quick_tags(self, tags: list[str]) -> bool:
        """
        커스텀 빠른 태그 목록을 파일에 저장합니다.
        """
        if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
            logger.error("[CustomTagManager] 저장할 커스텀 태그 목록 형식이 올바르지 않습니다.")
            return False
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(tags, f, ensure_ascii=False, indent=4)
            logger.debug(f"[CustomTagManager] 커스텀 태그 저장 성공: {tags}")
            return True
        except Exception as e:
            logger.error(f"[CustomTagManager] 커스텀 태그 저장 중 오류: {e}")
            return False
