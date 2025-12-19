import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

class AssistantGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NOVA Assistant")
        self.setGeometry(100, 100, 400, 300)
        self.layout = QVBoxLayout()

        self.status_label = QLabel("Status: Ready")
        self.layout.addWidget(self.status_label)

        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("Type your command here...")
        self.layout.addWidget(self.input_line)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.handle_command)
        self.layout.addWidget(self.send_button)

        self.response_box = QTextEdit()
        self.response_box.setReadOnly(True)
        self.layout.addWidget(self.response_box)

        self.settings_button = QPushButton("Settings (Coming Soon)")
        self.layout.addWidget(self.settings_button)

        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self.close)
        self.layout.addWidget(self.exit_button)

        self.setLayout(self.layout)

        # System tray icon
        self.tray_icon = QSystemTrayIcon(QIcon(), self)
        self.tray_icon.setToolTip("NOVA Assistant")
        tray_menu = QMenu()
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        tray_menu.addAction(exit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def handle_command(self):
        user_text = self.input_line.text().strip()
        if not user_text:
            return
        self.status_label.setText("Status: Processing...")
        # Placeholder: In real integration, call main assistant logic here
        response = f"[Simulated] You said: {user_text}"
        self.response_box.append(f"You: {user_text}")
        self.response_box.append(f"NOVA: {response}\n")
        self.status_label.setText("Status: Ready")
        self.input_line.clear()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = AssistantGUI()
    gui.show()
    sys.exit(app.exec_()) 