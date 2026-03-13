import threading
import socket
from plyer import notification  # type: ignore
import time
from typing import Optional

class NotificationServer:
    def __init__(self, port=80):
        self.port = port
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self.last_notified: float = 0.0

    def start(self):
        if not self.running:
            self.running = True
            self._thread = threading.Thread(target=self._run_server, daemon=True)
            self._thread.start()  # type: ignore

    def stop(self):
        self.running = False
        # Create a dummy connection to unblock the accept() call
        try:
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(('127.0.0.1', self.port))
        except:
            pass
        if self._thread is not None:
            self._thread.join(timeout=1.0)  # type: ignore

    def _run_server(self):
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(('127.0.0.1', self.port))
            server_socket.listen(5)
            # Increase socket timeout to allow checking self.running periodically without hanging
            server_socket.settimeout(1.0)
            
            while self.running:
                try:
                    client_socket, addr = server_socket.accept()
                    if not self.running:
                        break
                        
                    # Try to send a simple response if it's HTTP (port 80)
                    if self.port == 80:
                        try:
                            response = b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n<html><head><title>Blocked</title></head><body style='background-color: #1a1a1a; color: white; display: flex; justify-content: center; align-items: center; height: 100vh; font-family: sans-serif;'><h1>Blocked by Focus Fortress</h1></body></html>"
                            client_socket.sendall(response)
                        except:
                            pass
                    
                    client_socket.close()
                    self._trigger_notification()
                except socket.timeout:
                    continue
                except Exception as e:
                    pass
            server_socket.close()
        except OSError as e:
            print(f"Notification server on port {self.port} could not start: {e}. Port may be in use.")

    def _trigger_notification(self):
        current_time = time.time()
        # Prevent spamming notifications (wait at least 5 seconds between notifications)
        if current_time - self.last_notified > 5:
            try:
                notification.notify(  # type: ignore
                    title='Focus Fortress',
                    message='A blocked site was just accessed.',
                    app_name='Focus Fortress',
                    timeout=5
                )
                self.last_notified = current_time
            except Exception as e:
                print(f"Error showing notification: {e}")

class NotificationManager:
    def __init__(self):
        self.server_80 = NotificationServer(port=80)
        self.server_443 = NotificationServer(port=443)

    def start(self):
        self.server_80.start()
        self.server_443.start()

    def stop(self):
        self.server_80.stop()
        self.server_443.stop()
