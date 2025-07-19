import os
from typing import List, Dict, Any
from core.adapters.tag_manager_adapter import TagManagerAdapter

class SearchManager:
    def __init__(self, tag_manager: TagManagerAdapter):
        self.tag_manager = tag_manager

    def search_files(self, search_conditions: Dict[str, Any]) -> List[str]:
        """
        주어진 검색 조건에 따라 파일을 검색합니다.
        
        Args:
            search_conditions: 검색 조건 딕셔너리
                - 'exact': 정확한 문자열 매칭 조건
                - 'partial': 부분 문자열 매칭 조건
                - 'tags': {'query': '태그명'} 형식 (기존 형식)
                - 'filename': {'name': '파일명', 'extensions': []} 형식 (기존 형식)
        
        Returns:
            검색된 파일 경로 리스트
        """
        print(f"[DEBUG] SearchManager.search_files 호출: {search_conditions}")
        
        # 부분일치 검색 조건이 있으면 우선 처리
        if 'partial' in search_conditions and search_conditions['partial']:
            return self._search_files_with_partial_conditions(search_conditions['partial'])
        
        # 정확한 문자열 매칭 검색
        if 'exact' in search_conditions and search_conditions['exact']:
            return self._search_files_with_exact_conditions(search_conditions['exact'])
        
        # 기존 형식 처리 (하위 호환성)
        if 'tags' in search_conditions and search_conditions['tags'].get('query'):
            # 태그 정확한 매칭 검색
            tag_query = search_conditions['tags']['query'].strip()
            if tag_query:
                print(f"[DEBUG] 기존 형식 태그 검색: {tag_query}")
                files = self.tag_manager.get_files_by_tags([tag_query])
                print(f"[DEBUG] 기존 형식 태그 검색 결과: {len(files)}개 파일")
                return files
        
        # 파일명 검색 (기존 형식)
        if 'filename' in search_conditions:
            filename_cond = search_conditions['filename']
            search_text = filename_cond.get('name', '').strip()
            extensions = filename_cond.get('extensions', [])
            
            if search_text or extensions:
                print(f"[DEBUG] 기존 형식 파일명 검색: {search_text}, 확장자: {extensions}")
                return self._search_files_by_filename(search_text, extensions)
        
        return []

    def _search_files_with_partial_conditions(self, partial_conditions: Dict[str, Any]) -> List[str]:
        """
        부분 문자열 매칭 조건으로 파일을 검색합니다.
        """
        print(f"[DEBUG] 부분일치 검색 조건: {partial_conditions}")
        
        # 태그 부분일치 검색
        if 'tags' in partial_conditions and partial_conditions['tags'].get('partial'):
            partial_tags = partial_conditions['tags']['partial']
            print(f"[DEBUG] 태그 부분일치 검색: {partial_tags}")
            
            # DB에서 모든 태그가 있는 파일들을 가져옴
            # 완전일치가 아닌 모든 태그가 있는 파일들을 가져와야 하므로
            # 모든 태그를 가져와서 부분일치 필터링을 적용
            all_tags = self.tag_manager.get_all_tags()
            print(f"[DEBUG] DB의 모든 태그: {all_tags}")
            
            all_tagged_files = []
            for tag in all_tags:
                # 각 태그에 대해 파일들을 가져옴
                files_with_tag = self.tag_manager.get_files_by_tags([tag])
                all_tagged_files.extend(files_with_tag)
            
            # 중복 제거
            all_tagged_files = list(set(all_tagged_files))
            print(f"[DEBUG] DB에서 가져온 모든 태그가 있는 파일들: {len(all_tagged_files)}개")
            print(f"[DEBUG] 파일 목록: {all_tagged_files}")
            
            # 각 파일에 대해 부분일치 검색 적용
            search_results = []
            for file_path in all_tagged_files:
                if not os.path.exists(file_path):
                    continue
                    
                file_name = os.path.basename(file_path)
                file_ext = os.path.splitext(file_name)[1].lower().lstrip('.')
                
                # 파일명 부분일치 검색
                if 'filename' in partial_conditions:
                    partial_filename = partial_conditions['filename'].get('partial', '').strip().lower()
                    if partial_filename and partial_filename not in file_name.lower():
                        continue
                
                # 확장자 부분일치 검색
                if 'extensions' in partial_conditions:
                    partial_extensions = partial_conditions['extensions'].get('partial', [])
                    if partial_extensions:
                        # 확장자 중 하나라도 포함되어야 함
                        if not any(ext.lower() in file_ext for ext in partial_extensions):
                            continue
                
                # 태그 부분일치 검색 - TagManager를 통해 조회
                # TagManager.get_files_by_tags()에서 반환되는 경로는 이미 DB 형식으로 정규화됨
                file_tags = self.tag_manager.get_tags_for_file(file_path)
                file_tags_lower = [tag.lower() for tag in file_tags]
                
                print(f"[DEBUG] 파일: {file_name}, DB 경로: {file_path}, 태그: {file_tags}")
                
                # 입력된 태그 중 하나라도 파일 태그에 부분일치해야 함
                tag_found = False
                for partial_tag in partial_tags:
                    partial_tag_lower = partial_tag.lower()
                    for file_tag in file_tags_lower:
                        # 부분일치: 검색어가 파일 태그에 포함되거나, 파일 태그가 검색어에 포함되면 매치
                        if partial_tag_lower in file_tag or file_tag in partial_tag_lower:
                            tag_found = True
                            print(f"[DEBUG] 태그 매치: '{partial_tag}' in '{file_tag}' for {file_name}")
                            break
                    if tag_found:
                        break
                
                if tag_found:
                    search_results.append(file_path)
            
            print(f"[DEBUG] 부분일치 검색 결과: {len(search_results)}개 파일")
            return search_results
        
        return []

    def _search_files_with_exact_conditions(self, exact_conditions: Dict[str, Any]) -> List[str]:
        """
        정확한 문자열 매칭 조건으로 파일을 검색합니다.
        """
        print(f"[DEBUG] 정확한 문자열 매칭 검색 조건: {exact_conditions}")
        
        # 태그 정확한 매칭 검색
        if 'tags' in exact_conditions and exact_conditions['tags'].get('exact'):
            exact_tags = exact_conditions['tags']['exact']
            print(f"[DEBUG] 태그 정확한 매칭 검색: {exact_tags}")
            
            # TagManager를 통해 정확한 태그 매칭으로 파일 검색
            files = self.tag_manager.get_files_by_tags(exact_tags)
            print(f"[DEBUG] 정확한 태그 매칭 검색 결과: {len(files)}개 파일")
            return files
        
        return []

    def _search_files_with_both_conditions(self, exact_conditions: Dict[str, Any], partial_conditions: Dict[str, Any]) -> List[str]:
        """
        정확한 문자열 매칭과 부분 문자열 매칭 조건을 모두 사용하여 파일을 검색합니다.
        """
        print(f"[DEBUG] 복합 검색 조건 - 정확한 매칭: {exact_conditions}, 부분일치: {partial_conditions}")
        
        # 정확한 매칭 결과
        exact_results = self._search_files_with_exact_conditions(exact_conditions)
        
        # 부분일치 결과
        partial_results = self._search_files_with_partial_conditions(partial_conditions)
        
        # 교집합 계산
        combined_results = list(set(exact_results) & set(partial_results))
        print(f"[DEBUG] 복합 검색 결과: {len(combined_results)}개 파일")
        
        return combined_results 

    def _search_files_by_filename(self, search_text: str, extensions: List[str]) -> List[str]:
        """
        파일명과 확장자로 파일을 검색합니다.
        """
        from core.config_manager import config_manager
        workspace_path = config_manager.get_workspace_path()
        
        search_results = []
        for root, _, files in os.walk(workspace_path):
            for file in files:
                file_path = os.path.join(root, file)
                
                # 파일명 검색 (완전일치)
                if search_text and search_text.lower() not in file.lower():
                    continue
                
                # 확장자 필터
                if extensions:
                    file_ext = os.path.splitext(file)[1].lower()
                    if not any(ext.lower() in file_ext for ext in extensions):
                        continue
                
                search_results.append(file_path)
        
        print(f"[DEBUG] 파일명 검색 결과: {len(search_results)}개 파일")
        return search_results 