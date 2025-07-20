import pytest
from unittest.mock import Mock, MagicMock
from typing import List, Dict, Any
from core.search_manager import SearchManager
from core.adapters.tag_manager_adapter import TagManagerAdapter


class TestSearchManager:
    """SearchManager 클래스 테스트"""
    
    @pytest.fixture
    def mock_tag_manager(self):
        """Mock TagManagerAdapter"""
        return Mock(spec=TagManagerAdapter)
    
    @pytest.fixture
    def search_manager(self, mock_tag_manager):
        """SearchManager 인스턴스"""
        return SearchManager(mock_tag_manager)
    
    def test_search_files_exact_tags(self, search_manager, mock_tag_manager):
        """정확한 태그 매칭 검색"""
        # Mock 설정
        mock_tag_manager.get_files_by_tags.return_value = ["C:/test/file1.txt", "C:/test/file2.txt"]
        
        search_conditions = {
            'exact': {
                'tags': {
                    'exact': ['테스트태그', '개발']
                }
            }
        }
        
        result = search_manager.search_files(search_conditions)
        
        assert result == ["C:/test/file1.txt", "C:/test/file2.txt"]
        mock_tag_manager.get_files_by_tags.assert_called_once_with(['테스트태그', '개발'])
    
    def test_search_files_partial_tags(self, search_manager, mock_tag_manager):
        """태그 부분일치 검색"""
        # Mock 설정
        mock_tag_manager.get_all_tags.return_value = ['테스트태그', '개발태그', '문서태그']
        mock_tag_manager.get_files_by_tags.side_effect = [
            ["C:/test/file1.txt"],  # 테스트태그
            ["C:/test/file2.txt"],  # 개발태그
            ["C:/test/file3.txt"]   # 문서태그
        ]
        
        search_conditions = {
            'partial': {
                'tags': {
                    'partial': ['테스트', '개발']
                }
            }
        }
        
        result = search_manager.search_files(search_conditions)
        
        # 부분일치하는 태그들: '테스트태그', '개발태그' (문서태그는 매치되지 않음)
        assert len(result) == 2  # 중복 제거 후 2개 파일
        assert "C:/test/file1.txt" in result
        assert "C:/test/file2.txt" in result
    
    def test_search_files_legacy_format(self, search_manager, mock_tag_manager):
        """기존 형식 태그 검색"""
        # Mock 설정
        mock_tag_manager.get_files_by_tags.return_value = ["C:/test/file1.txt"]
        
        search_conditions = {
            'tags': {
                'query': '테스트태그'
            }
        }
        
        result = search_manager.search_files(search_conditions)
        
        assert result == ["C:/test/file1.txt"]
        mock_tag_manager.get_files_by_tags.assert_called_once_with(['테스트태그'])
    
    def test_search_files_by_filename(self, search_manager, mock_tag_manager, tmp_path, monkeypatch):
        """파일명 검색"""
        # 테스트 파일 생성
        test_file1 = tmp_path / "test_file1.txt"
        test_file1.write_text("test")
        test_file2 = tmp_path / "other_file.pdf"
        test_file2.write_text("test")
        
        # config_manager mock - 더 강력한 mock 설정
        mock_config = Mock()
        mock_config.get_workspace_path.return_value = str(tmp_path)
        
        with monkeypatch.context() as m:
            # config_manager 모듈 자체를 mock으로 교체
            m.setattr('core.config_manager', Mock())
            m.setattr('core.config_manager.config_manager', mock_config)
            
            search_conditions = {
                'filename': {
                    'name': 'test',
                    'extensions': ['txt']
                }
            }
            
            result = search_manager.search_files(search_conditions)
            
            assert len(result) == 1
            assert result[0].endswith("test_file1.txt")
    
    def test_search_files_partial_tags_with_filename_filter(self, search_manager, mock_tag_manager, tmp_path, monkeypatch):
        """태그 부분일치 + 파일명 필터"""
        # 테스트 파일 생성
        test_file1 = tmp_path / "test_file1.txt"
        test_file1.write_text("test")
        test_file2 = tmp_path / "other_file.txt"
        test_file2.write_text("test")
        
        # Mock 설정
        mock_tag_manager.get_all_tags.return_value = ['테스트태그', '개발태그']
        mock_tag_manager.get_files_by_tags.side_effect = [
            [str(test_file1)],  # 테스트태그
            [str(test_file2)]   # 개발태그
        ]
        
        # config_manager mock
        mock_config = Mock()
        mock_config.get_workspace_path.return_value = str(tmp_path)
        
        with monkeypatch.context() as m:
            # config_manager 모듈 자체를 mock으로 교체
            m.setattr('core.config_manager', Mock())
            m.setattr('core.config_manager.config_manager', mock_config)
            
            search_conditions = {
                'partial': {
                    'tags': {
                        'partial': ['테스트']
                    },
                    'filename': {
                        'partial': 'test'
                    }
                }
            }
            
            result = search_manager.search_files(search_conditions)
            
            # 테스트태그에 매치되고 파일명에 'test'가 포함된 파일만
            assert len(result) == 1
            assert result[0].endswith("test_file1.txt")
    
    def test_search_files_partial_tags_with_extension_filter(self, search_manager, mock_tag_manager, tmp_path, monkeypatch):
        """태그 부분일치 + 확장자 필터"""
        # 테스트 파일 생성
        test_file1 = tmp_path / "file1.txt"
        test_file1.write_text("test")
        test_file2 = tmp_path / "file2.pdf"
        test_file2.write_text("test")
        
        # Mock 설정
        mock_tag_manager.get_all_tags.return_value = ['테스트태그']
        mock_tag_manager.get_files_by_tags.return_value = [str(test_file1), str(test_file2)]
        
        # config_manager mock
        mock_config = Mock()
        mock_config.get_workspace_path.return_value = str(tmp_path)
        
        with monkeypatch.context() as m:
            # config_manager 모듈 자체를 mock으로 교체
            m.setattr('core.config_manager', Mock())
            m.setattr('core.config_manager.config_manager', mock_config)
            
            search_conditions = {
                'partial': {
                    'tags': {
                        'partial': ['테스트']
                    },
                    'extensions': {
                        'partial': ['txt']
                    }
                }
            }
            
            result = search_manager.search_files(search_conditions)
            
            # txt 확장자만 필터링
            assert len(result) == 1
            assert result[0].endswith("file1.txt")
    
    def test_search_files_no_matching_tags(self, search_manager, mock_tag_manager):
        """매칭되는 태그가 없는 경우"""
        # Mock 설정
        mock_tag_manager.get_all_tags.return_value = ['다른태그', '또다른태그']
        
        search_conditions = {
            'partial': {
                'tags': {
                    'partial': ['테스트']
                }
            }
        }
        
        result = search_manager.search_files(search_conditions)
        
        assert result == []
        mock_tag_manager.get_files_by_tags.assert_not_called()
    
    def test_search_files_empty_conditions(self, search_manager):
        """빈 검색 조건"""
        result = search_manager.search_files({})
        assert result == []
    
    def test_search_files_invalid_workspace_path(self, search_manager, mock_tag_manager, monkeypatch):
        """유효하지 않은 워크스페이스 경로"""
        # config_manager mock
        mock_config = Mock()
        mock_config.get_workspace_path.return_value = "/invalid/path"
        
        with monkeypatch.context() as m:
            # config_manager 모듈 자체를 mock으로 교체
            m.setattr('core.config_manager', Mock())
            m.setattr('core.config_manager.config_manager', mock_config)
            
            search_conditions = {
                'filename': {
                    'name': 'test'
                }
            }
            
            result = search_manager.search_files(search_conditions)
            assert result == []
    
    def test_search_files_tag_normalization(self, search_manager, mock_tag_manager):
        """태그 이름 정규화 확인"""
        # Mock 설정
        mock_tag_manager.get_files_by_tags.return_value = ["C:/test/file1.txt"]
        
        search_conditions = {
            'exact': {
                'tags': {
                    'exact': ['  테스트  태그  ', '  개발  ']
                }
            }
        }
        
        result = search_manager.search_files(search_conditions)
        
        # 정규화된 태그 이름으로 호출되었는지 확인
        mock_tag_manager.get_files_by_tags.assert_called_once_with(['테스트 태그', '개발'])
        assert result == ["C:/test/file1.txt"]
    
    def test_search_files_path_normalization(self, search_manager, mock_tag_manager, tmp_path, monkeypatch):
        """파일 경로 정규화 확인"""
        # 테스트 파일 생성
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("test")
        
        # config_manager mock
        mock_config = Mock()
        mock_config.get_workspace_path.return_value = str(tmp_path)
        
        with monkeypatch.context() as m:
            # config_manager 모듈 자체를 mock으로 교체
            m.setattr('core.config_manager', Mock())
            m.setattr('core.config_manager.config_manager', mock_config)
            
            search_conditions = {
                'filename': {
                    'name': 'test'
                }
            }
            
            result = search_manager.search_files(search_conditions)
            
            # 정규화된 경로로 반환되었는지 확인
            assert len(result) == 1
            assert result[0].replace('\\', '/').endswith("test_file.txt")
    
    def test_search_files_both_conditions(self, search_manager, mock_tag_manager):
        """정확한 매칭과 부분일치 조건 모두 사용"""
        # Mock 설정 - 부분일치 검색에서 사용할 태그들
        mock_tag_manager.get_all_tags.return_value = ['개발태그']
        mock_tag_manager.get_files_by_tags.side_effect = [
            ["C:/test/file1.txt", "C:/test/file2.txt"],  # exact tags
            ["C:/test/file2.txt", "C:/test/file3.txt"]   # partial tags
        ]
        
        search_conditions = {
            'exact': {
                'tags': {
                    'exact': ['테스트태그']
                }
            },
            'partial': {
                'tags': {
                    'partial': ['개발']
                }
            }
        }
        
        result = search_manager.search_files(search_conditions)
        
        # 교집합: file2만
        assert result == ["C:/test/file2.txt"]
    
    def test_search_files_exception_handling(self, search_manager, mock_tag_manager):
        """예외 처리 확인"""
        # Mock 설정 - 예외 발생
        mock_tag_manager.get_all_tags.side_effect = Exception("Database error")
        
        search_conditions = {
            'partial': {
                'tags': {
                    'partial': ['테스트']
                }
            }
        }
        
        result = search_manager.search_files(search_conditions)
        
        # 예외 발생 시 빈 리스트 반환
        assert result == [] 