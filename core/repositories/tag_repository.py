import logging
from pymongo import UpdateOne
from pymongo.errors import OperationFailure
from core.path_utils import normalize_path
import config

logger = logging.getLogger(__name__)

class TagRepository:
    """
    MongoDB와 직접 상호작용하여 태그 데이터를 관리하는 리포지토리 클래스.
    모든 데이터베이스 I/O 로직을 담당합니다.
    """
    def __init__(self, mongo_client):
        """
        초기화 시 MongoClient 인스턴스를 주입받습니다.
        """
        if not mongo_client:
            raise ValueError("mongo_client는 None일 수 없습니다.")
        self.client = mongo_client
        self.db = self.client[config.MONGO_DB_NAME]
        self.collection = self.db[config.MONGO_COLLECTION_NAME]
        logger.info("[TagRepository] 인스턴스 생성 및 DB/컬렉션 설정 완료")

    def get_tags_for_file(self, file_path: str) -> list[str]:
        """
        주어진 파일 경로에 대한 태그 리스트를 데이터베이스에서 검색합니다.
        """
        try:
            normalized_path = normalize_path(file_path)
            document = self.collection.find_one({"_id": normalized_path})
            return document.get("tags", []) if document else []
        except OperationFailure as e:
            logger.error(f"DB 조회 오류 (get_tags_for_file): {e}")
            raise

    def update_tags(self, file_path: str, tags: list[str]) -> bool:
        """
        파일에 대한 태그 리스트를 업데이트하거나 새로 생성(upsert)합니다.
        """
        try:
            normalized_path = normalize_path(file_path)
            self.collection.update_one(
                {"_id": normalized_path}, {"$set": {"tags": tags}}, upsert=True
            )
            return True
        except OperationFailure as e:
            logger.error(f"DB 업데이트 오류 (update_tags): {e}")
            raise

    def bulk_update_tags(self, operations: list[UpdateOne]) -> dict:
        """
        여러 파일에 대한 태그를 한번에 업데이트(bulk write)합니다.
        """
        if not operations:
            return {"success": True, "modified": 0, "upserted": 0}
        try:
            result = self.collection.bulk_write(operations, ordered=False)
            return {
                "success": True,
                "modified": result.modified_count,
                "upserted": result.upserted_count,
            }
        except OperationFailure as e:
            logger.error(f"DB 벌크 업데이트 오류 (bulk_update_tags): {e}")
            raise

    def get_all_unique_tags(self) -> list[str]:
        """
        데이터베이스에 있는 모든 고유한 태그 목록을 정렬하여 반환합니다.
        """
        try:
            return sorted(self.collection.distinct("tags"))
        except OperationFailure as e:
            logger.error(f"DB 고유 태그 조회 오류 (get_all_unique_tags): {e}")
            raise

    def get_files_by_tag(self, tag: str) -> list[str]:
        """
        특정 태그를 포함하는 모든 파일의 경로 목록을 검색합니다.
        """
        try:
            documents = self.collection.find({"tags": tag})
            return [doc["_id"] for doc in documents]
        except OperationFailure as e:
            logger.error(f"DB 태그별 파일 검색 오류 (get_files_by_tag): {e}")
            raise

    def find_files(self, file_paths: list[str]) -> dict[str, list[str]]:
        """
        주어진 파일 경로 리스트에 해당하는 문서들을 찾아 태그 정보를 반환합니다.
        """
        try:
            normalized_paths = [normalize_path(p) for p in file_paths]
            docs = self.collection.find({"_id": {"$in": normalized_paths}})
            return {doc['_id']: doc.get('tags', []) for doc in docs}
        except OperationFailure as e:
            logger.error(f"DB 파일 검색 오류 (find_files): {e}")
            raise