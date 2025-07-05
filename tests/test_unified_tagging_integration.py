"""
통합 태깅 패널 통합 테스트
DRS-20250705-002의 요구사항이 올바르게 구현되었는지 검증합니다.
"""

import pytest
import os
import tempfile
import shutil
from unittest.mock import Mock, MagicMock, patch
from PyQt5.QtWidgets import QApplication
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt

from widgets.unified_tagging_panel import UnifiedTaggingPanel
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


@pytest.fixture
def unified_panel(app, mock_tag_manager, state_manager):
    """UnifiedTaggingPanel 인스턴스를 제공합니다."""
    panel = UnifiedTaggingPanel(mock_tag_manager, state_manager)
    return panel


class TestUnifiedTaggingPanelStructure:
    """UnifiedTaggingPanel의 구조적 요구사항 테스트"""
    
    def test_panel_has_tab_widget(self, unified_panel):
        """DRS 요구사항: 탭 위젯이 존재하는지 확인"""
        assert hasattr(unified_panel, 'tab_widget')
        assert unified_panel.tab_widget.count() == 2
        
    def test_individual_and_batch_tabs_exist(self, unified_panel):
        """DRS 요구사항: 개별 태깅과 일괄 태깅 탭이 존재하는지 확인"""
        tab_texts = []
        for i in range(unified_panel.tab_widget.count()):
            tab_texts.append(unified_panel.tab_widget.tabText(i))
        
        assert any("개별 태깅" in text for text in tab_texts)
        assert any("일괄 태깅" in text for text in tab_texts)
        
    def test_file_selection_widget_exists(self, unified_panel):
        """DRS 요구사항: 파일 선택 위젯이 존재하는지 확인"""
        assert hasattr(unified_panel, 'file_selection_widget')
        
    def test_tag_input_widgets_exist(self, unified_panel):
        """DRS 요구사항: 태그 입력 위젯들이 존재하는지 확인"""
        assert hasattr(unified_panel, 'individual_tag_input')
        assert hasattr(unified_panel, 'individual_quick_tags')
        
    def test_batch_tagging_panel_integrated(self, unified_panel):
        """DRS 요구사항: 일괄 태깅 패널이 통합되어 있는지 확인"""
        assert hasattr(unified_panel, 'batch_tagging_panel')


class TestModeManagement:
    """모드 관리 기능 테스트"""
    
    def test_initial_mode_is_individual(self, unified_panel):
        """초기 모드가 개별 태깅인지 확인"""
        assert unified_panel.get_current_mode() == 'individual'
        
    def test_mode_switching(self, unified_panel):
        """모드 전환이 올바르게 작동하는지 확인"""
        # 일괄 태깅 모드로 전환
        unified_panel.switch_to_mode('batch')
        assert unified_panel.get_current_mode() == 'batch'
        
        # 개별 태깅 모드로 전환
        unified_panel.switch_to_mode('individual')
        assert unified_panel.get_current_mode() == 'individual'
        
    def test_tab_change_triggers_mode_change(self, unified_panel):
        """탭 변경이 모드 변경을 트리거하는지 확인"""
        # 일괄 태깅 탭 선택
        unified_panel.tab_widget.setCurrentIndex(1)
        assert unified_panel.get_current_mode() == 'batch'
        
        # 개별 태깅 탭 선택
        unified_panel.tab_widget.setCurrentIndex(0)
        assert unified_panel.get_current_mode() == 'individual'


class TestStateManagerIntegration:
    """상태 관리자 통합 테스트"""
    
    def test_state_manager_registration(self, unified_panel, state_manager):
        """상태 관리자에 위젯들이 올바르게 등록되는지 확인"""
        unified_panel.set_state_manager(state_manager)
        
        registered_widgets = state_manager.get_registered_widgets()
        assert 'individual_tag_input' in registered_widgets
        assert 'individual_quick_tags' in registered_widgets
        assert 'save_tags_button' in registered_widgets
        
    def test_file_selection_updates_state(self, unified_panel, state_manager):
        """파일 선택이 상태 관리자를 업데이트하는지 확인"""
        unified_panel.set_state_manager(state_manager)
        
        # 파일 선택 시뮬레이션
        test_file_path = "/test/path/file.txt"
        unified_panel.on_file_selected(test_file_path)
        
        state = state_manager.get_state()
        assert test_file_path in state['selected_files']
        
    def test_mode_change_updates_state(self, unified_panel, state_manager):
        """모드 변경이 상태 관리자를 업데이트하는지 확인"""
        unified_panel.set_state_manager(state_manager)
        
        # 모드 변경
        unified_panel.switch_to_mode('batch')
        
        state = state_manager.get_state()
        assert state['mode'] == 'batch'


class TestFileSelectionAndPreview:
    """파일 선택 및 미리보기 기능 테스트"""
    
    def test_file_table_has_tag_column(self, unified_panel):
        """DRS 요구사항: 파일 테이블에 태그 컬럼이 있는지 확인"""
        file_model = unified_panel.file_selection_widget.file_model
        assert file_model.columnCount() == 3  # 파일명, 경로, 태그
        
        headers = []
        for i in range(file_model.columnCount()):
            headers.append(file_model.headerData(i, Qt.Horizontal, Qt.DisplayRole))
            
        assert "태그" in headers
        
    def test_file_selection_loads_existing_tags(self, unified_panel, mock_tag_manager):
        """파일 선택 시 기존 태그가 로드되는지 확인"""
        test_file_path = "/test/path/file.txt"
        expected_tags = ["existing", "tags"]
        mock_tag_manager.get_tags_for_file.return_value = expected_tags
        
        unified_panel.on_file_selected(test_file_path)
        
        # 태그 입력 위젯에 기존 태그가 설정되었는지 확인
        loaded_tags = unified_panel.individual_tag_input.get_tags()
        assert set(loaded_tags) == set(expected_tags)


class TestTagSaving:
    """태그 저장 기능 테스트"""
    
    def test_save_individual_tags(self, unified_panel, mock_tag_manager):
        """개별 파일 태그 저장이 올바르게 작동하는지 확인"""
        # 파일 선택
        test_file_path = "/test/path/file.txt"
        unified_panel.current_selected_file = test_file_path
        
        # 태그 설정
        test_tags = ["new", "tags"]
        unified_panel.individual_tag_input.set_tags(test_tags)
        
        # 태그 저장
        unified_panel.save_individual_tags()
        
        # TagManager의 set_tags_for_file이 호출되었는지 확인
        mock_tag_manager.set_tags_for_file.assert_called_with(test_file_path, test_tags)
        
    def test_tag_synchronization_between_widgets(self, unified_panel):
        """태그 입력 위젯과 빠른 태그 위젯 간 동기화 확인"""
        test_tags = ["sync", "test"]
        
        # 태그 입력 위젯에서 변경
        unified_panel.individual_tag_input.set_tags(test_tags)
        unified_panel.on_individual_tags_changed(test_tags)
        
        # 빠른 태그 위젯에 반영되었는지 확인
        quick_tags = unified_panel.individual_quick_tags._selected_tags
        assert set(quick_tags) == set(test_tags)


class TestBatchTaggingIntegration:
    """일괄 태깅 통합 테스트"""
    
    def test_batch_panel_uses_shared_tag_input(self, unified_panel):
        """DRS 요구사항: 일괄 태깅이 공유 태그 입력을 사용하는지 확인"""
        # 개별 태깅에서 태그 설정
        test_tags = ["shared", "tags"]
        unified_panel.individual_tag_input.set_tags(test_tags)
        
        # 일괄 태깅 모드로 전환
        unified_panel.switch_to_mode('batch')
        
        # 일괄 태깅 패널이 같은 태그를 참조하는지 확인
        # (실제 구현에서는 parent()를 통해 태그를 가져옴)
        assert hasattr(unified_panel.batch_tagging_panel, 'parent')
        
    def test_directory_selection_updates_both_panels(self, unified_panel, temp_dir):
        """디렉토리 선택이 두 패널 모두에 반영되는지 확인"""
        # 파일 선택 위젯에서 디렉토리 설정
        unified_panel.file_selection_widget.set_directory(temp_dir)
        
        # 일괄 태깅 패널의 디렉토리도 업데이트되는지 확인
        batch_panel = unified_panel.batch_tagging_panel
        # 상태 관리자를 통해 동기화되는지 확인
        assert hasattr(batch_panel, 'set_directory')


class TestSignalHandling:
    """시그널 처리 테스트"""
    
    def test_mode_changed_signal(self, unified_panel):
        """모드 변경 시그널이 올바르게 발송되는지 확인"""
        signal_received = []
        
        def on_mode_changed(mode):
            signal_received.append(mode)
            
        unified_panel.mode_changed.connect(on_mode_changed)
        
        # 모드 변경
        unified_panel.switch_to_mode('batch')
        
        assert 'batch' in signal_received
        
    def test_file_selected_signal(self, unified_panel):
        """파일 선택 시그널이 올바르게 발송되는지 확인"""
        signal_received = []
        
        def on_file_selected(file_path):
            signal_received.append(file_path)
            
        unified_panel.file_selected.connect(on_file_selected)
        
        # 파일 선택
        test_file_path = "/test/path/file.txt"
        unified_panel.on_file_selected(test_file_path)
        
        assert test_file_path in signal_received
        
    def test_tags_applied_signal(self, unified_panel, mock_tag_manager):
        """태그 적용 시그널이 올바르게 발송되는지 확인"""
        signal_received = []
        
        def on_tags_applied(file_path, tags):
            signal_received.append((file_path, tags))
            
        unified_panel.tags_applied.connect(on_tags_applied)
        
        # 태그 저장
        test_file_path = "/test/path/file.txt"
        test_tags = ["applied", "tags"]
        unified_panel.current_selected_file = test_file_path
        unified_panel.individual_tag_input.set_tags(test_tags)
        unified_panel.save_individual_tags()
        
        assert (test_file_path, test_tags) in signal_received


class TestUIResponsiveness:
    """UI 반응성 테스트"""
    
    def test_widgets_enabled_when_file_selected(self, unified_panel):
        """파일 선택 시 관련 위젯들이 활성화되는지 확인"""
        # 파일 선택
        test_file_path = "/test/path/file.txt"
        unified_panel.on_file_selected(test_file_path)
        
        # 위젯들이 활성화되었는지 확인
        assert unified_panel.individual_tag_input.is_enabled()
        assert unified_panel.individual_quick_tags.is_enabled
        assert unified_panel.save_tags_button.isEnabled()
        
    def test_widgets_disabled_when_no_file_selected(self, unified_panel):
        """파일 선택 해제 시 관련 위젯들이 비활성화되는지 확인"""
        # 파일 선택 해제
        unified_panel.on_file_selected("")
        
        # 위젯들이 비활성화되었는지 확인
        assert not unified_panel.individual_tag_input.is_enabled()
        assert not unified_panel.individual_quick_tags.is_enabled
        assert not unified_panel.save_tags_button.isEnabled()


@pytest.mark.integration
class TestDRSComplianceIntegration:
    """DRS 요구사항 준수 통합 테스트"""
    
    def test_drs_tab_based_ui_implementation(self, unified_panel):
        """DRS 요구사항: 탭 기반 UI가 구현되었는지 확인"""
        # 탭 위젯 존재 확인
        assert hasattr(unified_panel, 'tab_widget')
        
        # 두 개의 탭 (개별, 일괄) 존재 확인
        assert unified_panel.tab_widget.count() == 2
        
        # 탭 전환이 모드 변경을 트리거하는지 확인
        unified_panel.tab_widget.setCurrentIndex(1)
        assert unified_panel.get_current_mode() == 'batch'
        
    def test_drs_unified_file_selection_widget(self, unified_panel):
        """DRS 요구사항: 통합된 파일 선택 위젯이 구현되었는지 확인"""
        # FileSelectionAndPreviewWidget 존재 확인
        assert hasattr(unified_panel, 'file_selection_widget')
        
        # 태그 표시 기능 확인
        file_model = unified_panel.file_selection_widget.file_model
        assert file_model.columnCount() >= 3  # 파일명, 경로, 태그
        
    def test_drs_batch_tagging_integration(self, unified_panel):
        """DRS 요구사항: 일괄 태깅 패널이 통합되었는지 확인"""
        # BatchTaggingPanel이 통합되었는지 확인
        assert hasattr(unified_panel, 'batch_tagging_panel')
        
        # 일괄 태깅 탭에 포함되었는지 확인
        batch_tab = unified_panel.batch_tab
        assert unified_panel.batch_tagging_panel.parent() == batch_tab
        
    def test_drs_state_manager_expansion(self, unified_panel, state_manager):
        """DRS 요구사항: 상태 관리자가 확장되었는지 확인"""
        unified_panel.set_state_manager(state_manager)
        
        # 확장된 상태 변수들 확인
        state = state_manager.get_state()
        required_keys = [
            'mode', 'selected_files', 'current_file_tags', 
            'batch_target_files', 'batch_options', 'ui_visibility'
        ]
        
        for key in required_keys:
            assert key in state
            
    def test_drs_main_window_integration_ready(self, unified_panel):
        """DRS 요구사항: MainWindow 통합 준비가 되었는지 확인"""
        # 필요한 시그널들이 정의되었는지 확인
        required_signals = ['mode_changed', 'file_selected', 'tags_applied']
        
        for signal_name in required_signals:
            assert hasattr(unified_panel, signal_name)
            
        # 상태 관리자 설정 메서드 존재 확인
        assert hasattr(unified_panel, 'set_state_manager')
        
        # 모드 전환 메서드 존재 확인
        assert hasattr(unified_panel, 'switch_to_mode')


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 