"""
macOS GUI wrapper for Model Deploy
Provides a tkinter interface for managing model deployment and the web dashboard.
"""
import sys
import os
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class ModelDeployApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Model Deploy")
        self.root.geometry("800x600")
        self.root.configure(bg="#0d1117")

        self.server_thread = None
        self.server_running = False
        self.server_instance = None

        self._build_ui()

    def _build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#0d1117")
        style.configure("TLabel", background="#0d1117", foreground="#c9d1d9", font=("Helvetica", 12))
        style.configure("Header.TLabel", font=("Helvetica", 18, "bold"), foreground="#58a6ff")
        style.configure("Status.TLabel", font=("Helvetica", 11), foreground="#8b949e")
        style.configure("TButton", font=("Helvetica", 11))

        # Header
        header = ttk.Frame(self.root)
        header.pack(fill=tk.X, padx=20, pady=(20, 10))
        ttk.Label(header, text="Model Deploy", style="Header.TLabel").pack(side=tk.LEFT)

        self.status_label = ttk.Label(header, text="Web Server: Stopped", style="Status.TLabel")
        self.status_label.pack(side=tk.RIGHT)

        # Control frame
        ctrl_frame = ttk.Frame(self.root)
        ctrl_frame.pack(fill=tk.X, padx=20, pady=10)

        self.start_btn = ttk.Button(ctrl_frame, text="Start Web Server", command=self.toggle_server)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(ctrl_frame, text="Open in Browser", command=self.open_browser).pack(side=tk.LEFT)

        # Port config
        port_frame = ttk.Frame(self.root)
        port_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        ttk.Label(port_frame, text="Port:").pack(side=tk.LEFT)
        self.port_var = tk.StringVar(value="8080")
        port_entry = ttk.Entry(port_frame, textvariable=self.port_var, width=8)
        port_entry.pack(side=tk.LEFT, padx=8)

        # Model management
        model_frame = ttk.Frame(self.root)
        model_frame.pack(fill=tk.X, padx=20, pady=10)
        ttk.Label(model_frame, text="Quick Actions:").pack(anchor=tk.W)

        btn_row = ttk.Frame(model_frame)
        btn_row.pack(fill=tk.X, pady=4)
        ttk.Button(btn_row, text="List Models", command=self.list_models).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(btn_row, text="System Status", command=self.system_status).pack(side=tk.LEFT, padx=(0, 8))

        # Log area
        ttk.Label(self.root, text="Activity Log:").pack(anchor=tk.W, padx=20, pady=(10, 0))
        self.log_area = scrolledtext.ScrolledText(
            self.root, height=15, bg="#161b22", fg="#c9d1d9",
            insertbackground="#c9d1d9", font=("SF Mono", 11), borderwidth=1, relief=tk.FLAT
        )
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=20, pady=(4, 20))

        self.log("Model Deploy GUI initialized.")
        self.log(f"Project root: {PROJECT_ROOT}")

    def log(self, msg):
        self.log_area.insert(tk.END, f"{msg}\n")
        self.log_area.see(tk.END)

    def toggle_server(self):
        if self.server_running:
            self.stop_server()
        else:
            self.start_server()

    def start_server(self):
        port = int(self.port_var.get())
        self.log(f"Starting web server on port {port}...")

        def run():
            try:
                import uvicorn
                from src.web.app import app
                self.server_instance = uvicorn.Server(uvicorn.Config(app, host="0.0.0.0", port=port, log_level="warning"))
                self.server_instance.run()
            except Exception as e:
                self.root.after(0, lambda: self.log(f"Server error: {e}"))
                self.root.after(0, lambda: self._set_server_state(False))

        self.server_thread = threading.Thread(target=run, daemon=True)
        self.server_thread.start()
        self._set_server_state(True)
        self.log(f"Web server started at http://localhost:{port}")

    def stop_server(self):
        if self.server_instance:
            self.server_instance.should_exit = True
        self._set_server_state(False)
        self.log("Web server stopped.")

    def _set_server_state(self, running):
        self.server_running = running
        if running:
            self.start_btn.configure(text="Stop Web Server")
            self.status_label.configure(text="Web Server: Running", foreground="#3fb950")
        else:
            self.start_btn.configure(text="Start Web Server")
            self.status_label.configure(text="Web Server: Stopped", foreground="#8b949e")

    def open_browser(self):
        import webbrowser
        port = self.port_var.get()
        webbrowser.open(f"http://localhost:{port}")
        self.log(f"Opened browser at http://localhost:{port}")

    def list_models(self):
        self.log("Fetching model list...")
        try:
            import urllib.request
            import json
            port = self.port_var.get()
            req = urllib.request.urlopen(f"http://localhost:{port}/api/models")
            data = json.loads(req.read())
            if data:
                for m in data:
                    self.log(f"  Model: {m['model_name']} | Format: {m['model_format']} | Loaded: {m['is_loaded']}")
            else:
                self.log("  No models loaded.")
        except Exception as e:
            self.log(f"  Error: {e} (Is the web server running?)")

    def system_status(self):
        self.log("Fetching system status...")
        try:
            import urllib.request
            import json
            port = self.port_var.get()
            req = urllib.request.urlopen(f"http://localhost:{port}/api/system/status")
            data = json.loads(req.read())
            self.log(f"  Loaded models: {data['models_loaded']}")
            self.log(f"  GPU memory: {data['gpu_memory_used']:.1f}/{data['gpu_memory_total']:.1f} GB")
            self.log(f"  Active requests: {data['active_requests']}")
            self.log(f"  Total requests: {data['total_requests']}")
        except Exception as e:
            self.log(f"  Error: {e} (Is the web server running?)")

    def run(self):
        self.root.mainloop()


def main():
    app = ModelDeployApp()
    app.run()


if __name__ == "__main__":
    main()
