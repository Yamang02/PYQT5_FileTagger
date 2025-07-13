
import pytest
from unittest.mock import MagicMock
from core.tag_manager import TagManager
import config
import os
from core.path_utils import normalize_path

# 테스트용 설정 오버라이드
config.MONGO_DB_NAME = "test_db"
config.MONGO_COLLECTION_NAME = "test_collection"

@pytest.fixture(scope="function")
def mock_mongo_client():
    """MagicMock을 사용하여 MongoDB 클라이언트를 모의(Mock)합니다."""
    mock_client = MagicMock()
    # connect 메서드가 항상 True를 반환하도록 설정
    mock_client.connect.return_value = True
    # admin.command("ping")이 오류 없이 동작하도록 설정
    mock_client.admin.command.return_value = {"ok": 1}
    yield mock_client

@pytest.fixture(scope="function")
def tag_manager(mock_mongo_client):
    """테스트용 TagManager 인스턴스를 생성하고 모의 DB에 연결합니다."""
    manager = TagManager()
    manager.client = mock_mongo_client
    manager.db = manager.client[config.MONGO_DB_NAME]
    manager.collection = manager.db[config.MONGO_COLLECTION_NAME]
    
    # 모의 collection 객체에 필요한 메서드들을 추가
    # 실제 MongoDB의 동작을 모방하여 테스트 로직을 구현
    mock_data = {}

    def mock_find_one(query):
        return mock_data.get(query.get("_id"))

    def mock_update_one(query, update, upsert=False):
        file_path = query.get("_id")
        tags = update.get("$set", {}).get("tags")
        if upsert and file_path not in mock_data:
            mock_data[file_path] = {"_id": file_path, "tags": tags}
            return MagicMock(modified_count=0, upserted_count=1)
        else:
            mock_data[file_path]["tags"] = tags
            return MagicMock(modified_count=1, upserted_count=0)

    def mock_distinct(field):
        all_tags = set()
        for doc in mock_data.values():
            all_tags.update(doc.get("tags", []))
        return sorted(list(all_tags))

    def mock_find(query):
        tag = query.get("tags")
        return [{"_id": fp} for fp, doc in mock_data.items() if tag in doc.get("tags", [])]

    def mock_bulk_write(operations, ordered=False):
        modified_count = 0
        upserted_count = 0
        for op in operations:
            if "updateOne" in op:
                query = op["updateOne"]["filter"]
                update = op["updateOne"]["update"]
                upsert = op["updateOne"].get("upsert", False)
                result = mock_update_one(query, update, upsert)
                modified_count += result.modified_count
                upserted_count += result.upserted_count
        return MagicMock(modified_count=modified_count, upserted_count=upserted_count)

    manager.collection.find_one.side_effect = mock_find_one
    manager.collection.update_one.side_effect = mock_update_one
    manager.collection.distinct.side_effect = mock_distinct
    manager.collection.find.side_effect = mock_find
    manager.collection.bulk_write.side_effect = mock_bulk_write
    manager.collection.delete_many.return_value = MagicMock(deleted_count=len(mock_data))

    yield manager
    mock_data.clear() # 테스트 후 데이터 클리어

# --- 기본 CRUD 및 연결 테스트 ---

@pytest.mark.unit
@pytest.mark.db
def test_connection(tag_manager):
    """DB 연결 상태 확인 테스트"""
    status = tag_manager.get_connection_status()
    assert status["connected"] is True
    assert status["status"] == "정상"

@pytest.mark.unit
@pytest.mark.db
def test_update_and_get_tags(tag_manager):
    """태그 추가 및 조회 기능 테스트"""
    file_path = "/test/file1.txt"
    tags = ["test1", "test2"]
    assert tag_manager.update_tags(file_path, tags) is True
    retrieved_tags = tag_manager.get_tags_for_file(file_path)
    assert sorted(retrieved_tags) == sorted(tags)

@pytest.mark.unit
@pytest.mark.db
def test_get_tags_for_non_existent_file(tag_manager):
    """존재하지 않는 파일의 태그 조회 시 빈 리스트 반환 테스트"""
    retrieved_tags = tag_manager.get_tags_for_file("/test/non_existent.txt")
    assert retrieved_tags == []

@pytest.mark.unit
@pytest.mark.db
def test_update_tags_with_invalid_path(tag_manager):
    """잘못된 파일 경로로 태그 업데이트 시 False 반환 테스트"""
    assert tag_manager.update_tags(None, ["tag1"]) is False
    assert tag_manager.update_tags("", ["tag1"]) is False

@pytest.mark.unit
@pytest.mark.db
def test_get_all_unique_tags(tag_manager):
    """모든 고유 태그 조회 기능 테스트"""
    tag_manager.update_tags("/test/file1.txt", ["apple", "banana"])
    tag_manager.update_tags("/test/file2.txt", ["banana", "cherry"])
    tag_manager.update_tags("/test/file3.txt", ["apple", "cherry", "date"])
    unique_tags = tag_manager.get_all_unique_tags()
    assert unique_tags == ["apple", "banana", "cherry", "date"]

@pytest.mark.unit
@pytest.mark.db
def test_get_files_by_tag(tag_manager):
    """태그별 파일 검색 기능 테스트"""
    tag_manager.update_tags("/test/file1.txt", ["dev", "python"])
    tag_manager.update_tags("/test/file2.txt", ["dev", "javascript"])
    tag_manager.update_tags("/test/file3.txt", ["docs", "python"])
    python_files = tag_manager.get_files_by_tag("python")
    expected = [normalize_path("/test/file1.txt"), normalize_path("/test/file3.txt")]
    assert sorted(python_files) == sorted(expected)
    dev_files = tag_manager.get_files_by_tag("dev")
    assert sorted(dev_files) == sorted(["/test/file1.txt", "/test/file2.txt"])
    non_existent_files = tag_manager.get_files_by_tag("non_existent")
    assert non_existent_files == []

# --- 일괄 태깅 (add_tags_to_directory) 테스트 ---

@pytest.fixture(scope="function")
def test_directory(tmp_path):
    """테스트용 디렉토리와 파일들을 생성하는 Fixture"""
    d = tmp_path / "test_dir"
    d.mkdir()
    (d / "file1.txt").touch()
    (d / "image.jpg").touch()
    (d / "document.pdf").touch()
    sub = d / "subdir"
    sub.mkdir()
    (sub / "sub_file.txt").touch()
    (sub / "sub_image.png").touch()
    return str(d)

@pytest.mark.unit
@pytest.mark.db
def test_add_tags_to_directory_non_recursive(tag_manager, test_directory):
    """일괄 태깅 (비재귀) 기능 테스트"""
    tags_to_add = ["batch", "test"]
    result = tag_manager.add_tags_to_directory(test_directory, tags_to_add)
    assert result["success"] is True
    assert result["processed"] == 3
    assert result["successful"] == 3
    assert sorted(tag_manager.get_tags_for_file(normalize_path(os.path.join(test_directory, "file1.txt")))) == sorted(tags_to_add)
    assert sorted(tag_manager.get_tags_for_file(normalize_path(os.path.join(test_directory, "image.jpg")))) == sorted(tags_to_add)
    assert sorted(tag_manager.get_tags_for_file(normalize_path(os.path.join(test_directory, "document.pdf")))) == sorted(tags_to_add)
    assert tag_manager.get_tags_for_file(normalize_path(os.path.join(test_directory, "subdir", "sub_file.txt"))) == []

@pytest.mark.unit
@pytest.mark.db
def test_add_tags_to_directory_recursive(tag_manager, test_directory):
    """일괄 태깅 (재귀) 기능 테스트"""
    tags_to_add = ["recursive", "all"]
    result = tag_manager.add_tags_to_directory(test_directory, tags_to_add, recursive=True)
    assert result["success"] is True
    assert result["processed"] == 5
    assert result["successful"] == 5
    assert sorted(tag_manager.get_tags_for_file(normalize_path(os.path.join(test_directory, "file1.txt")))) == sorted(tags_to_add)
    assert sorted(tag_manager.get_tags_for_file(normalize_path(os.path.join(test_directory, "subdir", "sub_file.txt")))) == sorted(tags_to_add)
    assert sorted(tag_manager.get_tags_for_file(normalize_path(os.path.join(test_directory, "subdir", "sub_image.png")))) == sorted(tags_to_add)

@pytest.mark.unit
@pytest.mark.db
def test_add_tags_to_directory_with_extension_filter(tag_manager, test_directory):
    """일괄 태깅 (확장자 필터) 기능 테스트"""
    tags_to_add = ["image", "filtered"]
    result = tag_manager.add_tags_to_directory(test_directory, tags_to_add, recursive=True, file_extensions=[".jpg", ".png"])
    assert result["success"] is True
    assert result["processed"] == 2
    assert result["successful"] == 2
    assert sorted(tag_manager.get_tags_for_file(normalize_path(os.path.join(test_directory, "image.jpg")))) == sorted(tags_to_add)
    assert sorted(tag_manager.get_tags_for_file(normalize_path(os.path.join(test_directory, "subdir", "sub_image.png")))) == sorted(tags_to_add)
    assert tag_manager.get_tags_for_file(normalize_path(os.path.join(test_directory, "file1.txt"))) == []
    assert tag_manager.get_tags_for_file(normalize_path(os.path.join(test_directory, "document.pdf"))) == []

@pytest.mark.unit
@pytest.mark.db
def test_add_tags_to_non_existent_directory(tag_manager):
    """존재하지 않는 디렉토리에 대한 일괄 태깅 시도 테스트"""
    result = tag_manager.add_tags_to_directory("/non/existent/dir", ["tag"])
    assert result["success"] is False
    assert "디렉토리를 찾을 수 없습니다" in result["error"]

@pytest.mark.unit
@pytest.mark.db
def test_add_tags_merges_with_existing_tags(tag_manager, test_directory):
    """기존 태그와 새 태그를 병합하는 기능 테스트"""
    file_path = os.path.join(test_directory, "file1.txt")
    tag_manager.update_tags(file_path, ["existing", "tag"])
    result = tag_manager.add_tags_to_directory(test_directory, ["new", "tag"])
    assert result["success"] is True
    retrieved_tags = tag_manager.get_tags_for_file(file_path)
    assert sorted(retrieved_tags) == sorted(["existing", "new", "tag"])
