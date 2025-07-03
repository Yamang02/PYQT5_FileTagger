import os
from datetime import datetime

class TaggedFile:
    """
    파일 하나의 정보(경로, 크기, 날짜 등)와 관련 동작을 캡슐화하는 데이터 모델 클래스입니다.
    UI 코드는 이 클래스를 사용하여 파일 정보를 얻고, 표시 형식을 요청합니다.
    """
    def __init__(self, file_path):
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File does not exist: {file_path}")

        self.file_path = file_path
        self.file_name = os.path.basename(file_path)
        
        # 파일 상태 정보 가져오기
        stat = os.stat(file_path)
        self.size_in_bytes = stat.st_size
        self.last_modified = datetime.fromtimestamp(stat.st_mtime)
        
        # TODO: 이 태그 정보는 나중에 TagManager를 통해 DB에서 가져와야 합니다.
        self.tags = []

    def get_display_info_html(self):
        """
        오른쪽 상세 정보 패널에 표시될 HTML 형식의 문자열을 반환합니다.
        """
        size_kb = self.size_in_bytes / 1024
        mod_time = self.last_modified.strftime("%Y-%m-%d %H:%M:%S")

        html = f"""
        <b>Name:</b> {self.file_name}<br>
        <b>Path:</b> {self.file_path}<br>
        <b>Size:</b> {size_kb:.2f} KB<br>
        <b>Modified:</b> {mod_time}
        """
        return html

    def get_tags_as_string(self):
        """
        태그 리스트를 쉼표로 구분된 하나의 문자열로 변환하여 반환합니다.
        """
        return ", ".join(self.tags)

    def set_tags_from_string(self, tag_string):
        """
        쉼표로 구분된 문자열을 파싱하여 태그 리스트를 설정합니다.
        """
        self.tags = [tag.strip() for tag in tag_string.split(",") if tag.strip()]
