import pytest
import os
from core.path_utils import normalize_path

class TestPathUtils:
    """파일 경로 정규화 함수 테스트"""
    
    def test_normalize_path_windows_style(self):
        """Windows 스타일 경로를 슬래시 기반으로 정규화"""
        # Windows 스타일 경로
        windows_path = "C:\\Users\\user\\Documents\\file.txt"
        expected = "C:/Users/user/Documents/file.txt"
        result = normalize_path(windows_path)
        assert result == expected
    
    def test_normalize_path_unix_style(self):
        """Unix 스타일 경로는 그대로 유지"""
        # Unix 스타일 경로
        unix_path = "/home/user/documents/file.txt"
        expected = "/home/user/documents/file.txt"
        result = normalize_path(unix_path)
        assert result == expected
    
    def test_normalize_path_mixed_separators(self):
        """혼합된 구분자가 있는 경로 정규화"""
        # 혼합된 구분자
        mixed_path = "C:\\Users/user\\Documents/file.txt"
        expected = "C:/Users/user/Documents/file.txt"
        result = normalize_path(mixed_path)
        assert result == expected
    
    def test_normalize_path_relative_path(self):
        """상대 경로 정규화"""
        # 상대 경로
        relative_path = "folder\\subfolder/file.txt"
        expected = "folder/subfolder/file.txt"
        result = normalize_path(relative_path)
        assert result == expected
    
    def test_normalize_path_duplicate_separators(self):
        """중복된 구분자 정규화"""
        # 중복된 구분자
        duplicate_path = "C:\\\\Users\\\\user\\Documents//file.txt"
        expected = "C:/Users/user/Documents/file.txt"
        result = normalize_path(duplicate_path)
        assert result == expected
    
    def test_normalize_path_empty_string(self):
        """빈 문자열 처리"""
        result = normalize_path("")
        assert result == ""
    
    def test_normalize_path_none_input(self):
        """None 입력 처리"""
        result = normalize_path(None)
        assert result is None
    
    def test_normalize_path_non_string_input(self):
        """문자열이 아닌 입력 처리"""
        result = normalize_path(123)
        assert result == 123
    
    def test_normalize_path_current_directory(self):
        """현재 디렉토리 경로"""
        current_path = "."
        expected = "."
        result = normalize_path(current_path)
        assert result == expected
    
    def test_normalize_path_parent_directory(self):
        """상위 디렉토리 경로"""
        parent_path = ".."
        expected = ".."
        result = normalize_path(parent_path)
        assert result == expected 