"""
The main Launcher window: sidebar navigation, page management, and every
page (Home, All Products, Installed, Updates, Store).
"""

import tkinter as tk
from tkinter import ttk, messagebox

from .theme import C, FONT, MONO
from .data import load_registry, save_registry, installed_apps, update_apps, sync_catalog
from .widgets import sep, icon_badge, pill_label, HoverButton, GhostButton, scrollable_frame
from .dialogs import Toast, GetAppDialog
from .download import launch_app, uninstall_app


def _same_category(app_cat, tab_cat):
    """Case-insensitive category match so a stray casing mismatch in
    apps.json never silently hides an app from its tab."""
    return (app_cat or "").strip().lower() == (tab_cat or "").strip().lower()


class Launcher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.registry  = load_registry()
        self.apps      = self.registry["apps"]
        self.info      = self.registry["launcher"]
        self.cats      = self.registry.get("categories", ["All"])
        self._page     = "Home"
        self._cat      = "All"

        self.title(self.info["name"])
        self.geometry("1020x800")
        self.minsize(860, 600)
        self.configure(bg=C["base"])
        self._style()
        self._build()
        sync_catalog(self.registry, lambda: self.after(0, self._refresh_all))

    # ── ttk global style ───────────────────────────────────────────────────
    def _style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("Vertical.TScrollbar",
                    background=C["card_border"], troughcolor=C["surface"],
                    bordercolor=C["surface"], arrowcolor=C["muted"],
                    relief="flat", width=6)
        s.map("Vertical.TScrollbar", background=[("active", C["sub"])])

    # ── Top-level layout ───────────────────────────────────────────────────
    def _build(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._sidebar = self._make_sidebar()
        self._sidebar.grid(row=0, column=0, sticky="nsew")
        self._content = tk.Frame(self, bg=C["base"])
        self._content.grid(row=0, column=1, sticky="nsew")
        self._content.grid_rowconfigure(0, weight=1)
        self._content.grid_columnconfigure(0, weight=1)
        self._pages   = {}   # name -> Frame
        self._dirty   = set()  # pages that need rebuilding before next show
        self._build_all_pages()
        self._show_page("Home")

    # ══════════════════════════════════════════════════════════════════════
    # SIDEBAR
    # ══════════════════════════════════════════════════════════════════════
    def _make_sidebar(self):
        sb = tk.Frame(self, bg=C["sidebar"], width=220)
        sb.pack_propagate(False)

        # Logo row
        logo = tk.Frame(sb, bg=C["sidebar"])
        logo.pack(fill="x", padx=18, pady=22)
        gem = tk.Label(logo, text="◈", font=(FONT, 22, "bold"),
                       bg=C["sidebar"], fg=C["accent"])
        gem.pack(side="left")
        nf = tk.Frame(logo, bg=C["sidebar"])
        nf.pack(side="left", padx=8)
        name_parts = self.info["name"].split()
        tk.Label(nf, text=" ".join(name_parts[:-1]).upper() if len(name_parts) > 1 else self.info["name"].upper(),
                 font=(FONT, 9, "bold"), bg=C["sidebar"], fg=C["text"]
                 ).pack(anchor="w")
        if len(name_parts) > 1:
            tk.Label(nf, text=name_parts[-1].upper(),
                     font=(FONT, 9, "bold"), bg=C["sidebar"], fg=C["accent"]
                     ).pack(anchor="w")

        sep(sb, pad=16)

        # Primary nav
        upd_count = len(update_apps(self.apps))
        primary = [
            ("⌂",  "Home",         None),
            ("⊞",  "All Products", None),
            ("✓",  "Installed",    len(installed_apps(self.apps))),
            ("↑",  "Updates",      upd_count if upd_count else None),
            ("⊕",  "Store",        None),
            ("∞",  "Free Tools",   None),
        ]
        self._nav_refs = {}
        for icon, label, badge in primary:
            self._nav_item(sb, icon, label, badge)

        sep(sb, pad=16)

        for icon, label, badge in [
            ("○", "Membership", None),
            ("◎", "Settings",   None),
            ("?", "Support",    None),
            ("↗", "Roadmap",    None),
        ]:
            self._nav_item(sb, icon, label, badge)

        # Spacer
        tk.Frame(sb, bg=C["sidebar"]).pack(fill="both", expand=True)

        # Pro card
        self._pro_card(sb)

        # Version
        tk.Label(sb, text=f"v{self.info['version']}",
                 font=(FONT, 7), bg=C["sidebar"], fg=C["muted"]
                 ).pack(pady=(0, 8))
        return sb

    def _nav_item(self, parent, icon, label, badge=None):
        is_sel = label == self._page
        row = tk.Frame(parent, bg=C["nav_sel_bg"] if is_sel else C["sidebar"],
                       cursor="hand2", height=38)
        row.pack(fill="x", padx=10, pady=1)
        row.pack_propagate(False)

        bar = tk.Frame(row, bg=C["nav_sel_bar"] if is_sel else C["sidebar"], width=3)
        bar.pack(side="left", fill="y")

        fg = C["text"] if is_sel else C["nav_text"]
        icon_lbl = tk.Label(row, text=icon, font=(FONT, 11),
                            bg=row["bg"], fg=fg, width=3)
        icon_lbl.pack(side="left", padx=(6, 0))
        text_lbl = tk.Label(row, text=label,
                            font=(FONT, 10, "bold" if is_sel else "normal"),
                            bg=row["bg"], fg=fg)
        text_lbl.pack(side="left", padx=4)

        if badge:
            col = C["amber"] if label == "Updates" else C["accent"]
            pill_label(row, str(badge), color=col).pack(side="right", padx=10)

        def _click(e, lbl=label):
            self._nav_goto(lbl)

        def _enter(e, lbl=label):
            if self._page != lbl:
                row.config(bg=C["card_hover"])
                for w in (bar, icon_lbl, text_lbl): w.config(bg=C["card_hover"])

        def _leave(e, lbl=label):
            bg = C["nav_sel_bg"] if self._page == lbl else C["sidebar"]
            row.config(bg=bg)
            for w in (bar, icon_lbl, text_lbl): w.config(bg=bg)

        for w in [row, bar, icon_lbl, text_lbl]:
            w.bind("<Button-1>", _click)
            w.bind("<Enter>", _enter)
            w.bind("<Leave>", _leave)

        # Store refs so we can update visual state without rebuilding
        self._nav_refs[label] = {
            "row": row, "bar": bar,
            "icon": icon_lbl, "text": text_lbl,
        }

    def _refresh_sidebar(self):
        """
        Update only the visual state of nav items — no destroy/rebuild.
        Called on every page switch. Fast and glitch-free.
        """
        for label, refs in self._nav_refs.items():
            is_sel = label == self._page
            bg  = C["nav_sel_bg"] if is_sel else C["sidebar"]
            fg  = C["text"]       if is_sel else C["nav_text"]
            bar = C["nav_sel_bar"] if is_sel else C["sidebar"]
            refs["row"].config(bg=bg)
            refs["bar"].config(bg=bar)
            refs["icon"].config(bg=bg, fg=fg)
            refs["text"].config(bg=bg, fg=fg,
                                font=(FONT, 10, "bold" if is_sel else "normal"))

    def _pro_card(self, parent):
        card = tk.Frame(parent, bg="#101216")
        card.pack(fill="x", padx=12, pady=6)
        # Top accent line
        tk.Frame(card, bg=C["accent"], height=2).pack(fill="x")
        inner = tk.Frame(card, bg="#101216")
        inner.pack(fill="x", padx=14, pady=12)
        tk.Label(inner, text="♛  Pro", font=(FONT, 11, "bold"),
                 bg="#101216", fg=C["white"]).pack(anchor="w")
        tk.Label(inner, text="Unlock everything.\nSupport the mission.",
                 font=(FONT, 8), bg="#101216", fg=C["sub"], justify="left"
                 ).pack(anchor="w", pady=4)
        HoverButton(inner, "Upgrade Now",
                    lambda: messagebox.showinfo("Pro", "Upgrade coming soon!"),
                    bg=C["accent"], hover_bg=C["accent_dim"],
                    padx=0, pady=6,
                    ).pack(fill="x", pady=(2, 0))

    # ══════════════════════════════════════════════════════════════════════
    # PAGE MANAGEMENT — frame-stack + lazy dirty rebuild
    # ══════════════════════════════════════════════════════════════════════
    # Pages are built once on startup and stacked with tkraise().
    # When data changes (install/uninstall), we mark data-dependent pages
    # dirty. A dirty page is rebuilt only the next time it is shown —
    # never while it's hidden, so there is no visual glitch.
    # ══════════════════════════════════════════════════════════════════════

    # Pages whose content depends on the app registry
    DATA_PAGES = {
        "Home":         "_page_home",
        "All Products": "_page_all",
        "Installed":    "_page_installed",
        "Updates":      "_page_updates",
        "Store":        "_page_store",
    }

    def _build_all_pages(self):
        for name, method in self.DATA_PAGES.items():
            self._make_page(name, getattr(self, method))
        for name in ("Free Tools", "Membership", "Settings", "Support", "Roadmap"):
            self._make_page(name, None)  # stubs handled inside _make_page

    def _make_page(self, name, builder):
        f = tk.Frame(self._content, bg=C["base"])
        f.grid(row=0, column=0, sticky="nsew")
        if name in ("Free Tools", "Membership", "Settings", "Support", "Roadmap"):
            self._stub_page(f, name)
        else:
            builder(f)
        self._pages[name] = f

    def _show_page(self, name):
        # If dirty, rebuild silently before raising
        if name in self._dirty and name in self.DATA_PAGES:
            self._dirty.discard(name)
            old = self._pages.get(name)
            if old:
                old.destroy()
            f = tk.Frame(self._content, bg=C["base"])
            f.grid(row=0, column=0, sticky="nsew")
            getattr(self, self.DATA_PAGES[name])(f)
            self._pages[name] = f

        frame = self._pages.get(name)
        if frame:
            frame.tkraise()

    def _mark_dirty(self):
        """Call after any registry change. Pages rebuild lazily on next open."""
        self._dirty.update(self.DATA_PAGES.keys())

    def _refresh_all(self):
        """After a data change: mark dirty, refresh sidebar, show current page."""
        self._mark_dirty()
        self._refresh_sidebar()
        self._show_page(self._page)   # rebuilds current page immediately; rest wait

    def _stub_page(self, parent, name):
        tk.Label(parent, text=name,
                 font=(FONT, 20, "bold"), bg=C["base"], fg=C["text"]
                 ).place(relx=0.5, rely=0.4, anchor="center")
        tk.Label(parent, text="Coming soon.",
                 font=(FONT, 11), bg=C["base"], fg=C["muted"]
                 ).place(relx=0.5, rely=0.48, anchor="center")

    # ══════════════════════════════════════════════════════════════════════
    # SHARED LAYOUT ATOMS
    # ══════════════════════════════════════════════════════════════════════
    def _page_header(self, parent, title, subtitle=None):
        hdr = tk.Frame(parent, bg=C["base"])
        hdr.pack(fill="x", padx=28, pady=(26, 4))
        tk.Label(hdr, text=title, font=(FONT, 17, "bold"),
                 bg=C["base"], fg=C["text"]).pack(anchor="w")
        if subtitle:
            tk.Label(hdr, text=subtitle, font=(FONT, 10),
                     bg=C["base"], fg=C["sub"]).pack(anchor="w", pady=2)
        return hdr

    def _section_label(self, parent, title, action_text=None, action_cmd=None):
        row = tk.Frame(parent, bg=C["base"])
        row.pack(fill="x", padx=28, pady=(18, 8))
        tk.Label(row, text=title, font=(FONT, 11, "bold"),
                 bg=C["base"], fg=C["text"]).pack(side="left")
        if action_text and action_cmd:
            lbl = tk.Label(row, text=action_text, font=(FONT, 9),
                           bg=C["base"], fg=C["accent"], cursor="hand2")
            lbl.pack(side="right")
            lbl.bind("<Button-1>", lambda e: action_cmd())
            lbl.bind("<Enter>", lambda e: lbl.config(fg=C["white"]))
            lbl.bind("<Leave>", lambda e: lbl.config(fg=C["accent"]))

    def _cat_tabs(self, parent, current, on_select):
        row = tk.Frame(parent, bg=C["base"])
        row.pack(fill="x", padx=26, pady=(0, 8))
        for cat in self.cats:
            is_sel = cat == current
            btn = tk.Label(
                row, text=cat,
                font=(FONT, 9, "bold" if is_sel else "normal"),
                bg=C["accent"] if is_sel else C["input"],
                fg=C["white"] if is_sel else C["sub"],
                padx=14, pady=5, cursor="hand2",
            )
            btn.pack(side="left", padx=(0, 4))
            btn.bind("<Button-1>", lambda e, c=cat: on_select(c))
            if not is_sel:
                btn.bind("<Enter>", lambda e, b=btn: b.config(bg=C["card_hover"], fg=C["text"]))
                btn.bind("<Leave>", lambda e, b=btn: b.config(bg=C["input"], fg=C["sub"]))

    # ══════════════════════════════════════════════════════════════════════
    # HOME PAGE
    # ══════════════════════════════════════════════════════════════════════
    def _page_home(self, parent):
        outer, _ = scrollable_frame(parent)
        inst = installed_apps(self.apps)
        upd  = update_apps(self.apps)

        # ── Hero ──────────────────────────────────────────────────────────
        hero = tk.Frame(outer, bg=C["card"])
        hero.pack(fill="x", padx=24, pady=(24, 0))
        # Left accent bar
        tk.Frame(hero, bg=C["accent"], width=4).pack(side="left", fill="y")
        left = tk.Frame(hero, bg=C["card"])
        left.pack(side="left", fill="both", expand=True, padx=20, pady=20)
        tk.Label(left, text="Welcome back.", font=(FONT, 16, "bold"),
                 bg=C["card"], fg=C["white"]).pack(anchor="w")
        tk.Label(left, text=self.info["tagline"], font=(FONT, 10),
                 bg=C["card"], fg=C["sub"]).pack(anchor="w", pady=2)

        stats = tk.Frame(hero, bg=C["card"])
        stats.pack(side="right", padx=24)
        self._stat_block(stats, str(len(inst)), "installed", C["text"])
        tk.Frame(stats, bg=C["card_border"], width=1).pack(side="left", fill="y", padx=16, pady=16)
        self._stat_block(stats, str(len(upd)), "updates",
                         C["amber"] if upd else C["muted"])

        # ── Installed grid ────────────────────────────────────────────────
        self._section_label(outer, "Installed apps",
                             "See all →", lambda: self._nav_goto("Installed"))
        grid = tk.Frame(outer, bg=C["base"])
        grid.pack(fill="x", padx=24, pady=(0, 4))
        for i, app in enumerate(inst[:3]):
            self._installed_card(grid, app, col=i)
            grid.grid_columnconfigure(i, weight=1)

        # ── All products list ─────────────────────────────────────────────
        self._section_label(outer, "All products",
                             "Browse store →", lambda: self._nav_goto("Store"))

        cat_var = {"v": "All"}
        cat_host = tk.Frame(outer, bg=C["base"])
        cat_host.pack(fill="x")
        list_host = tk.Frame(outer, bg=C["base"])
        list_host.pack(fill="x", padx=24)

        def _render_list():
            for w in list_host.winfo_children(): w.destroy()
            for app in self.apps:
                if app.get("installed"): continue
                if cat_var["v"] != "All" and not _same_category(app.get("category"), cat_var["v"]): continue
                self._store_row(list_host, app)

        def _on_cat(c):
            cat_var["v"] = c
            for w in cat_host.winfo_children(): w.destroy()
            self._cat_tabs(cat_host, c, _on_cat)
            _render_list()

        self._cat_tabs(cat_host, "All", _on_cat)
        _render_list()

        # ── Footer upsell ─────────────────────────────────────────────────
        self._upsell_banner(outer)
        tk.Frame(outer, bg=C["base"], height=20).pack()

    def _stat_block(self, parent, val, label, color):
        f = tk.Frame(parent, bg=C["card"])
        f.pack(side="left", pady=18)
        tk.Label(f, text=val, font=(FONT, 22, "bold"),
                 bg=C["card"], fg=color).pack()
        tk.Label(f, text=label, font=(FONT, 8),
                 bg=C["card"], fg=C["sub"]).pack()

    def _uc_banner(self, parent, app):
        """
        Show an 'Under construction' strip on any uninstalled product card
        that has  "under_construction": true  in apps.json.
        Never shown on installed cards — if it's installed, it's ready.
        """
        if not app.get("under_construction"):
            return
        banner = tk.Frame(parent, bg=C["amber"])
        banner.pack(fill="x")
        tk.Label(
            banner,
            text="🚧  Under construction — coming soon",
            font=(FONT, 8, "bold"),
            bg=C["amber"], fg="#1C1000",
            padx=10, pady=3,
        ).pack(side="left")

    def _installed_card(self, parent, app, col=0):
        """Rich installed-app card with green top border."""
        wrap = tk.Frame(parent, bg=C["green"])     # green top sliver
        wrap.grid(row=0, column=col, padx=(0, 10 if col < 2 else 0), sticky="nsew")

        card = tk.Frame(wrap, bg=C["card"])
        card.pack(fill="both", expand=True, pady=(2, 0))   # 2px green shows above

        top = tk.Frame(card, bg=C["card"])
        top.pack(fill="x", padx=14, pady=(14, 6))
        icon_badge(top, app, size=42).pack(side="left")
        status = tk.Frame(top, bg=C["card"])
        status.pack(side="left", padx=10)
        tk.Label(status, text=app["name"], font=(FONT, 11, "bold"),
                 bg=C["card"], fg=C["white"]).pack(anchor="w")
        pill_label(status, "● Installed", color=C["card"], fg=C["green"]
                   ).pack(anchor="w")

        tk.Label(card, text=app["description"], font=(FONT, 9),
                 bg=C["card"], fg=C["sub"], wraplength=170, justify="left"
                 ).pack(anchor="w", padx=14, pady=(2, 10))

        btns = tk.Frame(card, bg=C["card"])
        btns.pack(fill="x", padx=14, pady=(0, 14))
        HoverButton(btns, "Open", lambda a=app: launch_app(a),
                    padx=18, pady=6).pack(side="left")
        GhostButton(btns, "•••", lambda a=app: self._app_context_menu(a),
                    padx=10, pady=6).pack(side="left", padx=6)

    # ══════════════════════════════════════════════════════════════════════
    # ALL PRODUCTS PAGE
    # ══════════════════════════════════════════════════════════════════════
    def _page_all(self, parent):
        self._page_header(parent, "All Products", "Everything in the collection.")
        outer, _ = scrollable_frame(parent)

        cat_var = {"v": self._cat}
        cat_host = tk.Frame(outer, bg=C["base"])
        cat_host.pack(fill="x", padx=0, pady=(4,0))
        list_host = tk.Frame(outer, bg=C["base"])
        list_host.pack(fill="x", padx=24)

        def _render():
            for w in list_host.winfo_children(): w.destroy()
            for app in self.apps:
                if cat_var["v"] != "All" and not _same_category(app.get("category"), cat_var["v"]): continue
                if app.get("installed"):
                    self._installed_row(list_host, app)
                else:
                    self._store_row(list_host, app)

        def _on_cat(c):
            cat_var["v"] = c
            self._cat = c
            for w in cat_host.winfo_children(): w.destroy()
            self._cat_tabs(cat_host, c, _on_cat)
            _render()

        self._cat_tabs(cat_host, cat_var["v"], _on_cat)
        _render()
        tk.Frame(outer, bg=C["base"], height=20).pack()

    # ══════════════════════════════════════════════════════════════════════
    # INSTALLED PAGE
    # ══════════════════════════════════════════════════════════════════════
    def _page_installed(self, parent):
        self._page_header(parent, "Installed", "Your ready-to-run apps.")
        outer, _ = scrollable_frame(parent)
        inst = installed_apps(self.apps)
        if not inst:
            tk.Label(outer, text="Nothing installed yet.\nHead to the Store to download apps.",
                     font=(FONT, 12), bg=C["base"], fg=C["muted"], justify="center"
                     ).pack(pady=80)
            HoverButton(outer, "Browse Store", lambda: self._nav_goto("Store"),
                        padx=24, pady=8).pack()
        else:
            for app in inst:
                self._installed_row(outer, app)
        tk.Frame(outer, bg=C["base"], height=20).pack()

    def _installed_row(self, parent, app):
        row = tk.Frame(parent, bg=C["card"], cursor="hand2")
        row.pack(fill="x", pady=3)
        # Subtle left accent
        tk.Frame(row, bg=C["green"], width=3).pack(side="left", fill="y")

        icon_badge(row, app, size=42).pack(side="left", padx=14, pady=12)

        info = tk.Frame(row, bg=C["card"])
        info.pack(side="left", fill="both", expand=True, pady=12)
        tk.Label(info, text=app["name"], font=(FONT, 11, "bold"),
                 bg=C["card"], fg=C["white"]).pack(anchor="w")
        vline = tk.Frame(info, bg=C["card"])
        vline.pack(anchor="w")
        tk.Label(vline, text="Installed", font=(FONT, 9),
                 bg=C["card"], fg=C["green"]).pack(side="left")
        tk.Label(vline, text=f"  v{app.get('installed_version') or app.get('version','')}", font=(MONO, 8),
                 bg=C["card"], fg=C["muted"]).pack(side="left")

        btns = tk.Frame(row, bg=C["card"])
        btns.pack(side="right", padx=14)
        HoverButton(btns, "Open", lambda a=app: launch_app(a),
                    padx=16, pady=6).pack(side="left", padx=(0, 6))
        GhostButton(btns, "Uninstall", lambda a=app: self._uninstall(a),
                    padx=10, pady=6).pack(side="left")

    # ══════════════════════════════════════════════════════════════════════
    # UPDATES PAGE
    # ══════════════════════════════════════════════════════════════════════
    def _page_updates(self, parent):
        upd = update_apps(self.apps)
        hdr = self._page_header(parent, "Updates",
                                f"{len(upd)} update{'s' if len(upd) != 1 else ''} available" if upd else None)
        if upd:
            HoverButton(hdr, "Update All",
                        lambda: self._update_all(upd),
                        padx=14, pady=5, font_size=8).pack(side="right", anchor="n")
        outer, _ = scrollable_frame(parent)
        if not upd:
            tk.Label(outer, text="✓  All apps are up to date.",
                     font=(FONT, 13), bg=C["base"], fg=C["green"]
                     ).pack(pady=80)
        else:
            for app in upd:
                self._update_row(outer, app)
        tk.Frame(outer, bg=C["base"], height=20).pack()

    def _update_row(self, parent, app):
        row = tk.Frame(parent, bg=C["card"])
        row.pack(fill="x", pady=3)
        tk.Frame(row, bg=C["amber"], width=3).pack(side="left", fill="y")
        icon_badge(row, app, size=42).pack(side="left", padx=14, pady=12)
        info = tk.Frame(row, bg=C["card"])
        info.pack(side="left", fill="both", expand=True, pady=12)
        tk.Label(info, text=app["name"], font=(FONT, 11, "bold"),
                 bg=C["card"], fg=C["white"]).pack(anchor="w")
        ver_row = tk.Frame(info, bg=C["card"])
        ver_row.pack(anchor="w")
        tk.Label(ver_row, text=f"v{app.get('installed_version','?')}",
                 font=(MONO, 8), bg=C["card"], fg=C["muted"]).pack(side="left")
        tk.Label(ver_row, text="  →  ", font=(FONT, 8),
                 bg=C["card"], fg=C["muted"]).pack(side="left")
        tk.Label(ver_row, text=f"v{app.get('version','')}",
                 font=(MONO, 8, "bold"), bg=C["card"], fg=C["amber"]).pack(side="left")
        btns = tk.Frame(row, bg=C["card"])
        btns.pack(side="right", padx=14)
        HoverButton(btns, "Update", lambda a=app: self._do_update(a),
                    padx=16, pady=6).pack()

    # ══════════════════════════════════════════════════════════════════════
    # STORE PAGE
    # ══════════════════════════════════════════════════════════════════════
    def _page_store(self, parent):
        self._page_header(parent, "Store", "Download new apps to your launcher.")
        outer, _ = scrollable_frame(parent)

        cat_var = {"v": self._cat}
        cat_host = tk.Frame(outer, bg=C["base"])
        cat_host.pack(fill="x")
        list_host = tk.Frame(outer, bg=C["base"])
        list_host.pack(fill="x", padx=24)

        def _render():
            for w in list_host.winfo_children(): w.destroy()
            shown = 0
            for app in self.apps:
                if app.get("installed"): continue
                if cat_var["v"] != "All" and not _same_category(app.get("category"), cat_var["v"]): continue
                self._store_row(list_host, app)
                shown += 1
            if shown == 0:
                tk.Label(list_host, text="Nothing here yet.",
                         font=(FONT, 11), bg=C["base"], fg=C["muted"]
                         ).pack(pady=40)

        def _on_cat(c):
            cat_var["v"] = c
            self._cat = c
            for w in cat_host.winfo_children(): w.destroy()
            self._cat_tabs(cat_host, c, _on_cat)
            _render()

        self._cat_tabs(cat_host, cat_var["v"], _on_cat)
        _render()
        self._upsell_banner(outer)
        tk.Frame(outer, bg=C["base"], height=20).pack()

    def _store_row(self, parent, app):
        row = tk.Frame(parent, bg=C["card"])
        row.pack(fill="x", pady=3)
        tk.Frame(row, bg=C["card_border"], width=3).pack(side="left", fill="y")

        icon_badge(row, app, size=42).pack(side="left", padx=14, pady=12)

        info = tk.Frame(row, bg=C["card"])
        info.pack(side="left", fill="both", expand=True, pady=12)
        name_row = tk.Frame(info, bg=C["card"])
        name_row.pack(anchor="w")
        tk.Label(name_row, text=app["name"], font=(FONT, 11, "bold"),
                 bg=C["card"], fg=C["white"]).pack(side="left")
        tk.Label(name_row, text=f"  {app.get('category','')}",
                 font=(FONT, 8), bg=C["card"], fg=C["muted"]).pack(side="left", pady=2)
        tk.Label(info, text=app["description"], font=(FONT, 9),
                 bg=C["card"], fg=C["sub"]).pack(anchor="w")

        btns = tk.Frame(row, bg=C["card"])
        btns.pack(side="right", padx=14)
        HoverButton(btns, "Download", lambda a=app: self._do_download(a),
                    padx=14, pady=6).pack(side="left", padx=(0, 8))
        tk.Label(btns, text="🔒", bg=C["card"], fg=C["muted"]).pack(side="left")
        self._uc_banner(row, app)

    # ══════════════════════════════════════════════════════════════════════
    # UPSELL BANNER
    # ══════════════════════════════════════════════════════════════════════
    def _upsell_banner(self, parent):
        outer = tk.Frame(parent, bg=C["accent"])
        outer.pack(fill="x", padx=24, pady=20)
        inner = tk.Frame(outer, bg=C["accent"])
        inner.pack(fill="x", padx=18, pady=14)
        left = tk.Frame(inner, bg=C["accent"])
        left.pack(side="left", fill="both", expand=True)
        tk.Label(left, text="★  Get more with Pro",
                 font=(FONT, 12, "bold"), bg=C["accent"], fg=C["white"]
                 ).pack(anchor="w")
        tk.Label(left, text="Unlock all apps, premium support, and early access.",
                 font=(FONT, 9), bg=C["accent"], fg="#B9CBE3"
                 ).pack(anchor="w", pady=2)
        HoverButton(inner, "Upgrade →",
                    lambda: messagebox.showinfo("Pro", "Upgrade coming soon!"),
                    bg=C["white"], fg=C["accent"], hover_bg="#E5ECF5",
                    padx=18, pady=7,
                    ).pack(side="right")

    # ══════════════════════════════════════════════════════════════════════
    # ACTIONS
    # ══════════════════════════════════════════════════════════════════════
    def _nav_goto(self, page):
        self._page = page
        self._show_page(page)    # lazy rebuild if dirty
        self._refresh_sidebar()  # repaint nav items only — no destroy

    def _do_download(self, app):
        GetAppDialog(self, app, self.registry, self._refresh_all)

    def _do_update(self, app):
        """Open the download dialog in update mode — same flow, clears has_update on completion."""
        GetAppDialog(self, app, self.registry, self._refresh_all, is_update=True)

    def _update_all(self, apps_with_updates):
        """Queue update dialogs one at a time for every app that has an update."""
        pending = list(apps_with_updates)

        def _next():
            if not pending:
                self._refresh_all()
                Toast(self, "✓  All updates complete", "success")
                return
            app = pending.pop(0)
            GetAppDialog(self, app, self.registry, _next, is_update=True)

        _next()

    def _uninstall(self, app):
        if not messagebox.askyesno("Uninstall", f"Remove {app['name']}?",
                                   icon="warning"):
            return
        uninstall_app(app)
        for a in self.apps:
            if a["id"] == app["id"]:
                a["installed"] = False
        save_registry(self.registry)
        self._refresh_all()
        Toast(self, f"{app['name']} removed", "info")

    def _app_context_menu(self, app):
        menu = tk.Menu(self, tearoff=0, bg=C["card"], fg=C["text"],
                       activebackground=C["accent"], activeforeground=C["white"],
                       bd=0, relief="flat")
        menu.add_command(label="Open",       command=lambda: launch_app(app))
        menu.add_separator()
        menu.add_command(label="Properties", command=lambda: self._show_props(app))
        menu.add_command(label="Uninstall",  command=lambda: self._uninstall(app))
        try:
            menu.tk_popup(self.winfo_pointerx(), self.winfo_pointery())
        finally:
            menu.grab_release()

    def _show_props(self, app):
        win = tk.Toplevel(self)
        win.title(app["name"])
        win.geometry("360x260")
        win.configure(bg=C["card"])
        win.resizable(False, False)
        tk.Label(win, text=app["name"], font=(FONT, 13, "bold"),
                 bg=C["card"], fg=C["white"]).pack(pady=(18, 2))
        sep(win)
        for k, v in app.items():
            row = tk.Frame(win, bg=C["card"])
            row.pack(fill="x", padx=20, pady=2)
            tk.Label(row, text=k, font=(MONO, 8), bg=C["card"],
                     fg=C["muted"], width=16, anchor="w").pack(side="left")
            tk.Label(row, text=str(v), font=(FONT, 9),
                     bg=C["card"], fg=C["text"]).pack(side="left")
