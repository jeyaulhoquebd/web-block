import time
import sys
import os
import subprocess
import psutil # type: ignore
import threading
from datetime import datetime

# Standardize absolute imports for core modules
try:
    from core.system_tweaker import SystemTweaker # type: ignore
    from hosts_manager import HostsManager # type: ignore
except ImportError:
    # Handle direct script execution more gracefully
    import sys
    import os
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.append(project_root)
    # Re-attempt imports from root
    try:
        from core.system_tweaker import SystemTweaker # type: ignore
        from hosts_manager import HostsManager # type: ignore
    except ImportError:
        # Last resort: absolute-relative (if that makes sense)
        try:
            from system_tweaker import SystemTweaker # type: ignore
            from hosts_manager import HostsManager # type: ignore
        except ImportError:
            # Placeholder to prevent crash during initialization
            class SystemTweaker: 
                def apply_all_restrictions(self): pass
                def remove_all_restrictions(self): pass
            class HostsManager:
                def __init__(self):
                    self.hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
                def apply_blocks(self, *args, **kwargs): pass
                def remove_all_blocks(self): pass

class LockEngine:
    def __init__(self, config_manager, process_monitor):
        self.config = config_manager
        self.monitor = process_monitor
        self.tweaker = SystemTweaker()
        self.hosts = HostsManager()
        
        # Start background service for schedule checking
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

    def start_lock(self, duration_minutes, mode="DEEP_WORK"):
        end_time = time.time() + (duration_minutes * 60)
        self.config.settings["lock_end_time"] = end_time
        self.config.settings["is_locked"] = True
        self.config.settings["focus_mode"] = mode
        self.config.save_config()
        
        self.apply_all_blocks()
        self.monitor.start()
        self._start_watchdog()

    def _start_watchdog(self):
        """Starts the background watchdog process."""
        try:
            watchdog_script = os.path.join(os.path.dirname(__file__), "watchdog.py")
            main_script = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fortress_main.py")
            # We assume the process name is "python.exe" or "FocusFortress.exe"
            proc_name = os.path.basename(sys.executable)
            # 0x08000000 is CREATE_NO_WINDOW
            subprocess.Popen([sys.executable, watchdog_script, proc_name, main_script], 
                             creationflags=0x08000000)
        except Exception as e:
            print(f"Failed to start watchdog: {e}")

    def stop_lock(self, password=None, force=False):
        """Attempts to stop the lock. Returns True if successful."""
        if force or not self.config.is_currently_locked():
            return self._disengage()

        if password and self.verify_unlock(password):
            return self._disengage()
            
        return False

    def verify_unlock(self, password):
        """Verifies if the provided password is correct (primary or emergency)."""
        # Primary password check
        if self.config.verify_password(password):
            return True
        
        # Emergency password check (if implemented)
        # For now, let's assume it's a fixed emergency key or another hash
        return False

    def _disengage(self):
        self.config.settings["is_locked"] = False
        self.config.settings["lock_end_time"] = None
        self.config.settings["focus_mode"] = "IDLE"
        self.config.save_config()
        
        self.remove_all_blocks()
        self.monitor.stop()
        self._stop_watchdog()
        return True

    def _stop_watchdog(self):
        """Kills the watchdog process."""
        for proc in psutil.process_iter(['name', 'cmdline']):
            try:
                if "watchdog.py" in str(proc.info['cmdline']):
                    proc.terminate()
            except:
                pass

    def apply_all_blocks(self):
        """Applies all blocking mechanisms."""
        print("Engaging Focus Fortress mechanisms...")
        
        # Only apply restrictions and process monitor if focus is active or permanent blocks exist
        is_locked = self.config.is_currently_locked()
        if not is_locked:
            self.remove_all_blocks(force=True)
            return

        self.tweaker.apply_all_restrictions()
        
        keywords = self.config.settings.get("keywords", [])
        wildcards = self.config.settings.get("wildcards", [])
        
        # Determine which sites to block
        all_sites = []
        
        # Add permanent sites (always)
        all_sites.extend([s for s, e in self.config.get_active_permanent_blocks("sites")])
        
        # Add session sites ONLY if focus mode is active (manual toggle or timer)
        # Note: self.config.settings["is_locked"] tracks the Focus Session state
        if self.config.settings.get("is_locked"):
            all_sites.extend(self.config.settings.get("blocked_sites", []))
            
        all_sites = list(set(all_sites))
        
        self.hosts.apply_blocks(all_sites, 
                                keywords=keywords, 
                                wildcards=wildcards)
        self.monitor.start()

    def remove_all_blocks(self, force=False):
        """Removes all blocking mechanisms, unless permanent blocks are active."""
        # If not forcing AND either focus or permanent blocks are active, refresh instead of remove
        if not force and self.config.is_currently_locked():
            self.apply_all_blocks()
            return

        print("Disengaging Focus Fortress mechanisms...")
        self.tweaker.remove_all_restrictions()
        self.hosts.remove_all_blocks()
        self.monitor.stop()

    def is_site_blocked(self, site):
        """Checks if a site is actually present in the hosts file."""
        try:
            with open(self.hosts.hosts_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return site in content
        except:
            return False

    def is_app_monitor_active(self):
        """Checks if the process monitor thread is alive."""
        return self.monitor.is_running

    def check_and_resume(self):
        """Called at startup to see if we should still be locked."""
        if self.config.is_currently_locked():
            print("Resuming focus lock...")
            self.apply_all_blocks()
            return True
        return False
    def check_schedule(self):
        """Checks if a scheduled block should be active."""
        if not self.config.settings.get("schedule"):
            return
            
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        current_day = now.weekday()
        
        for block in self.config.settings["schedule"].get("daily_blocks", []):
            if current_day in block.get("days", []):
                if block["start"] <= current_time <= block["end"]:
                    if not self.config.settings["is_locked"]:
                        print(f"Scheduled block active: {block['start']} - {block['end']}")
                        # Default to 60 minutes for scheduled blocks if not specified
                        self.start_lock(duration_minutes=60, mode="SCHEDULED")
                    return
        
        # Auto-disengage if scheduled lock ends? 
        # (This depends on whether we want manual override to persist)
        if self.config.settings.get("focus_mode") == "SCHEDULED":
            self.stop_lock(force=True)

    def _monitor_loop(self):
        """Main internal loop for background tasks."""
        while self._monitoring:
            try:
                self.check_schedule()
            except Exception as e:
                print(f"Schedule check error: {e}")
            time.sleep(60) # Check every minute
