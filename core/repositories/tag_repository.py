from pymongo import MongoClient

class TagRepository:
    def __init__(self, mongo_client: MongoClient):
        self._client = mongo_client
        self._db = self._client.filetagger_db
        self._collection = self._db.tagged_files

    def add_tag(self, file_path: str, tag: str) -> bool:
        result = self._collection.update_one(
            {"file_path": file_path},
            {"$addToSet": {"tags": tag}},
            upsert=True
        )
        return result.modified_count > 0 or result.upserted_id is not None

    def remove_tag(self, file_path: str, tag: str) -> bool:
        result = self._collection.update_one(
            {"file_path": file_path},
            {"$pull": {"tags": tag}}
        )
        return result.modified_count > 0

    def get_tags_for_file(self, file_path: str) -> list:
        doc = self._collection.find_one({"file_path": file_path})
        return doc.get("tags", []) if doc else []

    def get_all_tags(self) -> list:
        # distinct 대신 find와 집합 연산을 사용
        all_tags = set()
        cursor = self._collection.find({}, {"tags": 1})
        for doc in cursor:
            if "tags" in doc and doc["tags"]:
                all_tags.update(doc["tags"])
        return sorted(list(all_tags))

    def get_files_by_tags(self, tags: list) -> list:
        docs = self._collection.find({"tags": {"$in": tags}})
        return [doc["file_path"] for doc in docs]

    def delete_file_entry(self, file_path: str) -> bool:
        result = self._collection.delete_one({"file_path": file_path})
        return result.deleted_count > 0

    def find_files(self, file_paths: list[str]) -> dict:
        """주어진 파일 경로 목록에 해당하는 문서들을 찾아 반환합니다.
        반환 형식: {normalized_file_path: [tag1, tag2], ...}
        """
        docs = self._collection.find({"file_path": {"$in": file_paths}})
        return {doc["file_path"]: doc.get("tags", []) for doc in docs}

    def bulk_update_tags(self, operations: list) -> dict:
        """주어진 bulk operations 리스트를 실행합니다.
        operations는 pymongo.UpdateOne 인스턴스 리스트여야 합니다.
        """
        if not operations:
            return {"modified": 0, "upserted": 0}
        
        result = self._collection.bulk_write(operations)
        return {"modified": result.modified_count, "upserted": result.upserted_count}
