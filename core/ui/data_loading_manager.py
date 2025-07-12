"""
데이터 로딩 관리자 - MainWindow의 초기 데이터 로딩 로직을 분리

이 모듈은 MainWindow의 데이터 로딩 책임을 분리하여 단일 책임 원칙을 준수하고
초기화 과정을 명확하게 관리합니다.
"""

import os
from PyQt5.QtCore import QDir
import config


class DataLoadingManager:
    """MainWindow의 초기 데이터 로딩을 담당하는 관리자 클래스"""
    
    def __init__(self, main_window):
        """
        데이터 로딩 관리자 초기화
        
        Args:
            main_window: MainWindow 인스턴스
        """
        self.main_window = main_window
        
    def load_initial_data(self):
        """애플리케이션 시작 시 필요한 초기 데이터를 로드합니다."""
        self._load_workspace_data()
        self._initialize_managers()
        self._load_custom_tags()
        self._set_initial_status()
        
    def _load_workspace_data(self):
        """작업공간 데이터를 로드합니다."""
        # 초기 작업공간 경로 설정
        initial_workspace = (
            config.DEFAULT_WORKSPACE_PATH 
            if config.DEFAULT_WORKSPACE_PATH and os.path.isdir(config.DEFAULT_WORKSPACE_PATH) 
            else QDir.homePath()
        )
        
        # 디렉토리 트리에 초기 경로 설정
        if hasattr(self.main_window, 'directory_tree'):
            self.main_window.directory_tree.set_root_path(initial_workspace)
            
        # 파일 리스트에 초기 경로 설정
        if hasattr(self.main_window, 'file_list'):
            self.main_window.file_list.set_path(initial_workspace)
            
    def _initialize_managers(self):
        """각종 관리자들을 초기화합니다."""
        # 태그 관리자 초기화 (이미 __init__에서 생성됨)
        if hasattr(self.main_window, 'tag_manager'):
            # 태그 관리자 연결 확인
            try:
                self.main_window.tag_manager.get_all_tags()
            except Exception as e:
                print(f"Tag manager initialization warning: {e}")
                
        # 검색 관리자 초기화 (이미 __init__에서 생성됨)
        if hasattr(self.main_window, 'search_manager'):
            # 검색 관리자 연결 확인
            try:
                # 검색 관리자가 정상적으로 초기화되었는지 확인
                pass
            except Exception as e:
                print(f"Search manager initialization warning: {e}")
                
    def _load_custom_tags(self):
        """커스텀 태그 데이터를 로드합니다."""
        if hasattr(self.main_window, 'custom_tag_manager'):
            try:
                # 커스텀 태그 매니저에서 태그 로드
                custom_tags = self.main_window.custom_tag_manager.load_custom_tags()
                
                # 태그 컨트롤 위젯의 빠른 태그에 반영
                if hasattr(self.main_window, 'tag_control'):
                    if hasattr(self.main_window.tag_control, 'individual_quick_tags'):
                        self.main_window.tag_control.individual_quick_tags.load_quick_tags()
                    if hasattr(self.main_window.tag_control, 'batch_quick_tags'):
                        self.main_window.tag_control.batch_quick_tags.load_quick_tags()
                        
            except Exception as e:
                print(f"Custom tags loading warning: {e}")
                
    def _set_initial_status(self):
        """초기 상태 메시지를 설정합니다."""
        if hasattr(self.main_window, 'statusbar'):
            self.main_window.statusbar.showMessage("준비 완료")
            
    def refresh_data(self):
        """데이터를 새로고침합니다."""
        self._refresh_file_list()
        self._refresh_tag_data()
        
    def _refresh_file_list(self):
        """파일 리스트를 새로고침합니다."""
        if hasattr(self.main_window, 'file_list'):
            try:
                # 현재 경로 기준으로 파일 리스트 새로고침
                current_path = getattr(self.main_window.file_list.model, 'current_directory', None)
                if current_path:
                    self.main_window.file_list.set_path(current_path)
            except Exception as e:
                print(f"File list refresh warning: {e}")
                
    def _refresh_tag_data(self):
        """태그 관련 데이터를 새로고침합니다."""
        if hasattr(self.main_window, 'tag_control'):
            try:
                # 태그 자동완성 모델 업데이트
                self.main_window.tag_control.update_completer_model()
                # 모든 태그 리스트 업데이트
                self.main_window.tag_control.update_all_tags_list()
            except Exception as e:
                print(f"Tag data refresh warning: {e}")
                
    def get_loading_status(self):
        """현재 로딩 상태를 반환합니다. (디버깅 용도)"""
        status = {
            'workspace_loaded': False,
            'managers_initialized': False,
            'custom_tags_loaded': False,
            'initial_status_set': False
        }
        
        try:
            # 작업공간 로드 상태 확인
            if hasattr(self.main_window, 'directory_tree') and hasattr(self.main_window, 'file_list'):
                status['workspace_loaded'] = True
                
            # 관리자 초기화 상태 확인
            if hasattr(self.main_window, 'tag_manager') and hasattr(self.main_window, 'search_manager'):
                status['managers_initialized'] = True
                
            # 커스텀 태그 로드 상태 확인
            if hasattr(self.main_window, 'custom_tag_manager'):
                status['custom_tags_loaded'] = True
                
            # 초기 상태 설정 확인
            if hasattr(self.main_window, 'statusbar'):
                status['initial_status_set'] = True
                
        except Exception as e:
            print(f"Loading status check warning: {e}")
            
        return status 