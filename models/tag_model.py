"""
태그 데이터 모델

태그 관련 데이터 구조와 유틸리티 함수를 정의합니다.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from bson import ObjectId


@dataclass
class TagMetadata:
    """
    태그 메타데이터 모델
    
    태그의 추가 정보를 저장하는 데이터 클래스입니다.
    """
    category: Optional[str] = None
    description: Optional[str] = None
    parent_tags: List[ObjectId] = field(default_factory=list)
    child_tags: List[ObjectId] = field(default_factory=list)
    related_tags: List[ObjectId] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """데이터베이스 저장용 딕셔너리로 변환"""
        result = {}
        
        if self.category is not None:
            result['category'] = self.category
        if self.description is not None:
            result['description'] = self.description
        if self.parent_tags:
            result['parent_tags'] = self.parent_tags
        if self.child_tags:
            result['child_tags'] = self.child_tags
        if self.related_tags:
            result['related_tags'] = self.related_tags
        if self.created_at:
            result['created_at'] = self.created_at
        if self.updated_at:
            result['updated_at'] = self.updated_at
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TagMetadata':
        """딕셔너리에서 TagMetadata 객체 생성"""
        return cls(
            category=data.get('category'),
            description=data.get('description'),
            parent_tags=data.get('parent_tags', []),
            child_tags=data.get('child_tags', []),
            related_tags=data.get('related_tags', []),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )


@dataclass
class Tag:
    """
    태그 모델
    
    태그의 기본 정보와 메타데이터를 포함하는 데이터 클래스입니다.
    """
    name: str
    metadata: TagMetadata = field(default_factory=TagMetadata)
    _id: Optional[ObjectId] = None
    
    def __post_init__(self):
        """초기화 후 검증"""
        if not self.name:
            raise ValueError("태그 이름은 필수입니다")
        if len(self.name) > 50:
            raise ValueError("태그 이름은 최대 50자까지 가능합니다")
        if self.metadata.category and len(self.metadata.category) > 50:
            raise ValueError("태그 카테고리는 최대 50자까지 가능합니다")
        if self.metadata.description and len(self.metadata.description) > 200:
            raise ValueError("태그 설명은 최대 200자까지 가능합니다")
    
    def to_dict(self) -> Dict[str, Any]:
        """데이터베이스 저장용 딕셔너리로 변환"""
        result = {
            'name': self.name,
            **self.metadata.to_dict()
        }
        
        if self._id:
            result['_id'] = self._id
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Tag':
        """딕셔너리에서 Tag 객체 생성"""
        tag_id = data.get('_id')
        name = data['name']
        
        # 메타데이터 추출
        metadata_dict = {k: v for k, v in data.items() 
                        if k not in ['_id', 'name']}
        metadata = TagMetadata.from_dict(metadata_dict)
        
        tag = cls(name=name, metadata=metadata)
        tag._id = tag_id
        return tag
    
    def update_metadata(self, **kwargs) -> None:
        """메타데이터 업데이트"""
        for key, value in kwargs.items():
            if hasattr(self.metadata, key):
                setattr(self.metadata, key, value)
            else:
                raise ValueError(f"알 수 없는 메타데이터 필드: {key}")
        
        # updated_at 자동 업데이트
        self.metadata.updated_at = datetime.utcnow()


def create_tag(name: str, category: Optional[str] = None, 
               description: Optional[str] = None) -> Tag:
    """
    새로운 태그를 생성합니다.
    
    Args:
        name: 태그 이름 (필수, 최대 50자)
        category: 태그 카테고리 (선택, 최대 50자)
        description: 태그 설명 (선택, 최대 200자)
        
    Returns:
        Tag: 생성된 태그 객체
        
    Raises:
        ValueError: 유효하지 않은 입력값
    """
    metadata = TagMetadata(
        category=category,
        description=description,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    return Tag(name=name, metadata=metadata)


def validate_tag_name(name: str) -> bool:
    """
    태그 이름의 유효성을 검사합니다.
    
    Args:
        name: 검사할 태그 이름
        
    Returns:
        bool: 유효한 태그 이름이면 True
    """
    if not name or not isinstance(name, str):
        return False
    
    if len(name.strip()) == 0:
        return False
    
    if len(name) > 50:
        return False
    
    return True


def normalize_tag_name(name: str) -> str:
    """
    태그 이름을 정규화합니다.
    
    Args:
        name: 정규화할 태그 이름
        
    Returns:
        str: 정규화된 태그 이름
    """
    if not name:
        return ""
    
    # 앞뒤 공백 제거
    normalized = name.strip()
    
    # 연속된 공백을 단일 공백으로 변환
    import re
    normalized = re.sub(r'\s+', ' ', normalized)
    
    return normalized 