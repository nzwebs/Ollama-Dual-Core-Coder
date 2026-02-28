import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import requests
import json
import time
import math
import os


# ── Colour palette ──────────────────────────────────────────────────────────
BG       = "#080c10"
SURFACE  = "#0d1117"
SURFACE2 = "#161b22"
BORDER   = "#21262d"
ACCENT1  = "#00ff88"
ACCENT2  = "#ff6b35"
ACCENT3  = "#4fc3f7"
TEXT     = "#e6edf3"
MUTED    = "#7d8590"
ERROR    = "#ff4444"


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


# ── Window Geometry Persistence ────────────────────────────────────────────
GEOMETRY_FILE = os.path.join(os.path.dirname(__file__), ".window_geometry.json")

def save_window_geometry(window_name, geometry):
    """Save window position and size"""
    try:
        data = {}
        if os.path.exists(GEOMETRY_FILE):
            with open(GEOMETRY_FILE, 'r') as f:
                data = json.load(f)
        data[window_name] = geometry
        with open(GEOMETRY_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        pass

def load_window_geometry(window_name):
    """Load saved window position and size"""
    try:
        if os.path.exists(GEOMETRY_FILE):
            with open(GEOMETRY_FILE, 'r') as f:
                data = json.load(f)
                return data.get(window_name)
    except Exception as e:
        pass
    return None


# ── Ollama query (streaming) ─────────────────────────────────────────────────
def query_ollama(url, model, prompt, on_token, stop_event):
    start = time.time()
    try:
        resp = requests.post(
            f"{url}/api/generate",
            json={"model": model, "prompt": prompt, "stream": True},
            stream=True,
            timeout=120,
        )
        resp.raise_for_status()
        full = ""
        for line in resp.iter_lines():
            if stop_event.is_set():
                break
            if line:
                try:
                    data = json.loads(line)
                    if data.get("response"):
                        full += data["response"]
                        on_token(full)
                    if data.get("done"):
                        break
                except json.JSONDecodeError:
                    pass
        elapsed = f"{time.time() - start:.1f}s"
        return {"text": full, "elapsed": elapsed, "error": None}
    except requests.exceptions.ConnectionError:
        return {"text": "", "elapsed": "—", "error": "Connection refused — is Ollama running?"}
    except requests.exceptions.Timeout:
        return {"text": "", "elapsed": "—", "error": "Request timed out"}
    except Exception as e:
        return {"text": "", "elapsed": "—", "error": str(e)}


def test_connection(url):
    try:
        resp = requests.get(f"{url}/api/tags", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        models = [m["name"] for m in data.get("models", [])]
        return True, models
    except requests.exceptions.ConnectionError:
        return False, "Connection refused"
    except Exception as e:
        return False, str(e)


def estimate_confidence(text):
    if not text:
        return 0
    score = 0
    if len(text) > 200: score += 30
    if len(text) > 500: score += 20
    code_signals = ["```", "def ", "function ", "class ", "return ", "import "]
    if any(s in text for s in code_signals): score += 30
    bad = ["i'm not sure", "i don't know", "i cannot", "i'm unable"]
    if not any(b in text.lower() for b in bad): score += 20
    return min(score, 100)


def build_consensus_prompt(original, r1, r2, mode, prompt_type="code"):
    is_code = prompt_type == "code"
    
    if mode == "verify":
        if is_code:
            return (
                f"You are a senior software engineer. Given this coding task and two solutions, "
                f"produce the FINAL BEST solution.\n\nTASK: {original}\n\n"
                f"SOLUTION A (original):\n{r1}\n\nSOLUTION B (reviewed/improved):\n{r2}\n\n"
                f"Output ONLY the final code with a brief explanation."
            )
        else:
            return (
                f"You are a thoughtful expert. Given a question and two answers, "
                f"synthesize the best response.\n\nQUESTION: {original}\n\n"
                f"ANSWER A:\n{r1}\n\nANSWER B (refined):\n{r2}\n\n"
                f"Provide the final, most accurate and complete answer."
            )
    elif mode == "debate":
        if is_code:
            return (
                f"You are a senior software engineer acting as judge. Two AI models answered "
                f"this coding question. Synthesise the BEST solution.\n\n"
                f"QUESTION: {original}\n\nMODEL A:\n{r1}\n\nMODEL B:\n{r2}\n\n"
                f"Provide the final, optimal, merged solution."
            )
        else:
            return (
                f"You are a wise mediator. Two AI models provided different answers to a question. "
                f"Synthesize the BEST combined answer.\n\n"
                f"QUESTION: {original}\n\nMODEL A:\n{r1}\n\nMODEL B:\n{r2}\n\n"
                f"Provide the most accurate, complete, and balanced answer."
            )
    else:  # parallel
        if is_code:
            return (
                f"Two AI models answered the same coding question. Choose the better solution "
                f"OR merge them if both have good parts.\n\n"
                f"QUESTION: {original}\n\nMODEL A:\n{r1}\n\nMODEL B:\n{r2}\n\n"
                f"Output the final best solution with a one-line note on why."
            )
        else:
            return (
                f"Two AI models answered a question differently. Evaluate both and provide "
                f"the single best answer.\n\n"
                f"QUESTION: {original}\n\nMODEL A:\n{r1}\n\nMODEL B:\n{r2}\n\n"
                f"Output the final, best answer with a one-line note on why it's superior."
            )


# ── Dashboard Window ─────────────────────────────────────────────────────────
class DashboardWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("DUAL CORE — Live Dashboard")
        
        # Restore saved geometry or use default
        saved_geom = load_window_geometry("dashboard")
        if saved_geom:
            self.geometry(saved_geom)
        else:
            self.geometry("900x600")
        
        self.minsize(600, 400)
        self.configure(bg=BG)
        self.resizable(True, True)
        
        # Data references
        self.alpha_confidence = tk.DoubleVar(value=0)
        self.beta_confidence = tk.DoubleVar(value=0)
        self.alpha_tokens = tk.IntVar(value=0)
        self.beta_tokens = tk.IntVar(value=0)
        self.consensus_quality = tk.DoubleVar(value=0)
        self.is_running = tk.BooleanVar(value=False)
        
        # Tracking for additional metrics
        self.run_start_time = None
        self.run_mode = "—"
        self.model_alpha = "—"
        self.model_beta = "—"
        
        # Interpolation values for smooth needle movement
        self.alpha_display = 0
        self.beta_display = 0
        self.consensus_display = 0
        
        self._build_dashboard()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
    def _build_dashboard(self):
        main = tk.Frame(self, bg=BG)
        main.pack(fill="both", expand=True, padx=20, pady=20)
        main.grid_rowconfigure(1, weight=1)
        main.grid_columnconfigure(0, weight=1)
        main.grid_columnconfigure(1, weight=1)
        
        # Title
        title = tk.Label(main, text="LIVE METRICS", bg=BG, fg=ACCENT1,
                        font=("Courier New", 18, "bold"))
        title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 20))
        
        # Gauges
        left_frame = tk.Frame(main, bg=BG)
        left_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        
        right_frame = tk.Frame(main, bg=BG)
        right_frame.grid(row=1, column=1, sticky="nsew", padx=(10, 0))
        
        # Alpha gauge
        self.alpha_gauge = self._create_gauge(left_frame, "ALPHA", ACCENT1)
        # Beta gauge
        self.beta_gauge = self._create_gauge(left_frame, "BETA", ACCENT2)
        # Consensus gauge
        self.consensus_gauge = self._create_gauge(right_frame, "CONSENSUS", ACCENT3)
        
        # Stats panel
        stats_frame = tk.Frame(main, bg=SURFACE)
        stats_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(20, 0))
        stats_frame.grid_columnconfigure(0, weight=1)
        
        # Row 1: Mode, Models, Delta
        row1 = tk.Frame(stats_frame, bg=SURFACE)
        row1.pack(fill="x", padx=10, pady=5)
        tk.Label(row1, text="Mode:", bg=SURFACE, fg=TEXT, font=("Courier New", 9)).pack(side="left")
        self.mode_label = tk.Label(row1, text="—", bg=SURFACE, fg=ACCENT1, font=("Courier New", 10, "bold"))
        self.mode_label.pack(side="left", padx=5)
        
        tk.Label(row1, text=" | Models:", bg=SURFACE, fg=TEXT, font=("Courier New", 9)).pack(side="left", padx=(10, 0))
        self.models_label = tk.Label(row1, text="— vs —", bg=SURFACE, fg=TEXT, font=("Courier New", 9))
        self.models_label.pack(side="left", padx=5)
        
        tk.Label(row1, text=" | Delta:", bg=SURFACE, fg=TEXT, font=("Courier New", 9)).pack(side="left", padx=(10, 0))
        self.delta_label = tk.Label(row1, text="—", bg=SURFACE, fg=MUTED, font=("Courier New", 10, "bold"))
        self.delta_label.pack(side="left", padx=5)
        
        # Row 2: Tokens, Speed, Time
        row2 = tk.Frame(stats_frame, bg=SURFACE)
        row2.pack(fill="x", padx=10, pady=5)
        tk.Label(row2, text="Tokens:", bg=SURFACE, fg=TEXT, font=("Courier New", 9)).pack(side="left")
        tk.Label(row2, text="α:", bg=SURFACE, fg=ACCENT1, font=("Courier New", 9)).pack(side="left", padx=(5, 0))
        tk.Label(row2, textvariable=self.alpha_tokens, bg=SURFACE, fg=ACCENT1, font=("Courier New", 10, "bold")).pack(side="left")
        
        tk.Label(row2, text=" | β:", bg=SURFACE, fg=ACCENT2, font=("Courier New", 9)).pack(side="left", padx=(10, 0))
        tk.Label(row2, textvariable=self.beta_tokens, bg=SURFACE, fg=ACCENT2, font=("Courier New", 10, "bold")).pack(side="left")
        
        tk.Label(row2, text=" | Speed:", bg=SURFACE, fg=TEXT, font=("Courier New", 9)).pack(side="left", padx=(10, 0))
        self.speed_label = tk.Label(row2, text="—", bg=SURFACE, fg=ACCENT3, font=("Courier New", 10, "bold"))
        self.speed_label.pack(side="left", padx=5)
        
        tk.Label(row2, text="Elapsed:", bg=SURFACE, fg=TEXT, font=("Courier New", 9)).pack(side="left", padx=(10, 0))
        self.elapsed_label = tk.Label(row2, text="—", bg=SURFACE, fg=MUTED, font=("Courier New", 10, "bold"))
        self.elapsed_label.pack(side="left", padx=5)
        
        self.status_label = tk.Label(stats_frame, text="Status: Ready", bg=SURFACE, fg=MUTED,
                         font=("Courier New", 9), anchor="e")
        self.status_label.pack(side="right", padx=10, pady=8)
        
        # Start update loop
        self._update_gauges()
        
    def _create_gauge(self, parent, label, color):
        """Create a compact digital gauge display"""
        frame = tk.Frame(parent, bg=BG)
        frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        # Title
        tk.Label(frame, text=label, bg=BG, fg=color,
                font=("Courier New", 10, "bold"), anchor="center").pack(fill="x", pady=(0, 8))
        
        # Digital display box (compact)
        display_frame = tk.Frame(frame, bg=SURFACE, relief="flat", bd=0, height=90)
        display_frame.pack(fill="x", padx=2, pady=3)
        display_frame.pack_propagate(False)
        
        # Percentage number (smaller, professional size)
        value_label = tk.Label(display_frame, text="0%", bg=SURFACE, fg=color,
                              font=("Courier New", 40, "bold"), anchor="center")
        value_label.pack(fill="both", expand=True, pady=5)
        
        return {"label": value_label, "frame": display_frame, "color": color, "value": 0}
        
    def _update_display_value(self, gauge, value, color):
        """Update digital gauge display"""
        gauge["label"].config(text=f"{int(value)}%", fg=color)
        # Color the background based on value
        if value < 33:
            bg_color = SURFACE  # Neutral
        elif value < 66:
            bg_color = "#3d5c2e"  # Greenish
        else:
            bg_color = "#1a4d2e"  # Darker green
        gauge["frame"].config(bg=bg_color)
        gauge["label"].config(bg=bg_color)
        

    def update_metrics(self, alpha_conf, beta_conf, alpha_tok, beta_tok, consensus_qual, running, mode=None, mdl1=None, mdl2=None):
        """Called from main app to update dashboard"""
        self.alpha_confidence.set(alpha_conf)
        self.beta_confidence.set(beta_conf)
        self.alpha_tokens.set(alpha_tok)
        self.beta_tokens.set(beta_tok)
        self.consensus_quality.set(consensus_qual)
        
        # Track if this is the start of a new run
        was_running = self.is_running.get()
        self.is_running.set(running)
        
        # Initialize start time on run start
        if running and not was_running:
            self.run_start_time = time.time()
        
        # Update mode and model names if provided
        if mode:
            self.run_mode = mode
        if mdl1:
            self.model_alpha = mdl1.split(":")[-1] if ":" in mdl1 else mdl1  # Extract version if present
        if mdl2:
            self.model_beta = mdl2.split(":")[-1] if ":" in mdl2 else mdl2
        
    def _update_gauges(self):
        try:
            if not self.winfo_exists():
                return
                
            # Get target values
            target_alpha = self.alpha_confidence.get()
            target_beta = self.beta_confidence.get()
            target_consensus = self.consensus_quality.get()
            
            # Smooth interpolation (easing towards target)
            ease_factor = 0.2
            self.alpha_display += (target_alpha - self.alpha_display) * ease_factor
            self.beta_display += (target_beta - self.beta_display) * ease_factor
            self.consensus_display += (target_consensus - self.consensus_display) * ease_factor
            
            # Update digital gauges
            self._update_display_value(self.alpha_gauge, self.alpha_display, ACCENT1)
            self._update_display_value(self.beta_gauge, self.beta_display, ACCENT2)
            self._update_display_value(self.consensus_gauge, self.consensus_display, ACCENT3)
            
            # Update mode label
            self.mode_label.config(text=self.run_mode or "—")
            
            # Update model names
            models = f"{self.model_alpha} vs {self.model_beta}"
            self.models_label.config(text=models)
            
            # Calculate and update delta
            alpha_val = self.alpha_confidence.get()
            beta_val = self.beta_confidence.get()
            delta = alpha_val - beta_val
            delta_color = ACCENT1 if delta > 0 else (ACCENT2 if delta < 0 else MUTED)
            self.delta_label.config(text=f"{delta:+.0f}%", fg=delta_color)
            
            # Calculate and update elapsed time and speed
            if self.is_running.get() and self.run_start_time:
                elapsed_sec = time.time() - self.run_start_time
                total_tokens = self.alpha_tokens.get() + self.beta_tokens.get()
                speed = total_tokens / elapsed_sec if elapsed_sec > 0 else 0
                
                # Format elapsed time
                mins = int(elapsed_sec) // 60
                secs = int(elapsed_sec) % 60
                elapsed_str = f"{mins}:{secs:02d}"
                self.elapsed_label.config(text=elapsed_str)
                
                # Format speed
                self.speed_label.config(text=f"{speed:.1f} tk/s")
            else:
                self.elapsed_label.config(text="—")
                self.speed_label.config(text="—")
            
            # Update status
            status = "RUNNING" if self.is_running.get() else "READY"
            status_color = ACCENT1 if self.is_running.get() else MUTED
            self.status_label.config(text=f"Status: {status}", fg=status_color)
            
            # Schedule next update
            self.after(40, self._update_gauges)
        except Exception as e:
            # Silently catch errors to prevent freezing
            pass

            
    def _on_close(self):
        try:
            # Save window geometry before closing
            save_window_geometry("dashboard", self.geometry())
            self.destroy()
        except:
            pass


# ── Model Settings Window ──────────────────────────────────────────────────────
class ModelSettingsWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("MODEL SETTINGS")
        
        # Restore saved geometry or use default
        saved_geom = load_window_geometry("model_settings")
        if saved_geom:
            self.geometry(saved_geom)
        else:
            self.geometry("1000x700")
        
        self.minsize(800, 500)
        self.configure(bg=BG)
        self.resizable(True, True)
        
        self.alpha_url = parent.url1.get()
        self.beta_url = parent.url2.get()
        self.selected_model = None
        self.pull_thread = None
        
        self._build_window()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._load_models()
        
    def _build_window(self):
        """Build the settings window UI"""
        main = tk.Frame(self, bg=BG)
        main.pack(fill="both", expand=True, padx=15, pady=15)
        main.grid_rowconfigure(1, weight=1)
        main.grid_columnconfigure(0, weight=1)
        
        # Title
        title = tk.Label(main, text="MODEL MANAGER", bg=BG, fg=ACCENT1,
                        font=("Courier New", 18, "bold"))
        title.grid(row=0, column=0, sticky="w", pady=(0, 15))
        
        # Control panel
        ctrl_frame = tk.Frame(main, bg=SURFACE, relief="flat", bd=1, 
                             highlightthickness=1, highlightbackground=BORDER)
        ctrl_frame.grid(row=1, column=0, sticky="nsew")
        ctrl_frame.grid_rowconfigure(1, weight=1)
        ctrl_frame.grid_columnconfigure(0, weight=1)
        
        # Search/Filter bar
        search_frame = tk.Frame(ctrl_frame, bg=SURFACE)
        search_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        search_frame.grid_columnconfigure(1, weight=1)
        
        tk.Label(search_frame, text="🔍 Search:", bg=SURFACE, fg=MUTED,
                font=("Courier New", 9)).pack(side="left", padx=(0, 5))
        
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *args: self._filter_models())
        search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                               bg="#010409", fg=TEXT, insertbackground=TEXT,
                               font=("Courier New", 10), relief="flat", bd=1,
                               highlightthickness=1, highlightbackground=BORDER)
        search_entry.pack(side="left", fill="x", expand=True, padx=(0, 15))
        
        # Pull model button
        tk.Button(search_frame, text="📥  PULL NEW MODEL",
                 bg=ACCENT2, fg="#000", activebackground="#ff8555",
                 font=("Courier New", 10, "bold"), bd=0, relief="flat",
                 cursor="hand2", padx=10, pady=5,
                 command=self._show_pull_dialog).pack(side="left", padx=(0, 5))
        
        # Refresh button
        tk.Button(search_frame, text="🔄 REFRESH",
                 bg=ACCENT3, fg="#000", activebackground="#6dd5ff",
                 font=("Courier New", 10, "bold"), bd=0, relief="flat",
                 cursor="hand2", padx=10, pady=5,
                 command=self._load_models).pack(side="left")
        
        # Quick pull section
        quick_pull_frame = tk.Frame(ctrl_frame, bg=SURFACE)
        quick_pull_frame.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=10)
        quick_pull_frame.grid_columnconfigure(1, weight=1)
        
        tk.Label(quick_pull_frame, text="Quick Pull:", bg=SURFACE, fg=MUTED,
                font=("Courier New", 9)).grid(row=0, column=0, sticky="w", padx=(0, 8))
        
        self.pull_model_entry = tk.Entry(quick_pull_frame, bg="#010409", fg=TEXT, 
                                        insertbackground=TEXT, font=("Courier New", 10),
                                        relief="flat", bd=1, highlightthickness=1,
                                        highlightbackground=BORDER)
        self.pull_model_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8))
        self.pull_model_entry.insert(0, "deepseek-coder")
        
        self.pull_server_var = tk.StringVar(value="Alpha")
        server_combo = ttk.Combobox(quick_pull_frame, textvariable=self.pull_server_var,
                                   values=["Alpha", "Beta"], state="readonly",
                                   font=("Courier New", 9), width=8, style="TCombobox")
        server_combo.grid(row=0, column=2, sticky="ew", padx=(0, 8))
        
        tk.Button(quick_pull_frame, text="📥 PULL",
                 bg=ACCENT2, fg="#000", activebackground="#ff8555",
                 font=("Courier New", 10, "bold"), bd=0, relief="flat",
                 cursor="hand2", padx=10, pady=5,
                 command=self._quick_pull).grid(row=0, column=3, sticky="ew")
        
        # Models list
        list_frame = tk.Frame(ctrl_frame, bg=SURFACE)
        list_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=(0, 10))
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        tk.Label(list_frame, text="Available Models:", bg=SURFACE, fg=MUTED,
                font=("Courier New", 9)).pack(anchor="w", pady=(0, 5))
        
        # Treeview for models
        tree_frame = tk.Frame(list_frame, bg=SURFACE)
        tree_frame.pack(fill="both", expand=True)
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        self.tree = ttk.Treeview(tree_frame, height=12, columns=("server", "size", "modified"),
                                 show="tree headings", style="Treeview")
        self.tree.column("#0", width=250, anchor="w")
        self.tree.column("server", width=100, anchor="center")
        self.tree.column("size", width=120, anchor="center")
        self.tree.column("modified", width=200, anchor="w")
        
        self.tree.heading("#0", text="Model Name")
        self.tree.heading("server", text="Server")
        self.tree.heading("size", text="Size")
        self.tree.heading("modified", text="Modified")
        
        # Style treeview
        s = ttk.Style()
        s.configure("Treeview", background=SURFACE, foreground=TEXT,
                   fieldbackground=SURFACE, borderwidth=0, relief="flat",
                   font=("Courier New", 9))
        s.configure("Treeview.Heading", background=SURFACE2, foreground=MUTED,
                   font=("Courier New", 9, "bold"), borderwidth=0, relief="flat")
        s.map("Treeview", background=[("selected", ACCENT1)],
              foreground=[("selected", "#000")])
        
        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(fill="both", expand=True, side="left")
        
        self.tree.bind("<<TreeviewSelect>>", self._on_model_select)
        
        # Details panel
        details_frame = tk.Frame(main, bg=SURFACE, relief="flat", bd=1,
                                highlightthickness=1, highlightbackground=BORDER)
        details_frame.grid(row=2, column=0, sticky="ew", pady=(15, 0))
        details_frame.grid_columnconfigure(0, weight=1)
        
        tk.Label(details_frame, text="Model Details & Configuration", bg=SURFACE, fg=MUTED,
                font=("Courier New", 9, "bold")).pack(anchor="w", padx=10, pady=(8, 5))
        
        self.details_var = tk.StringVar(value="Select a model to view details")
        details_label = tk.Label(details_frame, textvariable=self.details_var, 
                                bg=SURFACE, fg=TEXT, font=("Courier New", 9),
                                justify="left", wraplength=800)
        details_label.pack(anchor="w", padx=10, pady=(0, 8))
        
        # Model actions
        actions_frame = tk.Frame(details_frame, bg=SURFACE)
        actions_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        tk.Button(actions_frame, text="Remove Model", bg=ERROR, fg="#fff",
                 activebackground="#ff6666", font=("Courier New", 9),
                 bd=0, relief="flat", cursor="hand2",
                 command=self._remove_model).pack(side="left", padx=(0, 5))
        
        tk.Button(actions_frame, text="Show Info", bg=ACCENT3, fg="#000",
                 activebackground="#6dd5ff", font=("Courier New", 9),
                 bd=0, relief="flat", cursor="hand2",
                 command=self._show_model_info).pack(side="left", padx=(0, 5))
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        tk.Label(details_frame, textvariable=self.status_var, bg=SURFACE, fg=MUTED,
                font=("Courier New", 8)).pack(anchor="e", padx=10, pady=(5, 10))
        
    def _load_models(self):
        """Load models from both servers"""
        def fetch_models():
            self.tree.delete(*self.tree.get_children())
            all_models = []
            
            # Fetch from alpha server
            try:
                success, models = test_connection(self.alpha_url)
                if success:
                    for model in models:
                        all_models.append({"name": model, "server": "Alpha", "url": self.alpha_url})
            except:
                pass
            
            # Fetch from beta server
            try:
                success, models = test_connection(self.beta_url)
                if success:
                    for model in models:
                        all_models.append({"name": model, "server": "Beta", "url": self.beta_url})
            except:
                pass
            
            # Populate treeview
            self.all_models = all_models
            self._filter_models()
            
            if all_models:
                self._set_status(f"Loaded {len(all_models)} models")
            else:
                self._set_status("No models found")
        
        self._set_status("Loading models...")
        threading.Thread(target=fetch_models, daemon=True).start()
        
    def _filter_models(self):
        """Filter models based on search text"""
        self.tree.delete(*self.tree.get_children())
        search_text = self.search_var.get().lower()
        
        for model_info in self.all_models:
            name = model_info["name"]
            if search_text and search_text not in name.lower():
                continue
            
            # Get model size (extract from name or API)
            size_str = "—"
            modified_str = "—"
            
            self.tree.insert("", "end", values=(model_info["server"], size_str, modified_str),
                           text=name)
        
    def _on_model_select(self, event):
        """Handle model selection"""
        selection = self.tree.selection()
        if selection:
            item_id = selection[0]
            model_name = self.tree.item(item_id, "text")
            self.selected_model = model_name
            self._show_model_details(model_name)
        
    def _show_model_details(self, model_name):
        """Display details for selected model"""
        details_text = f"Model: {model_name}\n\n"
        details_text += "Parameters: Temperature, Context Length, Top-P, etc.\n"
        details_text += "Fine-tuning available for custom training\n"
        details_text += "Use 'Show Info' for full model details"
        
        self.details_var.set(details_text)
        
    def _show_model_info(self):
        """Show full model information"""
        if not self.selected_model:
            messagebox.showwarning("Select Model", "Please select a model first")
            return
        
        info = f"Model: {self.selected_model}\n\n"
        info += "Model Information:\n"
        info += "• Type: Large Language Model\n"
        info += "• Format: GGUF (quantized)\n"
        info += "• Status: Ready for inference\n\n"
        info += "Fine-tuning Options:\n"
        info += "• Custom training data\n"
        info += "• Adapter parameters\n"
        info += "• Response formatting\n"
        
        messagebox.showinfo("Model Information", info)
        
    def _show_pull_dialog(self):
        """Show dialog to pull a new model"""
        dialog = tk.Toplevel(self)
        dialog.title("Pull Model from Ollama Hub")
        dialog.geometry("500x250")
        dialog.configure(bg=BG)
        dialog.minsize(400, 200)
        
        # Ensure dialog stays on top
        dialog.transient(self)
        dialog.grab_set()
        
        frame = tk.Frame(dialog, bg=BG)
        frame.pack(fill="both", expand=True, padx=15, pady=15)
        frame.grid_rowconfigure(3, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        tk.Label(frame, text="Popular Models on Ollama Hub:", bg=BG, fg=TEXT,
                font=("Courier New", 10, "bold")).grid(row=0, column=0, columnspan=2, 
                                                       sticky="w", pady=(0, 10))
        
        models = [
            ("deepseek-coder", "Fast, code-focused model"),
            ("mistral", "General purpose, fast"),
            ("neural-chat", "Optimized for conversations"),
            ("llama2", "Meta's open LLM"),
            ("dolphin-mixtral", "Reliable multi-task"),
        ]
        
        var = tk.StringVar(value=models[0][0])
        for i, (mdl_name, mdl_desc) in enumerate(models):
            tk.Radiobutton(frame, text=f"{mdl_name} - {mdl_desc}",
                          variable=var, value=mdl_name,
                          bg=BG, fg=TEXT, activebackground=SURFACE,
                          activeforeground=ACCENT1, selectcolor=SURFACE,
                          font=("Courier New", 9)).grid(row=i+1, column=0, columnspan=2,
                                                        sticky="w", pady=3)
        
        # Server selection
        server_var = tk.StringVar(value="Alpha")
        tk.Label(frame, text="Pull to:", bg=BG, fg=MUTED,
                font=("Courier New", 9)).grid(row=6, column=0, sticky="w", pady=(10, 5))
        tk.Radiobutton(frame, text="Alpha Server", variable=server_var, value="Alpha",
                      bg=BG, fg=TEXT, activebackground=SURFACE, selectcolor=SURFACE,
                      font=("Courier New", 9)).grid(row=7, column=0, sticky="w")
        tk.Radiobutton(frame, text="Beta Server", variable=server_var, value="Beta",
                      bg=BG, fg=TEXT, activebackground=SURFACE, selectcolor=SURFACE,
                      font=("Courier New", 9)).grid(row=7, column=1, sticky="w")
        
        btn_frame = tk.Frame(frame, bg=BG)
        btn_frame.grid(row=8, column=0, columnspan=2, sticky="ew", pady=(15, 0))
        
        def do_pull():
            model_name = var.get()
            server = server_var.get()
            url = self.alpha_url if server == "Alpha" else self.beta_url
            self._pull_model(model_name, url, dialog)
        
        tk.Button(btn_frame, text="✓ PULL", bg=ACCENT1, fg="#000",
                 activebackground="#00cc6a", font=("Courier New", 11, "bold"),
                 bd=0, relief="flat", cursor="hand2", padx=20, pady=8,
                 command=do_pull).pack(side="left", padx=(0, 5))
        
        tk.Button(btn_frame, text="✕ CANCEL", bg=SURFACE2, fg=MUTED,
                 activebackground=SURFACE, font=("Courier New", 10),
                 bd=0, relief="flat", cursor="hand2", padx=20, pady=8,
                 command=dialog.destroy).pack(side="left")
        
    def _quick_pull(self):
        """Pull model directly from quick pull entry"""
        model_name = self.pull_model_entry.get().strip()
        if not model_name:
            messagebox.showwarning("Empty Model", "Please enter a model name")
            return
        
        url = self.alpha_url if self.pull_server_var.get() == "Alpha" else self.beta_url
        
        def pull_thread():
            self._set_status(f"Pulling {model_name}...")
            try:
                resp = requests.post(f"{url}/api/pull",
                                   json={"name": model_name},
                                   stream=True, timeout=3600)
                resp.raise_for_status()
                
                for line in resp.iter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            status = data.get("status", "")
                            if "downloading" in status.lower() or "pulling" in status.lower():
                                self._set_status(f"Pulling {model_name}: {status}")
                        except:
                            pass
                
                self._set_status(f"✓ Successfully pulled {model_name}")
                self.after(500, self._load_models)
                messagebox.showinfo("Success", f"Model '{model_name}' pulled successfully!")
                self.pull_model_entry.delete(0, "end")
                self.pull_model_entry.insert(0, "deepseek-coder")
                
            except requests.exceptions.ConnectionError:
                self._set_status(f"✗ Failed to connect to {self.pull_server_var.get()} server")
                messagebox.showerror("Connection Error", f"Cannot connect to {self.pull_server_var.get()} server at {url}")
            except Exception as e:
                self._set_status(f"✗ Pull failed: {str(e)}")
                messagebox.showerror("Pull Error", f"Failed to pull model: {str(e)}")
        
        self.pull_thread = threading.Thread(target=pull_thread, daemon=True)
        self.pull_thread.start()
        
    def _pull_model(self, model_name, url, dialog):
        """Pull model from Ollama Hub"""
        def pull_thread():
            self._set_status(f"Pulling {model_name}...")
            try:
                resp = requests.post(f"{url}/api/pull",
                                   json={"name": model_name},
                                   stream=True, timeout=3600)
                resp.raise_for_status()
                
                for line in resp.iter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            status = data.get("status", "")
                            digest = data.get("digest", "")
                            
                            # Update status
                            if "downloading" in status.lower():
                                self._set_status(f"Pulling {model_name}: {status}")
                        except:
                            pass
                
                self._set_status(f"✓ Successfully pulled {model_name}")
                self.after(500, self._load_models)
                dialog.destroy()
                messagebox.showinfo("Success", f"Model '{model_name}' pulled successfully!\n\nRefresh to see it in the list.")
                
            except Exception as e:
                self._set_status(f"✗ Pull failed: {str(e)}")
                messagebox.showerror("Pull Error", f"Failed to pull model: {str(e)}")
        
        self.pull_thread = threading.Thread(target=pull_thread, daemon=True)
        self.pull_thread.start()
        
    def _remove_model(self):
        """Remove selected model"""
        if not self.selected_model:
            messagebox.showwarning("Select Model", "Please select a model first")
            return
        
        if messagebox.askyesno("Confirm", f"Remove model '{self.selected_model}'?"):
            # TODO: Implement actual removal via Ollama API
            messagebox.showinfo("Info", "Model removal would be implemented here")
            
    def _set_status(self, msg):
        """Update status message"""
        self.after(0, lambda: self.status_var.set(msg))
        
    def _on_close(self):
        """Handle window close"""
        try:
            # Save window geometry before closing
            save_window_geometry("model_settings", self.geometry())
            self.destroy()
        except:
            pass


# ── Main Application ─────────────────────────────────────────────────────────
class DualCoreApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DUAL CORE — Parallel Ollama Coding Engine")
        self.configure(bg=BG)
        
        # Restore saved geometry or use default
        saved_geom = load_window_geometry("main")
        if saved_geom:
            self.geometry(saved_geom)
        else:
            self.geometry("1300x900")
        
        self.minsize(900, 700)

        self.mode = tk.StringVar(value="parallel")
        self.prompt_type = tk.StringVar(value="code")  # "code" or "general"
        self.stop_event = threading.Event()
        self.is_running = False
        self.dashboard = None
        self.settings_window = None

        self._build_styles()
        self._build_ui()
        
        # Save geometry on close
        self.protocol("WM_DELETE_WINDOW", self._on_app_close)
        
        # Auto-refresh models on startup
        self.after(500, self._refresh_models_on_startup)

    # ── Styles ───────────────────────────────────────────────────────────────
    def _build_styles(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("TFrame", background=BG)
        s.configure("Surface.TFrame", background=SURFACE)
        s.configure("TLabel", background=BG, foreground=TEXT, font=("Courier New", 10))
        s.configure("Title.TLabel", background=BG, foreground=ACCENT1,
                    font=("Courier New", 22, "bold"))
        s.configure("Sub.TLabel", background=BG, foreground=MUTED,
                    font=("Courier New", 9))
        s.configure("Card.TLabel", background=SURFACE, foreground=TEXT,
                    font=("Courier New", 10))
        s.configure("Accent1.TLabel", background=SURFACE, foreground=ACCENT1,
                    font=("Courier New", 9, "bold"))
        s.configure("Accent2.TLabel", background=SURFACE, foreground=ACCENT2,
                    font=("Courier New", 9, "bold"))
        s.configure("Accent3.TLabel", background=SURFACE, foreground=ACCENT3,
                    font=("Courier New", 11, "bold"))
        s.configure("Muted.TLabel", background=SURFACE, foreground=MUTED,
                    font=("Courier New", 9))
        s.configure("Status.TLabel", background=BG, foreground=MUTED,
                    font=("Courier New", 9))
        s.configure("TEntry", fieldbackground="#010409", foreground=TEXT,
                    bordercolor=BORDER, insertcolor=TEXT, font=("Courier New", 10))
        s.configure("TCombobox", fieldbackground=SURFACE, foreground=TEXT,
                    borderwidth=0, relief="flat", font=("Courier New", 10),
                    padding=0, arrowcolor=TEXT, background=SURFACE, 
                    darkcolor=SURFACE, lightcolor=SURFACE)
        s.map("TCombobox", 
              fieldbackground=[("readonly", SURFACE), ("focus", SURFACE)],
              background=[("readonly", SURFACE), ("focus", SURFACE)],
              foreground=[("readonly", TEXT), ("focus", TEXT)])
        s.configure("TProgressbar", troughcolor=BORDER,
                    background=ACCENT1, bordercolor=BORDER)

    # ── UI Builder ───────────────────────────────────────────────────────────
    def _build_ui(self):
        # Use grid for main layout with proper weight configuration
        self.grid_rowconfigure(0, weight=0)  # Header - fixed
        self.grid_rowconfigure(1, weight=0)  # Server config - fixed
        self.grid_rowconfigure(2, weight=0)  # Mode selector - fixed
        self.grid_rowconfigure(3, weight=0)  # Prompt - minimal
        self.grid_rowconfigure(4, weight=0)  # Status - fixed
        self.grid_rowconfigure(5, weight=1)  # Output area - fills remaining space
        self.grid_columnconfigure(0, weight=1)
        
        outer = ttk.Frame(self)
        outer.grid(row=0, column=0, rowspan=6, sticky="nsew", padx=20, pady=16)
        
        # Store references to build functions for grid placement
        header_frame = self._build_header(outer)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        
        server_frame = self._build_server_config_frame(outer)
        server_frame.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        
        mode_frame = self._build_mode_selector_frame(outer)
        mode_frame.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        
        prompt_frame = self._build_prompt_area_frame(outer)
        prompt_frame.grid(row=3, column=0, sticky="ew", pady=(0, 12))
        
        status_frame = self._build_status_bar_frame(outer)
        status_frame.grid(row=4, column=0, sticky="ew", pady=(0, 12))
        
        output_frame = self._build_output_area_frame(outer)
        output_frame.grid(row=5, column=0, sticky="nsew")
        
        outer.grid_rowconfigure(5, weight=1)
        outer.grid_columnconfigure(0, weight=1)

    def _build_header(self, parent):
        f = tk.Frame(parent, bg=BG, bd=0)

        tk.Label(f, text="DUAL CORE", bg=BG, fg=ACCENT1,
                 font=("Courier New", 26, "bold")).pack(side="left")
        tk.Label(f, text="  PARALLEL OLLAMA CODING ENGINE", bg=BG, fg=MUTED,
                 font=("Courier New", 10)).pack(side="left", padx=8)

        # Status pills
        pill_frame = tk.Frame(f, bg=BG)
        pill_frame.pack(side="right")
        self.pill1 = self._pill(pill_frame, "SERVER 1", MUTED)
        self.pill1.pack(side="left", padx=4)
        self.pill2 = self._pill(pill_frame, "SERVER 2", MUTED)
        self.pill2.pack(side="left", padx=4)

        # Divider
        div = tk.Frame(f, bg=BORDER, height=1)
        div.pack(fill="x", pady=(16, 0))
        return f

    def _build_server_config_frame(self, parent):
        frame = ttk.Frame(parent)
        self._build_server_config(frame)
        return frame
    
    def _build_mode_selector_frame(self, parent):
        frame = ttk.Frame(parent)
        self._build_mode_selector(frame)
        return frame
    
    def _build_prompt_area_frame(self, parent):
        frame = ttk.Frame(parent)
        self._build_prompt_area(frame)
        return frame
    
    def _build_status_bar_frame(self, parent):
        frame = ttk.Frame(parent)
        self._build_status_bar(frame)
        return frame
    
    def _build_output_area_frame(self, parent):
        frame = ttk.Frame(parent)
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        self._build_output_area(frame)
        return frame

    def _pill(self, parent, text, color):
        f = tk.Frame(parent, bg=color, bd=0)
        tk.Label(f, text=f"● {text}", bg=BG, fg=color,
                 font=("Courier New", 9), padx=10, pady=3).pack()
        return tk.Label(parent, text=f"● {text}", bg=BG, fg=color,
                        font=("Courier New", 9), relief="flat",
                        bd=1, padx=10, pady=3)

    def _set_pill(self, pill, color):
        pill.config(fg=color)

    def _build_server_config(self, parent):
        row = tk.Frame(parent, bg=BG)
        row.pack(fill="x", padx=0, pady=0)
        row.columnconfigure(0, weight=1)
        row.columnconfigure(1, weight=1)

        # Server 1
        c1 = self._card(row, border=ACCENT1)
        c1.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        tk.Label(c1, text="◈ SERVER ALPHA", bg=SURFACE, fg=ACCENT1,
                 font=("Courier New", 9, "bold")).pack(anchor="w", padx=12, pady=(10, 6))
        f1 = tk.Frame(c1, bg=SURFACE)
        f1.pack(fill="x", padx=12)
        tk.Label(f1, text="HOST URL", bg=SURFACE, fg=MUTED,
                 font=("Courier New", 8)).grid(row=0, column=0, sticky="w")
        tk.Label(f1, text="MODEL", bg=SURFACE, fg=MUTED,
                 font=("Courier New", 8)).grid(row=0, column=1, sticky="w", padx=(8, 0))
        self.url1 = self._entry(f1, "http://localhost:11434")
        self.url1.grid(row=1, column=0, sticky="ew", pady=(2, 0))
        self.model1 = self._combobox(f1, ["codellama"], "codellama")
        self.model1.grid(row=1, column=1, sticky="ew", pady=(2, 0), padx=(8, 0))
        f1.columnconfigure(0, weight=2)
        f1.columnconfigure(1, weight=1)
        self._btn(c1, "▶  TEST CONNECTION", lambda: self._test(1), MUTED).pack(
            fill="x", padx=12, pady=10)

        # Server 2
        c2 = self._card(row, border=ACCENT2)
        c2.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        tk.Label(c2, text="◈ SERVER BETA", bg=SURFACE, fg=ACCENT2,
                 font=("Courier New", 9, "bold")).pack(anchor="w", padx=12, pady=(10, 6))
        f2 = tk.Frame(c2, bg=SURFACE)
        f2.pack(fill="x", padx=12)
        tk.Label(f2, text="HOST URL", bg=SURFACE, fg=MUTED,
                 font=("Courier New", 8)).grid(row=0, column=0, sticky="w")
        tk.Label(f2, text="MODEL", bg=SURFACE, fg=MUTED,
                 font=("Courier New", 8)).grid(row=0, column=1, sticky="w", padx=(8, 0))
        self.url2 = self._entry(f2, "http://192.168.127.121:11434")
        self.url2.grid(row=1, column=0, sticky="ew", pady=(2, 0))
        self.model2 = self._combobox(f2, ["deepseek-coder"], "deepseek-coder")
        self.model2.grid(row=1, column=1, sticky="ew", pady=(2, 0), padx=(8, 0))
        f2.columnconfigure(0, weight=2)
        f2.columnconfigure(1, weight=1)
        self._btn(c2, "▶  TEST CONNECTION", lambda: self._test(2), MUTED).pack(
            fill="x", padx=12, pady=10)

    def _build_mode_selector(self, parent):
        card = self._card(parent)
        card.pack(fill="x", padx=0, pady=0)
        tk.Label(card, text="◈ CONSENSUS STRATEGY", bg=SURFACE, fg=MUTED,
                 font=("Courier New", 8, "bold")).pack(anchor="w", padx=12, pady=(10, 6))

        mf = tk.Frame(card, bg=SURFACE)
        mf.pack(fill="x", padx=12, pady=(0, 10))

        modes = [
            ("parallel", "⚡  PARALLEL", "Both run at once. Best output selected."),
            ("debate",   "⚔   DEBATE",   "Each reviews the other. Merged into final answer."),
            ("verify",   "✓   VERIFY",   "Alpha codes. Beta verifies & fixes. Final merged."),
        ]
        self.mode_btns = {}
        for val, label, desc in modes:
            f = tk.Frame(mf, bg=SURFACE2, bd=1, relief="flat",
                         highlightthickness=1, highlightbackground=BORDER)
            f.pack(side="left", expand=True, fill="x", padx=4)
            btn = tk.Button(
                f, text=f"{label}\n{desc}",
                bg=SURFACE2, fg=TEXT, activebackground=SURFACE,
                activeforeground=ACCENT1, font=("Courier New", 9),
                bd=0, relief="flat", cursor="hand2", wraplength=220,
                justify="center", pady=10,
                command=lambda v=val: self._set_mode(v)
            )
            btn.pack(fill="both", expand=True)
            self.mode_btns[val] = (f, btn)
        self._set_mode("parallel")

    def _set_mode(self, mode):
        self.mode.set(mode)
        for val, (frame, btn) in self.mode_btns.items():
            if val == mode:
                frame.config(highlightbackground=ACCENT1)
                btn.config(fg=ACCENT1, bg=SURFACE)
            else:
                frame.config(highlightbackground=BORDER)
                btn.config(fg=MUTED, bg=SURFACE2)

    def _build_prompt_area(self, parent):
        card = self._card(parent)
        card.pack(fill="x", padx=0, pady=0)
        
        # Prompt type selector
        type_frame = tk.Frame(card, bg=SURFACE)
        type_frame.pack(fill="x", padx=12, pady=(10, 8))
        tk.Label(type_frame, text="Mode:", bg=SURFACE, fg=MUTED,
                font=("Courier New", 9)).pack(side="left", padx=(0, 8))
        
        tk.Radiobutton(type_frame, text="💻 Code", variable=self.prompt_type, value="code",
                      bg=SURFACE, fg=TEXT, activebackground=SURFACE, activeforeground=ACCENT1,
                      font=("Courier New", 9), selectcolor=SURFACE).pack(side="left", padx=8)
        tk.Radiobutton(type_frame, text="❓ General", variable=self.prompt_type, value="general",
                      bg=SURFACE, fg=TEXT, activebackground=SURFACE, activeforeground=ACCENT1,
                      font=("Courier New", 9), selectcolor=SURFACE).pack(side="left", padx=8)
        
        # Prompt label
        prompt_label_text = "◈ PROMPT"
        tk.Label(card, text=prompt_label_text, bg=SURFACE, fg=MUTED,
                 font=("Courier New", 8, "bold")).pack(anchor="w", padx=12, pady=(0, 4))
        
        self.prompt_box = tk.Text(
            card, bg="#010409", fg=TEXT, insertbackground=TEXT,
            font=("Consolas", 11), relief="flat", bd=0,
            height=3, wrap="word", padx=8, pady=8,
            highlightthickness=1, highlightbackground=BORDER
        )
        self.prompt_box.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        bf = tk.Frame(card, bg=SURFACE)
        bf.pack(fill="x", padx=12, pady=(0, 10))
        self.run_btn = tk.Button(
            bf, text="▶  ENGAGE DUAL CORE",
            bg=ACCENT1, fg="#000000", activebackground="#00cc6a",
            font=("Courier New", 12, "bold"), bd=0, relief="flat",
            cursor="hand2", pady=10, command=self._run
        )
        self.run_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))
        tk.Button(
            bf, text="✕  CLEAR",
            bg=SURFACE2, fg=MUTED, activebackground=SURFACE,
            font=("Courier New", 10), bd=0, relief="flat",
            cursor="hand2", pady=10, command=self._clear,
            highlightthickness=1, highlightbackground=BORDER
        ).pack(side="left", padx=(0, 6), ipadx=20)
        tk.Button(
            bf, text="◐  DASHBOARD",
            bg=SURFACE2, fg=ACCENT3, activebackground=SURFACE,
            font=("Courier New", 10), bd=0, relief="flat",
            cursor="hand2", pady=10, command=self._toggle_dashboard,
            highlightthickness=1, highlightbackground=BORDER
        ).pack(side="left", padx=(0, 6), ipadx=20)
        tk.Button(
            bf, text="⚙  MODEL SETTINGS",
            bg=SURFACE2, fg=ACCENT2, activebackground=SURFACE,
            font=("Courier New", 10), bd=0, relief="flat",
            cursor="hand2", pady=10, command=self._toggle_settings,
            highlightthickness=1, highlightbackground=BORDER
        ).pack(side="left", padx=(0, 0), ipadx=20)

    def _build_status_bar(self, parent):
        self.status_var = tk.StringVar(value="Ready.")
        f = tk.Frame(parent, bg=SURFACE2, highlightthickness=1,
                     highlightbackground=BORDER)
        f.pack(fill="x", padx=0, pady=0)
        tk.Label(f, textvariable=self.status_var, bg=SURFACE2, fg=MUTED,
                 font=("Courier New", 9), anchor="w", padx=12, pady=6).pack(
            side="left", fill="x", expand=True)
        self.stop_btn = tk.Button(
            f, text="■  STOP", bg=SURFACE2, fg=ERROR,
            activebackground=SURFACE, font=("Courier New", 9),
            bd=0, relief="flat", cursor="hand2", padx=12,
            command=self._stop, state="disabled"
        )
        self.stop_btn.pack(side="right")

    def _build_output_area(self, parent):
        # Use PanedWindow for resizable sections
        self.paned = tk.PanedWindow(parent, orient="vertical", bg=BG, 
                               sashwidth=4, sashpad=2, relief="flat", bd=0)
        self.paned.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        
        # Score bars (non-resizable)
        sf = tk.Frame(self.paned, bg=BG, height=100)
        sf.grid_propagate(False)
        sf.columnconfigure(0, weight=1)
        sf.columnconfigure(1, weight=1)

        sc1 = self._card(sf)
        sc1.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        tk.Label(sc1, text="ALPHA CONFIDENCE", bg=SURFACE, fg=MUTED,
                 font=("Courier New", 8)).pack(anchor="w", padx=12, pady=(8, 2))
        self.score1_lbl = tk.Label(sc1, text="—", bg=SURFACE, fg=TEXT,
                                   font=("Courier New", 16, "bold"))
        self.score1_lbl.pack(anchor="w", padx=12)
        self.bar1 = ttk.Progressbar(sc1, style="TProgressbar",
                                     mode="determinate", maximum=100, value=0)
        self.bar1.pack(fill="x", padx=12, pady=(4, 10))

        sc2 = self._card(sf)
        sc2.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        tk.Label(sc2, text="BETA CONFIDENCE", bg=SURFACE, fg=MUTED,
                 font=("Courier New", 8)).pack(anchor="w", padx=12, pady=(8, 2))
        self.score2_lbl = tk.Label(sc2, text="—", bg=SURFACE, fg=TEXT,
                                   font=("Courier New", 16, "bold"))
        self.score2_lbl.pack(anchor="w", padx=12)
        self.bar2 = ttk.Progressbar(sc2, style="TProgressbar",
                                     mode="determinate", maximum=100, value=0)
        self.bar2.pack(fill="x", padx=12, pady=(4, 10))
        
        self.paned.add(sf, height=100)

        # Dual outputs (resizable)
        out_frame = tk.Frame(self.paned, bg=BG)
        out_frame.columnconfigure(0, weight=1)
        out_frame.columnconfigure(1, weight=1)
        out_frame.rowconfigure(0, weight=1)

        o1 = self._card(out_frame, border=ACCENT1)
        o1.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        o1.grid_rowconfigure(3, weight=1)
        hdr1 = tk.Frame(o1, bg=SURFACE)
        hdr1.pack(fill="x", padx=0)
        tk.Label(hdr1, text="◈ ALPHA OUTPUT", bg=SURFACE, fg=ACCENT1,
                 font=("Courier New", 9, "bold")).pack(side="left", padx=12, pady=8)
        self.time1_lbl = tk.Label(hdr1, text="—", bg=SURFACE, fg=MUTED,
                                   font=("Courier New", 8))
        self.time1_lbl.pack(side="right", padx=4)
        self._copy_btn(hdr1, lambda: self._copy(self.out1)).pack(side="right", padx=4)
        tk.Frame(o1, bg=BORDER, height=1).pack(fill="x")
        self.out1 = self._output_box(o1, ACCENT1, height=0)

        o2 = self._card(out_frame, border=ACCENT2)
        o2.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        o2.grid_rowconfigure(3, weight=1)
        hdr2 = tk.Frame(o2, bg=SURFACE)
        hdr2.pack(fill="x")
        tk.Label(hdr2, text="◈ BETA OUTPUT", bg=SURFACE, fg=ACCENT2,
                 font=("Courier New", 9, "bold")).pack(side="left", padx=12, pady=8)
        self.time2_lbl = tk.Label(hdr2, text="—", bg=SURFACE, fg=MUTED,
                                   font=("Courier New", 8))
        self.time2_lbl.pack(side="right", padx=4)
        self._copy_btn(hdr2, lambda: self._copy(self.out2)).pack(side="right", padx=4)
        tk.Frame(o2, bg=BORDER, height=1).pack(fill="x")
        self.out2 = self._output_box(o2, ACCENT2, height=0)
        
        self.paned.add(out_frame, sticky="nsew")

        # Consensus (resizable)
        con = self._card(self.paned, border=ACCENT3)
        con.grid_rowconfigure(3, weight=1)
        hdr_c = tk.Frame(con, bg=SURFACE)
        hdr_c.pack(fill="x")
        tk.Label(hdr_c, text="◈ CONSENSUS OUTPUT", bg=SURFACE, fg=ACCENT3,
                 font=("Courier New", 10, "bold")).pack(side="left", padx=12, pady=10)
        tk.Label(hdr_c, text="VERIFIED", bg="#0a1a22", fg=ACCENT3,
                 font=("Courier New", 8), padx=8, pady=2,
                 relief="flat").pack(side="left")
        self._copy_btn(hdr_c, lambda: self._copy(self.con_out)).pack(side="right", padx=12)
        tk.Frame(con, bg=BORDER, height=1).pack(fill="x")
        self.con_out = self._output_box(con, ACCENT3, height=0)
        
        self.paned.add(con, sticky="nsew")
        
        # Store reference to last sash positions for change detection
        self._last_sash_positions = None
        self._restore_attempts = 0
        
        # Restore sash positions with multiple aggressive attempts
        self.paned.update_idletasks()  # Force immediate layout
        self._restore_sash_positions()  # Try immediately
        self.after(10, self._restore_sash_positions)  # Try very soon
        self.after(50, self._restore_sash_positions)   # Try soon
        self.after(150, self._restore_sash_positions)  # Try later
        
        # Bind to paned window configuration events for restoration
        self.paned.bind("<Configure>", self._on_paned_configure)
        
        # Start periodic sash position monitoring (with initial delay)
        self.after(500, self._monitor_sash_positions)

    # ── Widget helpers ────────────────────────────────────────────────────────
    def _card(self, parent, border=BORDER):
        f = tk.Frame(parent, bg=SURFACE, highlightthickness=1,
                     highlightbackground=border)
        return f

    def _entry(self, parent, default=""):
        e = tk.Entry(parent, bg="#010409", fg=TEXT, insertbackground=TEXT,
                     font=("Courier New", 10), relief="flat", bd=4,
                     highlightthickness=1, highlightbackground=BORDER)
        e.insert(0, default)
        return e

    def _combobox(self, parent, values=None, default=""):
        cb = ttk.Combobox(parent, values=values or [], state="readonly",
                         font=("Courier New", 10), style="TCombobox")
        cb.set(default if default in (values or []) else (values[0] if values else ""))
        return cb

    def _btn(self, parent, text, cmd, color=ACCENT1):
        return tk.Button(
            parent, text=text, bg=SURFACE2, fg=color,
            activebackground=SURFACE, activeforeground=ACCENT1,
            font=("Courier New", 9), bd=0, relief="flat",
            cursor="hand2", pady=6, command=cmd,
            highlightthickness=1, highlightbackground=BORDER
        )

    def _copy_btn(self, parent, cmd):
        return tk.Button(
            parent, text="COPY", bg=SURFACE2, fg=MUTED,
            activebackground=SURFACE, activeforeground=ACCENT1,
            font=("Courier New", 8), bd=0, relief="flat",
            cursor="hand2", padx=8, pady=2, command=cmd,
            highlightthickness=1, highlightbackground=BORDER
        )

    def _output_box(self, parent, accent, height=0):
        # If height=0, use minimal height and let it expand
        box_height = 1 if height == 0 else height
        box = tk.Text(
            parent, bg="#010409", fg=TEXT, insertbackground=TEXT,
            font=("Consolas", 10), relief="flat", bd=0,
            height=box_height, wrap="word", padx=10, pady=10,
            selectbackground=accent, selectforeground="#000"
        )
        box.pack(fill="both", expand=True, padx=0, pady=0)
        sb = tk.Scrollbar(parent, command=box.yview, bg=SURFACE,
                          troughcolor=SURFACE, bd=0, relief="flat")
        sb.pack(side="right", fill="y")
        box.config(yscrollcommand=sb.set)
        return box

    # ── Actions ───────────────────────────────────────────────────────────────
    def _test(self, num):
        url = (self.url1 if num == 1 else self.url2).get().strip()
        pill = self.pill1 if num == 1 else self.pill2
        model_box = self.model1 if num == 1 else self.model2
        self._set_pill(pill, MUTED)
        self._set_status(f"Testing Server {num}...")

        def do():
            ok, info = test_connection(url)
            if ok:
                self._set_pill(pill, ACCENT1)
                self._set_status(f"Server {num} online ✓")
                models = info if info else []
                models_str = ", ".join(models) if models else "no models pulled"
                # Update combobox with available models (must be on main thread)
                def update_ui():
                    model_box['values'] = models
                    if models:
                        model_box.set(models[0])
                self.after(0, update_ui)
                messagebox.showinfo(
                    f"Server {num} — Connected",
                    f"✓ Online!\n\nAvailable models:\n{models_str}"
                )
            else:
                self._set_pill(pill, ERROR)
                self._set_status(f"Server {num} unreachable ✗")
                messagebox.showerror(
                    f"Server {num} — Failed",
                    f"✗ Cannot connect\n\n{info}\n\n"
                    f"Make sure Ollama is running:\n  ollama serve"
                )

        threading.Thread(target=do, daemon=True).start()

    def _refresh_models_on_startup(self):
        """Auto-refresh models from both servers on startup (silent)"""
        def refresh_server(num):
            url = (self.url1 if num == 1 else self.url2).get().strip()
            model_box = self.model1 if num == 1 else self.model2
            pill = self.pill1 if num == 1 else self.pill2
            
            ok, info = test_connection(url)
            if ok:
                models = info if info else []
                def update_ui():
                    model_box['values'] = models
                    if models:
                        model_box.set(models[0])
                    # Set pill to online color
                    self._set_pill(pill, ACCENT1)
                self.after(0, update_ui)
            else:
                # Set pill to offline color on startup
                def set_offline():
                    self._set_pill(pill, ERROR)
                self.after(0, set_offline)
        
        # Refresh both servers in parallel threads
        threading.Thread(target=lambda: refresh_server(1), daemon=True).start()
        threading.Thread(target=lambda: refresh_server(2), daemon=True).start()

    def _create_dashboard_callback(self, model_type, other_metrics=None):
        """Create a callback that updates both output AND dashboard in real-time"""
        accumulated_text = [None]  # Use list to allow update in nested function
        
        def on_token(full_text):
            accumulated_text[0] = full_text
            # Calculate confidence on partial text
            conf = estimate_confidence(full_text)
            tok_count = len(full_text.split()) if full_text else 0
            
            # Update dashboard in real-time
            if self.dashboard and self.dashboard.winfo_exists():
                if model_type == "alpha":
                    metrics = {
                        "alpha_conf": conf,
                        "alpha_tok": tok_count,
                        "beta_conf": other_metrics.get("beta_conf", 0) if other_metrics else 0,
                        "beta_tok": other_metrics.get("beta_tok", 0) if other_metrics else 0,
                        "consensus_qual": 0,
                        "running": True
                    }
                elif model_type == "beta":
                    metrics = {
                        "alpha_conf": other_metrics.get("alpha_conf", 0) if other_metrics else 0,
                        "alpha_tok": other_metrics.get("alpha_tok", 0) if other_metrics else 0,
                        "beta_conf": conf,
                        "beta_tok": tok_count,
                        "consensus_qual": 0,
                        "running": True
                    }
                elif model_type == "consensus":
                    metrics = {
                        "alpha_conf": other_metrics.get("alpha_conf", 0) if other_metrics else 0,
                        "alpha_tok": other_metrics.get("alpha_tok", 0) if other_metrics else 0,
                        "beta_conf": other_metrics.get("beta_conf", 0) if other_metrics else 0,
                        "beta_tok": other_metrics.get("beta_tok", 0) if other_metrics else 0,
                        "consensus_qual": conf,
                        "running": True
                    }
                self.dashboard.update_metrics(**metrics)
        
        return on_token

    def _run(self):
        if self.is_running:
            return
        prompt = self.prompt_box.get("1.0", "end").strip()
        if not prompt:
            messagebox.showwarning("No Prompt", "Please enter a coding prompt.")
            return

        url1  = self.url1.get().strip()
        url2  = self.url2.get().strip()
        mdl1  = self.model1.get().strip()
        mdl2  = self.model2.get().strip()
        mode  = self.mode.get()

        self.is_running = True
        self.stop_event.clear()
        self.run_btn.config(state="disabled", bg=BORDER, fg=MUTED)
        self.stop_btn.config(state="normal")

        self._clear_outputs()
        self._set_out(self.out1, "Waiting for Alpha...")
        self._set_out(self.out2, "Waiting for Beta...")
        self._set_out(self.con_out, "")

        threading.Thread(
            target=self._run_thread,
            args=(url1, url2, mdl1, mdl2, prompt, mode),
            daemon=True
        ).start()

    def _run_thread(self, url1, url2, mdl1, mdl2, prompt, mode):
        result1 = result2 = None
        current_metrics = {"alpha_conf": 0, "alpha_tok": 0, "beta_conf": 0, "beta_tok": 0}

        if mode == "parallel":
            self._set_status("Running both servers in parallel...")
            r1_container, r2_container = [None], [None]

            def run1():
                # Create combined callback for output + dashboard update
                def on_token_alpha(full_text):
                    self._set_out(self.out1, full_text)
                    # Real-time dashboard update
                    conf = estimate_confidence(full_text)
                    tokens = len(full_text.split()) if full_text else 0
                    current_metrics["alpha_conf"] = conf
                    current_metrics["alpha_tok"] = tokens
                    if self.dashboard and self.dashboard.winfo_exists():
                        self.dashboard.update_metrics(
                            alpha_conf=current_metrics["alpha_conf"],
                            beta_conf=current_metrics["beta_conf"],
                            alpha_tok=current_metrics["alpha_tok"],
                            beta_tok=current_metrics["beta_tok"],
                            consensus_qual=0,
                            running=True,
                            mode=mode,
                            mdl1=mdl1,
                            mdl2=mdl2
                        )
                
                r1_container[0] = query_ollama(
                    url1, mdl1, prompt, on_token_alpha, self.stop_event
                )

            def run2():
                # Create combined callback for output + dashboard update
                def on_token_beta(full_text):
                    self._set_out(self.out2, full_text)
                    # Real-time dashboard update
                    conf = estimate_confidence(full_text)
                    tokens = len(full_text.split()) if full_text else 0
                    current_metrics["beta_conf"] = conf
                    current_metrics["beta_tok"] = tokens
                    if self.dashboard and self.dashboard.winfo_exists():
                        self.dashboard.update_metrics(
                            alpha_conf=current_metrics["alpha_conf"],
                            beta_conf=current_metrics["beta_conf"],
                            alpha_tok=current_metrics["alpha_tok"],
                            beta_tok=current_metrics["beta_tok"],
                            consensus_qual=0,
                            running=True
                        )
                
                r2_container[0] = query_ollama(
                    url2, mdl2, prompt, on_token_beta, self.stop_event
                )

            t1 = threading.Thread(target=run1, daemon=True)
            t2 = threading.Thread(target=run2, daemon=True)
            t1.start(); t2.start()
            t1.join(); t2.join()
            result1 = r1_container[0]
            result2 = r2_container[0]

        elif mode == "verify":
            self._set_status("Alpha generating code...")
            
            # Real-time callback for Alpha
            def on_token_alpha_verify(full_text):
                self._set_out(self.out1, full_text)
                conf = estimate_confidence(full_text)
                tokens = len(full_text.split()) if full_text else 0
                current_metrics["alpha_conf"] = conf
                current_metrics["alpha_tok"] = tokens
                if self.dashboard and self.dashboard.winfo_exists():
                    self.dashboard.update_metrics(
                        alpha_conf=current_metrics["alpha_conf"],
                        beta_conf=current_metrics["beta_conf"],
                        alpha_tok=current_metrics["alpha_tok"],
                        beta_tok=current_metrics["beta_tok"],
                        consensus_qual=0,
                        running=True,
                        mode=mode,
                        mdl1=mdl1,
                        mdl2=mdl2
                    )
            
            result1 = query_ollama(
                url1, mdl1, prompt, on_token_alpha_verify, self.stop_event
            )
            if result1["error"]:
                self._set_out(self.out1, f"ERROR: {result1['error']}")

            prompt_type = self.prompt_type.get()
            if prompt_type == "code":
                self._set_status("Beta verifying Alpha's code...")
                verify_prompt = (
                    f"You are a strict code reviewer. Review and improve the following solution.\n\n"
                    f"ORIGINAL REQUEST: {prompt}\n\n"
                    f"ALPHA'S CODE:\n{result1['text']}\n\n"
                    f"Provide a corrected, improved version. Fix any bugs. "
                    f"If already correct, confirm briefly."
                )
            else:
                self._set_status("Beta refining Alpha's answer...")
                verify_prompt = (
                    f"You are a thoughtful expert. Review and refine the following answer.\n\n"
                    f"ORIGINAL QUESTION: {prompt}\n\n"
                    f"ALPHA'S ANSWER:\n{result1['text']}\n\n"
                    f"Provide a refined answer that's more complete, accurate, or well-explained. "
                    f"If already excellent, confirm briefly."
                )
            
            # Real-time callback for Beta
            def on_token_beta_verify(full_text):
                self._set_out(self.out2, full_text)
                conf = estimate_confidence(full_text)
                tokens = len(full_text.split()) if full_text else 0
                current_metrics["beta_conf"] = conf
                current_metrics["beta_tok"] = tokens
                if self.dashboard and self.dashboard.winfo_exists():
                    self.dashboard.update_metrics(
                        alpha_conf=current_metrics["alpha_conf"],
                        beta_conf=current_metrics["beta_conf"],
                        alpha_tok=current_metrics["alpha_tok"],
                        beta_tok=current_metrics["beta_tok"],
                        consensus_qual=0,
                        running=True,
                        mode=mode,
                        mdl1=mdl1,
                        mdl2=mdl2
                    )
            
            result2 = query_ollama(
                url2, mdl2, verify_prompt, on_token_beta_verify, self.stop_event
            )

        elif mode == "debate":
            self._set_status("Running initial parallel generation...")
            r1_container, r2_container = [None], [None]

            def run1():
                # Real-time callback for Alpha
                def on_token_alpha_debate(full_text):
                    self._set_out(self.out1, full_text)
                    conf = estimate_confidence(full_text)
                    tokens = len(full_text.split()) if full_text else 0
                    current_metrics["alpha_conf"] = conf
                    current_metrics["alpha_tok"] = tokens
                    if self.dashboard and self.dashboard.winfo_exists():
                        self.dashboard.update_metrics(
                            alpha_conf=current_metrics["alpha_conf"],
                            beta_conf=current_metrics["beta_conf"],
                            alpha_tok=current_metrics["alpha_tok"],
                            beta_tok=current_metrics["beta_tok"],
                            consensus_qual=0,
                            running=True,
                            mode=mode,
                            mdl1=mdl1,
                            mdl2=mdl2
                        )
                
                r1_container[0] = query_ollama(
                    url1, mdl1, prompt, on_token_alpha_debate, self.stop_event
                )

            def run2():
                # Real-time callback for Beta
                def on_token_beta_debate(full_text):
                    self._set_out(self.out2, full_text)
                    conf = estimate_confidence(full_text)
                    tokens = len(full_text.split()) if full_text else 0
                    current_metrics["beta_conf"] = conf
                    current_metrics["beta_tok"] = tokens
                    if self.dashboard and self.dashboard.winfo_exists():
                        self.dashboard.update_metrics(
                            alpha_conf=current_metrics["alpha_conf"],
                            beta_conf=current_metrics["beta_conf"],
                            alpha_tok=current_metrics["alpha_tok"],
                            beta_tok=current_metrics["beta_tok"],
                            consensus_qual=0,
                            running=True
                        )
                
                r2_container[0] = query_ollama(
                    url2, mdl2, prompt, on_token_beta_debate, self.stop_event
                )

            t1 = threading.Thread(target=run1, daemon=True)
            t2 = threading.Thread(target=run2, daemon=True)
            t1.start(); t2.start()
            t1.join(); t2.join()
            result1 = r1_container[0]
            result2 = r2_container[0]

        if self.stop_event.is_set():
            self._set_status("Stopped.")
            self._finish()
            return

        # Update score labels and progress bars (UI only, metrics already updated real-time)
        if result1:
            self.time1_lbl.config(text=result1["elapsed"])
            c1 = estimate_confidence(result1["text"])
            self.score1_lbl.config(text=f"{c1}%")
            self.bar1["value"] = c1

        if result2:
            self.time2_lbl.config(text=result2["elapsed"])
            c2 = estimate_confidence(result2["text"])
            self.score2_lbl.config(text=f"{c2}%")
            self.bar2["value"] = c2

        # Errors
        if result1 and result1["error"]:
            self._set_out(self.out1, f"⚠ {result1['error']}")
        if result2 and result2["error"]:
            self._set_out(self.out2, f"⚠ {result2['error']}")

        # Consensus
        if result1 and result2 and result1["text"] and result2["text"]:
            self._set_status("Building consensus...")
            prompt_type = self.prompt_type.get()
            con_prompt = build_consensus_prompt(
                prompt, result1["text"], result2["text"], mode, prompt_type
            )
            
            # Real-time callback for Consensus
            def on_token_consensus(full_text):
                self._set_out(self.con_out, full_text)
                conf = estimate_confidence(full_text)
                if self.dashboard and self.dashboard.winfo_exists():
                    self.dashboard.update_metrics(
                        alpha_conf=current_metrics["alpha_conf"],
                        beta_conf=current_metrics["beta_conf"],
                        alpha_tok=current_metrics["alpha_tok"],
                        beta_tok=current_metrics["beta_tok"],
                        consensus_qual=conf,
                        running=True
                    )
            
            con_result = query_ollama(
                url1, mdl1, con_prompt, on_token_consensus, self.stop_event
            )
            if con_result["error"]:
                # Fallback: pick higher confidence
                c1 = estimate_confidence(result1["text"])
                c2 = estimate_confidence(result2["text"])
                best = result1["text"] if c1 >= c2 else result2["text"]
                self._set_out(self.con_out, best)
            else:
                # Consensus complete - update dashboard to mark as done
                if self.dashboard and self.dashboard.winfo_exists():
                    self.dashboard.update_metrics(
                        alpha_conf=current_metrics["alpha_conf"],
                        beta_conf=current_metrics["beta_conf"],
                        alpha_tok=current_metrics["alpha_tok"],
                        beta_tok=current_metrics["beta_tok"],
                        consensus_qual=estimate_confidence(con_result["text"]),
                        running=False
                    )
        elif result1 and result1["text"]:
            self._set_out(self.con_out, result1["text"])
            # Mark as done
            if self.dashboard and self.dashboard.winfo_exists():
                self.dashboard.update_metrics(
                    alpha_conf=current_metrics["alpha_conf"],
                    beta_conf=0,
                    alpha_tok=current_metrics["alpha_tok"],
                    beta_tok=0,
                    consensus_qual=0,
                    running=False
                )
        elif result2 and result2["text"]:
            self._set_out(self.con_out, result2["text"])
            # Mark as done
            if self.dashboard and self.dashboard.winfo_exists():
                self.dashboard.update_metrics(
                    alpha_conf=0,
                    beta_conf=current_metrics["beta_conf"],
                    alpha_tok=0,
                    beta_tok=current_metrics["beta_tok"],
                    consensus_qual=0,
                    running=False
                )

        self._set_status("Done ✓")
        self._finish()

    def _stop(self):
        self.stop_event.set()
        self._set_status("Stopping...")

    def _finish(self):
        self.is_running = False
        self.run_btn.config(state="normal", bg=ACCENT1, fg="#000000")
        self.stop_btn.config(state="disabled")

    def _clear(self):
        self.prompt_box.delete("1.0", "end")
        self._clear_outputs()
        self._set_status("Ready.")

    def _clear_outputs(self):
        for box in (self.out1, self.out2, self.con_out):
            box.config(state="normal")
            box.delete("1.0", "end")
        self.score1_lbl.config(text="—")
        self.score2_lbl.config(text="—")
        self.bar1["value"] = 0
        self.bar2["value"] = 0
        self.time1_lbl.config(text="—")
        self.time2_lbl.config(text="—")

    def _set_out(self, box, text):
        def update():
            box.config(state="normal")
            box.delete("1.0", "end")
            box.insert("end", text)
            box.see("end")
        self.after(0, update)

    def _set_status(self, msg):
        self.after(0, lambda: self.status_var.set(msg))

    def _toggle_dashboard(self):
        if self.dashboard is None or not self.dashboard.winfo_exists():
            self.dashboard = DashboardWindow(self)
        else:
            self.dashboard.lift()
            self.dashboard.focus()

    def _toggle_settings(self):
        if self.settings_window is None or not self.settings_window.winfo_exists():
            self.settings_window = ModelSettingsWindow(self)
        else:
            self.settings_window.lift()
            self.settings_window.focus()

    def _copy(self, box):
        text = box.get("1.0", "end").strip()
        self.clipboard_clear()
        self.clipboard_append(text)
        self._set_status("Copied to clipboard ✓")

    def _on_app_close(self):
        """Handle main app close - save geometry"""
        try:
            self._save_sash_positions()
        except:
            pass
        try:
            save_window_geometry("main", self.geometry())
        except:
            pass
        try:
            self.destroy()
        except:
            pass

    def _save_sash_positions(self):
        """Save paned window sash positions as ratios"""
        if hasattr(self, 'paned') and self.paned.winfo_exists():
            try:
                paned_height = self.paned.winfo_height()
                
                if paned_height > 50:  # Only save if window is reasonably sized
                    # Get sash positions using sash_coord
                    sash_positions = []
                    i = 0
                    while True:
                        try:
                            x, y = self.paned.sash_coord(i)
                            sash_positions.append(y)
                            i += 1
                        except:
                            break
                    
                    if sash_positions:
                        # Convert absolute positions to ratios (0.0-1.0)
                        ratios = [max(0.05, min(0.95, s / float(paned_height))) for s in sash_positions]
                        data = {"sash_ratios": ratios}
                        save_window_geometry("sash_positions", data)
            except Exception as e:
                pass
    
    def _restore_sash_positions(self):
        """Restore paned window sash positions from ratios"""
        if hasattr(self, 'paned') and self.paned.winfo_exists():
            try:
                # Force window to update so we get accurate dimensions
                self.paned.update_idletasks()
                self.update_idletasks()
                
                data = load_window_geometry("sash_positions")
                if data and "sash_ratios" in data:
                    ratios = data["sash_ratios"]
                    paned_height = self.paned.winfo_height()
                    paned_width = self.paned.winfo_width()
                    
                    if paned_height > 100 and paned_width > 100:  # Window is properly sized
                        # Convert ratios back to absolute positions
                        restored = False
                        for i, ratio in enumerate(ratios):
                            pos = int(paned_height * ratio)
                            
                            # Ensure pos is within reasonable bounds (at least 30px from edges)
                            pos = max(30, min(pos, paned_height - 30))
                            
                            try:
                                # For vertical PanedWindow, the sash moves vertically
                                # sash_place(index, x, y) - x is usually window width, y is vertical position
                                self.paned.sash_place(i, paned_width, pos)
                                restored = True
                            except Exception as e:
                                pass
            except Exception as e:
                pass
    
    def _monitor_sash_positions(self):
        """Periodically monitor and save sash positions"""
        try:
            if hasattr(self, 'paned') and self.paned.winfo_exists():
                # Get current sash positions
                current_sashes = []
                i = 0
                try:
                    while True:
                        x, y = self.paned.sash_coord(i)
                        current_sashes.append(y)
                        i += 1
                except:
                    pass
                
                # Check if positions changed
                if current_sashes and current_sashes != self._last_sash_positions:
                    self._last_sash_positions = current_sashes
                    # Delay saving to avoid excessive writes
                    self.after(100, self._save_sash_positions)
        except:
            pass
        
        # Schedule next check
        if hasattr(self, 'paned'):
            try:
                self.after(1000, self._monitor_sash_positions)
            except:
                pass

    def _on_paned_configure(self, event=None):
        """Handle paned window configuration/resize events"""
        # Only restore on first few events or after significant size change
        if not hasattr(self, '_last_paned_height'):
            self._last_paned_height = self.paned.winfo_height()
            self.after(50, self._restore_sash_positions)
        else:
            current_height = self.paned.winfo_height()
            # If size changed significantly, try restoring again
            if current_height != self._last_paned_height:
                height_diff = abs(current_height - self._last_paned_height)
                if height_diff > 50:  # More than 50px change
                    self._last_paned_height = current_height
                    self.after(50, self._restore_sash_positions)


if __name__ == "__main__":
    app = DualCoreApp()
    app.mainloop()
