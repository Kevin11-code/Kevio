"""
Kevio – pill-shaped floating control panel (Windows 11 Fluent style).

Layout (380 × 56 px):
  ╭─────────────────────────────────────────────────╮
  │  [logo]  ┌──────────────────────┐  ···   ✕    │
  │          │  ●  Start Listening  │  drag zone   │
  │          └──────────────────────┘              │
  ╰─────────────────────────────────────────────────╯
"""

import ctypes
import ctypes.wintypes
import math
import os
import tkinter as tk
from tkinter import font as tkfont
from typing import Callable

from PIL import Image, ImageTk

# ── Windows 11 Fluent Dark tokens ────────────────────────────────────────────
BG_SURFACE   = "#1e1e1e"
DRAG_BOX_BG  = "#2a2a2a"  # slightly lighter box for the status area
DRAG_BOX_BD  = "#3d3d3d"  # subtle border on the drag handle box
ACCENT       = "#4cc2ff"
SUCCESS      = "#22c55e"
WARNING      = "#f59e0b"
DANGER       = "#ef4444"
MUTED        = "#555555"
TEXT_PRI     = "#ffffff"
TEXT_SEC     = "#8a8a8a"

# Window dimensions
W      = 380
H      = 56
RADIUS = 28   # full pill = H/2

# Status → (button label, dot color, interactive?)
_STATUS_MAP = {
    "loading":    ("Loading model…",  ACCENT,  False),
    "stopped":    ("Start Listening", SUCCESS, True),
    "listening":  ("Stop Listening",  DANGER,  True),
    "paused":     ("Start Listening", WARNING, True),
    "processing": ("Processing…",     ACCENT,  False),
}


class KevioUI:
    def __init__(self, on_toggle: Callable, on_exit: Callable):
        self.on_toggle = on_toggle
        self.on_exit   = on_exit

        self.status        = "stopped"
        self._pulse_active = False
        self._pulse_t      = 0.0
        self._dot_base_rgb = (0x55, 0x55, 0x55)

        self._drag_x = 0
        self._drag_y = 0

        self._build()

    # ─────────────────────────────────────────────────────────────────────────
    # Window
    # ─────────────────────────────────────────────────────────────────────────

    def _build(self):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            pass

        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.97)
        self.root.configure(bg="black")

        self._place()

        # Canvas paints the pill shape; Tk frame sits on top of it
        self.canvas = tk.Canvas(
            self.root, width=W, height=H,
            bg="black", highlightthickness=0,
        )
        self.canvas.pack()

        # Drop shadow
        self._pill(3, 5, W - 3, H - 1, RADIUS, fill="#111111")
        # Main surface
        self._pill_id = self._pill(0, 0, W, H, RADIUS, fill=BG_SURFACE)

        self._load_assets()
        self._build_content()

        # Apply Win11 rounded corners AFTER widgets are mapped
        self.root.update_idletasks()
        self._apply_win11_corners()

    def _place(self):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x  = (sw - W) // 2
        y  = sh - H - 80
        self.root.geometry(f"{W}x{H}+{x}+{y}")

    # ─────────────────────────────────────────────────────────────────────────
    # Pill helper
    # ─────────────────────────────────────────────────────────────────────────

    def _pill(self, x1, y1, x2, y2, r, **kw):
        pts = [
            x1 + r, y1,   x2 - r, y1,
            x2,     y1,   x2,     y1 + r,
            x2,     y2 - r, x2,   y2,
            x2 - r, y2,   x1 + r, y2,
            x1,     y2,   x1,     y2 - r,
            x1,     y1 + r, x1,   y1,
        ]
        return self.canvas.create_polygon(pts, smooth=True, **kw)

    # ─────────────────────────────────────────────────────────────────────────
    # Assets
    # ─────────────────────────────────────────────────────────────────────────

    def _load_assets(self):
        self._logo_img = None
        try:
            path = os.path.join(os.getcwd(), "assets", "kevio.png")
            if os.path.exists(path):
                img = Image.open(path).convert("RGBA")
                img.thumbnail((70, 70), Image.LANCZOS)   # aspect-safe resize
                self._logo_img = ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Logo load error: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # Content
    # ─────────────────────────────────────────────────────────────────────────

    def _build_content(self):
        f_label = tkfont.Font(family="Segoe UI", size=10, weight="normal")
        f_close = tkfont.Font(family="Segoe UI", size=9)

        # Overlay frame fills the whole pill (transparent background = pill color)
        row = tk.Frame(self.root, bg=BG_SURFACE, width=W, height=H)
        row.place(x=0, y=0)
        row.pack_propagate(False)

        # ── left padding ─────────────────────────────────────────────────────
        tk.Frame(row, bg=BG_SURFACE, width=15).pack(side="left")

        # ── logo (draggable) ─────────────────────────────────────────────────
        if self._logo_img:
            lbl_logo = tk.Label(
                row, image=self._logo_img,
                bg=BG_SURFACE, bd=0, padx=10, pady=0,
                cursor="fleur",   # move cursor hints draggable
            )
        else:
            lbl_logo = tk.Label(
                row, text="🎙",
                bg=BG_SURFACE, fg=ACCENT,
                font=tkfont.Font(size=15),
                cursor="fleur",
            )
        lbl_logo.pack(side="left", padx=(0, 8))
        self._bind_drag(lbl_logo)

        # ── left center spacer ───────────────────────────────────────────────
        left_spacer = tk.Frame(row, bg=BG_SURFACE)
        left_spacer.pack(side="left", fill="x", expand=True)
        self._bind_drag(left_spacer)

        # ── status box (drag handle with visible border) ──────────────────────
        # This box is the primary drag handle AND houses dot + label.
        drag_box = tk.Frame(
            row,
            bg=DRAG_BOX_BG,
            highlightbackground=DRAG_BOX_BD,
            highlightthickness=1,
            padx=7, pady=0,
            cursor="fleur",
        )
        drag_box.pack(side="left", ipady=3)
        self._bind_drag(drag_box)

        # Animated dot inside box
        self._dot_cv = tk.Canvas(
            drag_box, width=10, height=10,
            bg=DRAG_BOX_BG, highlightthickness=0,
            cursor="fleur",
        )
        self._dot_cv.pack(side="left", padx=(0, 7))
        self._dot_item = self._dot_cv.create_oval(1, 1, 9, 9,
                                                   fill=MUTED, outline="")
        self._bind_drag(self._dot_cv)

        # Action label inside box
        self._btn_var = tk.StringVar(value="Start Listening")
        self._btn_lbl = tk.Label(
            drag_box,
            textvariable=self._btn_var,
            bg=DRAG_BOX_BG, fg=TEXT_PRI,
            font=f_label,
            width=15, anchor="w",
            cursor="hand2",
        )
        self._btn_lbl.pack(side="left")
        self._btn_lbl.bind("<Button-1>", self._on_btn_click)
        self._btn_lbl.bind("<Enter>",    lambda _e: self._btn_hover(True))
        self._btn_lbl.bind("<Leave>",    lambda _e: self._btn_hover(False))

        # ── right center spacer ──────────────────────────────────────────────
        right_spacer = tk.Frame(row, bg=BG_SURFACE)
        right_spacer.pack(side="left", fill="x", expand=True)
        self._bind_drag(right_spacer)

        # ── close button ──────────────────────────────────────────────────────
        self._close_lbl = tk.Label(
            row, text="✕",
            bg=BG_SURFACE, fg=TEXT_SEC,
            font=f_close, width=2,
            cursor="hand2",
        )
        self._close_lbl.pack(side="left")
        self._close_lbl.bind("<Button-1>", lambda _e: self._exit())
        self._close_lbl.bind("<Enter>",    lambda _e: self._close_lbl.config(fg=DANGER))
        self._close_lbl.bind("<Leave>",    lambda _e: self._close_lbl.config(fg=TEXT_SEC))

        # ── right padding ─────────────────────────────────────────────────────
        tk.Frame(row, bg=BG_SURFACE, width=12).pack(side="left")

    # ─────────────────────────────────────────────────────────────────────────
    # Drag helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _bind_drag(self, widget):
        widget.bind("<ButtonPress-1>", self._drag_start)
        widget.bind("<B1-Motion>",     self._drag_move)

    def _drag_start(self, e):
        self._drag_x = e.x_root - self.root.winfo_x()
        self._drag_y = e.y_root - self.root.winfo_y()

    def _drag_move(self, e):
        self.root.geometry(f"+{e.x_root - self._drag_x}+{e.y_root - self._drag_y}")

    # ─────────────────────────────────────────────────────────────────────────
    # Button helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _on_btn_click(self, _e=None):
        if self.status not in ("loading", "processing"):
            self.on_toggle()

    def _btn_hover(self, entering: bool):
        if self.status in ("loading", "processing"):
            return
        self._btn_lbl.config(fg=ACCENT if entering else TEXT_PRI)

    # ─────────────────────────────────────────────────────────────────────────
    # Windows 11 – DWM rounded corners
    # ─────────────────────────────────────────────────────────────────────────

    def _apply_win11_corners(self):
        """Ask DWM to round the window corners (Win 11 only, silently fails on Win 10)."""
        try:
            DWMWA_WINDOW_CORNER_PREFERENCE = 33
            DWMWCP_ROUND = 2
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            # If overrideredirect, GetParent returns 0 — use winfo_id directly
            if hwnd == 0:
                hwnd = self.root.winfo_id()
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_WINDOW_CORNER_PREFERENCE,
                ctypes.byref(ctypes.c_int(DWMWCP_ROUND)),
                ctypes.sizeof(ctypes.c_int),
            )
        except Exception:
            pass

    # ─────────────────────────────────────────────────────────────────────────
    # Public status API
    # ─────────────────────────────────────────────────────────────────────────

    def update_status(self, status: str):
        """Thread-safe status push."""
        self.root.after(0, self._apply_status, status)

    def _apply_status(self, status: str):
        self.status = status
        label, dot_color, interactive = _STATUS_MAP.get(status, _STATUS_MAP["stopped"])

        self._btn_var.set(label)
        self._btn_lbl.config(
            cursor="hand2" if interactive else "watch",
            fg=TEXT_PRI,
        )

        # Store base RGB so pulse doesn't drift toward black
        self._dot_base_rgb = (
            int(dot_color[1:3], 16),
            int(dot_color[3:5], 16),
            int(dot_color[5:7], 16),
        )
        self._dot_cv.itemconfig(self._dot_item, fill=dot_color)

        if status in ("listening", "loading"):
            self._start_pulse()
        else:
            self._stop_pulse()

    def add_transcription(self, text: str):
        """No log panel – kept for API compat."""
        pass

    # ─────────────────────────────────────────────────────────────────────────
    # Pulse animation
    # ─────────────────────────────────────────────────────────────────────────

    def _start_pulse(self):
        if self._pulse_active:
            return
        self._pulse_active = True
        self._pulse_t = 0.0
        self._tick_pulse()

    def _stop_pulse(self):
        self._pulse_active = False
        r, g, b = self._dot_base_rgb
        self._dot_cv.itemconfig(self._dot_item, fill=f"#{r:02x}{g:02x}{b:02x}")

    def _tick_pulse(self):
        if not self._pulse_active:
            return
        self._pulse_t += 0.10
        alpha = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(self._pulse_t))
        r, g, b = self._dot_base_rgb
        self._dot_cv.itemconfig(
            self._dot_item,
            fill=f"#{int(r*alpha):02x}{int(g*alpha):02x}{int(b*alpha):02x}",
        )
        self.root.after(40, self._tick_pulse)

    # ─────────────────────────────────────────────────────────────────────────
    # Lifecycle
    # ─────────────────────────────────────────────────────────────────────────

    def _exit(self):
        self._pulse_active = False
        if self.on_exit:
            self.on_exit()

    def run(self):
        self.root.mainloop()

    def quit(self):
        """Called by KevioApp.stop() to tear down the window."""
        self._pulse_active = False
        try:
            self.root.quit()
            self.root.destroy()
        except Exception:
            pass