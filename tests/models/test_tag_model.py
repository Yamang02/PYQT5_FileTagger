import pytest
from datetime import datetime
from bson import ObjectId
from models.tag_model import Tag, TagMetadata, create_tag, validate_tag_name, normalize_tag_name


class TestTagMetadata:
    """TagMetadata 클래스 테스트"""
    
    def test_tag_metadata_default_values(self):
        """기본값으로 TagMetadata 생성"""
        metadata = TagMetadata()
        assert metadata.category is None
        assert metadata.description is None
        assert metadata.parent_tags == []
        assert metadata.child_tags == []
        assert metadata.related_tags == []
        assert metadata.created_at is None
        assert metadata.updated_at is None
    
    def test_tag_metadata_with_values(self):
        """값을 지정하여 TagMetadata 생성"""
        now = datetime.utcnow()
        metadata = TagMetadata(
            category="테스트",
            description="테스트 설명",
            created_at=now,
            updated_at=now
        )
        assert metadata.category == "테스트"
        assert metadata.description == "테스트 설명"
        assert metadata.created_at == now
        assert metadata.updated_at == now
    
    def test_tag_metadata_to_dict(self):
        """TagMetadata를 딕셔너리로 변환"""
        metadata = TagMetadata(
            category="테스트",
            description="테스트 설명"
        )
        result = metadata.to_dict()
        assert result['category'] == "테스트"
        assert result['description'] == "테스트 설명"
        assert 'parent_tags' not in result  # 빈 리스트는 포함하지 않음
    
    def test_tag_metadata_from_dict(self):
        """딕셔너리에서 TagMetadata 생성"""
        data = {
            'category': '테스트',
            'description': '테스트 설명',
            'parent_tags': [ObjectId()],
            'child_tags': [ObjectId()]
        }
        metadata = TagMetadata.from_dict(data)
        assert metadata.category == "테스트"
        assert metadata.description == "테스트 설명"
        assert len(metadata.parent_tags) == 1
        assert len(metadata.child_tags) == 1


class TestTag:
    """Tag 클래스 테스트"""
    
    def test_tag_creation(self):
        """태그 생성"""
        tag = Tag(name="테스트태그")
        assert tag.name == "테스트태그"
        assert tag._id is None
        assert isinstance(tag.metadata, TagMetadata)
    
    def test_tag_with_metadata(self):
        """메타데이터와 함께 태그 생성"""
        metadata = TagMetadata(category="테스트", description="설명")
        tag = Tag(name="테스트태그", metadata=metadata)
        assert tag.name == "테스트태그"
        assert tag.metadata.category == "테스트"
        assert tag.metadata.description == "설명"
    
    def test_tag_validation_empty_name(self):
        """빈 태그 이름 검증"""
        with pytest.raises(ValueError, match="태그 이름은 필수입니다"):
            Tag(name="")
    
    def test_tag_validation_long_name(self):
        """긴 태그 이름 검증"""
        long_name = "a" * 51
        with pytest.raises(ValueError, match="태그 이름은 최대 50자까지 가능합니다"):
            Tag(name=long_name)
    
    def test_tag_validation_long_category(self):
        """긴 카테고리 검증"""
        long_category = "a" * 51
        metadata = TagMetadata(category=long_category)
        with pytest.raises(ValueError, match="태그 카테고리는 최대 50자까지 가능합니다"):
            Tag(name="테스트", metadata=metadata)
    
    def test_tag_validation_long_description(self):
        """긴 설명 검증"""
        long_description = "a" * 201
        metadata = TagMetadata(description=long_description)
        with pytest.raises(ValueError, match="태그 설명은 최대 200자까지 가능합니다"):
            Tag(name="테스트", metadata=metadata)
    
    def test_tag_to_dict(self):
        """Tag를 딕셔너리로 변환"""
        tag = Tag(name="테스트태그")
        result = tag.to_dict()
        assert result['name'] == "테스트태그"
        assert '_id' not in result  # _id가 None이면 포함하지 않음
    
    def test_tag_to_dict_with_id(self):
        """_id가 있는 Tag를 딕셔너리로 변환"""
        tag_id = ObjectId()
        tag = Tag(name="테스트태그")
        tag._id = tag_id
        result = tag.to_dict()
        assert result['name'] == "테스트태그"
        assert result['_id'] == tag_id
    
    def test_tag_from_dict(self):
        """딕셔너리에서 Tag 생성"""
        data = {
            'name': '테스트태그',
            'category': '테스트',
            'description': '설명'
        }
        tag = Tag.from_dict(data)
        assert tag.name == "테스트태그"
        assert tag.metadata.category == "테스트"
        assert tag.metadata.description == "설명"
        assert tag._id is None
    
    def test_tag_from_dict_with_id(self):
        """_id가 있는 딕셔너리에서 Tag 생성"""
        tag_id = ObjectId()
        data = {
            '_id': tag_id,
            'name': '테스트태그'
        }
        tag = Tag.from_dict(data)
        assert tag.name == "테스트태그"
        assert tag._id == tag_id
    
    def test_tag_update_metadata(self):
        """태그 메타데이터 업데이트"""
        tag = Tag(name="테스트태그")
        tag.update_metadata(category="새카테고리", description="새설명")
        assert tag.metadata.category == "새카테고리"
        assert tag.metadata.description == "새설명"
        assert tag.metadata.updated_at is not None
    
    def test_tag_update_metadata_invalid_field(self):
        """잘못된 메타데이터 필드 업데이트"""
        tag = Tag(name="테스트태그")
        with pytest.raises(ValueError, match="알 수 없는 메타데이터 필드"):
            tag.update_metadata(invalid_field="값")


class TestTagUtilityFunctions:
    """태그 유틸리티 함수 테스트"""
    
    def test_create_tag(self):
        """create_tag 함수 테스트"""
        tag = create_tag("테스트태그", "테스트", "설명")
        assert tag.name == "테스트태그"
        assert tag.metadata.category == "테스트"
        assert tag.metadata.description == "설명"
        assert tag.metadata.created_at is not None
        assert tag.metadata.updated_at is not None
    
    def test_create_tag_minimal(self):
        """최소한의 정보로 태그 생성"""
        tag = create_tag("테스트태그")
        assert tag.name == "테스트태그"
        assert tag.metadata.category is None
        assert tag.metadata.description is None
    
    def test_validate_tag_name_valid(self):
        """유효한 태그 이름 검증"""
        assert validate_tag_name("테스트태그") is True
        assert validate_tag_name("a" * 50) is True  # 최대 길이
    
    def test_validate_tag_name_invalid(self):
        """유효하지 않은 태그 이름 검증"""
        assert validate_tag_name("") is False
        assert validate_tag_name("   ") is False
        assert validate_tag_name("a" * 51) is False  # 너무 긴 이름
        assert validate_tag_name(None) is False
        assert validate_tag_name(123) is False
    
    def test_normalize_tag_name(self):
        """태그 이름 정규화"""
        assert normalize_tag_name("  테스트태그  ") == "테스트태그"
        assert normalize_tag_name("테스트  태그") == "테스트 태그"
        assert normalize_tag_name("") == ""
        assert normalize_tag_name("   ") == "" 