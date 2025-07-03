import sys
from PyQt5.QtWidgets import QApplication
from main_window import MainWindow

if __name__ == "__main__":
    """
    애플리케이션의 메인 진입점(Entry Point)입니다.
    이 파일은 QApplication과 MainWindow 인스턴스를 생성하고 실행하는 역할만 합니다.
    """
    app = QApplication(sys.argv)

    mainWindow = MainWindow()

    mainWindow.show()

    sys.exit(app.exec_())
