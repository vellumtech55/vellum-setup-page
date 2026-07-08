import os
import sqlite3
import customtkinter as ctk
from tkinter import messagebox

# ---- Theme: black / gray / blue ----
BG_COLOR = "#0d0d0d"
PANEL_COLOR = "#1a1a1a"
GRAY = "#2b2b2b"
GRAY_LIGHT = "#3d3d3d"
BLUE = "#2f7dd6"
BLUE_HOVER = "#255fa8"
RED = "#c0392b"
RED_HOVER = "#992d22"
TEXT_COLOR = "#e6e6e6"
SUBTEXT_COLOR = "#9aa0a6"

DB_FILE = os.path.join(os.path.expanduser("~"), ".inventory_tracker.db")

ctk.set_appearance_mode("dark")


class InventoryApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Inventory Tracker")
        self.geometry("620x560")
        self.minsize(560, 480)
        self.configure(fg_color=BG_COLOR)

        self.db_conn = self.init_db()
        self.inventory = self.load_inventory()

        self._build_ui()
        self.refresh_list()

    # ---------- Persistence (SQLite) ----------
    def init_db(self):
        try:
            conn = sqlite3.connect(DB_FILE)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS inventory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    qty INTEGER NOT NULL DEFAULT 1
                )
            """)
            conn.commit()
            return conn
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Could not open database: {e}")
            raise

    def load_inventory(self):
        try:
            cursor = self.db_conn.execute("SELECT id, name, qty FROM inventory ORDER BY id")
            return [{"id": r[0], "name": r[1], "qty": r[2]} for r in cursor.fetchall()]
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Could not read inventory: {e}")
            return []

    def db_insert(self, name, qty):
        try:
            cursor = self.db_conn.execute(
                "INSERT INTO inventory (name, qty) VALUES (?, ?)", (name, qty)
            )
            self.db_conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Could not save item: {e}")
            return None

    def db_delete(self, item_id):
        try:
            self.db_conn.execute("DELETE FROM inventory WHERE id = ?", (item_id,))
            self.db_conn.commit()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Could not delete item: {e}")

    def db_clear_all(self):
        try:
            self.db_conn.execute("DELETE FROM inventory")
            self.db_conn.commit()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Could not clear inventory: {e}")

    # ---------- UI ----------
    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(24, 8))

        ctk.CTkLabel(
            header, text="Inventory Tracker",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=TEXT_COLOR
        ).pack(anchor="w")

        ctk.CTkLabel(
            header, text="Track items and quantities",
            font=ctk.CTkFont(size=13),
            text_color=SUBTEXT_COLOR
        ).pack(anchor="w", pady=(2, 0))

        # Input panel
        input_frame = ctk.CTkFrame(self, fg_color=PANEL_COLOR, corner_radius=10)
        input_frame.pack(fill="x", padx=24, pady=12)

        row = ctk.CTkFrame(input_frame, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=16)

        self.name_entry = ctk.CTkEntry(
            row, placeholder_text="Item name",
            fg_color=GRAY, border_color=GRAY_LIGHT, border_width=1,
            text_color=TEXT_COLOR
        )
        self.name_entry.pack(side="left", fill="x", expand=True, ipady=4)
        self.name_entry.bind("<Return>", lambda e: self.add_item())

        self.qty_entry = ctk.CTkEntry(
            row, placeholder_text="Qty", width=70,
            fg_color=GRAY, border_color=GRAY_LIGHT, border_width=1,
            text_color=TEXT_COLOR
        )
        self.qty_entry.pack(side="left", padx=(8, 0), ipady=4)
        self.qty_entry.bind("<Return>", lambda e: self.add_item())

        ctk.CTkButton(
            row, text="Add Item", width=100,
            fg_color=BLUE, hover_color=BLUE_HOVER, text_color="#ffffff",
            command=self.add_item
        ).pack(side="left", padx=(8, 0))

        # List panel
        list_frame = ctk.CTkFrame(self, fg_color=PANEL_COLOR, corner_radius=10)
        list_frame.pack(fill="both", expand=True, padx=24, pady=(0, 12))

        ctk.CTkLabel(
            list_frame, text="Current Inventory", text_color=SUBTEXT_COLOR,
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w", padx=16, pady=(12, 4))

        self.list_container = ctk.CTkScrollableFrame(
            list_frame, fg_color=GRAY, corner_radius=8
        )
        self.list_container.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        self.selected_id = None
        self.item_rows = []

        # Action buttons
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.pack(fill="x", padx=24, pady=(0, 24))

        self.delete_button = ctk.CTkButton(
            action_frame, text="Delete Selected", height=38,
            fg_color=RED, hover_color=RED_HOVER, text_color="#ffffff",
            command=self.delete_item
        )
        self.delete_button.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(
            action_frame, text="Clear All", height=38,
            fg_color=GRAY_LIGHT, hover_color=GRAY, text_color=TEXT_COLOR,
            command=self.clear_all
        ).pack(side="left", fill="x", expand=True, padx=(8, 0))

    # ---------- Logic ----------
    def add_item(self):
        name = self.name_entry.get().strip()
        qty_raw = self.qty_entry.get().strip()

        if not name:
            messagebox.showwarning("Warning", "Item name cannot be empty")
            return

        qty = 1
        if qty_raw:
            try:
                qty = int(qty_raw)
            except ValueError:
                messagebox.showwarning("Warning", "Quantity must be a whole number")
                return

        new_id = self.db_insert(name, qty)
        if new_id is not None:
            self.inventory.append({"id": new_id, "name": name, "qty": qty})
            self.refresh_list()

        self.name_entry.delete(0, "end")
        self.qty_entry.delete(0, "end")
        self.name_entry.focus()

    def delete_item(self):
        if self.selected_id is None:
            messagebox.showwarning("Warning", "No item selected")
            return

        self.db_delete(self.selected_id)
        self.inventory = [i for i in self.inventory if i["id"] != self.selected_id]
        self.selected_id = None
        self.refresh_list()

    def clear_all(self):
        if not self.inventory:
            return
        if messagebox.askyesno("Confirm", "Clear the entire inventory?"):
            self.db_clear_all()
            self.inventory = []
            self.selected_id = None
            self.refresh_list()

    def select_row(self, item_id):
        self.selected_id = item_id
        self.refresh_list()

    def refresh_list(self):
        for widget in self.item_rows:
            widget.destroy()
        self.item_rows = []

        if not self.inventory:
            empty_label = ctk.CTkLabel(
                self.list_container, text="No items yet",
                text_color=SUBTEXT_COLOR
            )
            empty_label.pack(pady=20)
            self.item_rows.append(empty_label)
            return

        for item in self.inventory:
            is_selected = (item["id"] == self.selected_id)
            row = ctk.CTkFrame(
                self.list_container,
                fg_color=BLUE if is_selected else "transparent",
                corner_radius=6
            )
            row.pack(fill="x", pady=2, padx=2)

            name_label = ctk.CTkLabel(
                row, text=item["name"], text_color=TEXT_COLOR,
                font=ctk.CTkFont(size=13), anchor="w"
            )
            name_label.pack(side="left", fill="x", expand=True, padx=(10, 4), pady=8)

            qty_label = ctk.CTkLabel(
                row, text=f"Qty: {item['qty']}", text_color=SUBTEXT_COLOR,
                font=ctk.CTkFont(size=12)
            )
            qty_label.pack(side="right", padx=(4, 10), pady=8)

            for widget in (row, name_label, qty_label):
                widget.bind("<Button-1>", lambda e, item_id=item["id"]: self.select_row(item_id))

            self.item_rows.append(row)


def on_close(app):
    app.db_conn.close()
    app.destroy()


if __name__ == "__main__":
    app = InventoryApp()
    app.protocol("WM_DELETE_WINDOW", lambda: on_close(app))
    app.mainloop()
