import os
import sys
import psutil # type: ignore
import time
import subprocess
import signal

def is_process_running(process_name):
    # type: ignore (psutil might not be installed in all environments)
    try:
        for proc in psutil.process_iter(['name']): 
            try:
                if proc.info['name'].lower() == process_name.lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
    except:
        pass
    return False

def start_main_app(app_path):
    try:
        # 0x08000000 is CREATE_NO_WINDOW
        if app_path.endswith(".py"):
            subprocess.Popen([sys.executable, app_path], creationflags=0x08000000)
        else:
            subprocess.Popen([app_path], creationflags=0x08000000)
    except Exception as e:
        print(f"Watchdog failed to restart app: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: watchdog.py <process_name> <app_path>")
        sys.exit(1)

    target_process = sys.argv[1]
    app_to_start = sys.argv[2]
    
    # Hide window if running on Windows
    if os.name == 'nt':
        try:
            import ctypes
            # Hide console window safely on Windows
            if hasattr(ctypes, 'windll'): # type: ignore
                ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0) # type: ignore
        except:
            pass

    print(f"Watchdog started. Monitoring {target_process}...")
    
    while True:
        if not is_process_running(target_process):
            # Check if the lock is actually active before restarting
            # We'd ideally check the config file here
            print(f"{target_process} is not running. Restarting...")
            start_main_app(app_to_start)
        
        time.sleep(5)
