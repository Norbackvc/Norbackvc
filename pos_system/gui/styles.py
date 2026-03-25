"""
Shared colors, fonts, and style helpers for the POS GUI.
"""
# ── Color palette ─────────────────────────────────────────────────────────────
DARK_BG    = "#1e1e2e"
PANEL_BG   = "#2a2a3e"
CARD_BG    = "#313148"
ACCENT     = "#7c6af7"
ACCENT2    = "#5e81f4"
SUCCESS    = "#2ecc71"
DANGER     = "#e74c3c"
WARNING    = "#f39c12"
TEXT       = "#e0e0f0"
TEXT_DIM   = "#8888aa"
BORDER     = "#44446a"
WHITE      = "#ffffff"
INPUT_BG   = "#3a3a55"

# ── Fonts ─────────────────────────────────────────────────────────────────────
FONT_TITLE  = ("Segoe UI", 18, "bold")
FONT_H1     = ("Segoe UI", 14, "bold")
FONT_H2     = ("Segoe UI", 12, "bold")
FONT_BODY   = ("Segoe UI", 10)
FONT_SMALL  = ("Segoe UI", 9)
FONT_MONO   = ("Courier New", 10)

# ── Padding ───────────────────────────────────────────────────────────────────
PAD  = 12
PADX = (PAD, PAD)
PADY = (6, 6)

# ── Button style helpers ──────────────────────────────────────────────────────
BTN_PRIMARY = dict(bg=ACCENT, fg=WHITE, font=FONT_BODY,
                   relief="flat", cursor="hand2", padx=10, pady=6,
                   activebackground=ACCENT2, activeforeground=WHITE)
BTN_DANGER  = dict(bg=DANGER, fg=WHITE, font=FONT_BODY,
                   relief="flat", cursor="hand2", padx=10, pady=6,
                   activebackground="#c0392b", activeforeground=WHITE)
BTN_SUCCESS = dict(bg=SUCCESS, fg=WHITE, font=FONT_BODY,
                   relief="flat", cursor="hand2", padx=10, pady=6,
                   activebackground="#27ae60", activeforeground=WHITE)
BTN_NEUTRAL = dict(bg=CARD_BG, fg=TEXT, font=FONT_BODY,
                   relief="flat", cursor="hand2", padx=10, pady=6,
                   activebackground=BORDER, activeforeground=TEXT)
