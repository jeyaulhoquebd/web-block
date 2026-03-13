import os
import shutil

class HostsManager:
    def __init__(self):
        self.hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
        self.redirect_ip = "127.0.0.1"
        self.marker_start = "# --- FOCUS FORTRESS START ---"
        self.marker_end = "# --- FOCUS FORTRESS END ---"

    def apply_blocks(self, sites, keywords=None, wildcards=None):
        """Applies blocks to the hosts file with keyword and wildcard expansion."""
        sites_to_block = list(sites)
        
        # Expand keywords (simplified: map common keywords to domains)
        if keywords:
            keyword_map = {
                "social": ["facebook.com", "instagram.com", "twitter.com", "t.co", "linkedin.com", "reddit.com"],
                "game": ["steamcommunity.com", "steampowered.com", "epicgames.com", "roblox.com", "twitch.tv"],
                "movie": ["netflix.com", "youtube.com", "hulu.com", "disneyplus.com", "primevideo.com"],
                "tiktok": ["tiktok.com"],
                "facebook": ["facebook.com", "fb.com", "messenger.com"],
                "youtube": ["youtube.com", "youtu.be"]
            }
            for kw in keywords:
                kw_str = str(kw)
                if kw_str in keyword_map:
                    sites_to_block.extend(keyword_map[kw_str])

        # Remove duplicates
        sites_to_block = list(set(sites_to_block))

        try:
            self._ensure_backup()
            
            with open(self.hosts_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Remove existing Focus Fortress block
            cleaned_lines = []
            in_block = False
            for line in lines:
                if line.strip() == self.marker_start:
                    in_block = True
                    continue
                if line.strip() == self.marker_end:
                    in_block = False
                    continue
                if not in_block:
                    cleaned_lines.append(line)

            # Ensure newline at the end if not present
            if cleaned_lines and not cleaned_lines[-1].endswith('\n'):
                cleaned_lines[-1] += '\n'

            # Add new block if there are sites to block
            if sites_to_block:
                cleaned_lines.append(f"{self.marker_start}\n")
                cleaned_lines.append("# Do not edit this block manually.\n")
                for site in sites_to_block:
                    # Block exact site
                    cleaned_lines.append(f"{self.redirect_ip} {site}\n")
                    # Block www variant if it doesn't start with www
                    if not site.startswith('www.'):
                        cleaned_lines.append(f"{self.redirect_ip} www.{site}\n")
                cleaned_lines.append(f"{self.marker_end}\n")

            with open(self.hosts_path, 'w', encoding='utf-8') as f:
                f.writelines(cleaned_lines)
                
            # Flush DNS to ensure immediate effect
            os.system("ipconfig /flushdns >nul 2>&1")
            return True
            
        except PermissionError:
            print("Permission denied: Cannot modify hosts file. Ensure app is run as Administrator.")
            return False
        except Exception as e:
            print(f"Error updating hosts file: {e}")
            return False

    def remove_all_blocks(self):
        """Removes the Focus Shield block entirely."""
        return self.apply_blocks([])

    def _ensure_backup(self):
        """Creates a backup of the original hosts file if one doesn't exist."""
        backup_path = self.hosts_path + ".fortress_backup"
        if not os.path.exists(backup_path) and os.path.exists(self.hosts_path):
            try:
                shutil.copy2(self.hosts_path, backup_path)
            except Exception as e:
                print(f"Failed to create backup: {e}")
