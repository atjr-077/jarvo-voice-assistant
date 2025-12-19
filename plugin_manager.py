import os
import sys
import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Any, Optional
import json

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QTextEdit, QGroupBox, QCheckBox, QDialog,
    QTabWidget, QScrollArea, QFrame, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon


class PluginInfo:
    """Information about a plugin"""
    def __init__(self, name: str, path: str, module=None, enabled: bool = True):
        self.name = name
        self.path = path
        self.module = module
        self.enabled = enabled
        self.functions = {}
        self.description = ""
        self.version = "1.0"
        self.author = "Unknown"
        
    def load_functions(self):
        """Load available functions from the plugin module"""
        if not self.module:
            return
            
        try:
            for name, obj in inspect.getmembers(self.module):
                if inspect.isfunction(obj) and not name.startswith('_'):
                    # Get function signature and docstring
                    sig = inspect.signature(obj)
                    doc = inspect.getdoc(obj) or "No description available"
                    
                    self.functions[name] = {
                        'function': obj,
                        'signature': str(sig),
                        'docstring': doc
                    }
        except Exception as e:
            print(f"Error loading functions from {self.name}: {e}")


class PluginManager:
    """Manages plugins for the voice assistant"""
    
    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = Path(plugins_dir)
        self.plugins: Dict[str, PluginInfo] = {}
        self.action_map: Dict[str, Any] = {}
        self.settings_file = Path("plugin_settings.json")
        self.load_settings()
        
    def discover_plugins(self):
        """Discover all available plugins in the plugins directory"""
        if not self.plugins_dir.exists():
            self.plugins_dir.mkdir(exist_ok=True)
            return
            
        for plugin_file in self.plugins_dir.glob("*.py"):
            if plugin_file.name.startswith("__"):
                continue
                
            plugin_name = plugin_file.stem
            try:
                # Import the plugin module
                spec = importlib.util.spec_from_file_location(plugin_name, plugin_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Create plugin info
                plugin_info = PluginInfo(
                    name=plugin_name,
                    path=str(plugin_file),
                    module=module,
                    enabled=self.is_plugin_enabled(plugin_name)
                )
                
                # Load plugin metadata if available
                if hasattr(module, 'PLUGIN_INFO'):
                    info = module.PLUGIN_INFO
                    plugin_info.description = info.get('description', '')
                    plugin_info.version = info.get('version', '1.0')
                    plugin_info.author = info.get('author', 'Unknown')
                
                # Load functions
                plugin_info.load_functions()
                
                # Register plugin if it has a register function
                if hasattr(module, 'register') and plugin_info.enabled:
                    try:
                        module.register(self.action_map)
                    except Exception as e:
                        print(f"Error registering plugin {plugin_name}: {e}")
                
                self.plugins[plugin_name] = plugin_info
                
            except Exception as e:
                print(f"Error loading plugin {plugin_name}: {e}")
                
    def is_plugin_enabled(self, plugin_name: str) -> bool:
        """Check if a plugin is enabled in settings"""
        return self.settings.get('enabled_plugins', {}).get(plugin_name, True)
        
    def enable_plugin(self, plugin_name: str):
        """Enable a plugin"""
        if plugin_name in self.plugins:
            plugin = self.plugins[plugin_name]
            plugin.enabled = True
            
            # Register plugin functions
            if plugin.module and hasattr(plugin.module, 'register'):
                try:
                    plugin.module.register(self.action_map)
                except Exception as e:
                    print(f"Error registering plugin {plugin_name}: {e}")
                    
            self.save_settings()
            
    def disable_plugin(self, plugin_name: str):
        """Disable a plugin"""
        if plugin_name in self.plugins:
            plugin = self.plugins[plugin_name]
            plugin.enabled = False
            
            # Remove plugin functions from action map
            if plugin.module and hasattr(plugin.module, 'register'):
                # This is a simplified approach - in a real implementation,
                # you'd want to track which functions belong to which plugin
                pass
                
            self.save_settings()
            
    def get_available_actions(self) -> List[str]:
        """Get list of available actions from all enabled plugins"""
        actions = []
        for plugin in self.plugins.values():
            if plugin.enabled:
                actions.extend(plugin.functions.keys())
        return actions
        
    def execute_action(self, action_name: str, *args, **kwargs):
        """Execute an action from a plugin"""
        if action_name in self.action_map:
            try:
                return self.action_map[action_name](*args, **kwargs)
            except Exception as e:
                print(f"Error executing action {action_name}: {e}")
                return None
        return None
        
    def load_settings(self):
        """Load plugin settings from file"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    self.settings = json.load(f)
            except Exception as e:
                print(f"Error loading plugin settings: {e}")
                self.settings = {}
        else:
            self.settings = {}
            
    def save_settings(self):
        """Save plugin settings to file"""
        # Update enabled plugins in settings
        enabled_plugins = {}
        for name, plugin in self.plugins.items():
            enabled_plugins[name] = plugin.enabled
            
        self.settings['enabled_plugins'] = enabled_plugins
        
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error saving plugin settings: {e}")


class PluginManagerWidget(QWidget):
    """Widget for managing plugins"""
    
    plugin_toggled = pyqtSignal(str, bool)  # plugin_name, enabled
    
    def __init__(self, plugin_manager: PluginManager, parent=None):
        super().__init__(parent)
        self.plugin_manager = plugin_manager
        self.init_ui()
        self.refresh_plugins()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.refresh_plugins)
        
        self.scan_btn = QPushButton("📁 Scan for Plugins")
        self.scan_btn.clicked.connect(self.scan_for_plugins)
        
        header_layout.addWidget(self.refresh_btn)
        header_layout.addWidget(self.scan_btn)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Plugin list
        self.plugin_list = QListWidget()
        self.plugin_list.itemChanged.connect(self.on_plugin_toggled)
        layout.addWidget(self.plugin_list)
        
        # Plugin details
        details_group = QGroupBox("Plugin Details")
        details_layout = QVBoxLayout()
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMaximumHeight(200)
        
        details_layout.addWidget(self.details_text)
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)
        
        # Connect selection change
        self.plugin_list.itemSelectionChanged.connect(self.on_plugin_selected)
        
        self.setLayout(layout)
        
    def refresh_plugins(self):
        """Refresh the plugin list"""
        self.plugin_list.clear()
        
        for name, plugin in self.plugin_manager.plugins.items():
            item = QListWidgetItem()
            item.setText(f"{name} {'✓' if plugin.enabled else '✗'}")
            item.setData(Qt.ItemDataRole.UserRole, name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if plugin.enabled else Qt.CheckState.Unchecked)
            self.plugin_list.addItem(item)
            
    def scan_for_plugins(self):
        """Scan for new plugins"""
        self.plugin_manager.discover_plugins()
        self.refresh_plugins()
        QMessageBox.information(self, "Scan Complete", "Plugin scan completed.")
        
    def on_plugin_toggled(self, item: QListWidgetItem):
        """Handle plugin enable/disable toggle"""
        plugin_name = item.data(Qt.ItemDataRole.UserRole)
        enabled = item.checkState() == Qt.CheckState.Checked
        
        if enabled:
            self.plugin_manager.enable_plugin(plugin_name)
        else:
            self.plugin_manager.disable_plugin(plugin_name)
            
        # Update display
        item.setText(f"{plugin_name} {'✓' if enabled else '✗'}")
        
        # Emit signal
        self.plugin_toggled.emit(plugin_name, enabled)
        
    def on_plugin_selected(self):
        """Handle plugin selection change"""
        current_item = self.plugin_list.currentItem()
        if not current_item:
            self.details_text.clear()
            return
            
        plugin_name = current_item.data(Qt.ItemDataRole.UserRole)
        plugin = self.plugin_manager.plugins.get(plugin_name)
        
        if not plugin:
            return
            
        # Build details text
        details = f"Plugin: {plugin.name}\n"
        details += f"Version: {plugin.version}\n"
        details += f"Author: {plugin.author}\n"
        details += f"Status: {'Enabled' if plugin.enabled else 'Disabled'}\n"
        details += f"Path: {plugin.path}\n\n"
        
        if plugin.description:
            details += f"Description:\n{plugin.description}\n\n"
            
        if plugin.functions:
            details += "Available Functions:\n"
            for func_name, func_info in plugin.functions.items():
                details += f"  • {func_name}{func_info['signature']}\n"
                if func_info['docstring']:
                    details += f"    {func_info['docstring']}\n"
                details += "\n"
                
        self.details_text.setPlainText(details)


class PluginManagerDialog(QDialog):
    """Dialog for managing plugins"""
    
    def __init__(self, plugin_manager: PluginManager, parent=None):
        super().__init__(parent)
        self.plugin_manager = plugin_manager
        self.setWindowTitle("Plugin Manager")
        self.setModal(True)
        self.resize(600, 500)
        
        layout = QVBoxLayout()
        
        # Create tabs
        tabs = QTabWidget()
        
        # Plugins tab
        self.plugin_widget = PluginManagerWidget(plugin_manager)
        tabs.addTab(self.plugin_widget, "Plugins")
        
        # Actions tab
        actions_tab = QWidget()
        actions_layout = QVBoxLayout()
        
        self.actions_list = QListWidget()
        actions_layout.addWidget(QLabel("Available Actions:"))
        actions_layout.addWidget(self.actions_list)
        
        actions_tab.setLayout(actions_layout)
        tabs.addTab(actions_tab, "Actions")
        
        layout.addWidget(tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        
        button_layout.addStretch()
        button_layout.addWidget(self.close_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Connect signals
        self.plugin_widget.plugin_toggled.connect(self.on_plugin_toggled)
        
        # Refresh actions list
        self.refresh_actions()
        
    def on_plugin_toggled(self, plugin_name: str, enabled: bool):
        """Handle plugin toggle"""
        self.refresh_actions()
        
    def refresh_actions(self):
        """Refresh the actions list"""
        self.actions_list.clear()
        actions = self.plugin_manager.get_available_actions()
        for action in sorted(actions):
            self.actions_list.addItem(action)
