import pytest
import os
import tempfile
import shutil
from datetime import datetime
from typing import List, Dict
from unittest.mock import patch

from core.repositories.tag_repository import TagRepository
from core.services.tag_service import TagService
from core.events import EventBus
from core.search_manager import SearchManager


class TestRealDatabaseIntegration:
    """실제 MongoDB 데이터베이스 통합 테스트"""
    
    @pytest.fixture
    def temp_test_dir(self):
        """임시 테스트 디렉토리 생성"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def tag_repository(self):
        """실제 TagRepository 인스턴스"""
        return TagRepository()
    
    @pytest.fixture
    def event_bus(self):
        """EventBus 인스턴스"""
        return EventBus()
    
    @pytest.fixture
    def tag_service(self, tag_repository, event_bus):
        """TagService 인스턴스"""
        return TagService(tag_repository, event_bus)
    
    @pytest.fixture
    def search_manager(self, tag_repository):
        """SearchManager 인스턴스"""
        return SearchManager(tag_repository)
    
    def test_database_connection(self, tag_repository):
        """데이터베이스 연결 테스트"""
        try:
            # 연결 테스트
            stats = tag_repository.get_tag_statistics()
            assert isinstance(stats, dict)
            print(f"[INFO] 데이터베이스 연결 성공: {stats}")
        except Exception as e:
            pytest.fail(f"데이터베이스 연결 실패: {e}")
    
    def test_index_creation(self, tag_repository):
        """인덱스 생성 테스트"""
        try:
            # 인덱스 정보 확인
            db = tag_repository._db
            
            # tags 컬렉션 인덱스 확인
            tags_indexes = list(db.tags.list_indexes())
            print(f"[INFO] tags 컬렉션 인덱스: {len(tags_indexes)}개")
            
            # tagged_files 컬렉션 인덱스 확인
            tagged_files_indexes = list(db.tagged_files.list_indexes())
            print(f"[INFO] tagged_files 컬렉션 인덱스: {len(tagged_files_indexes)}개")
            
            # 필수 인덱스 존재 확인
            index_names = [idx['name'] for idx in tags_indexes]
            assert 'name_1' in index_names, "태그명 고유 인덱스가 없습니다"
            assert 'name_text' in index_names, "태그명 텍스트 인덱스가 없습니다"
            
            index_names = [idx['name'] for idx in tagged_files_indexes]
            assert 'file_path_1' in index_names, "파일 경로 고유 인덱스가 없습니다"
            assert 'tags_1' in index_names, "태그 인덱스가 없습니다"
            
        except Exception as e:
            pytest.fail(f"인덱스 확인 실패: {e}")
    
    def test_basic_tag_operations(self, tag_service, temp_test_dir):
        """기본 태그 작업 테스트"""
        # 테스트 파일 생성
        test_file = os.path.join(temp_test_dir, "test_file.txt")
        with open(test_file, 'w') as f:
            f.write("테스트 파일 내용")
        
        try:
            # 태그 추가
            result = tag_service.add_tag_to_file(test_file, "테스트태그")
            assert result, "태그 추가 실패"
            
            # 태그 조회
            tags = tag_service.get_tags_for_file(test_file)
            assert "테스트태그" in tags, "추가된 태그가 조회되지 않습니다"
            
            # 태그 제거
            result = tag_service.remove_tag_from_file(test_file, "테스트태그")
            assert result, "태그 제거 실패"
            
            # 태그 제거 확인
            tags = tag_service.get_tags_for_file(test_file)
            assert "테스트태그" not in tags, "제거된 태그가 여전히 존재합니다"
            
            print(f"[INFO] 기본 태그 작업 테스트 성공")
            
        except Exception as e:
            pytest.fail(f"기본 태그 작업 실패: {e}")
    
    def test_bulk_tag_operations(self, tag_service, temp_test_dir):
        """대량 태그 작업 테스트"""
        # 테스트 파일들 생성
        test_files = []
        for i in range(10):
            test_file = os.path.join(temp_test_dir, f"test_file_{i}.txt")
            with open(test_file, 'w') as f:
                f.write(f"테스트 파일 {i} 내용")
            test_files.append(test_file)
        
        try:
            # 대량 태그 추가
            tags_to_add = ["개발", "중요", "테스트"]
            result = tag_service.add_tags_to_files(test_files, tags_to_add)
            
            assert result.get("success"), f"대량 태그 추가 실패: {result.get('error')}"
            assert result.get("successful") == 10, "모든 파일에 태그가 추가되지 않았습니다"
            
            # 태그 확인
            for file_path in test_files:
                tags = tag_service.get_tags_for_file(file_path)
                for tag in tags_to_add:
                    assert tag in tags, f"파일 {file_path}에 태그 {tag}가 없습니다"
            
            print(f"[INFO] 대량 태그 작업 테스트 성공: {result.get('successful')}개 파일")
            
        except Exception as e:
            pytest.fail(f"대량 태그 작업 실패: {e}")
    
    def test_search_functionality(self, search_manager, tag_service, temp_test_dir):
        """검색 기능 테스트"""
        # 테스트 파일들 생성 및 태그 추가
        test_files = []
        for i in range(5):
            test_file = os.path.join(temp_test_dir, f"document_{i}.pdf")
            with open(test_file, 'w') as f:
                f.write(f"문서 {i} 내용")
            test_files.append(test_file)
            
            # 각 파일에 다른 태그 추가
            if i < 3:
                tag_service.add_tag_to_file(test_file, "중요")
            if i % 2 == 0:
                tag_service.add_tag_to_file(test_file, "개발")
        
        try:
            # 태그 기반 검색
            search_conditions = {
                "exact": {
                    "tags": {
                        "exact": ["중요"]
                    }
                }
            }
            
            results = search_manager.search_files(search_conditions)
            assert len(results) == 3, f"중요 태그 검색 결과가 예상과 다릅니다: {len(results)}개"
            
            # 복합 검색
            search_conditions = {
                "exact": {
                    "tags": {
                        "exact": ["개발"]
                    }
                },
                "partial": {
                    "filename": {
                        "partial": "document"
                    }
                }
            }
            
            results = search_manager.search_files(search_conditions)
            assert len(results) == 3, f"복합 검색 결과가 예상과 다릅니다: {len(results)}개"
            
            print(f"[INFO] 검색 기능 테스트 성공")
            
        except Exception as e:
            pytest.fail(f"검색 기능 테스트 실패: {e}")
    
    def test_tag_statistics(self, tag_repository, tag_service, temp_test_dir):
        """태그 통계 테스트"""
        # 테스트 데이터 생성
        test_files = []
        for i in range(20):
            test_file = os.path.join(temp_test_dir, f"stats_test_{i}.txt")
            with open(test_file, 'w') as f:
                f.write(f"통계 테스트 파일 {i}")
            test_files.append(test_file)
            
            # 다양한 태그 조합으로 추가
            if i < 10:
                tag_service.add_tag_to_file(test_file, "자주사용")
            if i < 5:
                tag_service.add_tag_to_file(test_file, "매우자주")
            if i % 3 == 0:
                tag_service.add_tag_to_file(test_file, "간헐적")
        
        try:
            # 통계 조회
            stats = tag_repository.get_tag_statistics()
            
            assert "total_tags" in stats, "총 태그 수가 없습니다"
            assert "total_files" in stats, "총 파일 수가 없습니다"
            assert "popular_tags" in stats, "인기 태그가 없습니다"
            
            # 인기 태그 확인
            popular_tags = stats["popular_tags"]
            assert len(popular_tags) > 0, "인기 태그가 비어있습니다"
            
            # 가장 많이 사용된 태그 확인
            most_popular = popular_tags[0]
            assert most_popular["tag_name"] == "자주사용", f"가장 인기 있는 태그가 예상과 다릅니다: {most_popular}"
            
            print(f"[INFO] 태그 통계 테스트 성공: {stats['total_tags']}개 태그, {stats['total_files']}개 파일")
            
        except Exception as e:
            pytest.fail(f"태그 통계 테스트 실패: {e}")
    
    def test_recent_and_popular_files(self, tag_repository, tag_service, temp_test_dir):
        """최근 및 인기 파일 테스트"""
        # 테스트 파일들 생성
        test_files = []
        for i in range(15):
            test_file = os.path.join(temp_test_dir, f"recent_test_{i}.txt")
            with open(test_file, 'w') as f:
                f.write(f"최근 테스트 파일 {i}")
            test_files.append(test_file)
            
            # 태그 추가 (시간차를 두어 최근 파일 구분)
            tag_service.add_tag_to_file(test_file, f"태그{i}")
        
        try:
            # 최근 태그된 파일 조회
            recent_files = tag_repository.get_recently_tagged_files(limit=10)
            assert len(recent_files) <= 10, "최근 파일 수가 제한을 초과했습니다"
            
            # 가장 많이 태그된 파일 조회
            popular_files = tag_repository.get_most_tagged_files(limit=5)
            assert len(popular_files) <= 5, "인기 파일 수가 제한을 초과했습니다"
            
            print(f"[INFO] 최근/인기 파일 테스트 성공: 최근 {len(recent_files)}개, 인기 {len(popular_files)}개")
            
        except Exception as e:
            pytest.fail(f"최근/인기 파일 테스트 실패: {e}")
    
    def test_text_search(self, tag_repository, tag_service, temp_test_dir):
        """텍스트 검색 테스트"""
        # 다양한 태그 추가
        test_tags = ["개발프로젝트", "테스트코드", "문서작성", "개발환경", "테스트환경"]
        
        for i, tag in enumerate(test_tags):
            test_file = os.path.join(temp_test_dir, f"text_search_{i}.txt")
            with open(test_file, 'w') as f:
                f.write(f"텍스트 검색 테스트 파일 {i}")
            tag_service.add_tag_to_file(test_file, tag)
        
        try:
            # 텍스트 검색 테스트
            results = tag_repository.search_tags_by_text("개발", limit=5)
            assert len(results) > 0, "개발 관련 태그 검색 결과가 없습니다"
            
            # "개발"이 포함된 태그들 확인
            for tag in results:
                assert "개발" in tag, f"검색 결과에 '개발'이 포함되지 않은 태그가 있습니다: {tag}"
            
            # 테스트 검색
            results = tag_repository.search_tags_by_text("테스트", limit=5)
            assert len(results) > 0, "테스트 관련 태그 검색 결과가 없습니다"
            
            print(f"[INFO] 텍스트 검색 테스트 성공: '개발' {len(results)}개 결과")
            
        except Exception as e:
            pytest.fail(f"텍스트 검색 테스트 실패: {e}")
    
    def test_performance_with_large_dataset(self, tag_service, temp_test_dir):
        """대용량 데이터셋 성능 테스트"""
        import time
        
        # 대량의 테스트 파일 생성
        num_files = 100
        test_files = []
        
        print(f"[INFO] {num_files}개 테스트 파일 생성 중...")
        
        for i in range(num_files):
            test_file = os.path.join(temp_test_dir, f"perf_test_{i:03d}.txt")
            with open(test_file, 'w') as f:
                f.write(f"성능 테스트 파일 {i} 내용")
            test_files.append(test_file)
        
        try:
            # 대량 태그 추가 성능 테스트
            start_time = time.time()
            
            tags_to_add = ["성능테스트", "대용량", "벤치마크"]
            result = tag_service.add_tags_to_files(test_files, tags_to_add)
            
            end_time = time.time()
            duration = end_time - start_time
            
            assert result.get("success"), f"대량 태그 추가 실패: {result.get('error')}"
            assert result.get("successful") == num_files, "모든 파일에 태그가 추가되지 않았습니다"
            
            print(f"[INFO] {num_files}개 파일 태그 추가 완료: {duration:.2f}초")
            print(f"[INFO] 평균 처리 속도: {num_files / duration:.1f} 파일/초")
            
            # 성능 기준 확인 (100개 파일을 10초 이내에 처리)
            assert duration < 10, f"성능이 기준을 만족하지 않습니다: {duration:.2f}초"
            
        except Exception as e:
            pytest.fail(f"대용량 데이터셋 성능 테스트 실패: {e}")
    
    def test_data_consistency(self, tag_repository, tag_service, temp_test_dir):
        """데이터 일관성 테스트"""
        # 테스트 파일 생성
        test_file = os.path.join(temp_test_dir, "consistency_test.txt")
        with open(test_file, 'w') as f:
            f.write("일관성 테스트 파일")
        
        try:
            # 태그 추가
            tag_service.add_tag_to_file(test_file, "일관성태그")
            
            # 직접 데이터베이스에서 확인
            file_tags = tag_repository.get_tags_for_file(test_file)
            assert "일관성태그" in file_tags, "데이터베이스에 태그가 저장되지 않았습니다"
            
            # 태그 통계 확인
            stats = tag_repository.get_tag_statistics()
            assert stats["total_files"] > 0, "파일 수가 0입니다"
            
            # 태그 제거
            tag_service.remove_tag_from_file(test_file, "일관성태그")
            
            # 제거 확인
            file_tags = tag_repository.get_tags_for_file(test_file)
            assert "일관성태그" not in file_tags, "태그가 제대로 제거되지 않았습니다"
            
            print(f"[INFO] 데이터 일관성 테스트 성공")
            
        except Exception as e:
            pytest.fail(f"데이터 일관성 테스트 실패: {e}")


if __name__ == "__main__":
    # 직접 실행 시 테스트 수행
    pytest.main([__file__, "-v"]) 