import psutil # type: ignore
import threading
import time
import os
import ctypes
from typing import Optional

class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]

class ProcessMonitor:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.blocked_launchers = ["steam.exe", "epicgameslauncher.exe", "origin.exe", "battle.net.exe", "riotclientux.exe"]
        self.installers = ["setup.exe", "install.exe", "msiexec.exe"]
        self.idle_threshold = 300 # 5 minutes by default

    @property
    def is_running(self):
        return self._thread is not None and self._thread.is_alive()

    def start(self):
        if self.is_running:
            return
            
        self._stop_event.clear()
        thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread = thread
        thread.start()

    def stop(self):
        self._stop_event.set()
        thread_ref = self._thread
        if thread_ref is not None:
            thread_ref.join(timeout=1.0)
            self._thread = None

    def get_idle_time(self) -> float:
        """Returns the number of seconds since last user input on Windows."""
        if os.name != 'nt':
            return 0
        try:
            lii = LASTINPUTINFO()
            lii.cbSize = ctypes.sizeof(LASTINPUTINFO) # type: ignore
            if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii)): # type: ignore
                millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime # type: ignore
                return millis / 1000.0
        except:
            pass
        return 0

    def _report_distraction(self, name, save=True):
        """Logs a distraction attempt to analytics."""
        try:
            analytics = self.config_manager.settings.setdefault("analytics", {})
            analytics["distraction_attempts"] = analytics.get("distraction_attempts", 0) + 1
            if save:
                self.config_manager.save_config()
        except:
            pass

    def _monitor_loop(self):
        while not self._stop_event.is_set():
            if self.config_manager.is_currently_locked():
                # Block user-defined apps
                blocked_apps = [app.lower() for app in self.config_manager.settings.get("blocked_apps", [])]
                perm_apps = [app.lower() for app, e in self.config_manager.get_active_permanent_blocks("apps")]
                all_blocked_apps = list(set(blocked_apps + perm_apps))
                
                try:
                    for proc in psutil.process_iter(['name']): # type: ignore
                        if self._stop_event.is_set(): break
                        try:
                            name = proc.info['name'].lower()
                            
                            # Flexible matching: exact match or name-only match
                            is_blocked = False
                            for app in all_blocked_apps:
                                if name == app:
                                    is_blocked = True
                                elif name.split('.')[0] == app.split('.')[0] and app:
                                    # Matches "discord" == "discord.exe" or "discord.exe" == "discord"
                                    is_blocked = True
                                if is_blocked: break

                            # Check for blocked apps, launchers, or unwanted installers
                            if is_blocked or name in self.blocked_launchers or name in self.installers:
                                try:
                                    proc.terminate()
                                    print(f"Terminated blocked/launcher/installer: {name}")
                                    self._report_distraction(name)
                                except psutil.AccessDenied:
                                    # Fallback for some processes: try to kill by PID
                                    try:
                                        os.kill(proc.pid, 9)
                                    except:
                                        pass
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
                except Exception as e:
                    print(f"Monitor error: {e}")
                
                # AI Feature: Idle detection
                idle_sec = self.get_idle_time()
                if idle_sec > self.idle_threshold:
                    # User is idle, maybe record this for analytics or pause session?
                    # For Pro, we just track it.
                    pass
                    
            time.sleep(2)
