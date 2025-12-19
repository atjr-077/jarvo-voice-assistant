"""
Simple Voice Test - Click Start to test your microphone
"""
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QTextEdit
from PyQt6.QtCore import QThread, pyqtSignal
import speech_recognition as sr

class VoiceTestWorker(QThread):
    result = pyqtSignal(str)
    status = pyqtSignal(str)
    
    def run(self):
        recognizer = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                self.status.emit("🎤 Listening... Speak now!")
                recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                
                self.status.emit("🔄 Processing...")
                text = recognizer.recognize_google(audio)
                self.result.emit(f"✅ You said: {text}")
        except sr.WaitTimeoutError:
            self.result.emit("⏱️ Timeout - No speech detected")
        except sr.UnknownValueError:
            self.result.emit("❌ Could not understand audio")
        except Exception as e:
            self.result.emit(f"❌ Error: {str(e)}")

class SimpleVoiceTest(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Voice Test")
        self.setGeometry(100, 100, 500, 400)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout()
        
        # Status label
        self.status_label = QLabel("Click 'Start Test' to begin")
        self.status_label.setStyleSheet("font-size: 16px; padding: 20px;")
        layout.addWidget(self.status_label)
        
        # Start button
        self.start_btn = QPushButton("🎤 Start Test")
        self.start_btn.setStyleSheet("""
            QPushButton {
                font-size: 18px;
                padding: 20px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.start_btn.clicked.connect(self.start_test)
        layout.addWidget(self.start_btn)
        
        # Results
        self.results = QTextEdit()
        self.results.setReadOnly(True)
        self.results.setStyleSheet("font-size: 14px; padding: 10px;")
        layout.addWidget(self.results)
        
        central.setLayout(layout)
        self.worker = None
        
    def start_test(self):
        self.start_btn.setEnabled(False)
        self.results.append("\n--- New Test ---")
        
        self.worker = VoiceTestWorker()
        self.worker.status.connect(self.update_status)
        self.worker.result.connect(self.show_result)
        self.worker.finished.connect(lambda: self.start_btn.setEnabled(True))
        self.worker.start()
        
    def update_status(self, text):
        self.status_label.setText(text)
        
    def show_result(self, text):
        self.results.append(text)
        self.status_label.setText("Ready for next test")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SimpleVoiceTest()
    window.show()
    sys.exit(app.exec())
