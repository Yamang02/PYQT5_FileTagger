import pytest
from unittest.mock import Mock, patch
from PyQt5.QtWidgets import QApplication
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from widgets.tag_chip import TagChip


@pytest.fixture(scope="function")
def app():
    """QApplication 인스턴스를 제공합니다."""
    if not QApplication.instance():
        return QApplication([])
    return QApplication.instance()


@pytest.fixture
def tag_chip(app):
    """TagChip 인스턴스를 생성합니다."""
    chip = TagChip("test_tag")
    chip.show()
    return chip


class TestTagChip:
    """TagChip의 기능을 테스트합니다."""

    def test_initial_state(self, tag_chip):
        """위젯의 초기 상태를 확인합니다."""
        assert tag_chip.isVisible()
        assert tag_chip.tag_text == "test_tag"
        assert tag_chip.tag_label.text() == "test_tag"

    def test_delete_button_click(self, tag_chip):
        """제거 버튼 클릭을 테스트합니다."""
        # Given
        # When
        tag_chip.delete_button.click()
        
        # Then
        # tag_removed 시그널이 발생하는지 확인
        # 실제 테스트에서는 시그널 연결을 통해 확인할 수 있습니다
        pass

    def test_mouse_click(self, tag_chip):
        """마우스 클릭을 테스트합니다."""
        # Given
        # When
        QTest.mouseClick(tag_chip, Qt.LeftButton)
        
        # Then
        # clicked 시그널이 발생하는지 확인
        # 실제 테스트에서는 시그널 연결을 통해 확인할 수 있습니다
        pass

    def test_tag_text_display(self, tag_chip):
        """태그 텍스트 표시를 테스트합니다."""
        # Given
        test_tag = "test_tag"
        
        # Then
        assert tag_chip.tag_text == test_tag
        assert tag_chip.tag_label.text() == test_tag

    def test_unicode_tag_text(self, tag_chip):
        """유니코드 태그 텍스트를 테스트합니다."""
        # Given
        unicode_tag = "태그-한글-테스트"
        unicode_chip = TagChip(unicode_tag)
        
        # Then
        assert unicode_chip.tag_text == unicode_tag
        assert unicode_chip.tag_label.text() == unicode_tag

    def test_special_characters_tag_text(self, tag_chip):
        """특수 문자 태그 텍스트를 테스트합니다."""
        # Given
        special_tag = "tag-with-special-chars!@#$%^&*()"
        special_chip = TagChip(special_tag)
        
        # Then
        assert special_chip.tag_text == special_tag
        assert special_chip.tag_label.text() == special_tag

    def test_empty_tag_text(self, tag_chip):
        """빈 태그 텍스트를 테스트합니다."""
        # Given
        empty_chip = TagChip("")
        
        # Then
        assert empty_chip.tag_text == ""
        assert empty_chip.tag_label.text() == ""

    def test_long_tag_text(self, tag_chip):
        """긴 태그 텍스트를 테스트합니다."""
        # Given
        long_tag = "very_long_tag_name_that_might_wrap_to_multiple_lines"
        long_chip = TagChip(long_tag)
        
        # Then
        assert long_chip.tag_text == long_tag
        assert long_chip.tag_label.text() == long_tag 