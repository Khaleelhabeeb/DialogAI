import sys
import threading
import asyncio
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QWidget
from PyQt5.QtCore import Qt, QEventLoop
from PyQt5.QtGui import QPixmap
from app.conversation_manager import ConversationManager

class ChatApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Dialog AI")
        self.setGeometry(100, 100, 800, 600)
        
        self.manager = ConversationManager()
        self.conversation_task = None
        self.interrupted = False
        self.loop = QEventLoop()
        
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
        self.set_background_image("ui/bg.png")  # Set initial background
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
        self.talk_button.clicked.connect(self.start_listening)
        right_layout.addWidget(self.talk_button, 10, alignment=Qt.AlignCenter)
        
        self.interrupt_button = QPushButton("Interrupt")
        self.interrupt_button.setStyleSheet("font-size: 18px;")
        self.interrupt_button.setFixedSize(100, 50)
        self.interrupt_button.clicked.connect(self.interrupt_conversation)
        right_layout.addWidget(self.interrupt_button, 10, alignment=Qt.AlignCenter)
        
        self.stop_button = QPushButton("STOP")
        self.stop_button.setStyleSheet("font-size: 18px;")
        self.stop_button.setFixedSize(100, 50)
        self.stop_button.clicked.connect(self.stop_conversation)
        right_layout.addWidget(self.stop_button, 10, alignment=Qt.AlignCenter)
        
        self.recording_label = QLabel("recording........")
        self.recording_label.setStyleSheet("font-size: 14px; color: red;")
        right_layout.addWidget(self.recording_label, 10, alignment=Qt.AlignCenter)
        
        main_layout.addLayout(right_layout, 30)
        
        self.central_widget.setLayout(main_layout)
        
    def set_background_image(self, image_path):
        pixmap = QPixmap(image_path)
        self.dialog_ai_image.setPixmap(pixmap)

    def start_listening(self):
        self.thought_bubble.setText('Listening...')
        self.talk_button.setDisabled(True)
        self.interrupted = False
        self.set_background_image("ui/bg2.gif")  # Set image for speaking
        
        self.conversation_task = threading.Thread(target=self.run_conversation)
        self.conversation_task.start()

    def run_conversation(self):
        asyncio.run(self.manager.main())
        if not self.interrupted:
            self.loop.call_soon_threadsafe(self.update_output)

    def update_output(self):
        self.thought_bubble.setText('Conversation ended or "goodbye" detected.')
        self.talk_button.setDisabled(False)
        self.set_background_image("ui/bg2.png")  # Set image for LLM response
        
    def stop_conversation(self):
        self.interrupted = True
        if self.conversation_task:
            self.conversation_task.join()
        QApplication.quit()

    def interrupt_conversation(self):
        self.interrupted = True
        self.thought_bubble.setText('Listening...')
        self.talk_button.setDisabled(True)
        if self.conversation_task:
            self.conversation_task.join()
        self.start_listening()

    def closeEvent(self, event):
        self.stop_conversation()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatApp()
    window.show()
    sys.exit(app.exec_())

