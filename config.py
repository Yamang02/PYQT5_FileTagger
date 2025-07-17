import urllib.parse

# MongoDB connection settings
MONGO_HOST = "localhost"
MONGO_PORT = 27018
MONGO_DB_NAME = "file_tagger"
MONGO_COLLECTION_NAME = "tags"

# MongoDB URI (인증 정보 포함)
# 사용자 이름과 비밀번호를 URL 인코딩하여 특수문자 문제를 방지합니다.
username = urllib.parse.quote_plus("root")
password = urllib.parse.quote_plus("password")
MONGO_URI = f"mongodb://{username}:{password}@{MONGO_HOST}:{MONGO_PORT}/?authSource=admin"

# Application settings
DEFAULT_WORKSPACE_PATH = "G:/내 드라이브/obsidian"
CUSTOM_TAGS_FILE = "custom_tags.json" # 커스텀 태그 저장 파일