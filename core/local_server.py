import http.server
import socketserver
import threading
import os
import urllib.parse
import logging

logger = logging.getLogger(__name__)

class FileHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        logger.debug(f"[FileHandler] Received GET request for path: {self.path}")
        # URL 경로에서 쿼리 파라미터 파싱
        parsed_path = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_path.query)
        
        # 'path' 쿼리 파라미터에서 실제 파일 경로 가져오기
        file_path_param = query_params.get('path')
        logger.debug(f"[FileHandler] Parsed file_path_param: {file_path_param}")

        if file_path_param:
            file_path = file_path_param[0]
            logger.debug(f"[FileHandler] Decoded and normalized file_path: {file_path}")
            if os.path.exists(file_path) and os.path.isfile(file_path):
                try:
                    self.send_response(200)
                    # MIME 타입 추론
                    mime_type, _ = mimetypes.guess_type(file_path)
                    if mime_type:
                        self.send_header('Content-type', mime_type)
                    else:
                        self.send_header('Content-type', 'application/octet-stream')
                    self.end_headers()

                    with open(file_path, 'rb') as f:
                        self.wfile.write(f.read())
                    logger.debug(f"Served file: {file_path}")
                except Exception as e:
                    logger.exception(f"Error serving file {file_path}:") # 스택 트레이스 포함
                    self.send_error(500, f"Error serving file: {e}")
            else:
                logger.warning(f"File not found or not a file: {file_path}")
                self.send_error(404, "File not found")
        else:
            logger.warning("No 'path' parameter in URL")
            self.send_error(400, "Missing 'path' parameter")

class LocalFileServer:
    def __init__(self, port=8000):
        self.port = port
        self.handler = FileHandler
        self.httpd = None
        self.server_thread = None
        logger.info(f"LocalFileServer initialized on port {self.port}")

    def start(self):
        if self.server_thread and self.server_thread.is_alive():
            logger.info("LocalFileServer is already running.")
            return

        try:
            self.httpd = socketserver.TCPServer(("127.0.0.1", self.port), self.handler)
            self.server_thread = threading.Thread(target=self.httpd.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()
            logger.info(f"LocalFileServer started on port {self.port} in a new thread.")
        except Exception as e:
            logger.error(f"Failed to start LocalFileServer on port {self.port}: {e}")

    def stop(self):
        if self.httpd:
            logger.info("Stopping LocalFileServer...")
            self.httpd.shutdown()
            self.httpd.server_close()
            self.server_thread.join(timeout=1)
            logger.info("LocalFileServer stopped.")
            self.httpd = None
            self.server_thread = None

    def get_file_url(self, file_path):
        logger.debug(f"[LocalFileServer] Original file_path for URL: {file_path}")
        # 백슬래시를 슬래시로 변환하여 경로 정규화
        normalized_path = file_path.replace('\\', '/')
        encoded_path = urllib.parse.quote(normalized_path)
        logger.debug(f"[LocalFileServer] Normalized and Encoded file_path: {encoded_path}")
        url = f"http://127.0.0.1:{self.port}/?path={encoded_path}"
        logger.debug(f"[LocalFileServer] Generated URL: {url}")
        return url

import mimetypes
import http.server
import socketserver
import threading
import os
import urllib.parse
import logging

mimetypes.add_type("video/webm", ".webm")
mimetypes.add_type("video/mp4", ".mp4")
mimetypes.add_type("video/x-matroska", ".mkv")
mimetypes.add_type("video/x-msvideo", ".avi")
mimetypes.add_type("video/quicktime", ".mov")
