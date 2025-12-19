import os
import sys
import winreg
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import QMessageBox


class StartupManager:
    """Manages Windows startup integration for the voice assistant"""
    
    def __init__(self, app_name: str = "JarvoVoiceAssistant"):
        self.app_name = app_name
        self.registry_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
        
    def is_startup_enabled(self) -> bool:
        """Check if the application is set to start with Windows"""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_key) as key:
                try:
                    winreg.QueryValueEx(key, self.app_name)
                    return True
                except FileNotFoundError:
                    return False
        except Exception as e:
            print(f"Error checking startup status: {e}")
            return False
            
    def enable_startup(self, app_path: Optional[str] = None) -> bool:
        """Enable startup with Windows"""
        try:
            if app_path is None:
                app_path = sys.executable
                
            # Get the path to the main script
            script_dir = Path(__file__).parent
            main_script = script_dir / "modern_gui.py"
            
            if not main_script.exists():
                main_script = script_dir / "main.py"
                
            if not main_script.exists():
                return False
                
            # Create the command to run
            command = f'"{app_path}" "{main_script}"'
            
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_key, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, self.app_name, 0, winreg.REG_SZ, command)
                
            return True
            
        except Exception as e:
            print(f"Error enabling startup: {e}")
            return False
            
    def disable_startup(self) -> bool:
        """Disable startup with Windows"""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_key, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, self.app_name)
            return True
        except FileNotFoundError:
            # Key doesn't exist, which means startup is already disabled
            return True
        except Exception as e:
            print(f"Error disabling startup: {e}")
            return False
            
    def toggle_startup(self, app_path: Optional[str] = None) -> bool:
        """Toggle startup status"""
        if self.is_startup_enabled():
            return self.disable_startup()
        else:
            return self.enable_startup(app_path)
            
    def get_startup_command(self) -> Optional[str]:
        """Get the current startup command"""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_key) as key:
                command, _ = winreg.QueryValueEx(key, self.app_name)
                return command
        except FileNotFoundError:
            return None
        except Exception as e:
            print(f"Error getting startup command: {e}")
            return None


def create_startup_shortcut():
    """Create a startup shortcut in the Startup folder"""
    try:
        import winshell
        from win32com.client import Dispatch
        
        # Get the Startup folder path
        startup_folder = winshell.startup()
        
        # Get the path to the main script
        script_dir = Path(__file__).parent
        main_script = script_dir / "modern_gui.py"
        
        if not main_script.exists():
            main_script = script_dir / "main.py"
            
        if not main_script.exists():
            return False
            
        # Create shortcut
        shortcut_path = os.path.join(startup_folder, "Jarvo Voice Assistant.lnk")
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = sys.executable
        shortcut.Arguments = f'"{main_script}"'
        shortcut.WorkingDirectory = str(script_dir)
        shortcut.IconLocation = sys.executable
        shortcut.save()
        
        return True
        
    except ImportError:
        print("winshell and pywin32 required for shortcut creation")
        return False
    except Exception as e:
        print(f"Error creating startup shortcut: {e}")
        return False


def remove_startup_shortcut():
    """Remove the startup shortcut"""
    try:
        import winshell
        
        startup_folder = winshell.startup()
        shortcut_path = os.path.join(startup_folder, "Jarvo Voice Assistant.lnk")
        
        if os.path.exists(shortcut_path):
            os.remove(shortcut_path)
            return True
        return True
        
    except ImportError:
        print("winshell required for shortcut removal")
        return False
    except Exception as e:
        print(f"Error removing startup shortcut: {e}")
        return False


def is_startup_shortcut_exists() -> bool:
    """Check if startup shortcut exists"""
    try:
        import winshell
        
        startup_folder = winshell.startup()
        shortcut_path = os.path.join(startup_folder, "Jarvo Voice Assistant.lnk")
        return os.path.exists(shortcut_path)
        
    except ImportError:
        return False
    except Exception as e:
        print(f"Error checking startup shortcut: {e}")
        return False


class StartupManagerWidget:
    """Widget for managing startup settings"""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.registry_manager = StartupManager()
        
    def get_startup_status(self) -> dict:
        """Get current startup status"""
        return {
            'registry_enabled': self.registry_manager.is_startup_enabled(),
            'shortcut_exists': is_startup_shortcut_exists(),
            'registry_command': self.registry_manager.get_startup_command()
        }
        
    def enable_startup(self, method: str = 'registry') -> bool:
        """Enable startup using specified method"""
        if method == 'registry':
            return self.registry_manager.enable_startup()
        elif method == 'shortcut':
            return create_startup_shortcut()
        else:
            return False
            
    def disable_startup(self, method: str = 'registry') -> bool:
        """Disable startup using specified method"""
        if method == 'registry':
            return self.registry_manager.disable_startup()
        elif method == 'shortcut':
            return remove_startup_shortcut()
        else:
            return False
            
    def toggle_startup(self, method: str = 'registry') -> bool:
        """Toggle startup using specified method"""
        if method == 'registry':
            return self.registry_manager.toggle_startup()
        elif method == 'shortcut':
            if is_startup_shortcut_exists():
                return remove_startup_shortcut()
            else:
                return create_startup_shortcut()
        else:
            return False


def test_startup_manager():
    """Test the startup manager functionality"""
    manager = StartupManager()
    
    print("Testing Startup Manager...")
    print(f"Current startup status: {manager.is_startup_enabled()}")
    
    if manager.is_startup_enabled():
        print(f"Startup command: {manager.get_startup_command()}")
        print("Disabling startup...")
        manager.disable_startup()
    else:
        print("Enabling startup...")
        manager.enable_startup()
        
    print(f"New startup status: {manager.is_startup_enabled()}")


if __name__ == "__main__":
    test_startup_manager()
