import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QTextEdit
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Dialog AI")
        self.setGeometry(100, 100, 800, 600)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Main layout
        main_layout = QHBoxLayout()
        
        # Left side (Dialog AI image and title)
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(2)
        
        self.dialog_ai_title = QLabel("Dialog AI")
        self.dialog_ai_title.setAlignment(Qt.AlignCenter)
        self.dialog_ai_title.setStyleSheet("font-size: 24px; font-weight: bold;")
        left_layout.addWidget(self.dialog_ai_title)
        
        self.dialog_ai_image = QLabel()
        pixmap = QPixmap("ui/bg.png")  # IMG
        self.dialog_ai_image.setPixmap(pixmap)
        self.dialog_ai_image.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.dialog_ai_image)
        
        main_layout.addLayout(left_layout, 70)
        
        # Right side (Buttons and labels)
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(10, 10, 10, 10)
        right_layout.setSpacing(10)
        
        self.thought_bubble = QLabel(" ")
        self.thought_bubble.setAlignment(Qt.AlignCenter)
        self.thought_bubble.setStyleSheet("background-color: black; color: white; font-size: 20px; border-radius: 15px; padding: 10px;")
        right_layout.addWidget(self.thought_bubble, 20)
        
        self.talk_button = QPushButton("Talk")
        self.talk_button.setStyleSheet("font-size: 18px;")
        self.talk_button.setFixedSize(100, 50)
        right_layout.addWidget(self.talk_button, 10, alignment=Qt.AlignCenter)
        
        self.interrupt_button = QPushButton("Interrupt")
        self.interrupt_button.setStyleSheet("font-size: 18px;")
        self.interrupt_button.setFixedSize(100, 50)
        right_layout.addWidget(self.interrupt_button, 10, alignment=Qt.AlignCenter)
        
        self.stop_button = QPushButton("STOP")
        self.stop_button.setStyleSheet("font-size: 18px;")
        self.stop_button.setFixedSize(100, 50)
        right_layout.addWidget(self.stop_button, 10, alignment=Qt.AlignCenter)
        
        self.recording_label = QLabel("recording........")
        self.recording_label.setStyleSheet("font-size: 14px; color: red;")
        right_layout.addWidget(self.recording_label, 10, alignment=Qt.AlignCenter)
        
        main_layout.addLayout(right_layout, 30)
        
        self.central_widget.setLayout(main_layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
