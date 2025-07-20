from pymongo import MongoClient
from bson import ObjectId
from typing import List, Dict, Optional, Any
from datetime import datetime
from models.tag_model import Tag, TagMetadata, create_tag, validate_tag_name, normalize_tag_name
from core.path_utils import normalize_path


class TagRepository:
    """
    태그 저장소
    
    새로운 아키텍처에 맞춰 태그와 파일-태그 연결을 관리합니다.
    - tags 컬렉션: 태그 메타데이터 저장
    - tagged_files 컬렉션: 파일-태그 연결 저장
    """
    
    def __init__(self, mongo_client: MongoClient):
        self._client = mongo_client
        self._db = self._client.filetagger_db
        self._tags_collection = self._db.tags
        self._tagged_files_collection = self._db.tagged_files
        
        # 인덱스 생성
        self._create_indexes()
    
    def _create_indexes(self):
        """필요한 인덱스를 생성합니다."""
        try:
            # tags 컬렉션 인덱스
            # 1. 태그 이름 고유 인덱스 (기본 검색용)
            self._tags_collection.create_index("name", unique=True)
            
            # 2. 카테고리 인덱스 (카테고리별 필터링용)
            self._tags_collection.create_index("category")
            
            # 3. 태그 이름 텍스트 인덱스 (부분일치 검색용)
            self._tags_collection.create_index([("name", "text")])
            
            # 4. 복합 인덱스: 카테고리 + 이름 (카테고리별 정렬용)
            self._tags_collection.create_index([("category", 1), ("name", 1)])
            
            # 5. 생성일자 인덱스 (최신 태그 조회용)
            self._tags_collection.create_index("created_at")
            
            # tagged_files 컬렉션 인덱스
            # 1. 파일 경로 고유 인덱스 (파일별 태그 조회용)
            self._tagged_files_collection.create_index("file_path", unique=True)
            
            # 2. 태그 배열 인덱스 (태그별 파일 조회용)
            self._tagged_files_collection.create_index("tags")
            
            # 3. 복합 인덱스: 태그 + 파일 경로 (태그별 파일 정렬용)
            self._tagged_files_collection.create_index([("tags", 1), ("file_path", 1)])
            
            # 4. 파일 경로 텍스트 인덱스 (파일명 부분일치 검색용)
            self._tagged_files_collection.create_index([("file_path", "text")])
            
            # 5. 업데이트일자 인덱스 (최근 태깅된 파일 조회용)
            self._tagged_files_collection.create_index("updated_at")
            
            # 6. 태그 개수 인덱스 (태그가 많은 파일 우선 조회용)
            self._tagged_files_collection.create_index([("tag_count", -1)])
            
            print("[INFO] MongoDB 인덱스 생성 완료")
            
        except Exception as e:
            print(f"[ERROR] 인덱스 생성 실패: {e}")
    
    def _update_tag_count(self, file_path: str):
        """
        파일의 태그 개수를 업데이트합니다.
        
        Args:
            file_path: 파일 경로
        """
        try:
            doc = self._tagged_files_collection.find_one({"file_path": file_path})
            if doc and "tags" in doc:
                tag_count = len(doc["tags"])
                self._tagged_files_collection.update_one(
                    {"file_path": file_path},
                    {"$set": {"tag_count": tag_count}}
                )
        except Exception as e:
            print(f"[ERROR] 태그 개수 업데이트 실패: {e}")
    
    def _update_timestamp(self, file_path: str):
        """
        파일의 업데이트 타임스탬프를 갱신합니다.
        
        Args:
            file_path: 파일 경로
        """
        try:
            self._tagged_files_collection.update_one(
                {"file_path": file_path},
                {"$set": {"updated_at": datetime.utcnow()}}
            )
        except Exception as e:
            print(f"[ERROR] 타임스탬프 업데이트 실패: {e}")
    
    def add_tag(self, file_path: str, tag_name: str) -> bool:
        """
        파일에 태그를 추가합니다.
        
        Args:
            file_path: 파일 경로
            tag_name: 태그 이름
            
        Returns:
            bool: 성공 여부
        """
        try:
            # 파일 경로 정규화
            normalized_path = normalize_path(file_path)
            
            # 태그 이름 정규화 및 검증
            normalized_tag_name = normalize_tag_name(tag_name)
            if not validate_tag_name(normalized_tag_name):
                return False
            
            # 태그가 존재하는지 확인하고, 없으면 생성
            tag_id = self._get_or_create_tag_id(normalized_tag_name)
            if not tag_id:
                return False
            
            # 파일에 태그 추가
            result = self._tagged_files_collection.update_one(
                {"file_path": normalized_path},
                {
                    "$addToSet": {"tags": tag_id},
                    "$set": {
                        "updated_at": datetime.utcnow(),
                        "created_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
            
            if result.modified_count > 0 or result.upserted_id is not None:
                # 태그 개수 업데이트
                self._update_tag_count(normalized_path)
                return True
            
            return False
            
        except Exception as e:
            print(f"[ERROR] TagRepository.add_tag 실패: {e}")
            return False
    
    def remove_tag(self, file_path: str, tag_name: str) -> bool:
        """
        파일에서 태그를 제거합니다.
        
        Args:
            file_path: 파일 경로
            tag_name: 태그 이름
            
        Returns:
            bool: 성공 여부
        """
        try:
            # 파일 경로 정규화
            normalized_path = normalize_path(file_path)
            
            # 태그 이름 정규화
            normalized_tag_name = normalize_tag_name(tag_name)
            
            # 태그 ID 조회
            tag_id = self._get_tag_id_by_name(normalized_tag_name)
            if not tag_id:
                return False
            
            # 파일에서 태그 제거
            result = self._tagged_files_collection.update_one(
                {"file_path": normalized_path},
                {
                    "$pull": {"tags": tag_id},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            if result.modified_count > 0:
                # 태그 개수 업데이트
                self._update_tag_count(normalized_path)
                return True
            
            return False
            
        except Exception as e:
            print(f"[ERROR] TagRepository.remove_tag 실패: {e}")
            return False
    
    def get_tags_for_file(self, file_path: str) -> List[str]:
        """
        파일의 태그 목록을 반환합니다.
        
        Args:
            file_path: 파일 경로
            
        Returns:
            List[str]: 태그 이름 목록
        """
        try:
            # 파일 경로 정규화
            normalized_path = normalize_path(file_path)
            
            # 파일의 태그 ID 목록 조회
            doc = self._tagged_files_collection.find_one({"file_path": normalized_path})
            if not doc or "tags" not in doc:
                return []
            
            tag_ids = doc["tags"]
            if not tag_ids:
                return []
            
            # 태그 ID를 태그 이름으로 변환
            tag_names = self._get_tag_names_by_ids(tag_ids)
            return tag_names
            
        except Exception as e:
            print(f"[ERROR] TagRepository.get_tags_for_file 실패: {e}")
            return []
    
    def get_all_tags(self) -> List[str]:
        """
        모든 태그 이름 목록을 반환합니다.
        
        Returns:
            List[str]: 태그 이름 목록
        """
        try:
            cursor = self._tags_collection.find({}, {"name": 1})
            tag_names = [doc["name"] for doc in cursor]
            return sorted(tag_names)
            
        except Exception as e:
            print(f"[ERROR] TagRepository.get_all_tags 실패: {e}")
            return []
    
    def get_files_by_tags(self, tag_names: List[str]) -> List[str]:
        """
        지정된 태그를 가진 파일 목록을 반환합니다.
        
        Args:
            tag_names: 태그 이름 목록
            
        Returns:
            List[str]: 파일 경로 목록
        """
        try:
            if not tag_names:
                return []
            
            # 태그 이름을 태그 ID로 변환
            tag_ids = []
            for tag_name in tag_names:
                normalized_tag_name = normalize_tag_name(tag_name)
                tag_id = self._get_tag_id_by_name(normalized_tag_name)
                if tag_id:
                    tag_ids.append(tag_id)
            
            if not tag_ids:
                return []
            
            # 태그를 가진 파일 조회
            cursor = self._tagged_files_collection.find({"tags": {"$in": tag_ids}})
            file_paths = [doc["file_path"] for doc in cursor]
            return file_paths
            
        except Exception as e:
            print(f"[ERROR] TagRepository.get_files_by_tags 실패: {e}")
            return []
    
    def search_tags_by_text(self, search_text: str, limit: int = 50) -> List[str]:
        """
        텍스트 검색으로 태그를 찾습니다.
        
        Args:
            search_text: 검색할 텍스트
            limit: 반환할 최대 태그 수
            
        Returns:
            List[str]: 태그 이름 목록
        """
        try:
            # 텍스트 검색 실행
            cursor = self._tags_collection.find(
                {"$text": {"$search": search_text}},
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).limit(limit)
            
            tag_names = [doc["name"] for doc in cursor]
            return tag_names
            
        except Exception as e:
            print(f"[ERROR] TagRepository.search_tags_by_text 실패: {e}")
            return []
    
    def get_recently_tagged_files(self, limit: int = 50) -> List[str]:
        """
        최근에 태깅된 파일 목록을 반환합니다.
        
        Args:
            limit: 반환할 최대 파일 수
            
        Returns:
            List[str]: 파일 경로 목록
        """
        try:
            cursor = self._tagged_files_collection.find().sort("updated_at", -1).limit(limit)
            file_paths = [doc["file_path"] for doc in cursor]
            return file_paths
            
        except Exception as e:
            print(f"[ERROR] TagRepository.get_recently_tagged_files 실패: {e}")
            return []
    
    def get_most_tagged_files(self, limit: int = 50) -> List[str]:
        """
        태그가 가장 많은 파일 목록을 반환합니다.
        
        Args:
            limit: 반환할 최대 파일 수
            
        Returns:
            List[str]: 파일 경로 목록
        """
        try:
            cursor = self._tagged_files_collection.find().sort("tag_count", -1).limit(limit)
            file_paths = [doc["file_path"] for doc in cursor]
            return file_paths
            
        except Exception as e:
            print(f"[ERROR] TagRepository.get_most_tagged_files 실패: {e}")
            return []
    
    def get_tags_by_category(self, category: str) -> List[str]:
        """
        특정 카테고리의 태그 목록을 반환합니다.
        
        Args:
            category: 카테고리명
            
        Returns:
            List[str]: 태그 이름 목록
        """
        try:
            cursor = self._tags_collection.find({"category": category}, {"name": 1})
            tag_names = [doc["name"] for doc in cursor]
            return sorted(tag_names)
            
        except Exception as e:
            print(f"[ERROR] TagRepository.get_tags_by_category 실패: {e}")
            return []
    
    def get_tag_statistics(self) -> Dict[str, Any]:
        """
        태그 통계 정보를 반환합니다.
        
        Returns:
            Dict[str, Any]: 통계 정보
        """
        try:
            # 전체 태그 수
            total_tags = self._tags_collection.count_documents({})
            
            # 전체 태깅된 파일 수
            total_files = self._tagged_files_collection.count_documents({})
            
            # 가장 많이 사용된 태그 (상위 10개)
            pipeline = [
                {"$unwind": "$tags"},
                {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10},
                {"$lookup": {
                    "from": "tags",
                    "localField": "_id",
                    "foreignField": "_id",
                    "as": "tag_info"
                }},
                {"$project": {
                    "tag_name": {"$arrayElemAt": ["$tag_info.name", 0]},
                    "count": 1
                }}
            ]
            
            popular_tags = list(self._tagged_files_collection.aggregate(pipeline))
            
            # 카테고리별 태그 수
            category_stats = list(self._tags_collection.aggregate([
                {"$group": {"_id": "$category", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]))
            
            return {
                "total_tags": total_tags,
                "total_files": total_files,
                "popular_tags": popular_tags,
                "category_stats": category_stats
            }
            
        except Exception as e:
            print(f"[ERROR] TagRepository.get_tag_statistics 실패: {e}")
            return {}
    
    def delete_file_entry(self, file_path: str) -> bool:
        """
        파일의 태그 정보를 삭제합니다.
        
        Args:
            file_path: 파일 경로
            
        Returns:
            bool: 성공 여부
        """
        try:
            # 파일 경로 정규화
            normalized_path = normalize_path(file_path)
            
            result = self._tagged_files_collection.delete_one({"file_path": normalized_path})
            return result.deleted_count > 0
            
        except Exception as e:
            print(f"[ERROR] TagRepository.delete_file_entry 실패: {e}")
            return False
    
    def find_files(self, file_paths: List[str]) -> Dict[str, List[str]]:
        """
        주어진 파일 경로 목록에 해당하는 태그 정보를 찾아 반환합니다.
        
        Args:
            file_paths: 파일 경로 목록
            
        Returns:
            Dict[str, List[str]]: {파일경로: [태그목록]} 형태의 딕셔너리
        """
        try:
            if not file_paths:
                return {}
            
            # 파일 경로 정규화
            normalized_paths = [normalize_path(path) for path in file_paths]
            
            # 파일들의 태그 정보 조회
            cursor = self._tagged_files_collection.find({"file_path": {"$in": normalized_paths}})
            
            result = {}
            for doc in cursor:
                file_path = doc["file_path"]
                tag_ids = doc.get("tags", [])
                
                # 태그 ID를 태그 이름으로 변환
                tag_names = self._get_tag_names_by_ids(tag_ids)
                result[file_path] = tag_names
            
            return result
            
        except Exception as e:
            print(f"[ERROR] TagRepository.find_files 실패: {e}")
            return {}
    
    def bulk_update_tags(self, operations: List) -> Dict[str, int]:
        """
        주어진 bulk operations 리스트를 실행합니다.
        
        Args:
            operations: pymongo.UpdateOne 인스턴스 리스트
            
        Returns:
            Dict[str, int]: {"modified": 수정된 문서 수, "upserted": 새로 생성된 문서 수}
        """
        try:
            if not operations:
                return {"modified": 0, "upserted": 0}
            
            result = self._tagged_files_collection.bulk_write(operations)
            return {"modified": result.modified_count, "upserted": result.upserted_count}
            
        except Exception as e:
            print(f"[ERROR] TagRepository.bulk_update_tags 실패: {e}")
            return {"modified": 0, "upserted": 0}
    
    def _get_or_create_tag_id(self, tag_name: str) -> Optional[ObjectId]:
        """
        태그 이름으로 태그 ID를 조회하고, 없으면 생성합니다.
        
        Args:
            tag_name: 태그 이름
            
        Returns:
            Optional[ObjectId]: 태그 ID
        """
        try:
            # 기존 태그 조회
            doc = self._tags_collection.find_one({"name": tag_name})
            if doc:
                return doc["_id"]
            
            # 새 태그 생성
            tag = create_tag(tag_name)
            tag_dict = tag.to_dict()
            # _id가 있으면 제거 (MongoDB가 자동 생성하도록)
            if "_id" in tag_dict:
                del tag_dict["_id"]
            
            result = self._tags_collection.insert_one(tag_dict)
            return result.inserted_id
            
        except Exception as e:
            print(f"[ERROR] TagRepository._get_or_create_tag_id 실패: {e}")
            return None
    
    def _get_tag_id_by_name(self, tag_name: str) -> Optional[ObjectId]:
        """
        태그 이름으로 태그 ID를 조회합니다.
        
        Args:
            tag_name: 태그 이름
            
        Returns:
            Optional[ObjectId]: 태그 ID
        """
        try:
            doc = self._tags_collection.find_one({"name": tag_name})
            return doc["_id"] if doc else None
            
        except Exception as e:
            print(f"[ERROR] TagRepository._get_tag_id_by_name 실패: {e}")
            return None
    
    def _get_tag_names_by_ids(self, tag_ids: List[ObjectId]) -> List[str]:
        """
        태그 ID 목록으로 태그 이름 목록을 조회합니다.
        
        Args:
            tag_ids: 태그 ID 목록
            
        Returns:
            List[str]: 태그 이름 목록
        """
        try:
            if not tag_ids:
                return []
            
            cursor = self._tags_collection.find({"_id": {"$in": tag_ids}}, {"name": 1})
            tag_names = [doc["name"] for doc in cursor]
            return tag_names
            
        except Exception as e:
            print(f"[ERROR] TagRepository._get_tag_names_by_ids 실패: {e}")
            return []
