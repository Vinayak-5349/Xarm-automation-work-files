import tkinter as tk
from tkinter import messagebox
import threading
import subprocess
import pystray
from PIL import Image, ImageDraw
import sys
from armsideclient import arm_status  # use your real dict from armsideclient

# Path to your server script
SERVER_SCRIPT = "roboticserver_u2.py"
server_process = None

# ---------------- Server Control ----------------
def start_server():
    global server_process
    if server_process is None:
        server_process = subprocess.Popen([sys.executable, SERVER_SCRIPT])
        return True
    return False

def stop_server():
    global server_process
    if server_process:
        server_process.terminate()
        try:
            server_process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            server_process.kill()
        server_process = None
        return True
    return False

# ---------------- GUI ----------------
class ArmGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Robotic Arm Server Control")
        self.root.geometry("400x300")

        self.btn = tk.Button(root, text="Start Server", width=20, command=self.toggle_server)
        self.btn.pack(pady=20)

        self.status_labels = {}
        for sys_id in arm_status.keys():
            lbl = tk.Label(root, text=f"System {sys_id}: {arm_status[sys_id]}", font=("Arial", 12))
            lbl.pack(pady=5)
            self.status_labels[sys_id] = lbl

        # periodic refresh
        self.update_status()

        # handle window close → minimize to tray
        self.root.protocol("WM_DELETE_WINDOW", self.hide_to_tray)

        # adjust button text if server already running
        if server_process:
            self.btn.config(text="Stop Server")

    def toggle_server(self):
        if server_process is None:
            if start_server():
                self.btn.config(text="Stop Server")
                messagebox.showinfo("Server", "Server started successfully")
        else:
            if stop_server():
                self.btn.config(text="Start Server")
                messagebox.showinfo("Server", "Server stopped successfully")

    def update_status(self):
        # Here you’d check your real arm_status dict (maybe from threads/IPC)
        for sys_id, lbl in self.status_labels.items():
            state = arm_status.get(sys_id, "unknown")
            color = {
                "idle": "green",
                "working": "orange",
                "offline": "red"
            }.get(state, "gray")
            lbl.config(text=f"System {sys_id}: {state}", fg=color)
        self.root.after(2000, self.update_status)  # refresh every 2s

    def hide_to_tray(self):
        self.root.withdraw()
        setup_tray(self)

# ---------------- Tray Icon ----------------
def create_image():
    img = Image.new("RGB", (64, 64), color=(0, 128, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([16, 16, 48, 48], fill=(255, 255, 255))
    return img

def setup_tray(gui):
    def on_show(icon, item):
        gui.root.deiconify()
        icon.stop()

    def on_exit(icon, item):
        stop_server()
        icon.stop()
        gui.root.destroy()

    icon = pystray.Icon("arm_gui", create_image(), menu=pystray.Menu(
        pystray.MenuItem("Show", on_show),
        pystray.MenuItem("Exit", on_exit)
    ))
    threading.Thread(target=icon.run, daemon=True).start()

# ---------------- Main ----------------
if __name__ == "__main__":
    root = tk.Tk()
    app = ArmGUI(root)
    root.mainloop()
