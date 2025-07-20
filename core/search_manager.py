import os
from typing import List, Dict, Any, Optional
from core.adapters.tag_manager_adapter import TagManagerAdapter
from core.path_utils import normalize_path
from models.tag_model import normalize_tag_name
from core.config_manager import config_manager


class SearchManager:
    """
    검색 관리자
    
    파일 및 태그 기반 검색을 처리하고, 새로운 태그 아키텍처를 활용합니다.
    """
    
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
        try:
            print(f"[DEBUG] SearchManager.search_files 호출: {search_conditions}")
            
            # 복합 검색 조건 처리 (정확한 매칭과 부분일치 모두 있는 경우)
            if ('exact' in search_conditions and search_conditions['exact'] and 
                'partial' in search_conditions and search_conditions['partial']):
                return self._search_files_with_both_conditions(
                    search_conditions['exact'], 
                    search_conditions['partial']
                )
            
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
            
        except Exception as e:
            print(f"[ERROR] SearchManager.search_files 실패: {e}")
            return []

    def _search_files_with_partial_conditions(self, partial_conditions: Dict[str, Any]) -> List[str]:
        """
        부분 문자열 매칭 조건으로 파일을 검색합니다.
        """
        try:
            print(f"[DEBUG] 부분일치 검색 조건: {partial_conditions}")
            
            # 태그 부분일치 검색
            if 'tags' in partial_conditions and partial_conditions['tags'].get('partial'):
                partial_tags = partial_conditions['tags']['partial']
                print(f"[DEBUG] 태그 부분일치 검색: {partial_tags}")
                
                # 태그 이름 정규화
                normalized_partial_tags = [normalize_tag_name(tag) for tag in partial_tags]
                
                # 새로운 아키텍처를 활용한 효율적인 태그 부분일치 검색
                search_results = self._search_files_by_partial_tags(normalized_partial_tags)
                
                # 추가 필터링 적용
                if 'filename' in partial_conditions or 'extensions' in partial_conditions:
                    search_results = self._apply_filename_filters(
                        search_results, 
                        partial_conditions.get('filename', {}),
                        partial_conditions.get('extensions', {})
                    )
                
                print(f"[DEBUG] 부분일치 검색 결과: {len(search_results)}개 파일")
                return search_results
            
            return []
            
        except Exception as e:
            print(f"[ERROR] SearchManager._search_files_with_partial_conditions 실패: {e}")
            return []

    def _search_files_by_partial_tags(self, partial_tags: List[str]) -> List[str]:
        """
        태그 부분일치로 파일을 검색합니다.
        
        Args:
            partial_tags: 부분일치할 태그 목록
            
        Returns:
            List[str]: 검색된 파일 경로 목록
        """
        try:
            if not partial_tags:
                return []
            
            # 모든 태그를 가져와서 부분일치 필터링
            all_tags = self.tag_manager.get_all_tags()
            print(f"[DEBUG] DB의 모든 태그: {all_tags}")
            
            # 부분일치하는 태그들을 찾음
            matching_tags = []
            for tag in all_tags:
                normalized_tag = normalize_tag_name(tag)
                for partial_tag in partial_tags:
                    if partial_tag and (partial_tag in normalized_tag or normalized_tag in partial_tag):
                        matching_tags.append(tag)
                        break
            
            print(f"[DEBUG] 부분일치하는 태그들: {matching_tags}")
            
            if not matching_tags:
                return []
            
            # 부분일치하는 태그를 가진 파일들을 가져옴
            all_tagged_files = []
            for tag in matching_tags:
                files_with_tag = self.tag_manager.get_files_by_tags([tag])
                all_tagged_files.extend(files_with_tag)
            
            # 중복 제거
            unique_files = list(set(all_tagged_files))
            print(f"[DEBUG] 부분일치 태그를 가진 파일들: {len(unique_files)}개")
            
            return unique_files
            
        except Exception as e:
            print(f"[ERROR] SearchManager._search_files_by_partial_tags 실패: {e}")
            return []

    def _apply_filename_filters(self, file_paths: List[str], 
                               filename_conditions: Dict[str, Any], 
                               extension_conditions: Dict[str, Any]) -> List[str]:
        """
        파일명 및 확장자 필터를 적용합니다.
        
        Args:
            file_paths: 필터링할 파일 경로 목록
            filename_conditions: 파일명 조건
            extension_conditions: 확장자 조건
            
        Returns:
            List[str]: 필터링된 파일 경로 목록
        """
        try:
            filtered_files = []
            
            for file_path in file_paths:
                if not os.path.exists(file_path):
                    continue
                
                file_name = os.path.basename(file_path)
                file_ext = os.path.splitext(file_name)[1].lower().lstrip('.')
                
                # 파일명 부분일치 검색
                if 'partial' in filename_conditions:
                    partial_filename = filename_conditions['partial'].strip().lower()
                    if partial_filename and partial_filename not in file_name.lower():
                        continue
                
                # 확장자 부분일치 검색
                if 'partial' in extension_conditions:
                    partial_extensions = extension_conditions['partial']
                    if partial_extensions:
                        # 확장자 중 하나라도 포함되어야 함
                        if not any(ext.lower() in file_ext for ext in partial_extensions):
                            continue
                
                filtered_files.append(file_path)
            
            return filtered_files
            
        except Exception as e:
            print(f"[ERROR] SearchManager._apply_filename_filters 실패: {e}")
            return file_paths

    def _search_files_with_exact_conditions(self, exact_conditions: Dict[str, Any]) -> List[str]:
        """
        정확한 문자열 매칭 조건으로 파일을 검색합니다.
        """
        try:
            print(f"[DEBUG] 정확한 문자열 매칭 검색 조건: {exact_conditions}")
            
            # 태그 정확한 매칭 검색
            if 'tags' in exact_conditions and exact_conditions['tags'].get('exact'):
                exact_tags = exact_conditions['tags']['exact']
                print(f"[DEBUG] 태그 정확한 매칭 검색: {exact_tags}")
                
                # 태그 이름 정규화
                normalized_exact_tags = [normalize_tag_name(tag) for tag in exact_tags]
                
                # TagManager를 통해 정확한 태그 매칭으로 파일 검색
                files = self.tag_manager.get_files_by_tags(normalized_exact_tags)
                print(f"[DEBUG] 정확한 태그 매칭 검색 결과: {len(files)}개 파일")
                return files
            
            return []
            
        except Exception as e:
            print(f"[ERROR] SearchManager._search_files_with_exact_conditions 실패: {e}")
            return []

    def _search_files_with_both_conditions(self, exact_conditions: Dict[str, Any], 
                                          partial_conditions: Dict[str, Any]) -> List[str]:
        """
        정확한 문자열 매칭과 부분 문자열 매칭 조건을 모두 사용하여 파일을 검색합니다.
        """
        try:
            print(f"[DEBUG] 복합 검색 조건 - 정확한 매칭: {exact_conditions}, 부분일치: {partial_conditions}")
            
            # 정확한 매칭 결과
            exact_results = self._search_files_with_exact_conditions(exact_conditions)
            
            # 부분일치 결과
            partial_results = self._search_files_with_partial_conditions(partial_conditions)
            
            # 교집합 계산
            combined_results = list(set(exact_results) & set(partial_results))
            print(f"[DEBUG] 복합 검색 결과: {len(combined_results)}개 파일")
            
            return combined_results
            
        except Exception as e:
            print(f"[ERROR] SearchManager._search_files_with_both_conditions 실패: {e}")
            return []

    def _search_files_by_filename(self, search_text: str, extensions: List[str]) -> List[str]:
        """
        파일명과 확장자로 파일을 검색합니다.
        """
        try:
            workspace_path = config_manager.get_workspace_path()
            
            if not workspace_path or not os.path.exists(workspace_path):
                print(f"[WARNING] 워크스페이스 경로가 유효하지 않음: {workspace_path}")
                return []
            
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
                    
                    # 경로 정규화
                    normalized_path = normalize_path(file_path)
                    search_results.append(normalized_path)
            
            print(f"[DEBUG] 파일명 검색 결과: {len(search_results)}개 파일")
            return search_results
            
        except Exception as e:
            print(f"[ERROR] SearchManager._search_files_by_filename 실패: {e}")
            return [] 