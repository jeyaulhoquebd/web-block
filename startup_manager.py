import os
import sys
import subprocess

class StartupManager:
    def __init__(self):
        self.task_name = "FocusFortress"
        # If running from a PyInstaller executable, use that instead of python.
        if getattr(sys, 'frozen', False):
            self.command = sys.executable
        else:
            python_exe = sys.executable
            # Ensure we use pythonw.exe if available so it doesn't open a console
            if python_exe.endswith("python.exe"):
                pythonw = python_exe.replace("python.exe", "pythonw.exe")
                if os.path.exists(pythonw):
                    python_exe = pythonw
            script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "fortress_main.py"))
            self.command = f'"{python_exe}" "{script_path}"'

    def enable_startup(self):
        # Create a scheduled task to run on logon with highest privileges
        cmd = f'schtasks /create /tn "{self.task_name}" /tr "{self.command}" /sc onlogon /rl highest /f'
        try:
            subprocess.run(cmd, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to enable startup: {e}")
            return False

    def disable_startup(self):
        # Delete the scheduled task
        cmd = f'schtasks /delete /tn "{self.task_name}" /f'
        try:
            subprocess.run(cmd, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError:
            return False

    def is_startup_enabled(self):
        # Check if the task exists
        cmd = f'schtasks /query /tn "{self.task_name}"'
        try:
            # We must use capture_output to not leak to console
            result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return result.returncode == 0
        except Exception:
            return False
