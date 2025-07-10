import sys
import logging

logging.basicConfig(level=logging.INFO, format='[%(levelname)s:%(name)s:%(lineno)d] %(message)s')

from PyQt5.QtWidgets import QApplication
from main_window import MainWindow
from core.local_server import LocalFileServer

if __name__ == '__main__':
    # 로컬 파일 서버 인스턴스 생성 및 시작
    file_server = LocalFileServer(port=8000)
    file_server.start()

    app = QApplication(sys.argv)
    window = MainWindow(file_server=file_server)
    
    # 애플리케이션 종료 시 서버 중지
    app.aboutToQuit.connect(file_server.stop)

    sys.exit(app.exec_())