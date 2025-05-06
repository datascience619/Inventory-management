import smtplib
import sqlite3
import numpy as np
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
from sklearn.linear_model import LinearRegression
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Database setup
def create_db():
    print("[DEBUG] Initializing database...")
    con = sqlite3.connect("smart_inventory.db")
    cur = con.cursor()

    # Create tables
    cur.execute(""" 
    CREATE TABLE IF NOT EXISTS product (
        pid INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price REAL,
        qty INTEGER,
        reorder_point INTEGER,
        supplier TEXT
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS sales (
        sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        quantity INTEGER,
        sale_date TEXT,
        FOREIGN KEY (product_id) REFERENCES product(pid)
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS reorder (
        reorder_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        quantity INTEGER,
        reorder_date TEXT,
        FOREIGN KEY (product_id) REFERENCES product(pid)
    )""")

    con.commit()
    con.close()
    print("[DEBUG] Database setup complete.")

# Add a product to the database
def add_product_to_db(name, price, qty, reorder_point, supplier):
    print(f"[DEBUG] Adding product: {name}, Price: {price}, Qty: {qty}, Reorder Point: {reorder_point}, Supplier: {supplier}")

    try:
        con = sqlite3.connect("smart_inventory.db")
        cur = con.cursor()
        cur.execute("INSERT INTO product (name, price, qty, reorder_point, supplier) VALUES (?, ?, ?, ?, ?)",
                    (name, price, qty, reorder_point, supplier))
        con.commit()
        con.close()
        print("[DEBUG] Product added successfully.")
        return "Product added successfully."
    except Exception as e:
        print(f"[ERROR] Error adding product: {e}")
        return f"Error: {e}"

# Update inventory after a sale
def process_sale_in_db(product_name, quantity_sold):
    print(f"[DEBUG] Processing sale for product: {product_name}, Quantity Sold: {quantity_sold}")

    con = sqlite3.connect("smart_inventory.db")
    cur = con.cursor()

    cur.execute("SELECT pid, qty FROM product WHERE name = ?", (product_name,))
    product = cur.fetchone()

    if product:
        product_id, current_qty = product
        print(f"[DEBUG] Current Quantity: {current_qty}, Product ID: {product_id}")

        if current_qty >= quantity_sold:
            new_qty = current_qty - quantity_sold
            cur.execute("UPDATE product SET qty = ? WHERE pid = ?", (new_qty, product_id))

            sale_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cur.execute("INSERT INTO sales (product_id, quantity, sale_date) VALUES (?, ?, ?)",
                        (product_id, quantity_sold, sale_date))

            cur.execute("SELECT reorder_point FROM product WHERE pid = ?", (product_id,))
            reorder_point = cur.fetchone()[0]
            print(f"[DEBUG] Reorder Point: {reorder_point}")

            if new_qty <= reorder_point:
                reorder_quantity = 100
                reorder_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cur.execute("INSERT INTO reorder (product_id, quantity, reorder_date) VALUES (?, ?, ?)",
                            (product_id, reorder_quantity, reorder_date))
                print("[DEBUG] Reorder triggered.")

            con.commit()
            con.close()
            print("[DEBUG] Sale processed successfully.")
            return "Sale processed successfully."
        else:
            con.close()
            print("[DEBUG] Not enough stock to complete the sale.")
            return "Not enough stock to complete the sale."
    else:
        con.close()
        print("[DEBUG] Product not found in inventory.")
        return "Product not found in inventory."

# Predict demand for the next 7 days
def predict_demand_for_product(product_name):
    print(f"[DEBUG] Predicting demand for product: {product_name}")
    con = sqlite3.connect("smart_inventory.db")
    cur = con.cursor()

    cur.execute("SELECT name, qty, price FROM product WHERE name = ?", (product_name,))
    product_data = cur.fetchone()

    if not product_data:
        con.close()
        print("[DEBUG] Product not found in inventory.")
        return "Product not found in inventory."

    cur.execute("""
    SELECT strftime('%Y-%m-%d', sale_date) as sale_date, quantity
    FROM sales s
    JOIN product p ON s.product_id = p.pid
    WHERE p.name = ?
    """, (product_name,))

    sales_data = cur.fetchall()

    if not sales_data:
        con.close()
        print("[DEBUG] No sales data available for this product.")
        return "No sales data available for this product."

    dates = [row[0] for row in sales_data]
    quantities = [row[1] for row in sales_data]

    start_date = datetime.strptime(dates[0], '%Y-%m-%d')
    days = [(datetime.strptime(date, '%Y-%m-%d') - start_date).days for date in dates]

    X = np.array(days).reshape(-1, 1)
    y = np.array(quantities)

    model = LinearRegression()
    model.fit(X, y)

    future_days = np.array([[max(days) + i] for i in range(1, 8)])
    predicted_demand = model.predict(future_days)

    prediction_text = "Predicted Demand for Next 7 Days:\n"
    for i, prediction in enumerate(predicted_demand, 1):
        prediction_text += f"Day {i}: {prediction:.2f} units\n"

    con.close()
    print("[DEBUG] Demand prediction complete.")
    return prediction_text

# Show all product details
def show_all_product_data():
    con = sqlite3.connect("smart_inventory.db")
    cur = con.cursor()

    cur.execute("SELECT name, price, qty, reorder_point, supplier FROM product")
    all_products_data = cur.fetchall()

    if not all_products_data:
        con.close()
        return "No products available in inventory."

    product_text = "All Product Data:\n\n"
    for product in all_products_data:
        product_text += f"Product Name: {product[0]}\n"
        product_text += f"Price: ${product[1]:.2f}\n"
        product_text += f"Quantity in Stock: {product[2]}\n"
        product_text += f"Reorder Point: {product[3]}\n"
        product_text += f"Supplier: {product[4]}\n\n"

    con.close()
    return product_text

# Generate sales report
def generate_sales_report():
    con = sqlite3.connect("smart_inventory.db")
    cur = con.cursor()

    cur.execute("""
    SELECT p.name, SUM(s.quantity) AS total_qty, SUM(s.quantity * p.price) AS total_revenue
    FROM sales s
    JOIN product p ON s.product_id = p.pid
    GROUP BY p.name
    ORDER BY total_revenue DESC
    """)

    sales_data = cur.fetchall()

    if not sales_data:
        con.close()
        return "No sales data available."

    report_text = "Sales Report:\n\n"
    for row in sales_data:
        report_text += f"Product: {row[0]}\n"
        report_text += f"Total Quantity Sold: {row[1]}\n"
        report_text += f"Total Revenue: ${row[2]:.2f}\n\n"

    con.close()
    return report_text

def send_email_alert(subject, body, to_email):
    from_email = "sciencedata610@gmail.com"
    from_password = "sh114nafees"  # Consider using environment variables for security

    # Create message container
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    # Attach message body
    msg.attach(MIMEText(body, 'plain'))

    # Set up the SMTP server and send email
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)  # Gmail's SMTP server
        server.starttls()
        server.login(from_email, from_password)
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")

# GUI Class (within your InventoryApp)
class InventoryApp:
    def __init__(self, root):
        self.supplier = None
        self.root = root
        self.root.title("Smart Inventory Management")
        self.root.geometry("1000x700")
        self.root.state('zoomed')
        self.root.config(bg="#f0f0f0")
        self.create_widgets()

    def create_widgets(self):
        title_label = tk.Label(self.root, text="Smart Inventory Management", font=("Helvetica", 24, 'bold'),
                               fg="#4A90E2", bg="#f0f0f0")
        title_label.pack(pady=30)

        add_product_frame = tk.LabelFrame(self.root, text="Add Product", padx=20, pady=20,
                                          font=("Helvetica", 12, 'bold'), bg="#ffffff")
        add_product_frame.pack(padx=20, pady=10, fill="both", expand=True)

        tk.Label(add_product_frame, text="Product Name:", bg="#ffffff").grid(row=0, column=0, sticky="w", padx=10,pady=5)
        tk.Label(add_product_frame, text="Price:", bg="#ffffff").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        tk.Label(add_product_frame, text="Quantity:", bg="#ffffff").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        tk.Label(add_product_frame, text="Reorder Point:", bg="#ffffff").grid(row=3, column=0, sticky="w", padx=10,pady=5)
        tk.Label(add_product_frame, text="Supplier:", bg="#ffffff").grid(row=4, column=0, sticky="w", padx=10, pady=5)

        self.product_name = tk.Entry(add_product_frame)
        self.product_name.grid(row=0, column=1, padx=10, pady=5)
        self.price = tk.Entry(add_product_frame)
        self.price.grid(row=1, column=1, padx=10, pady=5)
        self.qty = tk.Entry(add_product_frame)
        self.qty.grid(row=2, column=1, padx=10, pady=5)
        self.reorder_point = tk.Entry(add_product_frame)
        self.reorder_point.grid(row=3, column=1, padx=10, pady=5)
        self.supplier = tk.Entry(add_product_frame)
        self.supplier.grid(row=4, column=1, padx=10, pady=5)

        # # Initialize supplier_var and supplier_menu here
        # self.supplier_var = tk.StringVar()
        # self.supplier_menu = tk.OptionMenu(add_product_frame, self.supplier_var, "")
        # self.supplier_menu.grid(row=4, column=1, padx=10, pady=5)

        add_button = tk.Button(add_product_frame, text="Add Product", bg="#4A90E2", fg="white",
                               command=self.add_product)
        add_button.grid(row=5, column=0, columnspan=2, pady=10)

        sales_frame = tk.LabelFrame(self.root, text="Process Sale", padx=20, pady=20, font=("Helvetica", 12, 'bold'),
                                    bg="#ffffff")
        sales_frame.pack(padx=20, pady=10, fill="both", expand=True)

        tk.Label(sales_frame, text="Product Name:", bg="#ffffff").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        tk.Label(sales_frame, text="Quantity Sold:", bg="#ffffff").grid(row=1, column=0, sticky="w", padx=10, pady=5)

        self.sale_product_name = tk.Entry(sales_frame)
        self.sale_product_name.grid(row=0, column=1, padx=10, pady=5)
        self.sale_qty = tk.Entry(sales_frame)
        self.sale_qty.grid(row=1, column=1, padx=10, pady=5)

        sale_button = tk.Button(sales_frame, text="Process Sale", bg="#4A90E2", fg="white", command=self.process_sale)
        sale_button.grid(row=2, column=0, columnspan=2, pady=10)

        demand_frame = tk.LabelFrame(self.root, text="Demand Prediction", padx=20, pady=20,
                                     font=("Helvetica", 12, 'bold'), bg="#ffffff")
        demand_frame.pack(padx=20, pady=10, fill="both", expand=True)

        tk.Label(demand_frame, text="Product Name:", bg="#ffffff").grid(row=0, column=0, sticky="w", padx=10, pady=5)

        self.demand_product_name = tk.Entry(demand_frame)
        self.demand_product_name.grid(row=0, column=1, padx=10, pady=5)

        demand_button = tk.Button(demand_frame, text="Predict Demand", bg="#4A90E2", fg="white",
                                  command=self.predict_demand)
        demand_button.grid(row=1, column=0, columnspan=2, pady=10)

        # Horizontal button frame for 'Generate Bill', 'Generate Report', and 'Show Data'
        button_frame = tk.Frame(self.root, bg="#f0f0f0")
        button_frame.pack(pady=20)

        bill_button = tk.Button(button_frame, text="Generate Bill", bg="#4A90E2", fg="white",
                                command=self.generate_bill)
        bill_button.grid(row=0, column=0, padx=10)

        report_button = tk.Button(button_frame, text="Generate Sales Report", bg="#4A90E2", fg="white",
                                  command=self.generate_report)
        report_button.grid(row=0, column=1, padx=10)

        show_data_button = tk.Button(button_frame, text="Show Data", bg="#4A90E2", fg="white",
                                     command=self.show_all_data)
        show_data_button.grid(row=0, column=2, padx=10)

        # Load suppliers after UI is created

    def load_suppliers(self):
        """Fetch all supplier names from the database and update the supplier dropdown."""
        con = sqlite3.connect("smart_inventory.db")
        cur = con.cursor()
        cur.execute("SELECT DISTINCT supplier FROM product")
        suppliers = [row[0] for row in cur.fetchall()]
        con.close()

        if not suppliers:
            suppliers = ["No suppliers available"]

        # Update dropdown menu
        self.supplier_menu["menu"].delete(0, "end")
        for supplier in suppliers:
            self.supplier_menu["menu"].add_command(label=supplier, command=tk._setit(self.supplier_var, supplier))

        self.supplier_var.set(suppliers[0])  # Set default selection

    def add_product(self):
        name = self.product_name.get()
        price = float(self.price.get())
        qty = int(self.qty.get())
        reorder_point = int(self.reorder_point.get())
        supplier = self.supplier.get()

        result = add_product_to_db(name, price, qty, reorder_point, supplier)
        messagebox.showinfo("Product Status", result)

    def process_sale(self):
        product_name = self.sale_product_name.get()
        try:
            quantity_sold = int(self.sale_qty.get())
        except ValueError:
            messagebox.showerror("Input Error", "Please enter a valid quantity")
            return

        result = process_sale_in_db(product_name, quantity_sold)
        if "sale processed" in result.lower():
            message = f"Sale processed successfully!\nProduct: {product_name}\nQuantity Sold: {quantity_sold}"
        else:
            message = f"Error: {result}"

        messagebox.showinfo("Sale Status", message)

    def generate_bill(self):
        product_name = self.sale_product_name.get()
        try:
            quantity_sold = int(self.sale_qty.get())
        except ValueError:
            messagebox.showerror("Input Error", "Please enter a valid quantity")
            return

        con = sqlite3.connect("smart_inventory.db")
        cur = con.cursor()

        # Fetch product details from the database
        cur.execute("SELECT name, price FROM product WHERE name = ?", (product_name,))
        product = cur.fetchone()

        if not product:
            con.close()
            messagebox.showerror("Error", f"Product '{product_name}' not found in inventory.")
            return

        product_name, price = product
        total = price * quantity_sold
        bill_text = f"========== Bill ==========\n"
        bill_text += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        bill_text += f"{product_name}: {quantity_sold} x {price:.2f} = {total:.2f}\n"
        bill_text += "\n==========================\n"
        bill_text += f"Total: {total:.2f}\n"
        bill_text += "==========================\n"

        con.close()
        messagebox.showinfo("Bill Generated", bill_text)

    def predict_demand(self):
        product_name = self.demand_product_name.get()
        result = predict_demand_for_product(product_name)
        messagebox.showinfo("Demand Prediction", result)

    def show_all_data(self):
        product_data = show_all_product_data()
        messagebox.showinfo("All Product Data", product_data)

    def create_scrollable_window(self, product_data):
        scroll_window = tk.Toplevel(self.root)
        scroll_window.title("Product Data")
        scroll_window.geometry("600x400")

        canvas = tk.Canvas(scroll_window)
        scrollbar = tk.Scrollbar(scroll_window, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Populate the scrollable frame with product data
        product_lines = product_data.splitlines()
        for line in product_lines:
            tk.Label(scrollable_frame, text=line, anchor="w").pack(fill="x")

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def generate_report(self):
        report = generate_sales_report()
        messagebox.showinfo("Sales Report", report)

if __name__ == "__main__":
    create_db()
    root = tk.Tk()
    app = InventoryApp(root)
    root.mainloop()
