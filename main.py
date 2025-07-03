import sys
from PyQt5.QtWidgets import QApplication
from main_window import MainWindow

if __name__ == '__main__':
    """
    애플리케이션의 메인 진입점(Entry Point)입니다.
    이 파일은 QApplication과 MainWindow 인스턴스를 생성하고 실행하는 역할만 합니다.
    """
    print("[main.py] 애플리케이션 시작")
    app = QApplication(sys.argv)
    print("[main.py] QApplication 인스턴스 생성 완료")
    
    print("[main.py] MainWindow 인스턴스 생성 시작")
    mainWindow = MainWindow()
    print("[main.py] MainWindow 인스턴스 생성 완료")
    
    print("[main.py] mainWindow.show() 호출 시작")
    mainWindow.show()
    print("[main.py] mainWindow.show() 호출 완료")
    
    print("[main.py] app.exec_() 실행")
    sys.exit(app.exec_())
