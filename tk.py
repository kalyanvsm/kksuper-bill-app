import tkinter as tk
from tkinter import ttk

class BillingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Billing Application")

        # Create tabs
        self.tabControl = ttk.Notebook(self.root)

        # Billing Tab
        self.billing_tab = ttk.Frame(self.tabControl)
        self.tabControl.add(self.billing_tab, text='Billing')
        self.create_billing_tab()

        # Stock Tab
        self.stock_tab = ttk.Frame(self.tabControl)
        self.tabControl.add(self.stock_tab, text='Stock')
        self.create_stock_tab()

        # Customer Entry Tab
        self.customer_tab = ttk.Frame(self.tabControl)
        self.tabControl.add(self.customer_tab, text='Customer Entry')
        self.create_customer_tab()

        # Add tabs to the main window
        self.tabControl.pack(expand=1, fill="both")

    def create_billing_tab(self):
        # Add widgets for the billing tab
        label = ttk.Label(self.billing_tab, text="Billing Tab Content")
        label.pack(padx=10, pady=10)

        # Example: Entry for scanning barcode
        barcode_entry = ttk.Entry(self.billing_tab)
        barcode_entry.pack(pady=10)

        # Example: Button to print bill
        print_button = ttk.Button(self.billing_tab, text="Print Bill", command=self.print_bill)
        print_button.pack(pady=10)

    def create_stock_tab(self):
        # Add widgets for the stock tab
        label = ttk.Label(self.stock_tab, text="Stock Tab Content")
        label.pack(padx=10, pady=10)

    def create_customer_tab(self):
        # Add widgets for the customer entry tab
        label = ttk.Label(self.customer_tab, text="Customer Entry Tab Content")
        label.pack(padx=10, pady=10)

    def print_bill(self):
        # Add logic to print the bill
        print("Printing Bill...")

if __name__ == "__main__":
    root = tk.Tk()
    app = BillingApp(root)
    root.mainloop()
