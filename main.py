import sys
from PyQt5.QtWidgets import QApplication
from app.chat_app import ChatApp

if __name__ == '__main__':
    app = QApplication(sys.argv)
    chat_app = ChatApp()
    chat_app.show()
    sys.exit(app.exec_())
