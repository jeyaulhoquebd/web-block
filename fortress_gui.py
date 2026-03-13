import customtkinter as ctk # type: ignore
import tkinter as tk
import tkinter.messagebox as messagebox
import time
import os
import sys
import math
import winreg
from datetime import datetime

# Resilient imports for standalone components
try:
    from gui.lock_screen import LockScreen # type: ignore
    import startup_manager # type: ignore
except ImportError:
    # Handle the case where gui/ is in the same dir and not a package
    import sys
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.append(project_root)
    try:
        from gui.lock_screen import LockScreen # type: ignore
        import startup_manager # type: ignore
    except ImportError:
        # Fallback to avoid NoneType errors while keeping linter somewhat happy
        class LockScreen: 
            def __init__(self, *args, **kwargs): pass
            def grab_set(self): pass
        startup_manager = None

class ProgressRing(tk.Canvas):
    def __init__(self, master, size=250, **kwargs):
        # Try to get background color safely
        try:
            bg = master._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["fg_color"])
        except:
            bg = "#2b2b2b" if ctk.get_appearance_mode() == "Dark" else "#dbdbdb"
        super().__init__(master, width=size, height=size, bg=bg, 
                         highlightthickness=0, **kwargs)
        self.size = size
        self.padding = 20
        self.stroke = 15
        self.progress = 0
        self.bind("<Configure>", lambda e: self.draw())

    def set_progress(self, progress):
        self.progress = max(0, min(1, progress))
        self.draw()

    def draw(self):
        self.delete("all")
        bg_color = "#333333" if ctk.get_appearance_mode() == "Dark" else "#DDDDDD"
        accent_color = "#1f6aa5" # Professional Blue
        
        # Background Circle
        self.create_oval(self.padding, self.padding, self.size-self.padding, self.size-self.padding, 
                         outline=bg_color, width=self.stroke)
        
        # Progress Arc
        if self.progress > 0:
            angle = 360 * self.progress
            self.create_arc(self.padding, self.padding, self.size-self.padding, self.size-self.padding, 
                           start=90, extent=-angle, outline=accent_color, width=self.stroke, style="arc")

class FocusFortressApp(ctk.CTk):
    def __init__(self, config, engine):
        super().__init__()
        self.config = config
        self.engine = engine
        
        self.title("Focus Fortress Pro")
        self.geometry("1000x700")
        
        # Intercept closing attempts
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self._setup_ui()
        self._load_lists()
        self._update_timer_loop()

    def _setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.logo = ctk.CTkLabel(self.sidebar, text="FOCUS FORTRESS", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo.pack(pady=30, padx=20)
        
        self.status_lbl = ctk.CTkLabel(self.sidebar, text="STATUS: IDLE", font=ctk.CTkFont(size=14, weight="bold"))
        self.status_lbl.pack(pady=10)
        
        self.focus_toggle = ctk.CTkSwitch(self.sidebar, text="Focus Mode", command=self.toggle_focus_mode)
        self.focus_toggle.pack(pady=20, padx=20)

        self.timer_entry = ctk.CTkEntry(self.sidebar, placeholder_text="Mins (e.g. 30)")
        self.timer_entry.pack(pady=10, padx=20)
        
        self.start_btn = ctk.CTkButton(self.sidebar, text="START TIMER LOCK", command=self.start_lock, fg_color="#d9534f")
        self.start_btn.pack(pady=10, padx=20)

        # Main Area (Tabs)
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        self.tabview.add("Dashboard")
        self.tabview.add("Focus Modes")
        self.tabview.add("Schedule")
        self.tabview.add("Websites")
        self.tabview.add("Applications")
        self.tabview.add("Analytics")
        self.tabview.add("Settings")

        self.tabview.configure(command=self._on_tab_change)

        self._setup_dashboard_tab()
        self._setup_focus_modes_tab_content()
        self._setup_schedule_tab()
        self._setup_websites_tab()
        self._setup_apps_tab()
        self._setup_analytics_tab()
        self._setup_settings_tab()

    def _setup_dashboard_tab(self):
        tab = self.tabview.tab("Dashboard")
        self.dashboard_frame = ctk.CTkFrame(tab, fg_color="transparent")
        self.dashboard_frame.pack(expand=True, fill="both")
        
        self.progress_ring = ProgressRing(self.dashboard_frame, size=300)
        self.progress_ring.pack(pady=40)
        
        self.big_timer = ctk.CTkLabel(self.dashboard_frame, text="00:00:00", font=ctk.CTkFont(size=60, weight="bold"))
        self.big_timer.place(relx=0.5, rely=0.45, anchor="center")

        self.hint_label = ctk.CTkLabel(self.dashboard_frame, text="Your fortress is ready.", font=ctk.CTkFont(slant="italic"))
        self.hint_label.pack(pady=10)
        
        self.quote_label = ctk.CTkLabel(self.dashboard_frame, text="\"Deep work is the superpower of the 21st century.\"", 
                                        font=ctk.CTkFont(size=14), wraplength=400)
        self.quote_label.pack(pady=20)

        self.stealth_btn = ctk.CTkButton(self.dashboard_frame, text="CUT OFF GUI (GO STEALTH)", 
                                         command=self._enable_stealth_mode, fg_color="#5bc0de", width=200)
        self.stealth_btn.pack(pady=10)

    def _setup_focus_modes_tab_content(self):
        tab = self.tabview.tab("Focus Modes")
        ctk.CTkLabel(tab, text="Select Your Focus Intensity", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)
        
        modes_frame = ctk.CTkFrame(tab, fg_color="transparent")
        modes_frame.pack(fill="x", padx=50)
        
        self.mode_var = tk.StringVar(value="DEEP_WORK")
        
        modes = [
            ("Pomodoro (25/5)", "POMODORO", "25 minutes intense focus, 5 minutes break."),
            ("Deep Work", "DEEP_WORK", "Extended focus session (1-4 hours)."),
            ("Exam Mode", "EXAM_MODE", "Total system lockdown. No exceptions.")
        ]
        
        for name, key, desc in modes:
            f = ctk.CTkFrame(modes_frame)
            f.pack(fill="x", pady=10)
            
            rb = ctk.CTkRadioButton(f, text=name, variable=self.mode_var, value=key)
            rb.pack(side="left", padx=20, pady=10)
            ctk.CTkLabel(f, text=desc, font=ctk.CTkFont(size=12, slant="italic")).pack(side="left", padx=20)

    def _setup_schedule_tab(self):
        tab = self.tabview.tab("Schedule")
        ctk.CTkLabel(tab, text="Auto-Focus Schedule", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)
        
        self.sched_frame = ctk.CTkScrollableFrame(tab)
        self.sched_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        input_f = ctk.CTkFrame(tab)
        input_f.pack(fill="x", padx=20, pady=10)
        
        self.start_time_entry = ctk.CTkEntry(input_f, placeholder_text="Start (08:00)", width=100)
        self.start_time_entry.pack(side="left", padx=5)
        
        self.end_time_entry = ctk.CTkEntry(input_f, placeholder_text="End (12:00)", width=100)
        self.end_time_entry.pack(side="left", padx=5)
        
        ctk.CTkButton(input_f, text="Add Block", command=self._add_schedule_block, width=80).pack(side="left", padx=5)

    def _setup_websites_tab(self):
        tab = self.tabview.tab("Websites")
        ctk.CTkLabel(tab, text="Website Blocklist", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        self.sites_frame = ctk.CTkScrollableFrame(tab)
        self.sites_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        input_f = ctk.CTkFrame(tab)
        input_f.pack(fill="x", padx=20, pady=10)
        self.site_entry = ctk.CTkEntry(input_f, placeholder_text="example.com")
        self.site_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        self.site_perm_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(input_f, text="Permanent (30d)", variable=self.site_perm_var, width=120).pack(side="left", padx=5)
        
        ctk.CTkButton(input_f, text="Add", width=60, command=self._add_site).pack(side="left", padx=5)

    def _setup_apps_tab(self):
        tab = self.tabview.tab("Applications")
        
        # Main container
        self.apps_main_frame = ctk.CTkFrame(tab, fg_color="transparent")
        self.apps_main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.apps_main_frame.grid_columnconfigure(0, weight=1)
        self.apps_main_frame.grid_columnconfigure(1, weight=1)
        self.apps_main_frame.grid_rowconfigure(0, weight=1)

        # LEFT COLUMN: CURRENT BLOCKLIST
        left_col = ctk.CTkFrame(self.apps_main_frame)
        left_col.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        ctk.CTkLabel(left_col, text="Active Blocklist", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        self.apps_frame = ctk.CTkScrollableFrame(left_col)
        self.apps_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        input_f = ctk.CTkFrame(left_col)
        input_f.pack(fill="x", padx=10, pady=10)
        self.app_entry = ctk.CTkEntry(input_f, placeholder_text="Manual entry (e.g. Discord.exe)")
        self.app_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        self.app_perm_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(input_f, text="Perm (30d)", variable=self.app_perm_var, width=100).pack(side="left", padx=5)
        
        ctk.CTkButton(input_f, text="Add", width=60, command=self._add_app).pack(side="left", padx=5)

        # RIGHT COLUMN: DISCOVER APPS
        right_col = ctk.CTkFrame(self.apps_main_frame)
        right_col.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        ctk.CTkLabel(right_col, text="Discover Applications", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        search_f = ctk.CTkFrame(right_col)
        search_f.pack(fill="x", padx=10, pady=5)
        self.app_search_entry = ctk.CTkEntry(search_f, placeholder_text="Search installed apps...")
        self.app_search_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.app_search_entry.bind("<KeyRelease>", lambda e: self._filter_discovered_apps())
        
        ctk.CTkButton(search_f, text="Refresh", width=60, command=self._refresh_discovered_apps).pack(side="left", padx=5)

        self.discovered_apps_frame = ctk.CTkScrollableFrame(right_col)
        self.discovered_apps_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.all_discovered_apps = [] # List of tuples (name, exe_name)
        self.after(500, self._refresh_discovered_apps) # Initial load

    def _setup_analytics_tab(self):
        tab = self.tabview.tab("Analytics")
        ctk.CTkLabel(tab, text="Productivity Insights", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)
        
        self.stats_frame = ctk.CTkFrame(tab)
        self.stats_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.total_time_lbl = self._create_stat_box(self.stats_frame, "Total Focus Time", "0 hours", 0, 0)
        self.distractions_lbl = self._create_stat_box(self.stats_frame, "Distractions Blocked", "0", 0, 1)
        self.sessions_lbl = self._create_stat_box(self.stats_frame, "Sessions Completed", "0", 1, 0)
        self.score_lbl = self._create_stat_box(self.stats_frame, "Focus Score", "N/A", 1, 1)

    def _setup_settings_tab(self):
        tab = self.tabview.tab("Settings")
        ctk.CTkLabel(tab, text="System Protection Settings", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)
        
        f = ctk.CTkFrame(tab)
        f.pack(fill="both", expand=True, padx=40, pady=10)
        
        self.disable_tm_var = tk.BooleanVar(value=True)
        ctk.CTkSwitch(f, text="Disable Task Manager during lock", variable=self.disable_tm_var).pack(anchor="w", pady=10, padx=20)
        
        self.disable_cmd_var = tk.BooleanVar(value=False)
        ctk.CTkSwitch(f, text="Disable CMD/PowerShell during lock", variable=self.disable_cmd_var).pack(anchor="w", pady=10, padx=20)
        
        self.lock_settings_var = tk.BooleanVar(value=True)
        ctk.CTkSwitch(f, text="Lock Windows Settings during lock", variable=self.lock_settings_var).pack(anchor="w", pady=10, padx=20)
        
        ctk.CTkButton(f, text="SAVE SYSTEM SETTINGS", command=self._save_system_settings, fg_color="#1f6aa5").pack(pady=30)

    def _create_stat_box(self, master, label, value, r, c):
        f = ctk.CTkFrame(master)
        f.grid(row=r, column=c, padx=10, pady=10, sticky="nsew")
        master.grid_columnconfigure(c, weight=1)
        master.grid_rowconfigure(r, weight=1)
        
        ctk.CTkLabel(f, text=label, font=ctk.CTkFont(size=14)).pack(pady=5)
        v_lbl = ctk.CTkLabel(f, text=value, font=ctk.CTkFont(size=24, weight="bold"))
        v_lbl.pack(pady=10)
        return v_lbl

    def _on_tab_change(self):
        if self.tabview.get() == "Analytics":
            self._update_analytics_ui()

    def _update_analytics_ui(self):
        stats = self.config.settings.get("analytics", {})
        total_mins = stats.get("study_time_total", 0)
        self.total_time_lbl.configure(text=f"{total_mins // 60}h {total_mins % 60}m")
        self.distractions_lbl.configure(text=str(stats.get("distraction_attempts", 0)))
        self.sessions_lbl.configure(text=str(stats.get("sessions_completed", 0)))
        
        history = stats.get("history", [])
        if history:
            avg_score = sum(h.get("focus_score", 0) for h in history) / len(history)
            self.score_lbl.configure(text=f"{int(avg_score)}%")
        else:
            self.score_lbl.configure(text="N/A")

    def _load_lists(self):
        for widget in self.sites_frame.winfo_children(): widget.destroy()
        for widget in self.apps_frame.winfo_children(): widget.destroy()

        self.site_status_labels = {}
        # Normal sites
        for site in self.config.settings.get("blocked_sites", []):
            self._add_list_item(self.sites_frame, site, "sites", False)
            
        # Permanent sites
        for site, expiry in self.config.get_active_permanent_blocks("sites"):
            self._add_list_item(self.sites_frame, site, "sites", True, expiry)

        self.app_status_labels = {}
        # Normal apps
        for app in self.config.settings.get("blocked_apps", []):
            self._add_list_item(self.apps_frame, app, "apps", False)
            
        # Permanent apps
        for app, expiry in self.config.get_active_permanent_blocks("apps"):
            self._add_list_item(self.apps_frame, app, "apps", True, expiry)
        
        self._update_indicators()
        self._update_schedule_list()

    def _get_installed_apps(self):
        """Scans Registry for installed applications."""
        apps = set()
        paths = [
            (getattr(winreg, "HKEY_LOCAL_MACHINE", 0), r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (getattr(winreg, "HKEY_LOCAL_MACHINE", 0), r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            (getattr(winreg, "HKEY_CURRENT_USER", 1), r"Software\Microsoft\Windows\CurrentVersion\Uninstall")
        ]
        
        for root, path in paths:
            if not root: continue
            try:
                # Use getattr for constants and functions to satisfy linters
                # Cast to Callable to satisfy linter regarding context manager and callability
                f_open = cast(Callable, getattr(winreg, "OpenKey", None))
                f_info = cast(Callable, getattr(winreg, "QueryInfoKey", None))
                f_enum = cast(Callable, getattr(winreg, "EnumKey", None))
                f_val = cast(Callable, getattr(winreg, "QueryValueEx", None))
                
                if f_open and f_info and f_enum and f_val:
                    with f_open(root, path) as key:
                        count = f_info(key)[0]
                        for i in range(count):
                            try:
                                subkey_name = f_enum(key, i)
                                with f_open(key, subkey_name) as subkey:
                                    try:
                                        name_val = f_val(subkey, "DisplayName")
                                        name = name_val[0] if name_val and isinstance(name_val, tuple) else ""
                                        if not name: continue
                                        
                                        # Try to find an executable hint
                                        exe_hint = ""
                                        try:
                                            icon_val = f_val(subkey, "DisplayIcon")
                                            icon = icon_val[0] if icon_val and isinstance(icon_val, tuple) else ""
                                            if icon and ".exe" in icon.lower():
                                                exe_hint = os.path.basename(icon.split(",")[0]).strip('" ')
                                        except:
                                            pass
                                        
                                        if not exe_hint:
                                            try:
                                                install_path_val = f_val(subkey, "InstallLocation")
                                                install_path = install_path_val[0] if install_path_val and isinstance(install_path_val, tuple) else ""
                                                if install_path and os.path.exists(install_path):
                                                    # Look for exe files in the root of install path
                                                    exes = [f for f in os.listdir(install_path) if f.lower().endswith(".exe")]
                                                    if exes:
                                                        exe_hint = exes[0]
                                            except:
                                                pass
                                        
                                        apps.add((name, exe_hint))
                                    except: pass
                            except: pass
            except: pass
        
        return sorted(list(apps), key=lambda x: x[0])

    def _refresh_discovered_apps(self):
        self.all_discovered_apps = self._get_installed_apps()
        self._filter_discovered_apps()

    def _filter_discovered_apps(self):
        search_term = self.app_search_entry.get().lower()
        for widget in self.discovered_apps_frame.winfo_children():
            widget.destroy()
            
        count = 0
        for name, exe in self.all_discovered_apps:
            if search_term in name.lower() or (exe and search_term in exe.lower()):
                f = ctk.CTkFrame(self.discovered_apps_frame)
                f.pack(fill="x", pady=1, padx=2)
                
                ctk.CTkLabel(f, text=name, font=ctk.CTkFont(size=12), anchor="w").pack(side="left", padx=5, fill="x", expand=True)
                
                # Show exe if found
                if exe:
                    ctk.CTkLabel(f, text=f"({exe})", font=ctk.CTkFont(size=10, slant="italic"), text_color="gray").pack(side="left", padx=5)
                    add_cmd = lambda e=exe: self._quick_add_app(e)
                else:
                    add_cmd = None
                
                btn = ctk.CTkButton(f, text="+", width=30, height=20, command=add_cmd)
                btn.pack(side="right", padx=5)
                if not add_cmd: btn.configure(state="disabled")
                
                count += 1
                if count > 100: # Limit display for performance
                    ctk.CTkLabel(self.discovered_apps_frame, text="... more results found, refine search ...").pack(pady=5)
                    break

    def _quick_add_app(self, exe_name):
        if exe_name and exe_name not in self.config.settings["blocked_apps"]:
            self.config.settings["blocked_apps"].append(exe_name)
            self.config.save_config()
            self._load_lists()
            messagebox.showinfo("Success", f"Added {exe_name} to blocklist.")

    def _update_indicators(self):
        for site, lbl in self.site_status_labels.items():
            if self.engine.is_site_blocked(site):
                lbl.configure(text="✔️", text_color="#5cb85c")
            else:
                lbl.configure(text="❌", text_color="#d9534f")
                
        is_monitor_active = self.engine.is_app_monitor_active()
        for app, lbl in self.app_status_labels.items():
            if is_monitor_active:
                lbl.configure(text="✔️", text_color="#5cb85c")
            else:
                lbl.configure(text="❌", text_color="#d9534f")
        self.after(3000, self._update_indicators)

    def _add_site(self):
        site = self.site_entry.get().strip().lower()
        if site:
            if self.site_perm_var.get():
                self.config.add_permanent_block("sites", site)
                self.engine.apply_all_blocks()
            elif site not in self.config.settings["blocked_sites"]:
                self.config.settings["blocked_sites"].append(site)
                self.config.save_config()
                self.engine.apply_all_blocks()
            self._load_lists()
            self.site_entry.delete(0, 'end')

    def _remove_site(self, site):
        if site in self.config.settings["blocked_sites"]:
            self.config.settings["blocked_sites"].remove(site)
            self.config.save_config()
            self.engine.remove_all_blocks()
            self._load_lists()

    def _add_app(self):
        app = self.app_entry.get().strip()
        if app:
            if not app.lower().endswith(".exe"): app += ".exe"
            if self.app_perm_var.get():
                self.config.add_permanent_block("apps", app)
                self.engine.apply_all_blocks()
            elif app not in self.config.settings["blocked_apps"]:
                self.config.settings["blocked_apps"].append(app)
                self.config.save_config()
                self.engine.apply_all_blocks()
            self._load_lists()
            self.app_entry.delete(0, 'end')

    def _remove_app(self, app):
        if app in self.config.settings["blocked_apps"]:
            self.config.settings["blocked_apps"].remove(app)
            self.config.save_config()
            self.engine.remove_all_blocks()
            self._load_lists()

    def _add_list_item(self, master, label, item_type, is_permanent, expiry=None):
        f = ctk.CTkFrame(master)
        f.pack(fill="x", pady=2, padx=2)
        
        status_lbl = ctk.CTkLabel(f, text="❌", width=30)
        status_lbl.pack(side="left", padx=5)
        
        if item_type == "sites":
            self.site_status_labels[label] = status_lbl
            remove_cmd = lambda: self._remove_site(label)
        else:
            self.app_status_labels[label] = status_lbl
            remove_cmd = lambda: self._remove_app(label)
            
        display_text = label
        if is_permanent:
            days_left = int((expiry - datetime.now().timestamp()) / (24 * 3600))
            display_text += f" (PERMANENT - {days_left}d left)"
            
        ctk.CTkLabel(f, text=display_text, anchor="w").pack(side="left", padx=10, fill="x", expand=True)
        
        btn = ctk.CTkButton(f, text="X", width=30, fg_color="#d9534f", command=remove_cmd)
        btn.pack(side="right", padx=5)
        if is_permanent:
            btn.configure(state="disabled", text="🔒")

    def _add_schedule_block(self):
        start = self.start_time_entry.get()
        end = self.end_time_entry.get()
        if start and end:
            new_block = {"start": start, "end": end, "days": [0,1,2,3,4,5,6]}
            self.config.settings["schedule"]["daily_blocks"].append(new_block)
            self.config.save_config()
            self._update_schedule_list()
            self.start_time_entry.delete(0, 'end')
            self.end_time_entry.delete(0, 'end')

    def _update_schedule_list(self):
        if not hasattr(self, 'sched_frame'): return
        for widget in self.sched_frame.winfo_children(): widget.destroy()
        for i, block in enumerate(self.config.settings["schedule"].get("daily_blocks", [])):
            f = ctk.CTkFrame(self.sched_frame)
            f.pack(fill="x", pady=2, padx=5)
            ctk.CTkLabel(f, text=f"{block['start']} - {block['end']} (Daily)").pack(side="left", padx=10)
            ctk.CTkButton(f, text="X", width=30, fg_color="#d9534f", command=lambda idx=i: self._remove_schedule_block(idx)).pack(side="right", padx=5)

    def _remove_schedule_block(self, idx):
        self.config.settings["schedule"]["daily_blocks"].pop(idx)
        self.config.save_config()
        self._update_schedule_list()

    def _save_system_settings(self):
        restr = self.config.settings["restrictions"]
        restr["disable_task_mgr"] = self.disable_tm_var.get()
        restr["disable_cmd"] = self.disable_cmd_var.get()
        restr["lock_settings"] = self.lock_settings_var.get()
        self.config.save_config()
        messagebox.showinfo("Success", "System settings saved successfully.")

    def start_lock(self):
        try:
            mins_str = self.timer_entry.get()
            if not mins_str: raise ValueError
            mins = int(mins_str)
            if mins <= 0: raise ValueError
            
            mode = self.mode_var.get()
            if messagebox.askyesno("Confirm Lock", f"Are you sure? System will be LOCKED for {mins} minutes in {mode} mode."):
                self.engine.start_lock(mins, mode=mode)
                self.config.settings["last_duration"] = mins
                self.config.save_config()
                self._lock_start_time = time.time()
                if startup_manager:
                    startup_manager.StartupManager().enable_startup()
                if mode == "EXAM_MODE" and LockScreen:
                    self.lock_screen = LockScreen(self, self.config, self.engine)
                    self.lock_screen.grab_set()
                self._enter_lock_state()
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number of minutes.")

    def toggle_focus_mode(self):
        if self.focus_toggle.get():
            self.config.settings["is_locked"] = True
            self.config.save_config()
            self.engine.apply_all_blocks()
            self.status_lbl.configure(text="STATUS: ACTIVE", text_color="#5cb85c")
        else:
            self.config.settings["is_locked"] = False
            self.config.save_config()
            self.engine.remove_all_blocks()
            self.status_lbl.configure(text="STATUS: IDLE", text_color="gray")
        self._update_indicators()

    def _enter_lock_state(self):
        self.status_lbl.configure(text="STATUS: LOCKED", text_color="#d9534f")
        self.focus_toggle.select()
        self.focus_toggle.configure(state="disabled")
        self.start_btn.configure(state="disabled")
        self.timer_entry.configure(state="disabled")
        self.attributes("-topmost", True)

    def _exit_lock_state(self):
        self.attributes("-topmost", False)
        self.status_lbl.configure(text="STATUS: IDLE", text_color="gray")
        self.focus_toggle.configure(state="normal")
        self.focus_toggle.deselect()
        self.start_btn.configure(state="normal")
        self.timer_entry.configure(state="normal")

    def _update_timer_loop(self):
        if self.config.is_currently_locked():
            self._enter_lock_state()
            end_time = self.config.settings.get("lock_end_time")
            if end_time:
                rem = int(end_time - time.time())
                if rem > 0:
                    h, m, s = rem // 3600, (rem % 3600) // 60, rem % 60
                    self.big_timer.configure(text=f"{h:02d}:{m:02d}:{s:02d}")
                    
                    # Calculate progress correctly based on start/end
                    if not hasattr(self, '_lock_start_time'):
                        self._lock_start_time = end_time - (self.config.settings.get("last_duration", 60) * 60)
                    
                    total_duration = end_time - self._lock_start_time
                    if total_duration > 0:
                        progress = 1 - (rem / total_duration)
                        self.progress_ring.set_progress(progress)
                    else:
                        self.progress_ring.set_progress(1)
                else:
                    self.engine.stop_lock(force=True)
                    self._exit_lock_state()
            else:
                # Manual lock - no timer, just show indicators
                self.big_timer.configure(text="--:--:--")
                self.progress_ring.set_progress(0.99)
        self.after(1000, self._update_timer_loop)

    def _enable_stealth_mode(self):
        if not self.config.is_currently_locked():
            messagebox.showinfo("Stealth Mode", "Stealth Mode can only be enabled during an active lock.")
            return
            
        msg = ("WARNING: This will close the application interface and run Focus Fortress in the background.\n\n"
               "The 'Undo' (Stop Lock) button will no longer be accessible until the lock expires or system is manually restored.\n\n"
               "Are you sure you want to 'Cut Off' the software?")
        if messagebox.askyesno("Confirm Cut Off", msg):
            self.config.settings["headless_mode"] = True
            self.config.save_config()
            self.destroy() # Exit GUI, main stays in background loop

    def on_closing(self):
        if self.config.is_currently_locked():
            # Transitions to background mode instead of blocking close
            self.destroy()
        else:
            self.destroy()
            sys.exit(0)

if __name__ == "__main__":
    try:
        from fortress_config import FortressConfig as Config
        from core.lock_engine import LockEngine
    except ImportError:
        # Fallback for direct execution cases
        class Config: pass
        class LockEngine: pass
    
    cfg = Config() # type: ignore
    eng = LockEngine(cfg) # type: ignore
    app = FocusFortressApp(cfg, eng)
    app.mainloop()
