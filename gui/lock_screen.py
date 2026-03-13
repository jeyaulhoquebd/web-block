import customtkinter as ctk # type: ignore
import tkinter as tk
import time

class LockScreen(ctk.CTkToplevel): # type: ignore
    def __init__(self, master=None, config=None, engine=None, **kwargs):
        super().__init__(master=master, **kwargs) # type: ignore
        self.config = config
        self.engine = engine
        
        self.title("FOCUS FORTRESS LOCK")
        self.attributes("-fullscreen", True)
        self.attributes("-topmost", True)
        self.overrideredirect(True) # Remove title bar
        
        self.configure(fg_color="#0a0a0a") # Deep Black
        
        self._setup_ui()
        self._update_loop()
        
        # Prevent exit
        self.protocol("WM_DELETE_WINDOW", lambda: None)
        self.bind("<Escape>", lambda e: None)
        self.bind("<Alt-F4>", lambda e: None)

    def _setup_ui(self):
        self.center_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.center_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        self.timer_lbl = ctk.CTkLabel(self.center_frame, text="00:00:00", 
                                      font=ctk.CTkFont(size=120, weight="bold"), text_color="#d9534f")
        self.timer_lbl.pack(pady=20)
        
        self.msg_lbl = ctk.CTkLabel(self.center_frame, text="EXAM MODE ACTIVE", 
                                    font=ctk.CTkFont(size=24, weight="bold"))
        self.msg_lbl.pack(pady=10)
        
        self.quote_lbl = ctk.CTkLabel(self.center_frame, text="Stay focused. Your future self will thank you.", 
                                      font=ctk.CTkFont(size=18, slant="italic"))
        self.quote_lbl.pack(pady=40)
        
        # Emergency Unlock (Hidden)
        self.unlock_entry = ctk.CTkEntry(self.center_frame, placeholder_text="Unlock Password", 
                                         show="*", width=200)
        self.unlock_entry.pack(pady=20)
        
        self.unlock_btn = ctk.CTkButton(self.center_frame, text="UNLOCK SESSION", 
                                        command=self._attempt_unlock, fg_color="#333333")
        self.unlock_btn.pack(pady=10)

    def _attempt_unlock(self):
        pwd = self.unlock_entry.get()
        if self.engine.stop_lock(password=pwd):
            self.destroy()
        else:
            self.unlock_entry.delete(0, 'end')
            self.msg_lbl.configure(text="INVALID PASSWORD", text_color="#d9534f")
            self.after(2000, lambda: self.msg_lbl.configure(text="EXAM MODE ACTIVE", text_color="white"))

    def _update_loop(self):
        if self.config.is_currently_locked():
            rem = int(self.config.settings["lock_end_time"] - time.time())
            if rem > 0:
                h = rem // 3600
                m = (rem % 3600) // 60
                s = rem % 60
                self.timer_lbl.configure(text=f"{h:02d}:{m:02d}:{s:02d}")
                self.after(1000, self._update_loop)
            else:
                self.destroy()
        else:
            self.destroy()
