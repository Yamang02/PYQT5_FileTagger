import urllib.parse
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import config  # config.py 파일을 import


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
        print("[TagManager] 인스턴스 생성됨 (연결 전)")

    def connect(self):
        """
        실제 데이터베이스 연결을 수행합니다.
        이 메서드는 UI 스레드에서 직접 호출하면 안 됩니다.
        """
        if self.client:
            print("[TagManager] 이미 연결되어 있습니다.")
            return True

        try:
            print("[TagManager] MongoDB 연결 시도...")
            # MongoDB 연결 URI 생성 (인증 정보 포함)
            # 사용자 이름과 비밀번호를 URL 인코딩하여 특수문자 문제를 방지합니다.
            username = urllib.parse.quote_plus("root")
            password = urllib.parse.quote_plus("password")
            uri = f"mongodb://{username}:{password}@{config.MONGO_HOST}:{config.MONGO_PORT}/"

            self.client = MongoClient(uri, serverSelectionTimeoutMS=5000)
            # 서버에 연결을 시도하여 연결 상태를 즉시 확인합니다.
            self.client.admin.command("ping")

            self.db = self.client[config.MONGO_DB_NAME]
            self.collection = self.db[config.MONGO_COLLECTION_NAME]
            print("[TagManager] MongoDB에 성공적으로 연결되었습니다.")
            return True
        except ConnectionFailure as e:
            print(f"[TagManager] MongoDB 연결 오류: {e}")
            self.client = None
            self.db = None
            self.collection = None
            return False

    def get_tags_for_file(self, file_path):
        """
        주어진 파일 경로에 대한 태그 리스트를 데이터베이스에서 검색합니다.
        파일이 존재하지 않으면 빈 리스트를 반환합니다.
        """
        if self.collection is None:
            print("[TagManager] DB 연결이 없어 태그를 가져올 수 없습니다.")
            return []

        document = self.collection.find_one({"_id": file_path})
        return document.get("tags", []) if document else []

    def update_tags(self, file_path, tags):
        """
        파일에 대한 태그 리스트를 업데이트하거나 새로 생성(upsert)합니다.
        파일 경로는 문서의 고유 식별자(_id)로 사용됩니다.

        Args:
            file_path (str): 파일 경로
            tags (list[str]): 태그 리스트
        """
        if self.collection is None:
            print("[TagManager] DB 연결이 없어 태그를 업데이트할 수 없습니다.")
            return False

        # tags가 문자열이면 리스트로 변환 (하위 호환성)
        if isinstance(tags, str):
            tags = [tag.strip() for tag in tags.split(",") if tag.strip()]
        elif not isinstance(tags, list):
            print(f"[TagManager] 잘못된 태그 형식: {type(tags)}")
            return False

        try:
            self.collection.update_one(
                {"_id": file_path}, {"$set": {"tags": tags}}, upsert=True
            )
            print(f"태그 업데이트 성공: {file_path} -> {tags}")
            return True
        except Exception as e:
            print(f"태그 업데이트 오류: {e}")
            return False

    def get_all_unique_tags(self):
        """
        데이터베이스에 있는 모든 고유한 태그 목록을 알파벳 순으로 정렬하여 반환합니다.
        """
        if self.collection is None:
            print("[TagManager] DB 연결이 없어 태그를 가져올 수 없습니다.")
            return []

        return sorted(self.collection.distinct("tags"))

    def get_files_by_tag(self, tag):
        """
        특정 태그를 포함하는 모든 파일의 경로 목록을 검색합니다.
        """
        if self.collection is None:
            print("[TagManager] DB 연결이 없어 파일을 가져올 수 없습니다.")
            return []

        documents = self.collection.find({"tags": tag})
        return [doc["_id"] for doc in documents]

    def disconnect(self):
        """
        데이터베이스 연결을 종료합니다.
        """
        if self.client:
            self.client.close()
            print("MongoDB 연결이 종료되었습니다.")
