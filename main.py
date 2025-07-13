import sys
import logging
from PyQt5.QtWidgets import QApplication
from pymongo import MongoClient
import config
from main_window import MainWindow

logging.basicConfig(level=logging.INFO, format='[%(levelname)s:%(name)s:%(lineno)d] %(message)s')

if __name__ == '__main__':
    try:
        # MongoDB 클라이언트 생성
        client = MongoClient(config.MONGO_URI, serverSelectionTimeoutMS=5000)
        # 연결 테스트
        client.admin.command('ping')
        logging.info("MongoDB에 성공적으로 연결되었습니다.")

        app = QApplication(sys.argv)
        # MainWindow에 MongoClient 인스턴스 전달
        window = MainWindow(client)
        sys.exit(app.exec_())

    except Exception as e:
        logging.critical(f"애플리케이션 시작 중 심각한 오류 발생: {e}")
        # 여기서 사용자에게 오류 메시지를 표시하는 것이 좋습니다 (QMessageBox 사용).
        sys.exit(1)
