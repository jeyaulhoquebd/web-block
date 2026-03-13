import winreg
import ctypes
import os

class SystemTweaker:
    """Handles Windows registry tweaks for system-level restrictions."""
    
    POLICY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Policies\System"
    EXPLORER_POLICY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer"

    @staticmethod
    def set_registry_value(path, name, value, root=winreg.HKEY_CURRENT_USER): # type: ignore
        try:
            key = winreg.CreateKeyEx(root, path, 0, winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY) # type: ignore
            winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, value) # type: ignore
            winreg.CloseKey(key) # type: ignore
            return True
        except Exception as e:
            print(f"Registry error: {e}")
            return False

    def toggle_task_manager(self, disable=True):
        """Disables or enables Task Manager."""
        val = 1 if disable else 0
        return self.set_registry_value(self.POLICY_PATH, "DisableTaskMgr", val)

    def toggle_cmd(self, disable=True):
        """Disables or enables Command Prompt."""
        val = 1 if disable else 0
        return self.set_registry_value(self.POLICY_PATH, "DisableCMD", val)

    def toggle_reg_edit(self, disable=True):
        """Disables or enables Registry Editor."""
        val = 1 if disable else 0
        return self.set_registry_value(self.POLICY_PATH, "DisableRegistryTools", val)

    def toggle_user_switching(self, disable=True):
        """Disables or enables Fast User Switching."""
        val = 1 if disable else 0
        return self.set_registry_value(self.EXPLORER_POLICY_PATH, "NoFastUserSwitching", val)

    def toggle_settings_app(self, disable=True):
        """Disables or enables the Windows Settings app."""
        val = 1 if disable else 0
        # NoControlPanel policy disables Settings and Control Panel
        return self.set_registry_value(self.EXPLORER_POLICY_PATH, "NoControlPanel", val)

    def apply_safe_mode_persistence(self):
        """Adds Focus Fortress to Safe Mode boot keys so it runs even in Safe Mode."""
        # Note: This requires admin and targeting HKLM
        safe_boot_path = r"SYSTEM\CurrentControlSet\Control\SafeBoot\Minimal\FocusFortress"
        # Since we use schtasks for startup, adding to SafeBoot Minimal is more complex
        # A simpler way is to prevent F8/Advanced Boot or just log it later.
        # But for focus app, we'll try to add a service entry if possible.
        pass

    def toggle_uninstall_protection(self, disable=True):
        """Prevents uninstallation and access to 'Add or Remove Programs'."""
        val = 1 if disable else 0
        success = True
        # Policies\Explorer: NoAddRemovePrograms
        if not self.set_registry_value(self.EXPLORER_POLICY_PATH, "NoAddRemovePrograms", val):
            success = False
        # Policies\Explorer: NoControlPanel (already handled in toggle_settings_app, but redundant is safe)
        if not self.set_registry_value(self.EXPLORER_POLICY_PATH, "NoControlPanel", val):
            success = False
        # Policies\System: NoConfigPage (Prevents access to the 'Settings' about page)
        if not self.set_registry_value(self.POLICY_PATH, "NoConfigPage", val):
            success = False
        return success

    def apply_all_restrictions(self):
        self.toggle_task_manager(True)
        self.toggle_cmd(True)
        self.toggle_reg_edit(True)
        self.toggle_user_switching(True)
        self.toggle_settings_app(True)
        self.toggle_uninstall_protection(True)

    def remove_all_restrictions(self):
        self.toggle_task_manager(False)
        self.toggle_cmd(False)
        self.toggle_reg_edit(False)
        self.toggle_user_switching(False)
        self.toggle_settings_app(False)
        self.toggle_uninstall_protection(False)
