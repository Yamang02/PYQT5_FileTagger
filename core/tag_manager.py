import urllib.parse
import logging
import os
from pymongo import MongoClient, UpdateOne
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, OperationFailure
import config  # config.py 파일을 import

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TagManagerError(Exception):
    """TagManager 관련 커스텀 예외 클래스"""
    pass


class TagManager:
    """
    MongoDB와 상호작용하여 파일 태그를 관리하는 모든 데이터베이스 로직을 처리합니다.
    이 클래스는 UI에 대해 전혀 알지 못합니다.
    """

    def __init__(self):
        """
        초기화 시에는 연결을 시도하지 않고, 변수만 None으로 설정합니다.
        """
        self.client = None
        self.db = None
        self.collection = None
        self._connection_retry_count = 0
        self._max_retry_attempts = 3
        logger.info("[TagManager] 인스턴스 생성됨 (연결 전)")

    def connect(self):
        """
        실제 데이터베이스 연결을 수행합니다.
        이 메서드는 UI 스레드에서 직접 호출하면 안 됩니다.
        """
        if self.client:
            logger.info("[TagManager] 이미 연결되어 있습니다.")
            return True

        try:
            logger.info("[TagManager] MongoDB 연결 시도...")
            # MongoDB 연결 URI 생성 (인증 정보 포함)
            # 사용자 이름과 비밀번호를 URL 인코딩하여 특수문자 문제를 방지합니다.
            username = urllib.parse.quote_plus("root")
            password = urllib.parse.quote_plus("password")
            uri = f"mongodb://{username}:{password}@{config.MONGO_HOST}:{config.MONGO_PORT}/?authSource=admin"

            self.client = MongoClient(uri, serverSelectionTimeoutMS=5000)
            # 서버에 연결을 시도하여 연결 상태를 즉시 확인합니다.
            self.client.admin.command("ping")

            self.db = self.client[config.MONGO_DB_NAME]
            self.collection = self.db[config.MONGO_COLLECTION_NAME]
            
            # 연결 성공 시 재시도 카운터 리셋
            self._connection_retry_count = 0
            
            logger.info("[TagManager] MongoDB에 성공적으로 연결되었습니다.")
            return True
            
        except ConnectionFailure as e:
            logger.error(f"[TagManager] MongoDB 연결 실패: {e}")
            self._handle_connection_error(e)
            return False
        except ServerSelectionTimeoutError as e:
            logger.error(f"[TagManager] MongoDB 서버 선택 타임아웃: {e}")
            self._handle_connection_error(e)
            return False
        except Exception as e:
            logger.error(f"[TagManager] 예상치 못한 연결 오류: {e}")
            self._handle_connection_error(e)
            return False

    def _handle_connection_error(self, error):
        """연결 오류 처리 및 재시도 로직"""
        self.client = None
        self.db = None
        self.collection = None
        
        self._connection_retry_count += 1
        
        if self._connection_retry_count < self._max_retry_attempts:
            logger.warning(f"[TagManager] 연결 재시도 {self._connection_retry_count}/{self._max_retry_attempts}")
        else:
            logger.error(f"[TagManager] 최대 재시도 횟수 초과. 연결 실패")

    def _ensure_connection(self):
        """연결 상태를 확인하고 필요시 재연결을 시도합니다."""
        if self.collection is None:
            logger.warning("[TagManager] DB 연결이 없습니다. 재연결을 시도합니다.")
            if not self.connect():
                raise TagManagerError("데이터베이스 연결을 설정할 수 없습니다.")
        return True

    def get_tags_for_file(self, file_path):
        """
        주어진 파일 경로에 대한 태그 리스트를 데이터베이스에서 검색합니다.
        파일이 존재하지 않으면 빈 리스트를 반환합니다.
        """
        try:
            self._ensure_connection()
            
            if not file_path or not isinstance(file_path, str):
                logger.warning(f"[TagManager] 잘못된 파일 경로: {file_path}")
                return []

            document = self.collection.find_one({"_id": file_path})
            tags = document.get("tags", []) if document else []
            
            logger.debug(f"[TagManager] 파일 '{file_path}'의 태그 조회: {tags}")
            return tags
            
        except TagManagerError:
            raise
        except OperationFailure as e:
            logger.error(f"[TagManager] 데이터베이스 조회 오류: {e}")
            raise TagManagerError(f"태그 조회 중 데이터베이스 오류: {e}")
        except Exception as e:
            logger.error(f"[TagManager] 태그 조회 중 예상치 못한 오류: {e}")
            raise TagManagerError(f"태그 조회 중 오류: {e}")

    def update_tags(self, file_path, tags):
        """
        파일에 대한 태그 리스트를 업데이트하거나 새로 생성(upsert)합니다.
        파일 경로는 문서의 고유 식별자(_id)로 사용됩니다.

        Args:
            file_path (str): 파일 경로
            tags (list[str]): 태그 리스트

        Returns:
            bool: 업데이트 성공 여부
        """
        try:
            self._ensure_connection()
            
            if not file_path or not isinstance(file_path, str):
                logger.error(f"[TagManager] 잘못된 파일 경로: {file_path}")
                return False

            # tags가 문자열이면 리스트로 변환 (하위 호환성)
            if isinstance(tags, str):
                tags = [tag.strip() for tag in tags.split(",") if tag.strip()]
            elif not isinstance(tags, list):
                logger.error(f"[TagManager] 잘못된 태그 형식: {type(tags)}")
                return False

            # 태그 유효성 검사
            if not self._validate_tags(tags):
                logger.error(f"[TagManager] 유효하지 않은 태그: {tags}")
                return False

            result = self.collection.update_one(
                {"_id": file_path}, {"$set": {"tags": tags}}, upsert=True
            )
            
            logger.info(f"[TagManager] 태그 업데이트 성공: {file_path} -> {tags}")
            return True
            
        except TagManagerError:
            raise
        except OperationFailure as e:
            logger.error(f"[TagManager] 데이터베이스 업데이트 오류: {e}")
            raise TagManagerError(f"태그 업데이트 중 데이터베이스 오류: {e}")
        except Exception as e:
            logger.error(f"[TagManager] 태그 업데이트 중 예상치 못한 오류: {e}")
            raise TagManagerError(f"태그 업데이트 중 오류: {e}")

    def _validate_tags(self, tags):
        """태그 리스트의 유효성을 검사합니다."""
        if not isinstance(tags, list):
            return False
        
        for tag in tags:
            if not isinstance(tag, str) or not tag.strip():
                return False
            # 태그 길이 제한 (예: 50자)
            if len(tag.strip()) > 50:
                return False
            # 특수문자 제한 (필요시)
            if any(char in tag for char in ['<', '>', '&', '"', "'"]):
                return False
                
        return True

    def get_all_unique_tags(self):
        """
        데이터베이스에 있는 모든 고유한 태그 목록을 알파벳 순으로 정렬하여 반환합니다.
        """
        try:
            self._ensure_connection()
            
            tags = sorted(self.collection.distinct("tags"))
            logger.debug(f"[TagManager] 전체 고유 태그 조회: {len(tags)}개")
            return tags
            
        except TagManagerError:
            raise
        except OperationFailure as e:
            logger.error(f"[TagManager] 고유 태그 조회 중 데이터베이스 오류: {e}")
            raise TagManagerError(f"고유 태그 조회 중 데이터베이스 오류: {e}")
        except Exception as e:
            logger.error(f"[TagManager] 고유 태그 조회 중 예상치 못한 오류: {e}")
            raise TagManagerError(f"고유 태그 조회 중 오류: {e}")

    def get_all_tags(self):
        """
        get_all_unique_tags의 별칭 메서드 (하위 호환성)
        """
        return self.get_all_unique_tags()

    def save_tags(self, file_path, tags):
        """
        update_tags의 별칭 메서드 (하위 호환성)
        """
        return self.update_tags(file_path, tags)

    def set_tags_for_file(self, file_path, tags):
        """
        update_tags의 별칭 메서드 (하위 호환성)
        """
        return self.update_tags(file_path, tags)

    def get_files_by_tag(self, tag):
        """
        특정 태그를 포함하는 모든 파일의 경로 목록을 검색합니다.
        """
        try:
            self._ensure_connection()
            
            if not tag or not isinstance(tag, str):
                logger.warning(f"[TagManager] 잘못된 태그: {tag}")
                return []

            documents = self.collection.find({"tags": tag})
            file_paths = [doc["_id"] for doc in documents]
            
            logger.debug(f"[TagManager] 태그 '{tag}'로 파일 검색: {len(file_paths)}개")
            return file_paths
            
        except TagManagerError:
            raise
        except OperationFailure as e:
            logger.error(f"[TagManager] 태그별 파일 검색 중 데이터베이스 오류: {e}")
            raise TagManagerError(f"태그별 파일 검색 중 데이터베이스 오류: {e}")
        except Exception as e:
            logger.error(f"[TagManager] 태그별 파일 검색 중 예상치 못한 오류: {e}")
            raise TagManagerError(f"태그별 파일 검색 중 오류: {e}")

    def add_tags_to_files(self, file_paths, tags):
        """
        여러 파일에 대해 일괄적으로 태그를 추가합니다. (기존 태그 보존)

        Args:
            file_paths (list[str]): 대상 파일 경로 리스트
            tags (list[str]): 추가할 태그 리스트

        Returns:
            dict: 처리 결과 정보
        """
        try:
            self._ensure_connection()

            if not isinstance(file_paths, list) or not file_paths:
                return {"success": False, "error": "잘못된 파일 경로 리스트"}
            
            if not self._validate_tags(tags):
                return {"success": False, "error": "유효하지 않은 태그가 포함되어 있습니다"}

            logger.info(f"[TagManager] 다중 파일 태그 추가 시작: {len(file_paths)}개 파일, 태그: {tags}")

            bulk_operations = []
            error_files = []

            # DB에서 기존 태그를 한 번에 가져옵니다.
            existing_docs = {doc['_id']: doc.get('tags', []) for doc in self.collection.find({"_id": {"$in": file_paths}})}

            for file_path in file_paths:
                try:
                    existing_tags = existing_docs.get(file_path, [])
                    new_tags = list(set(existing_tags + tags))
                    
                    bulk_operations.append(
                        UpdateOne({"_id": file_path}, {"$set": {"tags": new_tags}}, upsert=True)
                    )
                except Exception as e:
                    logger.error(f"[TagManager] 파일 '{file_path}' 처리 중 오류: {e}")
                    error_files.append({"file": file_path, "error": str(e)})

            if not bulk_operations:
                 return {"success": True, "message": "태그를 추가할 파일이 없습니다.", "processed": 0}

            result = self.collection.bulk_write(bulk_operations, ordered=False)
            
            success_count = len(file_paths) - len(error_files)
            logger.info(f"[TagManager] 다중 파일 태그 추가 완료: {success_count}개 성공, {len(error_files)}개 실패")
            
            return {
                "success": True,
                "processed": len(file_paths),
                "successful": success_count,
                "failed": len(error_files),
                "modified": result.modified_count,
                "upserted": result.upserted_count,
                "errors": error_files
            }

        except TagManagerError as e:
            logger.error(f"[TagManager] 다중 파일 태그 추가 중 TagManager 오류: {e}")
            return {"success": False, "error": str(e)}
        except OperationFailure as e:
            logger.error(f"[TagManager] 다중 파일 태그 추가 중 데이터베이스 오류: {e}")
            return {"success": False, "error": f"데이터베이스 오류: {e}"}
        except Exception as e:
            logger.error(f"[TagManager] 다중 파일 태그 추가 중 예상치 못한 오류: {e}")
            return {"success": False, "error": f"예상치 못한 오류: {e}"}

    def _get_files_in_directory(self, directory_path, recursive=False, file_extensions=None):
        """
        지정된 디렉토리 내에서 조건에 맞는 파일 경로를 탐색하여 반환합니다.
        """
        if not directory_path or not isinstance(directory_path, str):
            logger.error("[TagManager] _get_files_in_directory: 잘못된 디렉토리 경로")
            return []

        if not os.path.isdir(directory_path):
            logger.error(f"[TagManager] _get_files_in_directory: 디렉토리가 존재하지 않거나 유효하지 않음: {directory_path}")
            return []

        target_files = []

        def should_include_file(file_path):
            if file_extensions is None or len(file_extensions) == 0:
                logger.debug(f"[TagManager] _get_files_in_directory: 필터 없음, 모든 파일 포함: {file_path}")
                return True
            for ext in file_extensions:
                if file_path.lower().endswith(ext.lower()):
                    logger.debug(f"[TagManager] _get_files_in_directory: 확장자 필터 일치: {file_path} (.{ext})")
                    return True
            logger.debug(f"[TagManager] _get_files_in_directory: 확장자 필터 불일치: {file_path}")
            return False

        try:
            if recursive:
                logger.info(f"[TagManager] _get_files_in_directory: 하위 디렉토리 포함하여 파일 탐색 시작: {directory_path}")
                for root, _, files in os.walk(directory_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if should_include_file(file_path):
                            target_files.append(file_path)
            else:
                logger.info(f"[TagManager] _get_files_in_directory: 현재 디렉토리만 파일 탐색 시작: {directory_path}")
                for item in os.listdir(directory_path):
                    item_path = os.path.join(directory_path, item)
                    if os.path.isfile(item_path) and should_include_file(item_path):
                        target_files.append(item_path)
            logger.info(f"[TagManager] _get_files_in_directory: 탐색된 파일 수: {len(target_files)}")
            return target_files
        except Exception as e:
            logger.error(f"[TagManager] _get_files_in_directory: 파일 탐색 중 오류: {e}")
            return []

    def add_tags_to_directory(self, directory_path, tags, recursive=False, file_extensions=None):
        """
        특정 디렉토리 내의 파일들에 대해 일괄적으로 태그를 추가합니다.
        """
        logger.info(f"[TagManager] add_tags_to_directory 호출됨: dir={directory_path}, tags={tags}, recursive={recursive}, ext={file_extensions}")
        try:
            self._ensure_connection()
            
            if not self._validate_tags(tags):
                logger.error(f"[TagManager] 유효하지 않은 태그가 포함되어 있습니다: {tags}")
                return {"success": False, "error": "유효하지 않은 태그가 포함되어 있습니다"}

            target_files = self._get_files_in_directory(directory_path, recursive, file_extensions)
            
            if not target_files:
                logger.info("[TagManager] 조건에 맞는 파일이 없습니다. 태그 작업 건너뜀.")
                return {"success": True, "message": "조건에 맞는 파일이 없습니다", "processed": 0}

            logger.info(f"[TagManager] 일괄 태그 추가 시작: {len(target_files)}개 파일, 태그: {tags}")

            bulk_operations = []
            error_files = []
            
            # DB에서 기존 태그를 한 번에 가져옵니다.
            existing_docs = {doc['_id']: doc.get('tags', []) for doc in self.collection.find({"_id": {"$in": target_files}})}

            for file_path in target_files:
                try:
                    # 기존 태그 가져오기
                    existing_doc = self.collection.find_one({"_id": file_path})
                    existing_tags = existing_doc.get("tags", []) if existing_doc else []
                    
                    # 중복 제거하면서 새 태그 추가
                    new_tags = list(set(existing_tags + tags))
                    
                    bulk_operations.append(
                        UpdateOne({"_id": file_path}, {"$set": {"tags": new_tags}}, upsert=True)
                    )
                except Exception as e:
                    logger.error(f"[TagManager] 파일 '{file_path}' 처리 중 오류: {e}")
                    error_files.append({"file": file_path, "error": str(e)})

            # 벌크 업데이트 실행
            if bulk_operations:
                result = self.collection.bulk_write(bulk_operations, ordered=False)
                
                success_count = len(target_files) - len(error_files)
                logger.info(f"[TagManager] 일괄 태그 추가 완료: {success_count}개 성공, {len(error_files)}개 실패")
                
                return {
                    "success": True,
                    "processed": len(target_files),
                    "successful": success_count,
                    "failed": len(error_files),
                    "modified": result.modified_count,
                    "upserted": result.upserted_count,
                    "errors": error_files
                }

        except Exception as e:
            logger.error(f"[TagManager] 파일 수집 중 오류: {e}")
            return {"success": False, "error": f"파일 수집 중 오류: {e}"}

        except TagManagerError as e:
            logger.error(f"[TagManager] 일괄 태그 추가 중 TagManager 오류: {e}")
            return {"success": False, "error": str(e)}
        except OperationFailure as e:
            logger.error(f"[TagManager] 일괄 태그 추가 중 데이터베이스 오류: {e}")
            return {"success": False, "error": f"데이터베이스 오류: {e}"}
        except Exception as e:
            logger.error(f"[TagManager] 일괄 태그 추가 중 예상치 못한 오류: {e}")
            return {"success": False, "error": f"예상치 못한 오류: {e}"}

    def get_connection_status(self):
        """현재 데이터베이스 연결 상태를 반환합니다."""
        try:
            if self.client:
                # 연결 상태 확인
                self.client.admin.command("ping")
                return {"connected": True, "status": "정상"}
            else:
                return {"connected": False, "status": "연결되지 않음"}
        except Exception as e:
            return {"connected": False, "status": f"오류: {str(e)}"}

    def disconnect(self):
        """
        데이터베이스 연결을 종료합니다.
        """
        try:
            if self.client:
                self.client.close()
                self.client = None
                self.db = None
                self.collection = None
                logger.info("[TagManager] 데이터베이스 연결이 종료되었습니다.")
        except Exception as e:
            logger.error(f"[TagManager] 연결 종료 중 오류: {e}")

    def set_selected_directory(self, directory_path):
        """
        디렉토리 선택 메서드 (하위 호환성)
        현재는 로깅만 수행하고 실제 동작은 없음
        """
        logger.info(f"[TagManager] 선택된 디렉토리: {directory_path}")
        return True
