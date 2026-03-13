import os
import sys
import ctypes
import traceback
import time
from datetime import datetime

# Setup basic error logging (only for crashes)
logging_dir = os.path.join(os.environ.get('APPDATA', ''), 'FocusFortress')
if not os.path.exists(logging_dir): os.makedirs(logging_dir)
error_log = os.path.join(logging_dir, 'error.log')

def log_error(msg):
    try:
        with open(error_log, 'a') as f:
            f.write(f"{datetime.now()}: {msg}\n")
    except:
        pass

# Verify critical imports early
try:
    import customtkinter as ctk # type: ignore
    import psutil # type: ignore
    from fortress_config import FortressConfig # type: ignore
    from core.process_monitor import ProcessMonitor # type: ignore
    from core.lock_engine import LockEngine # type: ignore
except Exception as e:
    log_error(f"STARTUP ERROR: {e}\n{traceback.format_exc()}")
    ctypes.windll.user32.MessageBoxW(0, f"Startup error: {e}. Check error.log", "Focus Fortress", 0x10) # type: ignore
    sys.exit(1)

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() # type: ignore
    except:
        return False

def run_as_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1) # type: ignore

if __name__ == "__main__":
    try:
        if not is_admin():
            run_as_admin()
            sys.exit()

        config = FortressConfig()
        process_monitor = ProcessMonitor(config)
        engine = LockEngine(config, process_monitor)

        # Check if we need to resume a previous lock
        engine.check_and_resume()

        if not config.settings.get("headless_mode"):
            from fortress_gui import FocusFortressApp # type: ignore
            app = FocusFortressApp(config, engine)
            app.mainloop()

        # After GUI exits (self.destroy() or normal close)
        # If we are locked or headless, keep the process alive to monitor apps
        if config.is_currently_locked() or config.settings.get("headless_mode"):
            # Hide console if it was shown (rare case)
            try:
                if os.name == 'nt' and hasattr(ctypes, 'windll'):
                    getattr(ctypes, 'windll').user32.ShowWindow(getattr(ctypes, 'windll').kernel32.GetConsoleWindow(), 0)
            except: pass
            
            while True:
                time.sleep(10)
    except Exception as e:
        log_error(f"CRITICAL ERROR: {e}\n{traceback.format_exc()}")
        ctypes.windll.user32.MessageBoxW(0, f"A critical error occurred.\n\nError: {e}", "Focus Fortress", 0x10) # type: ignore
        sys.exit(1)
