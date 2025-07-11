import sys
import logging
from PyQt5.QtWidgets import QApplication
from main_window import MainWindow

logging.basicConfig(level=logging.INFO, format='[%(levelname)s:%(name)s:%(lineno)d] %(message)s')


if __name__ == '__main__':
    

    app = QApplication(sys.argv)
    window = MainWindow()
    
    

    sys.exit(app.exec_())