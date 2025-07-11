"""
통합 태깅 패널 통합 테스트
DRS-20250705-002의 요구사항이 올바르게 구현되었는지 검증합니다.
"""

import pytest
import tempfile
import shutil
from unittest.mock import Mock
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt


from core.tag_ui_state_manager import TagUIStateManager
from core.tag_manager import TagManager


@pytest.fixture
def app():
    """QApplication 인스턴스를 제공합니다."""
    if not QApplication.instance():
        return QApplication([])
    return QApplication.instance()


@pytest.fixture
def temp_dir():
    """임시 디렉토리를 생성합니다."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def mock_tag_manager():
    """Mock TagManager를 제공합니다."""
    manager = Mock(spec=TagManager)
    manager.get_tags_for_file.return_value = ["test", "example"]
    manager.set_tags_for_file.return_value = True
    manager.get_all_tags.return_value = ["test", "example", "important", "work"]
    return manager


@pytest.fixture
def state_manager():
    """TagUIStateManager 인스턴스를 제공합니다."""
    return TagUIStateManager()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])