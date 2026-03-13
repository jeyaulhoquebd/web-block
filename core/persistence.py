import subprocess
import os
import sys

class PersistenceManager:
    """Manages application persistence using Windows Task Scheduler."""
    
    TASK_NAME = "FocusFortressGuardian"

    @staticmethod
    def enable_startup(exe_path=None):
        if not exe_path:
            exe_path = sys.executable if not getattr(sys, 'frozen', False) else sys.executable
            
        # Create a scheduled task that runs with highest privileges at logon
        try:
            # First, try to delete if already exists
            PersistenceManager.disable_startup()
            
            cmd = [
                'schtasks', '/create', '/tn', PersistenceManager.TASK_NAME,
                '/tr', f'"{exe_path}"', '/sc', 'onlogon', '/rl', 'highest', '/f'
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except Exception as e:
            print(f"Failed to enable startup: {e}")
            return False

    @staticmethod
    def disable_startup():
        try:
            cmd = ['schtasks', '/delete', '/tn', PersistenceManager.TASK_NAME, '/f']
            subprocess.run(cmd, capture_output=True)
            return True
        except:
            return False

    @staticmethod
    def is_startup_enabled():
        try:
            cmd = ['schtasks', '/query', '/tn', PersistenceManager.TASK_NAME]
            result = subprocess.run(cmd, capture_output=True)
            return result.returncode == 0
        except:
            return False
