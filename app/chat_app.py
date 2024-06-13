from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtGui import QMovie
import threading
import asyncio
from app.conversation_manager import ConversationManager

class ChatApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.manager = ConversationManager()

    def initUI(self):
        self.setWindowTitle('Dialog AI')
        self.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout()

        self.label = QLabel('Press the button and speak')
        layout.addWidget(self.label)

        self.start_button = QPushButton('Start Talking..')
        self.start_button.clicked.connect(self.start_listening)
        layout.addWidget(self.start_button)

        self.output_label = QLabel('')
        layout.addWidget(self.output_label)

        self.animation_label = QLabel(self)
        layout.addWidget(self.animation_label)

        self.setLayout(layout)

    def start_listening(self):
        self.output_label.setText('Listening...')
        self.start_button.setDisabled(True)
        self.show_animation()

        threading.Thread(target=self.run_conversation).start()

    def run_conversation(self):
        asyncio.run(self.manager.main())
        self.update_output()

    def update_output(self):
        self.output_label.setText('Conversation ended or "goodbye" detected.')
        self.start_button.setDisabled(False)
        self.stop_animation()

    def show_animation(self):
        movie = QMovie("loading.gif")
        self.animation_label.setMovie(movie)
        movie.start()

    def stop_animation(self):
        self.animation_label.clear()
