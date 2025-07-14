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
        tags = self._collection.distinct("tags")
        return tags

    def get_files_by_tags(self, tags: list) -> list:
        docs = self._collection.find({"tags": {"$in": tags}})
        return [doc["file_path"] for doc in docs]

    def delete_file_entry(self, file_path: str) -> bool:
        result = self._collection.delete_one({"file_path": file_path})
        return result.deleted_count > 0
