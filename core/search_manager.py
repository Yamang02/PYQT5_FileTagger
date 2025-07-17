from core.adapters.tag_manager_adapter import TagManagerAdapter
import os

class SearchManager:
    def __init__(self, tag_manager: TagManagerAdapter):
        self.tag_manager = tag_manager

    def search_files(self, conditions: dict) -> list:
        """
        통합 검색: 파일명, 확장자, 태그 등 다양한 조건을 받아 파일 경로 리스트를 반환
        복합 검색 지원: 파일명 + 태그 AND 조건
        """
        # 복합 검색: 파일명 + 태그
        if 'filename' in conditions and 'tags' in conditions:
            return self._search_files_with_both_conditions(conditions)
        
        # 1. 태그 기반 검색 (단일 태그만 우선)
        if 'tags' in conditions:
            tag_cond = conditions['tags']
            tag_query = tag_cond.get('query', '').strip()
            if tag_query:
                return self.tag_manager.get_files_by_tags([tag_query])

        # 2. 파일명/확장자 기반 검색
        if 'filename' in conditions:
            filename_cond = conditions['filename']
            search_text = filename_cond.get('name', '').strip()
            extensions = filename_cond.get('extensions', [])
            workspace_path = getattr(self.tag_manager, 'workspace_path', None)
            if not workspace_path:
                from core.config_manager import config_manager
                workspace_path = config_manager.get_workspace_path()
            search_results = []
            for root, _, files in os.walk(workspace_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    # 파일명 검색
                    if search_text and search_text.lower() not in file.lower():
                        continue
                    # 확장자 필터
                    if extensions:
                        file_ext = os.path.splitext(file)[1].lower()
                        if not any(ext.lower() in file_ext for ext in extensions):
                            continue
                    search_results.append(file_path)
            return search_results

        # 3. (추후) 복합/고급 검색 조건 처리
        # ...
        return []
    
    def _search_files_with_both_conditions(self, conditions: dict) -> list:
        """
        파일명과 태그 조건을 모두 만족하는 파일들을 검색합니다.
        """
        # 1. 태그 조건으로 파일 검색
        tag_cond = conditions['tags']
        tag_query = tag_cond.get('query', '').strip()
        if not tag_query:
            return []
        
        tag_files = self.tag_manager.get_files_by_tags([tag_query])
        if not tag_files:
            return []
        
        # 2. 파일명 조건으로 필터링
        filename_cond = conditions['filename']
        search_text = filename_cond.get('name', '').strip()
        extensions = filename_cond.get('extensions', [])
        
        filtered_files = []
        for file_path in tag_files:
            if not os.path.exists(file_path):
                continue
                
            file_name = os.path.basename(file_path)
            
            # 파일명 검색 조건 확인
            if search_text and search_text.lower() not in file_name.lower():
                continue
                
            # 확장자 필터 조건 확인
            if extensions:
                file_ext = os.path.splitext(file_name)[1].lower()
                if not any(ext.lower() in file_ext for ext in extensions):
                    continue
                    
            filtered_files.append(file_path)
        
        return filtered_files 