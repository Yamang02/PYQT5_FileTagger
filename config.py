import urllib.parse

# MongoDB connection settings
MONGO_HOST = "localhost"
MONGO_PORT = 27018
MONGO_DB_NAME = "file_tagger"
MONGO_COLLECTION_NAME = "tags"

# MongoDB URI (인증 없음)
MONGO_URI = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/"

# Application settings
DEFAULT_WORKSPACE_PATH = "G:/내 드라이브/obsidian"
CUSTOM_TAGS_FILE = "custom_tags.json" # 커스텀 태그 저장 파일