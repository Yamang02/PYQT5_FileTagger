import os

def normalize_path(path: str) -> str:
    """
    주어진 파일 경로를 표준화하고, Windows 환경에 맞게 역슬래시로 통일합니다.
    """
    if not isinstance(path, str):
        return path
    # os.path.normpath를 사용하여 운영체제에 맞는 경로 구분자로 정규화
    normalized = os.path.normpath(path)
    # Windows 환경이므로 모든 슬래시를 역슬래시로 변환
    if os.sep == '\\': # 현재 OS의 경로 구분자가 역슬래시인 경우 (Windows)
        normalized = normalized.replace('/', '\\')
    return normalized

