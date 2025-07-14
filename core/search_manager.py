from core.adapters.tag_manager_adapter import TagManagerAdapter
import os

class SearchManager:
    def __init__(self, tag_manager: TagManagerAdapter):
        self.tag_manager = tag_manager

    def search_files(self, conditions: dict) -> list:
        """
        통합 검색: 파일명, 확장자, 태그 등 다양한 조건을 받아 파일 경로 리스트를 반환
        (복합/고급 검색은 추후 확장)
        """
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
                import config
                workspace_path = config.DEFAULT_WORKSPACE_PATH if hasattr(config, 'DEFAULT_WORKSPACE_PATH') and os.path.isdir(config.DEFAULT_WORKSPACE_PATH) else os.path.expanduser('~')
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