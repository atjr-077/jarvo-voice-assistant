import sys
import json
import os
import threading
import time
import random
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QTabWidget,
    QSystemTrayIcon, QMenu, QDialog, QComboBox, QCheckBox, QSpinBox,
    QGroupBox, QScrollArea, QFrame, QSplitter, QListWidget, QListWidgetItem,
    QMessageBox, QFileDialog, QProgressBar, QSlider, QButtonGroup, QRadioButton
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QSettings, QSize, QPropertyAnimation,
    QEasingCurve, QRect, QPoint
)
from PyQt6.QtGui import (
    QIcon, QFont, QPalette, QColor, QPixmap, QPainter, QLinearGradient,
    QBrush, QAction, QKeySequence, QShortcut
)

# Import your existing modules
from speech import speak, listen, listen_direct, list_microphones, set_mic_index
from actions import route_action
from utils import match_intent, log_command
from wake_word import WakeWordDetector
from config import get_gemini_api_key, get_livekit_api_key, get_livekit_api_secret
from assistant.state import INTERACTION_IN_PROGRESS
from plugin_manager import PluginManager, PluginManagerDialog
from startup_manager import StartupManagerWidget


class VoiceWorker(QThread):
    """Worker thread for voice processing to keep UI responsive"""
    command_received = pyqtSignal(str)
    status_update = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    text_recognized = pyqtSignal(str)  # New signal for recognized text
    
    def __init__(self, mode='voice'):
        super().__init__()
        self.mode = mode
        self.running = False
        self.wake_detector = None
        
    def run(self):
        if self.mode == 'voice':
            self._voice_mode()
        elif self.mode == 'wake_word':
            self._wake_word_mode()
            
    def _voice_mode(self):
        self.running = True
        while self.running:
            try:
                self.status_update.emit("Listening...")
                command = listen_direct()  # Use direct listening to bypass wake word
                if command:
                    # Emit recognized text first
                    self.text_recognized.emit(command)
                    self.command_received.emit(command)
                    self.status_update.emit("Processing...")
                else:
                    self.status_update.emit("No input detected")
            except Exception as e:
                self.error_occurred.emit(str(e))
                self.status_update.emit("Error occurred")
            time.sleep(0.1)
            
    def _wake_word_mode(self):
        try:
            self.wake_detector = WakeWordDetector(
                keyword="jarvis",
                sensitivity=0.7,
                callback=self._on_wake_word_detected
            )
            self.status_update.emit("Listening for wake word 'jarvis'...")
            self.wake_detector.listen()
        except Exception as e:
            self.error_occurred.emit(f"Wake word error: {str(e)}")
            
    def _on_wake_word_detected(self):
        self.status_update.emit("Wake word detected! Listening for command...")
        try:
            command = listen()
            if command:
                # Emit recognized text first
                self.text_recognized.emit(command)
                self.command_received.emit(command)
        except Exception as e:
            self.error_occurred.emit(str(e))
        self.status_update.emit("Listening for wake word 'jarvis'...")
        
    def stop(self):
        self.running = False
        if self.wake_detector:
            self.wake_detector.stop()


class SettingsDialog(QDialog):
    """Settings dialog for configuration"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(500, 400)
        
        self.settings = QSettings("VoiceAssistant", "Settings")
        self.init_ui()
        self.load_settings()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Create tab widget
        tabs = QTabWidget()
        
        # Audio tab
        audio_tab = QWidget()
        audio_layout = QVBoxLayout()
        
        # Microphone selection
        mic_group = QGroupBox("Microphone")
        mic_layout = QVBoxLayout()
        
        self.mic_combo = QComboBox()
        self.refresh_mics_btn = QPushButton("Refresh")
        self.refresh_mics_btn.clicked.connect(self.refresh_microphones)
        
        mic_layout.addWidget(QLabel("Select Microphone:"))
        mic_layout.addWidget(self.mic_combo)
        mic_layout.addWidget(self.refresh_mics_btn)
        mic_group.setLayout(mic_layout)
        audio_layout.addWidget(mic_group)
        
        # Audio settings
        audio_settings_group = QGroupBox("Audio Settings")
        audio_settings_layout = QVBoxLayout()
        
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        audio_settings_layout.addWidget(QLabel("TTS Volume:"))
        audio_settings_layout.addWidget(self.volume_slider)
        
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(50, 300)
        self.speed_slider.setValue(200)
        audio_settings_layout.addWidget(QLabel("TTS Speed:"))
        audio_settings_layout.addWidget(self.speed_slider)
        
        audio_settings_group.setLayout(audio_settings_layout)
        audio_layout.addWidget(audio_settings_group)
        
        audio_tab.setLayout(audio_layout)
        tabs.addTab(audio_tab, "Audio")
        
        # API tab
        api_tab = QWidget()
        api_layout = QVBoxLayout()
        
        # Gemini API
        gemini_group = QGroupBox("Gemini API")
        gemini_layout = QVBoxLayout()
        
        self.gemini_key_edit = QLineEdit()
        self.gemini_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        gemini_layout.addWidget(QLabel("API Key:"))
        gemini_layout.addWidget(self.gemini_key_edit)
        
        gemini_group.setLayout(gemini_layout)
        api_layout.addWidget(gemini_group)
        
        # LiveKit API
        livekit_group = QGroupBox("LiveKit API")
        livekit_layout = QVBoxLayout()
        
        self.livekit_url_edit = QLineEdit()
        self.livekit_key_edit = QLineEdit()
        self.livekit_secret_edit = QLineEdit()
        self.livekit_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.livekit_secret_edit.setEchoMode(QLineEdit.EchoMode.Password)
        
        livekit_layout.addWidget(QLabel("URL:"))
        livekit_layout.addWidget(self.livekit_url_edit)
        livekit_layout.addWidget(QLabel("API Key:"))
        livekit_layout.addWidget(self.livekit_key_edit)
        livekit_layout.addWidget(QLabel("API Secret:"))
        livekit_layout.addWidget(self.livekit_secret_edit)
        
        livekit_group.setLayout(livekit_layout)
        api_layout.addWidget(livekit_group)
        
        api_tab.setLayout(api_layout)
        tabs.addTab(api_tab, "API Keys")
        
        # General tab
        general_tab = QWidget()
        general_layout = QVBoxLayout()
        
        # Theme selection
        theme_group = QGroupBox("Appearance")
        theme_layout = QVBoxLayout()
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark", "Auto"])
        theme_layout.addWidget(QLabel("Theme:"))
        theme_layout.addWidget(self.theme_combo)
        
        theme_group.setLayout(theme_layout)
        general_layout.addWidget(theme_group)
        
        # Startup options
        startup_group = QGroupBox("Startup")
        startup_layout = QVBoxLayout()
        
        self.auto_start_check = QCheckBox("Start with Windows")
        self.minimize_to_tray_check = QCheckBox("Minimize to system tray")
        self.start_minimized_check = QCheckBox("Start minimized")
        
        # Connect auto-start checkbox to startup manager
        self.auto_start_check.toggled.connect(self.toggle_auto_start)
        
        startup_layout.addWidget(self.auto_start_check)
        startup_layout.addWidget(self.minimize_to_tray_check)
        startup_layout.addWidget(self.start_minimized_check)
        
        startup_group.setLayout(startup_layout)
        general_layout.addWidget(startup_group)
        
        general_tab.setLayout(general_layout)
        tabs.addTab(general_tab, "General")
        
        layout.addWidget(tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.cancel_btn = QPushButton("Cancel")
        
        self.save_btn.clicked.connect(self.save_settings)
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def refresh_microphones(self):
        self.mic_combo.clear()
        mics = list_microphones()
        for i, mic in enumerate(mics):
            self.mic_combo.addItem(mic, i)
            
    def load_settings(self):
        # Load microphone
        self.refresh_microphones()
        mic_index = self.settings.value("microphone_index", 0, type=int)
        self.mic_combo.setCurrentIndex(mic_index)
        
        # Load audio settings
        self.volume_slider.setValue(self.settings.value("tts_volume", 50, type=int))
        self.speed_slider.setValue(self.settings.value("tts_speed", 200, type=int))
        
        # Load API keys
        self.gemini_key_edit.setText(self.settings.value("gemini_api_key", ""))
        self.livekit_url_edit.setText(self.settings.value("livekit_url", ""))
        self.livekit_key_edit.setText(self.settings.value("livekit_api_key", ""))
        self.livekit_secret_edit.setText(self.settings.value("livekit_api_secret", ""))
        
        # Load general settings
        theme = self.settings.value("theme", "Light")
        self.theme_combo.setCurrentText(theme)
        self.auto_start_check.setChecked(self.settings.value("auto_start", False, type=bool))
        self.minimize_to_tray_check.setChecked(self.settings.value("minimize_to_tray", True, type=bool))
        self.start_minimized_check.setChecked(self.settings.value("start_minimized", False, type=bool))
        
    def save_settings(self):
        # Save microphone
        self.settings.setValue("microphone_index", self.mic_combo.currentData())
        set_mic_index(self.mic_combo.currentData())
        
        # Save audio settings
        self.settings.setValue("tts_volume", self.volume_slider.value())
        self.settings.setValue("tts_speed", self.speed_slider.value())
        
        # Save API keys
        self.settings.setValue("gemini_api_key", self.gemini_key_edit.text())
        self.settings.setValue("livekit_url", self.livekit_url_edit.text())
        self.settings.setValue("livekit_api_key", self.livekit_key_edit.text())
        self.settings.setValue("livekit_api_secret", self.livekit_secret_edit.text())
        
        # Save general settings
        self.settings.setValue("theme", self.theme_combo.currentText())
        self.settings.setValue("auto_start", self.auto_start_check.isChecked())
        self.settings.setValue("minimize_to_tray", self.minimize_to_tray_check.isChecked())
        self.settings.setValue("start_minimized", self.start_minimized_check.isChecked())
        
        self.accept()
        
    def toggle_auto_start(self, enabled: bool):
        """Toggle Windows auto-start"""
        try:
            if enabled:
                success = self.parent().startup_manager.enable_startup('registry')
            else:
                success = self.parent().startup_manager.disable_startup('registry')
                
            if not success:
                QMessageBox.warning(self, "Startup Error", 
                                  "Failed to update Windows startup settings. "
                                  "Please run as administrator or check permissions.")
        except Exception as e:
            QMessageBox.warning(self, "Startup Error", f"Error: {str(e)}")


class CommandHistoryWidget(QWidget):
    """Widget for displaying and managing command history"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_history()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Search bar
        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search commands...")
        self.search_edit.textChanged.connect(self.filter_history)
        
        self.clear_btn = QPushButton("Clear History")
        self.clear_btn.clicked.connect(self.clear_history)
        
        search_layout.addWidget(self.search_edit)
        search_layout.addWidget(self.clear_btn)
        layout.addLayout(search_layout)
        
        # History list
        self.history_list = QListWidget()
        self.history_list.itemDoubleClicked.connect(self.replay_command)
        layout.addWidget(self.history_list)
        
        self.setLayout(layout)
        
    def add_command(self, command: str, response: str, timestamp: str = None):
        if timestamp is None:
            timestamp = datetime.now().strftime("%H:%M:%S")
            
        item_text = f"[{timestamp}] {command}"
        item = QListWidgetItem(item_text)
        item.setData(Qt.ItemDataRole.UserRole, {"command": command, "response": response, "timestamp": timestamp})
        self.history_list.insertItem(0, item)
        
        # Save to file
        self.save_history()
        
    def filter_history(self, text: str):
        for i in range(self.history_list.count()):
            item = self.history_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())
            
    def replay_command(self, item: QListWidgetItem):
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            # Emit signal to parent to replay command
            self.parent().replay_command_signal.emit(data["command"])
            
    def clear_history(self):
        self.history_list.clear()
        self.save_history()
        
    def load_history(self):
        history_file = Path("command_history.json")
        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                    for entry in reversed(history):  # Show newest first
                        self.add_command(entry["command"], entry["response"], entry["timestamp"])
            except Exception as e:
                print(f"Error loading history: {e}")
                
    def save_history(self):
        history = []
        for i in range(min(100, self.history_list.count())):  # Keep last 100 commands
            item = self.history_list.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            if data:
                history.append(data)
                
        try:
            with open("command_history.json", 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving history: {e}")


class ModernVoiceAssistantGUI(QMainWindow):
    """Modern PyQt6 GUI for the voice assistant"""
    
    # Custom signals
    replay_command_signal = pyqtSignal(str)
    command_processed = pyqtSignal(str, str)  # command, response
    command_error = pyqtSignal(str)  # error message
    
    # Follow-up messages for after actions
    FOLLOW_UP_MESSAGES = [
        "What do you want me to do next?",
        "Anything else?",
        "What's the next task?"
    ]
    
    def __init__(self):
        super().__init__()
        self.settings = QSettings("VoiceAssistant", "Settings")
        self.voice_worker = None
        self.current_mode = "idle"
        self.command_history = []
        
        # Initialize plugin manager
        self.plugin_manager = PluginManager()
        self.plugin_manager.discover_plugins()
        
        # Initialize startup manager
        self.startup_manager = StartupManagerWidget()
        
        self.init_ui()
        self.setup_system_tray()
        self.apply_theme()
        self.setup_shortcuts()
        
        # Connect signals
        self.replay_command_signal.connect(self.process_text_command)
        self.command_processed.connect(self.on_command_processed)
        self.command_error.connect(self.handle_error)
        
        # Store current recognized text and matched intent
        self.current_recognized_text = ""
        self.current_matched_intent = ""
        
    def init_ui(self):
        self.setWindowTitle("Jarvo Voice Assistant")
        self.setGeometry(100, 100, 900, 700)
        self.setMinimumSize(800, 600)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout()
        
        # Left panel - Controls and status
        left_panel = self.create_left_panel()
        main_layout.addWidget(left_panel, 1)
        
        # Right panel - History and logs
        right_panel = self.create_right_panel()
        main_layout.addWidget(right_panel, 1)
        
        central_widget.setLayout(main_layout)
        
        # Status bar
        self.status_bar = self.statusBar()
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)
        
        # Progress bar for processing
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
    def create_left_panel(self):
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Status display
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout()
        
        self.status_display = QLabel("Idle")
        self.status_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_display.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                padding: 20px;
                border: 2px solid #ccc;
                border-radius: 10px;
                background-color: #f0f0f0;
            }
        """)
        status_layout.addWidget(self.status_display)
        
        # Mode selection
        mode_group = QGroupBox("Mode")
        mode_layout = QVBoxLayout()
        
        self.mode_buttons = QButtonGroup()
        self.voice_btn = QRadioButton("Voice Mode")
        self.text_btn = QRadioButton("Text Mode")
        self.wake_word_btn = QRadioButton("Wake Word Mode")
        
        self.mode_buttons.addButton(self.voice_btn, 0)
        self.mode_buttons.addButton(self.text_btn, 1)
        self.mode_buttons.addButton(self.wake_word_btn, 2)
        
        self.voice_btn.setChecked(True)
        
        mode_layout.addWidget(self.voice_btn)
        mode_layout.addWidget(self.text_btn)
        mode_layout.addWidget(self.wake_word_btn)
        
        mode_group.setLayout(mode_layout)
        status_layout.addWidget(mode_group)
        
        # Control buttons
        control_group = QGroupBox("Controls")
        control_layout = QVBoxLayout()
        
        self.start_btn = QPushButton("🎤 Start Listening")
        self.start_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                padding: 15px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.start_btn.clicked.connect(self.toggle_listening)
        
        self.stop_btn = QPushButton("🛑 Stop")
        self.stop_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                padding: 15px;
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:pressed {
                background-color: #c1170a;
            }
        """)
        self.stop_btn.clicked.connect(self.stop_listening)
        self.stop_btn.setEnabled(False)
        
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        
        # Text input for text mode
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Type your command here...")
        self.text_input.returnPressed.connect(self.process_text_command)
        self.text_input.setVisible(False)
        
        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.process_text_command)
        self.send_btn.setVisible(False)
        
        control_layout.addWidget(self.text_input)
        control_layout.addWidget(self.send_btn)
        
        control_group.setLayout(control_layout)
        status_layout.addWidget(control_group)
        
        # Quick actions
        actions_group = QGroupBox("Quick Actions")
        actions_layout = QGridLayout()
        
        quick_actions = [
            ("Time", "tell_time"),
            ("Date", "tell_date"),
            ("Joke", "tell_joke"),
            ("IP", "get_ip"),
            ("Screenshot", "take_screenshot"),
            ("Volume Up", "increase_volume"),
            ("Volume Down", "decrease_volume"),
            ("Mute", "mute_audio")
        ]
        
        for i, (label, action) in enumerate(quick_actions):
            btn = QPushButton(label)
            btn.clicked.connect(lambda checked, a=action: self.execute_quick_action(a))
            actions_layout.addWidget(btn, i // 4, i % 4)
            
        actions_group.setLayout(actions_layout)
        status_layout.addWidget(actions_group)
        
        # Settings and Plugin buttons
        settings_layout = QHBoxLayout()
        
        self.settings_btn = QPushButton("⚙️ Settings")
        self.settings_btn.clicked.connect(self.show_settings)
        
        self.plugins_btn = QPushButton("🔌 Plugins")
        self.plugins_btn.clicked.connect(self.show_plugin_manager)
        
        settings_layout.addWidget(self.settings_btn)
        settings_layout.addWidget(self.plugins_btn)
        status_layout.addLayout(settings_layout)
        
        layout.addLayout(status_layout)
        panel.setLayout(layout)
        
        # Connect mode change signals
        self.mode_buttons.buttonClicked.connect(self.on_mode_changed)
        
        return panel
        
    def create_right_panel(self):
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Create tab widget
        tabs = QTabWidget()
        
        # Command history tab
        self.history_widget = CommandHistoryWidget()
        tabs.addTab(self.history_widget, "History")
        
        # Response display tab
        response_tab = QWidget()
        response_layout = QVBoxLayout()
        
        self.response_display = QTextEdit()
        self.response_display.setReadOnly(True)
        self.response_display.setStyleSheet("""
            QTextEdit {
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                background-color: #f8f8f8;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
        """)
        
        response_layout.addWidget(QLabel("Assistant Responses:"))
        response_layout.addWidget(self.response_display)
        
        response_tab.setLayout(response_layout)
        tabs.addTab(response_tab, "Responses")
        
        # Logs tab
        logs_tab = QWidget()
        logs_layout = QVBoxLayout()
        
        self.logs_display = QTextEdit()
        self.logs_display.setReadOnly(True)
        self.logs_display.setStyleSheet("""
            QTextEdit {
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 10px;
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #444;
                border-radius: 5px;
            }
        """)
        
        logs_layout.addWidget(QLabel("System Logs:"))
        logs_layout.addWidget(self.logs_display)
        
        logs_tab.setLayout(logs_layout)
        tabs.addTab(logs_tab, "Logs")
        
        layout.addWidget(tabs)
        panel.setLayout(layout)
        
        return panel
        
    def setup_system_tray(self):
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)
            self.tray_icon.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon))
            
            # Create tray menu
            tray_menu = QMenu()
            
            show_action = QAction("Show", self)
            show_action.triggered.connect(self.show)
            tray_menu.addAction(show_action)
            
            hide_action = QAction("Hide", self)
            hide_action.triggered.connect(self.hide)
            tray_menu.addAction(hide_action)
            
            tray_menu.addSeparator()
            
            settings_action = QAction("Settings", self)
            settings_action.triggered.connect(self.show_settings)
            tray_menu.addAction(settings_action)
            
            tray_menu.addSeparator()
            
            quit_action = QAction("Quit", self)
            quit_action.triggered.connect(self.close)
            tray_menu.addAction(quit_action)
            
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.activated.connect(self.tray_icon_activated)
            self.tray_icon.show()
            
    def setup_shortcuts(self):
        # Global shortcuts
        self.voice_shortcut = QShortcut(QKeySequence("Ctrl+Shift+V"), self)
        self.voice_shortcut.activated.connect(self.toggle_listening)
        
        self.settings_shortcut = QShortcut(QKeySequence("Ctrl+,"), self)
        self.settings_shortcut.activated.connect(self.show_settings)
        
    def apply_theme(self):
        theme = self.settings.value("theme", "Light")
        
        if theme == "Dark":
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QGroupBox {
                    font-weight: bold;
                    border: 2px solid #555;
                    border-radius: 5px;
                    margin-top: 1ex;
                    padding-top: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px 0 5px;
                }
                QPushButton {
                    background-color: #404040;
                    border: 1px solid #555;
                    border-radius: 4px;
                    padding: 8px;
                    color: #ffffff;
                }
                QPushButton:hover {
                    background-color: #505050;
                }
                QPushButton:pressed {
                    background-color: #353535;
                }
                QLineEdit {
                    background-color: #404040;
                    border: 1px solid #555;
                    border-radius: 4px;
                    padding: 8px;
                    color: #ffffff;
                }
                QTextEdit {
                    background-color: #404040;
                    border: 1px solid #555;
                    border-radius: 4px;
                    color: #ffffff;
                }
                QListWidget {
                    background-color: #404040;
                    border: 1px solid #555;
                    border-radius: 4px;
                    color: #ffffff;
                }
                QTabWidget::pane {
                    border: 1px solid #555;
                    background-color: #2b2b2b;
                }
                QTabBar::tab {
                    background-color: #404040;
                    border: 1px solid #555;
                    padding: 8px;
                    color: #ffffff;
                }
                QTabBar::tab:selected {
                    background-color: #505050;
                }
            """)
        else:
            self.setStyleSheet("")
            
    def on_mode_changed(self, button):
        if button == self.voice_btn:
            self.current_mode = "voice"
            self.text_input.setVisible(False)
            self.send_btn.setVisible(False)
        elif button == self.text_btn:
            self.current_mode = "text"
            self.text_input.setVisible(True)
            self.send_btn.setVisible(True)
        elif button == self.wake_word_btn:
            self.current_mode = "wake_word"
            self.text_input.setVisible(False)
            self.send_btn.setVisible(False)
            
    def toggle_listening(self):
        if self.voice_worker and self.voice_worker.isRunning():
            self.stop_listening()
        else:
            self.start_listening()
            
    def start_listening(self):
        if self.current_mode == "voice":
            self.voice_worker = VoiceWorker("voice")
        elif self.current_mode == "wake_word":
            self.voice_worker = VoiceWorker("wake_word")
        else:
            return
            
        # Connect signals
        self.voice_worker.command_received.connect(self.process_voice_command)
        self.voice_worker.status_update.connect(self.update_status)
        self.voice_worker.error_occurred.connect(self.handle_error)
        self.voice_worker.text_recognized.connect(self.on_text_recognized)
        
        # Start worker
        self.voice_worker.start()
        
        # Update UI
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_display.setText("Listening...")
        self.status_display.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                padding: 20px;
                border: 2px solid #4CAF50;
                border-radius: 10px;
                background-color: #e8f5e8;
                color: #2e7d32;
            }
        """)
        
        # Add pulsing animation to start button
        self.add_button_animation()
        
    def stop_listening(self):
        if self.voice_worker:
            self.voice_worker.stop()
            self.voice_worker.wait()
            self.voice_worker = None
            
        # Update UI
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_display.setText("Idle")
        self.status_display.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                padding: 20px;
                border: 2px solid #ccc;
                border-radius: 10px;
                background-color: #f0f0f0;
            }
        """)
        
        # Remove button animation
        self.remove_button_animation()
        
    def process_voice_command(self, command: str):
        self.process_command(command)
        
    def process_text_command(self, command: str = None):
        if command is None:
            command = self.text_input.text().strip()
            if not command:
                return
            self.text_input.clear()
            
        self.process_command(command)
        
    def process_command(self, command: str):
        if not command:
            from speech import speak
            speak("No input detected. Please try again.")
            self.response_display.append("Response: No input detected. Please try again.")
            log_command(command, "no_input")
            return
            
        # Store the recognized text
        self.current_recognized_text = command
        
        # Show recognized text in responses tab
        self.response_display.append(f"You said: {command}")
        
        # Log the recognized text
        self.log_recognized_text(command)
        
        # Update status
        self.update_status("Processing...")
        
        # Match intent and route action
        from utils import match_intent
        from actions import route_action
        from speech import speak
        
        action = match_intent(command)
        self.log_matched_intent(action if action else "unknown")
        
        # Handle stop command explicitly
        if action == "stop_assistant":
            speak("Okay, stopping now. Goodbye!")
            self.response_display.append("Response: Okay, stopping now. Goodbye!")
            log_command(command, action)
            self.close()
            return
            
        if action:
            # Execute the action in a background thread
            def execute_action():
                try:
                    result = route_action(action, command)
                    response = result if result else "Command executed successfully."
                    self.command_processed.emit(command, response)
                except Exception as e:
                    error_msg = f"Error executing command: {str(e)}"
                    self.command_error.emit(error_msg)
            
            threading.Thread(target=execute_action, daemon=True).start()
            log_command(command, action)
        else:
            # Use AI as fallback for unknown commands
            def ai_fallback():
                try:
                    from ai_conversation import ask_ai
                    response = ask_ai(command)
                    speak(response)
                    self.command_processed.emit(command, response)
                    log_command(command, "ai_fallback")
                except Exception as e:
                    error_msg = "Sorry, I didn't understand. Try rephrasing."
                    speak(error_msg)
                    self.command_processed.emit(command, error_msg)
                    log_command(command, f"unknown_action: {e}")
            
            threading.Thread(target=ai_fallback, daemon=True).start()
    def execute_quick_action(self, action: str):
        self.process_command(action)
        
    def on_command_processed(self, command: str, response: str):
        """Handle command processing completion"""
        # Hide progress bar
        self.progress_bar.setVisible(False)
        
        # Update status to Done!
        self.update_status("Done!")
        
        # Add to history
        self.history_widget.add_command(command, response)
        
        # Display response
        self.response_display.append(f"Response: {response}")
        
        # Add follow-up message
        follow_up = random.choice(self.FOLLOW_UP_MESSAGES)
        self.response_display.append(f"\n{follow_up}\n")
        
        # Auto-scroll response display
        scrollbar = self.response_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        # Log command
        log_command(command, "processed")
        
        # Reset status to Ready after a short delay
        QTimer.singleShot(2000, lambda: self.update_status("Ready"))
        
    def update_status(self, status: str):
        self.status_label.setText(status)
        
        # Update the main status display with dynamic styling
        if status == "Listening...":
            self.status_display.setText("Listening...")
            self.status_display.setStyleSheet("""
                QLabel {
                    font-size: 18px;
                    font-weight: bold;
                    padding: 20px;
                    border: 2px solid #4CAF50;
                    border-radius: 10px;
                    background-color: #e8f5e8;
                    color: #2e7d32;
                }
            """)
        elif status == "Processing...":
            self.status_display.setText("Processing...")
            self.status_display.setStyleSheet("""
                QLabel {
                    font-size: 18px;
                    font-weight: bold;
                    padding: 20px;
                    border: 2px solid #FF9800;
                    border-radius: 10px;
                    background-color: #fff3e0;
                    color: #e65100;
                }
            """)
        elif status == "Done!":
            self.status_display.setText("Done!")
            self.status_display.setStyleSheet("""
                QLabel {
                    font-size: 18px;
                    font-weight: bold;
                    padding: 20px;
                    border: 2px solid #2196F3;
                    border-radius: 10px;
                    background-color: #e3f2fd;
                    color: #0d47a1;
                }
            """)
        elif status == "Ready":
            self.status_display.setText("Ready")
            self.status_display.setStyleSheet("""
                QLabel {
                    font-size: 18px;
                    font-weight: bold;
                    padding: 20px;
                    border: 2px solid #ccc;
                    border-radius: 10px;
                    background-color: #f0f0f0;
                }
            """)
        
        self.log_message(f"Status: {status}")
        
    def handle_error(self, error: str):
        self.log_message(f"Error: {error}")
        QMessageBox.warning(self, "Error", f"An error occurred: {error}")
        
    def log_message(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs_display.append(log_entry)
        
        # Auto-scroll to bottom
        scrollbar = self.logs_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def on_text_recognized(self, text: str):
        """Handle when text is recognized from speech"""
        self.current_recognized_text = text
        
    def log_recognized_text(self, text: str):
        """Log the recognized text in a readable format"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] Heard: \"{text}\""
        self.logs_display.append(log_entry)
        
        # Auto-scroll to bottom
        scrollbar = self.logs_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def log_matched_intent(self, intent: str):
        """Log the matched intent in a readable format"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        if intent:
            log_entry = f"    → Matched intent: {intent}"
        else:
            log_entry = f"    → Matched intent: unknown"
        self.logs_display.append(log_entry)
        
        # Auto-scroll to bottom
        scrollbar = self.logs_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def add_button_animation(self):
        """Add pulsing animation to the start button"""
        self.button_animation = QPropertyAnimation(self.start_btn, b"styleSheet")
        self.button_animation.setDuration(1000)
        self.button_animation.setLoopCount(-1)  # Infinite loop
        
        # Create pulsing effect
        self.button_animation.setKeyValueAt(0, """
            QPushButton {
                font-size: 16px;
                padding: 15px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
            }
        """)
        self.button_animation.setKeyValueAt(0.5, """
            QPushButton {
                font-size: 16px;
                padding: 15px;
                background-color: #66BB6A;
                color: white;
                border: none;
                border-radius: 8px;
                box-shadow: 0 0 10px rgba(76, 175, 80, 0.5);
            }
        """)
        self.button_animation.setKeyValueAt(1, """
            QPushButton {
                font-size: 16px;
                padding: 15px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
            }
        """)
        
        self.button_animation.start()
        
    def remove_button_animation(self):
        """Remove the button animation"""
        if hasattr(self, 'button_animation'):
            self.button_animation.stop()
            # Reset to original style
            self.start_btn.setStyleSheet("""
                QPushButton {
                    font-size: 16px;
                    padding: 15px;
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 8px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QPushButton:pressed {
                    background-color: #3d8b40;
                }
            """)
        
    def show_settings(self):
        dialog = SettingsDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.apply_theme()
            
    def show_plugin_manager(self):
        dialog = PluginManagerDialog(self.plugin_manager, self)
        dialog.exec()
            
    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.raise_()
                self.activateWindow()
                
    def closeEvent(self, event):
        if self.settings.value("minimize_to_tray", True, type=bool):
            if QSystemTrayIcon.isSystemTrayAvailable() and self.tray_icon.isVisible():
                self.hide()
                event.ignore()
            else:
                event.accept()
        else:
            event.accept()
            
        # Stop voice worker
        if self.voice_worker:
            self.voice_worker.stop()
            self.voice_worker.wait()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Jarvo Voice Assistant")
    app.setApplicationVersion("2.0")
    
    # Set application icon (if available)
    # app.setWindowIcon(QIcon("icon.png"))
    
    # Create and show main window
    window = ModernVoiceAssistantGUI()
    
    # Check if should start minimized
    settings = QSettings("VoiceAssistant", "Settings")
    if not settings.value("start_minimized", False, type=bool):
        window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
