import sys
import logging
import os # os 모듈 추가
from PyQt5.QtWidgets import QApplication
from pymongo import MongoClient
import config
from main_window import MainWindow

logging.basicConfig(level=logging.WARNING, format='[%(levelname)s:%(name)s:%(lineno)d] %(message)s')

if __name__ == '__main__':
    try:
        # MongoDB 클라이언트 생성
        client = MongoClient(config.MONGO_URI, serverSelectionTimeoutMS=5000)
        # 연결 테스트
        client.admin.command('ping')
        logging.info("MongoDB에 성공적으로 연결되었습니다.")

        app = QApplication(sys.argv)

        # QSS 파일 로드 및 적용
        qss_file_path = os.path.join(os.path.dirname(__file__), 'assets', 'style.qss')
        if os.path.exists(qss_file_path):
            with open(qss_file_path, 'r', encoding='utf-8') as f:
                _qss = f.read()
            app.setStyleSheet(_qss)
            logging.info(f"QSS 파일 '{qss_file_path}'이(가) 성공적으로 적용되었습니다.")
        else:
            logging.warning(f"QSS 파일 '{qss_file_path}'을(를) 찾을 수 없습니다. 스타일이 적용되지 않습니다.")

        # MainWindow에 MongoClient 인스턴스 전달
        window = MainWindow(client)
        sys.exit(app.exec_())

    except Exception as e:
        logging.critical(f"애플리케이션 시작 중 심각한 오류 발생: {e}")
        # 여기서 사용자에게 오류 메시지를 표시하는 것이 좋습니다 (QMessageBox 사용).
        sys.exit(1)
