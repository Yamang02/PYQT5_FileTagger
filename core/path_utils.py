import os

def normalize_path(path: str) -> str:
    """
    주어진 파일 경로를 표준화하고, 운영체제에 독립적인 슬래시(/) 기반으로 통일합니다.
    
    Args:
        path (str): 정규화할 파일 경로
        
    Returns:
        str: 정규화된 파일 경로 (슬래시(/) 기반)
        
    Examples:
        >>> normalize_path("C:\\Users\\user\\Documents\\file.txt")
        "C:/Users/user/Documents/file.txt"
        >>> normalize_path("/home/user/documents/file.txt")
        "/home/user/documents/file.txt"
    """
    if not isinstance(path, str):
        return path
    
    # 빈 문자열 처리
    if path == "":
        return ""
    
    # os.path.normpath를 사용하여 경로 정규화 (중복 구분자 제거, 상대 경로 해결 등)
    normalized = os.path.normpath(path)
    
    # 모든 경로 구분자를 슬래시(/)로 통일
    # Windows의 경우 역슬래시(\)를 슬래시(/)로 변환
    normalized = normalized.replace('\\', '/')
    
    # Windows 드라이브 문자 뒤의 슬래시 정규화 (예: C:/ → C:/)
    # 이미 올바른 형태이므로 추가 처리 불필요
    
    return normalized

