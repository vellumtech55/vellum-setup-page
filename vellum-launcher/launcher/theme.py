"""
Design tokens — colors, fonts, and platform detection.
Every widget in the app pulls its styling from the C dict below, so the
whole theme can be re-skinned by editing this one file.
"""

import sys

PLAT = sys.platform

# ── Palette: black / gray surfaces with a dark blue accent ─────────────────
C = {
    # Surfaces (black / near-black grays)
    "base":         "#0A0A0B",
    "surface":      "#131315",
    "card":         "#1A1A1D",
    "card_border":  "#2A2A2E",
    "card_hover":   "#222226",
    "sidebar":      "#08080A",
    "input":        "#1E1E22",

    # Accents (dark blue)
    "accent":       "#2F5D9C",
    "accent_dim":   "#24466F",
    "accent_glow":  "#2F5D9C15",
    "amber":        "#F59E0B",   # updates / badges
    "green":        "#22C55E",
    "red":          "#EF4444",

    # Text
    "text":         "#E8E8EA",
    "sub":          "#9C9CA3",
    "muted":        "#5C5C63",
    "white":        "#FFFFFF",

    # Sidebar
    "nav_text":     "#8B8B92",
    "nav_sel_bg":   "#18181C",
    "nav_sel_bar":  "#2F5D9C",
}

FONT = ("Segoe UI"      if PLAT == "win32"
        else "SF Pro Text" if PLAT == "darwin"
        else "Ubuntu")
MONO = ("Consolas" if PLAT == "win32"
        else "SF Mono" if PLAT == "darwin"
        else "Ubuntu Mono")
