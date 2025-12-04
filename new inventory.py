import smtplib, sqlite3, numpy as np, pandas as pd, json, hashlib, threading, warnings, math, io, os
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from tkinter.font import Font
import matplotlib.dates as mdates
from matplotlib.patches import FancyBboxPatch

warnings.filterwarnings('ignore')

DB_FILE = "smart_inventory_advanced.db"
plt.rcParams["axes.facecolor"] = "#fafafa"
plt.rcParams["figure.facecolor"] = "#fafafa"
plt.rcParams["xtick.color"] = "#333"
plt.rcParams["ytick.color"] = "#333"


# ------------------  THEME  ------------------
class Theme:
    def __init__(self):
        self.dark = False
        self.colors = {
            "bg": "#ffffff", "fg": "#2b2b2b", "accent": "#0078d4",
            "card": "#f3f3f3", "success": "#107c10", "danger": "#d13438"
        }

    def toggle(self):
        self.dark = not self.dark
        self.colors = {
            "bg": "#1e1e1e", "fg": "#cccccc", "accent": "#58a6ff",
            "card": "#252526", "success": "#89d185", "danger": "#f85149"
        } if self.dark else {
            "bg": "#ffffff", "fg": "#2b2b2b", "accent": "#0078d4",
            "card": "#f3f3f3", "success": "#107c10", "danger": "#d13438"
        }


theme = Theme()


# ------------------  DATABASE  ------------------
class AdvancedInventorySystem:
    def __init__(self):
        self.create_db()
        self.setup_ai_models()

    def create_db(self):
        with sqlite3.connect(DB_FILE) as con:
            cur = con.cursor()
            cur.execute("""
            CREATE TABLE IF NOT EXISTS product (
                pid INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, price REAL, cost REAL,
                qty INTEGER, min_stock INTEGER, max_stock INTEGER, reorder_point INTEGER,
                supplier_id INTEGER, category TEXT, sku TEXT UNIQUE, last_updated TEXT,
                FOREIGN KEY (supplier_id) REFERENCES supplier(supplier_id))""")
            cur.execute("""
            CREATE TABLE IF NOT EXISTS supplier (
                supplier_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, email TEXT,
                phone TEXT, address TEXT, rating REAL, delivery_time INTEGER)""")
            cur.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                sale_id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER, quantity INTEGER,
                sale_date TEXT, revenue REAL, customer_id INTEGER,
                FOREIGN KEY (product_id) REFERENCES product(pid))""")
            cur.execute("""
            CREATE TABLE IF NOT EXISTS customer (
                customer_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT,
                phone TEXT, loyalty_points INTEGER DEFAULT 0)""")
            cur.execute("""
            CREATE TABLE IF NOT EXISTS purchase_order (
                po_id INTEGER PRIMARY KEY AUTOINCREMENT, supplier_id INTEGER, product_id INTEGER,
                quantity INTEGER, order_date TEXT, expected_date TEXT, status TEXT, total_cost REAL,
                FOREIGN KEY (supplier_id) REFERENCES supplier(supplier_id),
                FOREIGN KEY (product_id) REFERENCES product(pid))""")
            cur.execute("""
            CREATE TABLE IF NOT EXISTS inventory_alert (
                alert_id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER, alert_type TEXT,
                message TEXT, alert_date TEXT, resolved BOOLEAN DEFAULT 0,
                FOREIGN KEY (product_id) REFERENCES product(pid))""")
            cur.execute("""
            CREATE TABLE IF NOT EXISTS user (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE,
                password_hash TEXT, role TEXT, email TEXT)""")
            admin_hash = hashlib.sha256("admin123".encode()).hexdigest()
            cur.execute("INSERT OR IGNORE INTO user(username,password_hash,role,email) VALUES(?,?,?,?)",
                        ("admin", admin_hash, "admin", "admin@company.com"))
            # inject dummy suppliers if empty
            if not cur.execute("SELECT 1 FROM supplier LIMIT 1").fetchone():
                cur.executemany(
                    "INSERT INTO supplier(name,email,phone,address,rating,delivery_time) VALUES(?,?,?,?,?,?)",
                    [("TechParts Ltd", "tech@parts.com", "1234567890", "Silicon Valley", 4.8, 5),
                     ("Global Wholesale", "info@global.com", "0987654321", "New York", 4.5, 7)])
            con.commit()
        print("[DB] Ready")

    def setup_ai_models(self):
        self.demand_model = None
        self.scaler = StandardScaler()


# ------------------  AI  ------------------
class IntelligentDemandPredictor:
    def train_product_model(self, sales_df):
        if len(sales_df) < 10: return LinearRegression()
        sales_df = sales_df.copy()
        sales_df['day_of_week'] = pd.to_datetime(sales_df['date']).dt.dayofweek
        sales_df['month'] = pd.to_datetime(sales_df['date']).dt.month
        sales_df['lag7'] = sales_df['quantity'].shift(7).fillna(0)
        sales_df['roll7'] = sales_df['quantity'].rolling(7).mean().fillna(0)
        X = sales_df[['day_of_week', 'month', 'lag7', 'roll7']]
        y = sales_df['quantity']
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)
        return model


# ------------------  GUI  ------------------
class ModernInventoryApp:
    def __init__(self, root):
        self.root = root
        self.sys = AdvancedInventorySystem()
        self.pred = IntelligentDemandPredictor()
        self.current_user = None
        self.theme = theme
        self.root.title("Smart Inventory 2025")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 700)
        self.setup_styles()
        self.build_login()

    # ----------  STYLES  ----------
    def setup_styles(self):
        self.style = ttk.Style()
        self.update_style_sheet()

    def update_style_sheet(self):
        colors = self.theme.colors
        self.root.config(bg=colors["bg"])
        self.style.theme_use('clam')
        self.style.configure("TNotebook", background=colors["bg"], borderwidth=0)
        self.style.configure("TNotebook.Tab", background=colors["card"], foreground=colors["fg"],
                             padding=[10, 5], borderwidth=0, focuscolor=colors["accent"])
        self.style.map("TNotebook.Tab", background=[("selected", colors["accent"])],
                       foreground=[("selected", "#fff")])
        self.style.configure("Treeview", background=colors["card"], foreground=colors["fg"],
                             fieldbackground=colors["card"], borderwidth=0)
        self.style.configure("Treeview.Heading", background=colors["bg"], foreground=colors["fg"])
        self.style.map('Treeview', background=[('selected', colors["accent"])])
        self.style.configure("TLabelframe", background=colors["bg"], foreground=colors["fg"])
        self.style.configure("TLabelframe.Label", background=colors["bg"], foreground=colors["fg"])

    # ----------  LOGIN  ----------
    def build_login(self):
        for w in self.root.winfo_children(): w.destroy()
        frm = ttk.Frame(self.root)
        frm.place(relx=.5, rely=.5, anchor="center")
        ttk.Label(frm, text="Smart Inventory", font=("Segoe UI", 24, "bold")).grid(row=0, column=0, columnspan=2,
                                                                                   pady=10)
        ttk.Label(frm, text="Username").grid(row=1, column=0, sticky="w", pady=3)
        ttk.Label(frm, text="Password").grid(row=2, column=0, sticky="w", pady=3)
        self.u_ent = ttk.Entry(frm);
        self.u_ent.grid(row=1, column=1, padx=5)
        self.p_ent = ttk.Entry(frm, show="*");
        self.p_ent.grid(row=2, column=1, padx=5)
        self.u_ent.focus()
        ttk.Button(frm, text="Login", command=self.do_login).grid(row=3, column=0, columnspan=2, pady=15)
        self.root.bind("<Return>", lambda e: self.do_login())

    def do_login(self):
        u, p = self.u_ent.get(), self.p_ent.get()
        with sqlite3.connect(DB_FILE) as con:
            cur = con.cursor()
            cur.execute("SELECT 1 FROM user WHERE username=? AND password_hash=?",
                        (u, hashlib.sha256(p.encode()).hexdigest()))
            if cur.fetchone():
                self.current_user = u
                self.build_main_ui()
            else:
                messagebox.showerror("Login failed", "Invalid credentials")

    # ----------  MAIN UI  ----------
    def build_main_ui(self):
        for w in self.root.winfo_children(): w.destroy()
        # header
        hdr = tk.Frame(self.root, bg=self.theme.colors["accent"], height=60)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Smart Inventory 2025", fg="white", bg=self.theme.colors["accent"],
                 font=("Segoe UI", 18, "bold")).pack(side="left", padx=20)
        tk.Label(hdr, text=f"Welcome, {self.current_user}", fg="white", bg=self.theme.colors["accent"],
                 font=("Segoe UI", 10)).pack(side="right", padx=20)
        ttk.Button(hdr, text="🌙", command=self.toggle_theme, width=3).pack(side="right", padx=5)

        # notebook
        self.nb = ttk.Notebook(self.root)
        self.nb.pack(fill="both", expand=True, padx=10, pady=10)
        self.build_dashboard_tab()
        self.build_inventory_tab()
        self.build_sales_tab()
        self.build_suppliers_tab()
        self.build_analytics_tab()
        self.build_ai_tab()
        self.build_reports_tab()
        self.start_monitor()

    def toggle_theme(self):
        self.theme.toggle()
        self.update_style_sheet()
        self.build_main_ui()  # quick & dirty full reload

    # ----------  DASHBOARD  ----------
    def build_dashboard_tab(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text=" Dashboard ")
        # kpis
        kpi_bar = tk.Frame(tab, bg=self.theme.colors["bg"])
        kpi_bar.pack(fill="x", pady=10)
        kpis = self.get_kpis()
        for k, v in kpis.items():
            self.kpi_card(kpi_bar, k, v)
        # charts
        charts = tk.Frame(tab, bg=self.theme.colors["bg"])
        charts.pack(fill="both", expand=True)
        self.sales_chart(charts)
        self.inventory_health_chart(charts)

    def kpi_card(self, parent, title, value):
        f = tk.Frame(parent, bg=self.theme.colors["card"], relief="flat", bd=1)
        f.pack(side="left", expand=True, fill="both", padx=5)
        tk.Label(f, text=value, font=("Segoe UI", 22, "bold"), fg=self.theme.colors["accent"],
                 bg=self.theme.colors["card"]).pack(pady=(10, 0))
        tk.Label(f, text=title, font=("Segoe UI", 10), fg=self.theme.colors["fg"],
                 bg=self.theme.colors["card"]).pack(pady=(0, 10))

    def get_kpis(self):
        with sqlite3.connect(DB_FILE) as con:
            cur = con.cursor()
            total_value = cur.execute("SELECT SUM(price*qty) FROM product").fetchone()[0] or 0
            low_stock = cur.execute("SELECT COUNT(*) FROM product WHERE qty<=reorder_point").fetchone()[0]
            monthly_rev = \
            cur.execute("SELECT SUM(revenue) FROM sales WHERE sale_date>=date('now','-30 days')").fetchone()[0] or 0
            pending_po = cur.execute("SELECT COUNT(*) FROM purchase_order WHERE status='Pending'").fetchone()[0]
        return {"Total Value": f"${total_value:,.0f}", "Low-Stock Items": str(low_stock),
                "30-Day Revenue": f"${monthly_rev:,.0f}", "Pending PO": str(pending_po)}

    def sales_chart(self, parent):
        fig, ax = plt.subplots(figsize=(6, 3))
        with sqlite3.connect(DB_FILE) as con:
            df = pd.read_sql(
                "SELECT sale_date, SUM(revenue) rev FROM sales WHERE sale_date>=date('now','-30 days') GROUP BY sale_date ORDER BY sale_date",
                con)
        if not df.empty:
            df['sale_date'] = pd.to_datetime(df['sale_date'])
            ax.plot(df['sale_date'], df['rev'], marker='o', color=self.theme.colors["accent"])
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
            ax.set_title("Sales Trend (30 days)")
            ax.grid(alpha=.3)
        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(side="left", fill="both", expand=True)

    def inventory_health_chart(self, parent):
        fig, ax = plt.subplots(figsize=(6, 3))
        with sqlite3.connect(DB_FILE) as con:
            df = pd.read_sql(
                "SELECT CASE WHEN qty=0 THEN 'Out of Stock' WHEN qty<=reorder_point THEN 'Low' ELSE 'OK' END status, COUNT(*) c FROM product GROUP BY status",
                con)
        if not df.empty:
            ax.pie(df['c'], labels=df['status'], autopct='%1.0f%%',
                   colors=[self.theme.colors["danger"], self.theme.colors["success"], self.theme.colors["accent"]])
            ax.set_title("Inventory Health")
        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(side="left", fill="both", expand=True)

    # ----------  INVENTORY  ----------
    def build_inventory_tab(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text=" Inventory ")
        # form
        frm = ttk.LabelFrame(tab, text="Product", padding=10)
        frm.pack(fill="x", padx=10, pady=5)
        self.inv_vars = {}
        fields = [("Name", ""), ("SKU", ""), ("Price", "0"), ("Cost", "0"), ("Quantity", "0"),
                  ("Min Stock", "0"), ("Max Stock", "0"), ("Reorder", "0"), ("Category", "")]
        for i, (k, d) in enumerate(fields):
            ttk.Label(frm, text=k).grid(row=i // 3, column=(i % 3) * 2, sticky="w", padx=5, pady=3)
            ent = ttk.Entry(frm);
            ent.insert(0, d);
            ent.grid(row=i // 3, column=(i % 3) * 2 + 1, padx=5, pady=3, sticky="ew");
            self.inv_vars[k.lower().replace(" ", "_")] = ent
        ttk.Label(frm, text="Supplier").grid(row=3, column=4, sticky="w", padx=5)
        self.supp_var = tk.StringVar()
        self.supp_cb = ttk.Combobox(frm, textvariable=self.supp_var, state="readonly", width=15)
        self.supp_cb.grid(row=3, column=5, padx=5, sticky="ew")
        self.load_suppliers()
        btn_bar = ttk.Frame(frm)
        btn_bar.grid(row=4, column=0, columnspan=6, pady=10)
        ttk.Button(btn_bar, text="Add", command=self.add_product).pack(side="left", padx=3)
        ttk.Button(btn_bar, text="Update", command=self.update_product).pack(side="left", padx=3)
        ttk.Button(btn_bar, text="Delete", command=self.delete_product).pack(side="left", padx=3)
        ttk.Button(btn_bar, text="Export CSV", command=self.export_inventory_csv).pack(side="left", padx=3)
        # tree
        tree_frm = ttk.LabelFrame(tab, text="Current Stock", padding=10)
        tree_frm.pack(fill="both", expand=True, padx=10, pady=5)
        cols = ("ID", "Name", "SKU", "Price", "Cost", "Qty", "Min", "Max", "Reorder", "Category", "Supplier")
        self.inv_tree = ttk.Treeview(tree_frm, columns=cols, show="headings", height=12)
        for c in cols: self.inv_tree.heading(c, text=c); self.inv_tree.column(c, width=80)
        vsb = ttk.Scrollbar(tree_frm, orient="vertical", command=self.inv_tree.yview)
        self.inv_tree.configure(yscrollcommand=vsb.set)
        self.inv_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        tree_frm.rowconfigure(0, weight=1);
        tree_frm.columnconfigure(0, weight=1)
        self.inv_tree.bind("<<TreeviewSelect>>", self.on_inv_select)
        self.load_inventory()

    def load_suppliers(self):
        with sqlite3.connect(DB_FILE) as con:
            sups = [r[0] for r in con.execute("SELECT name FROM supplier").fetchall()]
        self.supp_cb['values'] = sups
        if sups: self.supp_var.set(sups[0])

    def add_product(self):
        try:
            # Get values from form fields
            name = self.inv_vars['name'].get()
            sku = self.inv_vars['sku'].get()
            price = float(self.inv_vars['price'].get())
            cost = float(self.inv_vars['cost'].get())
            quantity = int(self.inv_vars['quantity'].get())
            min_stock = int(self.inv_vars['min_stock'].get())
            max_stock = int(self.inv_vars['max_stock'].get())
            reorder_point = int(self.inv_vars['reorder'].get())
            category = self.inv_vars['category'].get()
            sup_name = self.supp_var.get()

            with sqlite3.connect(DB_FILE) as con:
                # Get supplier ID
                sup_id = con.execute("SELECT supplier_id FROM supplier WHERE name=?", (sup_name,)).fetchone()
                if not sup_id:
                    messagebox.showerror("Error", "Supplier not found")
                    return
                sup_id = sup_id[0]

                # Insert product
                con.execute("""INSERT INTO product(name,sku,price,cost,qty,min_stock,max_stock,reorder_point,category,supplier_id,last_updated)
                               VALUES(?,?,?,?,?,?,?,?,?,?,datetime('now'))""",
                            (name, sku, price, cost, quantity, min_stock, max_stock, reorder_point, category, sup_id))
                con.commit()

            messagebox.showinfo("Success", "Product added successfully")
            self.load_inventory()
            self.clear_inv_form()

        except sqlite3.IntegrityError as e:
            messagebox.showerror("Error", "Product name or SKU already exists")
        except ValueError as e:
            messagebox.showerror("Error", "Please enter valid numeric values for price, cost, and quantities")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add product: {str(e)}")

    def update_product(self):
        selected = self.inv_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a product to update")
            return

        pid = self.inv_tree.item(selected[0])['values'][0]  # Get ID from first column
        try:
            # Get values from form fields
            name = self.inv_vars['name'].get()
            sku = self.inv_vars['sku'].get()
            price = float(self.inv_vars['price'].get())
            cost = float(self.inv_vars['cost'].get())
            quantity = int(self.inv_vars['quantity'].get())
            min_stock = int(self.inv_vars['min_stock'].get())
            max_stock = int(self.inv_vars['max_stock'].get())
            reorder_point = int(self.inv_vars['reorder'].get())
            category = self.inv_vars['category'].get()
            sup_name = self.supp_var.get()

            with sqlite3.connect(DB_FILE) as con:
                # Get supplier ID
                sup_id = con.execute("SELECT supplier_id FROM supplier WHERE name=?", (sup_name,)).fetchone()
                if not sup_id:
                    messagebox.showerror("Error", "Supplier not found")
                    return
                sup_id = sup_id[0]

                # Update product
                con.execute("""UPDATE product SET name=?,sku=?,price=?,cost=?,qty=?,min_stock=?,max_stock=?,reorder_point=?,category=?,supplier_id=?,last_updated=datetime('now') 
                               WHERE pid=?""",
                            (name, sku, price, cost, quantity, min_stock, max_stock, reorder_point, category, sup_id,
                             pid))
                con.commit()

            messagebox.showinfo("Success", "Product updated successfully")
            self.load_inventory()

        except sqlite3.IntegrityError as e:
            messagebox.showerror("Error", "Product name or SKU already exists")
        except ValueError as e:
            messagebox.showerror("Error", "Please enter valid numeric values for price, cost, and quantities")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update product: {str(e)}")

    def delete_product(self):
        selected = self.inv_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a product to delete")
            return

        pid = self.inv_tree.item(selected[0])['values'][0]  # Get ID from first column

        if messagebox.askyesno("Confirm", "Are you sure you want to delete this product?"):
            try:
                with sqlite3.connect(DB_FILE) as con:
                    con.execute("DELETE FROM product WHERE pid=?", (pid,))
                    con.commit()

                messagebox.showinfo("Success", "Product deleted successfully")
                self.load_inventory()
                self.clear_inv_form()

            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete product: {str(e)}")

    def export_inventory_csv(self):
        file = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not file: return
        try:
            with sqlite3.connect(DB_FILE) as con:
                df = pd.read_sql(
                    "SELECT p.*, s.name supplier FROM product p LEFT JOIN supplier s ON p.supplier_id=s.supplier_id",
                    con)
                df.to_csv(file, index=False)
            messagebox.showinfo("Export", "Saved to " + file)
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def load_inventory(self):
        for i in self.inv_tree.get_children():
            self.inv_tree.delete(i)
        try:
            with sqlite3.connect(DB_FILE) as con:
                for row in con.execute("""SELECT p.pid, p.name, p.sku, p.price, p.cost, p.qty, p.min_stock, p.max_stock, p.reorder_point, p.category, s.name
                                          FROM product p LEFT JOIN supplier s ON p.supplier_id=s.supplier_id"""):
                    self.inv_tree.insert("", "end", values=row)
        except Exception as e:
            print(f"Error loading inventory: {e}")

    def on_inv_select(self, event):
        sel = self.inv_tree.selection()
        if not sel: return
        try:
            vals = self.inv_tree.item(sel[0])['values']
            # Fill form with selected product data
            self.inv_vars['name'].delete(0, tk.END)
            self.inv_vars['name'].insert(0, vals[1] if len(vals) > 1 else "")

            self.inv_vars['sku'].delete(0, tk.END)
            self.inv_vars['sku'].insert(0, vals[2] if len(vals) > 2 else "")

            self.inv_vars['price'].delete(0, tk.END)
            self.inv_vars['price'].insert(0, vals[3] if len(vals) > 3 else "0")

            self.inv_vars['cost'].delete(0, tk.END)
            self.inv_vars['cost'].insert(0, vals[4] if len(vals) > 4 else "0")

            self.inv_vars['quantity'].delete(0, tk.END)
            self.inv_vars['quantity'].insert(0, vals[5] if len(vals) > 5 else "0")

            self.inv_vars['min_stock'].delete(0, tk.END)
            self.inv_vars['min_stock'].insert(0, vals[6] if len(vals) > 6 else "0")

            self.inv_vars['max_stock'].delete(0, tk.END)
            self.inv_vars['max_stock'].insert(0, vals[7] if len(vals) > 7 else "0")

            self.inv_vars['reorder'].delete(0, tk.END)
            self.inv_vars['reorder'].insert(0, vals[8] if len(vals) > 8 else "0")

            self.inv_vars['category'].delete(0, tk.END)
            self.inv_vars['category'].insert(0, vals[9] if len(vals) > 9 else "")

            # Set supplier
            if len(vals) > 10 and vals[10]:
                self.supp_var.set(vals[10])

        except Exception as e:
            print(f"Error loading product data: {e}")

    def clear_inv_form(self):
        for ent in self.inv_vars.values():
            ent.delete(0, tk.END)
        # Reset to default values
        self.inv_vars['price'].insert(0, "0")
        self.inv_vars['cost'].insert(0, "0")
        self.inv_vars['quantity'].insert(0, "0")
        self.inv_vars['min_stock'].insert(0, "0")
        self.inv_vars['max_stock'].insert(0, "0")
        self.inv_vars['reorder'].insert(0, "0")

    # ----------  SALES  ----------
    def build_sales_tab(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text=" Sales ")
        frm = ttk.LabelFrame(tab, text="Record Sale", padding=10)
        frm.pack(fill="x", padx=10, pady=5)
        ttk.Label(frm, text="Product").grid(row=0, column=0, sticky="w")
        self.sale_prod = ttk.Combobox(frm, state="readonly", width=25)
        self.sale_prod.grid(row=0, column=1, padx=5)
        ttk.Label(frm, text="Quantity").grid(row=0, column=2, sticky="w")
        self.sale_qty = ttk.Spinbox(frm, from_=1, to=999, width=10)
        self.sale_qty.grid(row=0, column=3, padx=5)
        ttk.Button(frm, text="Record Sale", command=self.record_sale).grid(row=0, column=4, padx=15)
        ttk.Button(frm, text="Export Sales CSV", command=self.export_sales_csv).grid(row=0, column=5, padx=5)
        # tree
        tree_frm = ttk.LabelFrame(tab, text="Sales History", padding=10)
        tree_frm.pack(fill="both", expand=True, padx=10, pady=5)
        cols = ("ID", "Date", "Product", "Qty", "Revenue")
        self.sales_tree = ttk.Treeview(tree_frm, columns=cols, show="headings", height=12)
        for c in cols: self.sales_tree.heading(c, text=c); self.sales_tree.column(c, width=100)
        vsb = ttk.Scrollbar(tree_frm, orient="vertical", command=self.sales_tree.yview)
        self.sales_tree.configure(yscrollcommand=vsb.set)
        self.sales_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        tree_frm.rowconfigure(0, weight=1);
        tree_frm.columnconfigure(0, weight=1)
        self.load_sales_products();
        self.load_sales()

    def load_sales_products(self):
        with sqlite3.connect(DB_FILE) as con:
            prods = [r[0] for r in con.execute("SELECT name FROM product").fetchall()]
        self.sale_prod['values'] = prods
        if prods: self.sale_prod.set(prods[0])

    def record_sale(self):
        try:
            prod = self.sale_prod.get()
            qty = int(self.sale_qty.get())
            with sqlite3.connect(DB_FILE) as con:
                result = con.execute("SELECT pid, price, qty FROM product WHERE name=?", (prod,)).fetchone()
                if not result:
                    messagebox.showerror("Error", "Product not found")
                    return
                pid, price, current_qty = result

                # Check if enough stock
                if current_qty < qty:
                    messagebox.showerror("Error", f"Insufficient stock. Only {current_qty} available.")
                    return

                revenue = qty * price
                con.execute("INSERT INTO sales(product_id,quantity,sale_date,revenue) VALUES(?,?,datetime('now'),?)",
                            (pid, qty, revenue))
                con.execute("UPDATE product SET qty=qty-? WHERE pid=?", (qty, pid))
                con.commit()
            messagebox.showinfo("Success", "Sale recorded successfully")
            self.load_sales();
            self.load_inventory();
            self.check_alerts()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to record sale: {str(e)}")

    def export_sales_csv(self):
        file = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not file: return
        try:
            with sqlite3.connect(DB_FILE) as con:
                df = pd.read_sql("""SELECT s.sale_id, s.sale_date, p.name product, s.quantity, s.revenue
                                    FROM sales s JOIN product p ON s.product_id=p.pid ORDER BY s.sale_date DESC""", con)
                df.to_csv(file, index=False)
            messagebox.showinfo("Export", "Saved to " + file)
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def load_sales(self):
        for i in self.sales_tree.get_children():
            self.sales_tree.delete(i)
        try:
            with sqlite3.connect(DB_FILE) as con:
                for row in con.execute("""SELECT s.sale_id, s.sale_date, p.name, s.quantity, s.revenue
                                          FROM sales s JOIN product p ON s.product_id=p.pid ORDER BY s.sale_date DESC LIMIT 200"""):
                    self.sales_tree.insert("", "end", values=row)
        except Exception as e:
            print(f"Error loading sales: {e}")

    # ----------  SUPPLIERS  ----------
    def build_suppliers_tab(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text=" Suppliers ")
        frm = ttk.LabelFrame(tab, text="Add Supplier", padding=10)
        frm.pack(fill="x", padx=10, pady=5)
        fields = [("Name", ""), ("Email", ""), ("Phone", ""), ("Address", ""), ("Rating", "5"), ("Lead Days", "7")]
        self.sup_vars = {}
        for i, (k, d) in enumerate(fields):
            ttk.Label(frm, text=k).grid(row=0, column=i * 2, sticky="w", padx=5)
            ent = ttk.Entry(frm);
            ent.insert(0, d);
            ent.grid(row=0, column=i * 2 + 1, padx=5);
            self.sup_vars[k.lower().replace(" ", "_")] = ent
        ttk.Button(frm, text="Add", command=self.add_supplier).grid(row=0, column=len(fields) * 2, padx=10)
        # tree
        tree_frm = ttk.LabelFrame(tab, text="Suppliers", padding=10)
        tree_frm.pack(fill="both", expand=True, padx=10, pady=5)
        cols = ("ID", "Name", "Email", "Phone", "Address", "Rating", "Lead Days")
        self.sup_tree = ttk.Treeview(tree_frm, columns=cols, show="headings", height=12)
        for c in cols: self.sup_tree.heading(c, text=c); self.sup_tree.column(c, width=90)
        vsb = ttk.Scrollbar(tree_frm, orient="vertical", command=self.sup_tree.yview)
        self.sup_tree.configure(yscrollcommand=vsb.set)
        self.sup_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        tree_frm.rowconfigure(0, weight=1);
        tree_frm.columnconfigure(0, weight=1)
        self.load_suppliers_tab()

    def add_supplier(self):
        try:
            name = self.sup_vars['name'].get()
            email = self.sup_vars['email'].get()
            phone = self.sup_vars['phone'].get()
            address = self.sup_vars['address'].get()
            rating = float(self.sup_vars['rating'].get())
            lead_days = int(self.sup_vars['lead_days'].get())

            with sqlite3.connect(DB_FILE) as con:
                con.execute("INSERT INTO supplier(name,email,phone,address,rating,delivery_time) VALUES(?,?,?,?,?,?)",
                            (name, email, phone, address, rating, lead_days))
                con.commit()
            messagebox.showinfo("Success", "Supplier added successfully")
            self.load_suppliers_tab();
            self.load_suppliers()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Supplier name already exists")
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numeric values for rating and lead days")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add supplier: {str(e)}")

    def load_suppliers_tab(self):
        for i in self.sup_tree.get_children():
            self.sup_tree.delete(i)
        try:
            with sqlite3.connect(DB_FILE) as con:
                for row in con.execute("SELECT * FROM supplier"):
                    self.sup_tree.insert("", "end", values=row)
        except Exception as e:
            print(f"Error loading suppliers: {e}")

    # ----------  ANALYTICS  ----------
    def build_analytics_tab(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text=" Analytics ")
        ttk.Label(tab, text="Under construction – placeholder for advanced analytics", font=("Segoe UI", 16)).pack(
            pady=100)

    # ----------  AI  ----------
    def build_ai_tab(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text=" AI Prediction ")
        frm = ttk.LabelFrame(tab, text="Demand Prediction", padding=10)
        frm.pack(fill="x", padx=10, pady=5)
        ttk.Label(frm, text="Product").grid(row=0, column=0, sticky="w")
        self.ai_prod = ttk.Combobox(frm, state="readonly", width=25)
        self.ai_prod.grid(row=0, column=1, padx=5)
        ttk.Label(frm, text="Days ahead").grid(row=0, column=2, sticky="w")
        self.ai_days = ttk.Spinbox(frm, from_=7, to=365, width=10)
        self.ai_days.set(30)
        self.ai_days.grid(row=0, column=3, padx=5)
        ttk.Button(frm, text="Predict", command=self.run_prediction).grid(row=0, column=4, padx=15)
        # result
        txt_frm = ttk.Frame(tab)
        txt_frm.pack(fill="both", expand=True, padx=10, pady=5)
        self.ai_text = scrolledtext.ScrolledText(txt_frm, height=15, font=("Consolas", 10))
        self.ai_text.pack(fill="both", expand=True)
        self.load_ai_products()

    def load_ai_products(self):
        with sqlite3.connect(DB_FILE) as con:
            prods = [r[0] for r in con.execute("SELECT name FROM product").fetchall()]
        self.ai_prod['values'] = prods
        if prods: self.ai_prod.set(prods[0])

    def run_prediction(self):
        prod = self.ai_prod.get()
        days = int(self.ai_days.get())
        try:
            with sqlite3.connect(DB_FILE) as con:
                result = con.execute("SELECT pid FROM product WHERE name=?", (prod,)).fetchone()
                if not result:
                    messagebox.showerror("Error", "Product not found")
                    return
                pid = result[0]
                df = pd.read_sql("SELECT sale_date date, quantity FROM sales WHERE product_id=? ORDER BY sale_date",
                                 con, params=(pid,))
            if len(df) < 5:
                messagebox.showwarning("Data", "Insufficient sales history");
                return
            model = self.pred.train_product_model(df)
            future = pd.DataFrame(pd.date_range(start=datetime.now() + timedelta(1), periods=days), columns=['date'])
            future['day_of_week'] = future['date'].dt.dayofweek
            future['month'] = future['date'].dt.month
            future['lag7'] = df['quantity'].iloc[-7:].mean() if len(df) >= 7 else df['quantity'].mean()
            future['roll7'] = df['quantity'].iloc[-7:].mean() if len(df) >= 7 else df['quantity'].mean()
            preds = model.predict(future[['day_of_week', 'month', 'lag7', 'roll7']])
            total = sum(max(0, int(p)) for p in preds)
            self.ai_text.delete(1.0, tk.END)
            self.ai_text.insert(tk.END, f"AI Demand Prediction for {prod} – next {days} days\n")
            self.ai_text.insert(tk.END, "=" * 60 + "\n")
            for d, p in zip(future['date'], preds):
                self.ai_text.insert(tk.END, f"{d.strftime('%Y-%m-%d')}  –  {max(0, int(p))} units\n")
            self.ai_text.insert(tk.END, f"\nTotal forecast: {total} units\n")
        except Exception as e:
            messagebox.showerror("Prediction error", f"Failed to generate prediction: {str(e)}")

    # ----------  REPORTS  ----------
    def build_reports_tab(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text=" Reports ")
        ttk.Button(tab, text="Generate PDF Report", command=self.gen_pdf_report).pack(pady=20)

    def gen_pdf_report(self):
        try:
            from matplotlib.backends.backend_pdf import PdfPages
            file = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
            if not file: return
            with PdfPages(file) as pdf:
                # page 1 kpis
                fig = plt.figure(figsize=(8, 6))
                fig.text(0.5, 0.9, "Smart Inventory Report", ha="center", size=16)
                kpis = self.get_kpis()
                y = 0.8
                for k, v in kpis.items():
                    fig.text(0.1, y, f"{k}: {v}", size=12);
                    y -= 0.1
                pdf.savefig(fig);
                plt.close()
                # page 2 sales chart
                with sqlite3.connect(DB_FILE) as con:
                    df = pd.read_sql(
                        "SELECT sale_date, SUM(revenue) rev FROM sales WHERE sale_date>=date('now','-30 days') GROUP BY sale_date ORDER BY sale_date",
                        con)
                fig, ax = plt.subplots(figsize=(8, 6))
                if not df.empty:
                    df['sale_date'] = pd.to_datetime(df['sale_date'])
                    ax.plot(df['sale_date'], df['rev'], marker='o')
                    ax.set_title("30-Day Sales")
                pdf.savefig(fig);
                plt.close()
            messagebox.showinfo("Reports", "PDF saved to " + file)
        except Exception as e:
            messagebox.showerror("PDF error", f"Failed to generate PDF: {str(e)}")

    # ----------  MONITORING  ----------
    def start_monitor(self):
        def run():
            while True:
                try:
                    self.check_alerts()
                    threading.Event().wait(300)
                except:
                    pass

        t = threading.Thread(target=run, daemon=True);
        t.start()

    def check_alerts(self):
        try:
            with sqlite3.connect(DB_FILE) as con:
                cur = con.cursor()
                low = cur.execute(
                    "SELECT pid, name, qty, reorder_point FROM product WHERE qty<=reorder_point AND qty>0").fetchall()
                out = cur.execute("SELECT pid, name FROM product WHERE qty=0").fetchall()
                for pid, name, qty, rp in low:
                    if not cur.execute(
                            "SELECT 1 FROM inventory_alert WHERE product_id=? AND alert_type='low_stock' AND resolved=0",
                            (pid,)).fetchone():
                        cur.execute(
                            "INSERT INTO inventory_alert(product_id,alert_type,message,alert_date,resolved) VALUES(?,?,?,datetime('now'),0)",
                            (pid, 'low_stock', f"{name} is low ({qty} <= {rp})"))
                for pid, name in out:
                    if not cur.execute(
                            "SELECT 1 FROM inventory_alert WHERE product_id=? AND alert_type='out_of_stock' AND resolved=0",
                            (pid,)).fetchone():
                        cur.execute(
                            "INSERT INTO inventory_alert(product_id,alert_type,message,alert_date,resolved) VALUES(?,?,?,datetime('now'),0)",
                            (pid, 'out_of_stock', f"{name} is out of stock"))
                con.commit()
            if low or out:
                self.root.after(0, lambda: messagebox.showwarning("Inventory Alert",
                                                                  f"{len(low)} low-stock, {len(out)} out-of-stock items detected."))
        except Exception as e:
            print(f"Error checking alerts: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ModernInventoryApp(root)
    root.mainloop()
