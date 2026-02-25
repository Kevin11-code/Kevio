"""
Kevio – compact floating control panel.

Structure  (260 × 130 px):
  ┌──────────────────────────┐
  │  🎙 Kevio          _  ×  │  ← drag zone / title bar
  ├──────────────────────────┤
  │   ●  Listening …         │  ← status row
  │  ╔══════════════════════╗ │
  │  ║   ■  Stop Listening  ║ │  ← action button
  │  ╚══════════════════════╝ │
  └──────────────────────────┘
"""

import logging
import math
import tkinter as tk
from tkinter import font as tkfont
from typing import Callable

logger = logging.getLogger(__name__)

# ── palette ───────────────────────────────────────────────────────────────────
BG        = "#0f1117"
SURFACE   = "#181c27"
HEADER    = "#13161f"
BORDER    = "#252d3f"
GREEN     = "#22c55e"
GREEN_DK  = "#15803d"
RED       = "#ef4444"
RED_DK    = "#b91c1c"
AMBER     = "#f59e0b"
BLUE      = "#3b82f6"
TEXT_PRI  = "#f1f5f9"
TEXT_SEC  = "#64748b"
TEXT_MUT  = "#334155"

W = 260
H = 130


class KevioUI:
    def __init__(self, on_toggle: Callable, on_exit: Callable):
        self.on_toggle = on_toggle
        self.on_exit   = on_exit

        self.status        = "stopped"
        self._pulse_run    = False
        self._pulse_angle  = 0.0
        self._drag_ox      = 0
        self._drag_oy      = 0
        self._minimized    = False

        self._build()

    # ── window ────────────────────────────────────────────────────────────────

    def _build(self):
        self.root = tk.Tk()
        self.root.title("Kevio")
        self.root.configure(bg=BG)
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.97)
        self.root.resizable(False, False)

        self._place(W, H)

        self._f_brand  = tkfont.Font(family="Segoe UI", size=10, weight="bold")
        self._f_status = tkfont.Font(family="Segoe UI", size=9)
        self._f_btn    = tkfont.Font(family="Segoe UI", size=9,  weight="bold")
        self._f_ctrl   = tkfont.Font(family="Segoe UI", size=10)

        self._build_chrome()
        self._build_body()

    def _place(self, w, h):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x  = (sw - w) // 2
        y  = sh - h - 52
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    # ── chrome (title bar) ────────────────────────────────────────────────────

    def _build_chrome(self):
        self._hdr = tk.Frame(self.root, bg=HEADER, height=34)
        self._hdr.pack(fill="x", side="top")
        self._hdr.pack_propagate(False)

        # brand
        brand = tk.Label(
            self._hdr, text="🎙  Kevio",
            bg=HEADER, fg=TEXT_PRI,
            font=self._f_brand, anchor="w", padx=12
        )
        brand.pack(side="left", fill="y")

        # window controls – right side
        ctrl_frame = tk.Frame(self._hdr, bg=HEADER)
        ctrl_frame.pack(side="right", fill="y", padx=6)

        self._min_btn = self._ctrl_btn(ctrl_frame, "−", self._toggle_minimize,
                                       hover_fg="#f0f0f0")
        self._min_btn.pack(side="left", padx=(0, 2))

        close_btn = self._ctrl_btn(ctrl_frame, "✕", self._exit,
                                   hover_fg=RED)
        close_btn.pack(side="left")

        # separator
        sep = tk.Frame(self.root, bg=BORDER, height=1)
        sep.pack(fill="x")

        # make entire header draggable
        for w in (self._hdr, brand, ctrl_frame):
            w.bind("<ButtonPress-1>",  self._drag_start)
            w.bind("<B1-Motion>",      self._drag_move)

    def _ctrl_btn(self, parent, text, cmd, hover_fg=TEXT_PRI):
        lbl = tk.Label(
            parent, text=text,
            bg=HEADER, fg=TEXT_SEC,
            font=self._f_ctrl, width=2, cursor="hand2"
        )
        lbl.bind("<Button-1>", lambda _e: cmd())
        lbl.bind("<Enter>",    lambda _e: lbl.config(fg=hover_fg))
        lbl.bind("<Leave>",    lambda _e: lbl.config(fg=TEXT_SEC))
        return lbl

    # ── body ──────────────────────────────────────────────────────────────────

    def _build_body(self):
        self._body = tk.Frame(self.root, bg=SURFACE)
        self._body.pack(fill="both", expand=True)

        # ── status row ────────────────────────────────────────────────────────
        status_row = tk.Frame(self._body, bg=SURFACE)
        status_row.pack(fill="x", padx=14, pady=(10, 6))

        # animated dot canvas
        self._dot_cv = tk.Canvas(
            status_row, width=12, height=12,
            bg=SURFACE, highlightthickness=0
        )
        self._dot_cv.pack(side="left")
        self._draw_dot(1.0)

        self._status_var = tk.StringVar(value="Idle  –  press Start or F9")
        status_lbl = tk.Label(
            status_row,
            textvariable=self._status_var,
            bg=SURFACE, fg=TEXT_SEC,
            font=self._f_status, anchor="w", padx=6
        )
        status_lbl.pack(side="left", fill="x", expand=True)

        # ── toggle button ─────────────────────────────────────────────────────
        self._btn_var = tk.StringVar(value="▶   Start Listening")
        self._btn = tk.Button(
            self._body,
            textvariable=self._btn_var,
            command=self.on_toggle,
            bg=GREEN, fg="#ffffff",
            activebackground=GREEN_DK, activeforeground="#ffffff",
            font=self._f_btn,
            relief="flat", bd=0,
            pady=9, cursor="hand2",
        )
        self._btn.pack(fill="x", padx=14, pady=(0, 12))

    # ── status dot ────────────────────────────────────────────────────────────

    def _dot_color(self):
        return {
            "listening":  GREEN,
            "paused":     AMBER,
            "processing": BLUE,
        }.get(self.status, TEXT_MUT)

    def _draw_dot(self, scale: float = 1.0):
        c  = self._dot_cv
        cx = cy = 6
        r  = max(1, int(5 * scale))
        c.delete("all")
        color = self._dot_color()
        if self.status == "listening":
            c.create_oval(cx - 6, cy - 6, cx + 6, cy + 6,
                          fill="", outline=color, width=1)
        c.create_oval(cx - r, cy - r, cx + r, cy + r,
                      fill=color, outline="")

    # ── dot pulse animation ───────────────────────────────────────────────────

    def _start_pulse(self):
        if self._pulse_run:
            return
        self._pulse_run = True
        self._tick()

    def _stop_pulse(self):
        self._pulse_run = False
        self._draw_dot(1.0)

    def _tick(self):
        if not self._pulse_run:
            return
        self._pulse_angle += 0.12
        self._draw_dot(0.7 + 0.3 * math.sin(self._pulse_angle))
        self.root.after(40, self._tick)

    # ── minimize  ─────────────────────────────────────────────────────────────

    def _toggle_minimize(self):
        self._minimized = not self._minimized
        if self._minimized:
            self._body.pack_forget()
            self.root.geometry(f"{W}x34")
            self._min_btn.config(text="□")
        else:
            self._body.pack(fill="both", expand=True)
            self.root.geometry(f"{W}x{H}")
            self._min_btn.config(text="−")

    # ── dragging ──────────────────────────────────────────────────────────────

    def _drag_start(self, e):
        self._drag_ox = e.x_root - self.root.winfo_x()
        self._drag_oy = e.y_root - self.root.winfo_y()

    def _drag_move(self, e):
        self.root.geometry(f"+{e.x_root - self._drag_ox}+{e.y_root - self._drag_oy}")

    # ── public API ────────────────────────────────────────────────────────────

    def update_status(self, status: str):
        """Thread-safe status update."""
        self.root.after(0, self._apply_status, status)

    def _apply_status(self, status: str):
        self.status = status

        cfg = {
            "listening":  ("Listening …",           GREEN,   "■   Stop Listening",  RED,   RED_DK),
            "paused":     ("Paused",                 AMBER,   "▶   Resume",          GREEN, GREEN_DK),
            "processing": ("Processing …",           BLUE,    "■   Stop",            RED,   RED_DK),
            "stopped":    ("Idle  –  press Start or F9", TEXT_SEC, "▶   Start Listening", GREEN, GREEN_DK),
        }.get(status, ("Idle  –  press Start or F9", TEXT_SEC, "▶   Start Listening", GREEN, GREEN_DK))

        st_text, st_color, btn_text, btn_bg, btn_abg = cfg
        self._status_var.set(st_text)

        # update status label color
        for w in self._body.winfo_children():
            if isinstance(w, tk.Frame):
                for c in w.winfo_children():
                    if isinstance(c, tk.Label):
                        c.config(fg=st_color)
                        break
                break

        self._btn_var.set(btn_text)
        self._btn.config(bg=btn_bg, activebackground=btn_abg)

        if status == "listening":
            self._start_pulse()
        else:
            self._stop_pulse()

    def add_transcription(self, text: str):
        """No log panel – kept for API compat."""
        pass

    def _exit(self):
        self._pulse_run = False
        self.on_exit()

    def run(self):
        self.root.mainloop()

    def quit(self):
        try:
            self.root.quit()
            self.root.destroy()
        except Exception:
            pass
