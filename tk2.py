import tkinter as tk
from tkinter import ttk, Listbox, StringVar
from datetime import datetime
from escpos.printer import Usb
from tkinter import PhotoImage
from tkinter import messagebox
import barcode
from barcode.writer import ImageWriter
import json
import pandas as pd
import uuid
from tkinter import Tk, Label, Entry, Button, Text, StringVar
from sqlalchemy import create_engine, Column, Integer, String, Float, BigInteger, ForeignKey, DECIMAL, DateTime, Uuid, select
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# Database connection string (replace with your actual connection details)
DATABASE_URL = "sqlite:///supermarket.db"

# Create database engine and session
engine = create_engine(DATABASE_URL)

# Define base class for ORM models
Base = declarative_base()

# Define product model
class Product(Base):
    __tablename__ = 'products'
    id = Column(Uuid, primary_key=True)
    product_details = Column(String)
    cost = Column(Float)
    barcode = Column(BigInteger)
    discount = Column(Float)
    wholesale_cost = Column(Float)
    in_stock = Column(BigInteger)
    in_cost = Column(Float)

    # def __repr__(self):
    #     return dict({'id':self.id, 'product_details':self.product_details, 'barcode':self.barcode, 'cost':self.cost, 'discount':self.discount, 'wholesale_cost':self.wholesale_cost, 'in_stock':self.in_stock})

class Vendor(Base):
    __tablename__ = 'vendors'

    id = Column(Uuid, primary_key=True)
    name = Column(String(255))
    
    products = relationship('Product', secondary='product_vendors')

class ProductVendor(Base):
    __tablename__ = 'product_vendors'

    id = Column(Uuid, primary_key=True)
    barcode = Column(BigInteger, ForeignKey('products.barcode'))
    vendor_id = Column(Integer, ForeignKey('vendors.id'))
    cost_price = Column(Float)

class Discount(Base):
    __tablename__ = 'discounts'

    id = Column(Uuid, primary_key = True)
    barcode = Column(BigInteger, ForeignKey('products.barcode'))
    vendor_id = Column(Integer, ForeignKey('vendors.id'))
    discount_percentage = Column(Float)

class Bill(Base):
    __tablename__ = 'bills'

    id = Column(Uuid, primary_key = True)
    date = Column(String)
    # cashier_id = Column(Integer, ForeignKey('employees.id'))
    total = Column(Float)
    intake_amount = Column(Float)

    items = relationship('BillItem', backref='bill')

class BillItem(Base):
    __tablename__ = 'bill_items'

    id = Column(Uuid, primary_key = True)
    bill_id = Column(Uuid, ForeignKey('bills.id'))
    product_details = Column(String)
    quantity = Column(Integer)
    unit_price = Column(Float)
    discount = Column(Float)
    sub_total = Column(Float)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = SessionLocal()

def create_db():
    Base.metadata.create_all(bind=engine)


# # Function to create a database session
# def get_db():
#     db = SessionLocal()
#     print(type(db))
#     try:
#         yield db
#     finally:
#         db.close()



# Function to add a new product
def add_product(product_details, barcode, cost, discount=0.0, in_stock=1, wholesale_cost=0.0):
    # db = get_db()
    # print(type(db))
    new_product = Product(product_details=product_details, barcode=barcode, cost=cost, discount=discount, wholesale_cost=wholesale_cost, in_stock=in_stock)
    # with db as db:
    #     db.add(new_product)
    # # db.send(new_product)
    session.add(new_product)
    session.commit()
    #     db.commit()
    # db.close()
    # print("Product added successfully!")


# Function to search products by barcode
def search_product(barcode):
    # db = get_db()
    product = session.query(Product).filter_by(barcode=barcode).first()
    # session.close()
    if product:
        print("1.0", "end")
        print("end", f"Product Name: {product.name}\nBarcode: {product.barcode}\nCost: ${product.cost}")
    else:
        print("1.0", "end")
        print("end", "Product not found!")


# Function to update product details
def update_product(product_id, name, barcode, cost):
    
    product = session.query(Product).filter_by(id=product_id).first()
    if product:
        product.name = name
        product.barcode = barcode
        product.cost = cost
        session.commit()
        print("Product updated successfully!")
    else:
        print("Product not found!")
    # db.close()


class BillingApp:
    
    def __init__(self, root):

        self.vendor_id = 0x4b43
        self.product_id = 0x3830
        self.printer = Usb(self.vendor_id, self.product_id)
        self.printer.set_with_default()
        # global isListBoxFocused, current_index
        self.current_index = 0

        # self.read_stock()

        self.root = root
        self.root.title("Billing Application")
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        self.root.geometry(f"{screen_width}x{screen_height}+0+0")

        # Create tabs
        self.tabControl = ttk.Notebook(self.root)

        # self.root
        style = ttk.Style(self.root)
        # self.root.tk.call("source", "forest-light.tcl")
        # self.root.tk.call("source", "forest-dark.tcl")
        # style.theme_use("forest-dark")
        # , foreground='blue',background='#66cc99',
        style.configure("TNotebook.Tab", padding=(75, 4), font=('Palatino', 14, 'bold'), borderwidth=2, foreground='blue',background='#66cc99')

        # Billing Tab
        self.billing_tab = ttk.Frame(self.tabControl)
        self.tabControl.add(self.billing_tab, text='Billing')
        # self.tabControl.
        self.create_billing_tab()
        self.barcode_entry.focus_force()

        # Stock Tab
        self.stock_tab = ttk.Frame(self.tabControl)
        self.tabControl.add(self.stock_tab, text='Stock')
        self.create_stock_tab()

        # Customer Entry Tab
        self.wholesale_tab = ttk.Frame(self.tabControl)
        self.tabControl.add(self.wholesale_tab, text='Wholesale')
        self.create_wholesale_tab()

        self.barcode_gen_tab = ttk.Frame(self.tabControl)
        self.tabControl.add(self.barcode_gen_tab, text='Barcode')
        self.create_barcode_gen_tab()

        self.check_bills_tab = ttk.Frame(self.tabControl)
        self.tabControl.add(self.check_bills_tab, text='Check Bills')
        self.create_check_bills_tab()

        # Add tabs to the main window
        self.tabControl.pack(expand=True, fill="both")
        self.tabControl.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        self.root.bind("<Shift_R>", self.on_tab_pressed)
    
    def on_tab_changed(self, event):
        current_tab = self.tabControl.index("current")
        if current_tab == 0:
            self.barcode_entry.focus_force()
        elif current_tab == 1:
            self.stock_barcode_entry.focus_force()
        elif current_tab == 2:
            self.wholesale_barcode_entry.focus_force()
        elif current_tab == 3:
            self.custom_barcode_entry.focus_force()

    # def read_stock(self):
    #     self.stock = pd.read_csv("9MarBarcodes.csv")
    #     self.stock['cost'] = self.stock['cost'].astype(float).astype(str)
    #     self.stock['barcode'] = self.stock['barcode'].astype('Int64').astype(str)
    #     self.stock['discount'] = self.stock['discount'].astype(float).astype(str)
    #     self.stock['in_stock'] = self.stock['in_stock'].astype('Int64').astype(str)
    #     self.stock = self.stock.drop(self.stock.columns[0], axis=1)

    def on_scan(self, e):
        self.scanned_data = e.name
        # print(f"Scanned: {scanned_data}")
        # return scanned_data
    
    def get_values(self, barcode=""):

        # print(barcode)
        # filtered_row = self.stock.loc[self.stock['barcode'] == barcode]
        query = session.query(Product).filter(getattr(Product, 'barcode') == barcode)
        result = query.first()
        # print(result.product_details)

        # print(type(self.stock))
        if result:
            return result
        else:
            return None
    def get_values_by_details(self, details=""):
        query = session.query(Product).filter_by(product_details=details)
        results = query.first()
        if results:
            return results
        else:
            return None
    
    def print_bill(self):
        if self.bill_tree.get_children():
            self.printer.set_with_default()
            gap = " "*21
            current_date = datetime.now().strftime("%d/%m/%Y")
            current_time = datetime.now().strftime("%H:%M")
            self.printer.image(img_source="kk_logo_print.png",center=True,)
            self.printer.textln(" "*48)
            self.printer.textln(f"Date: {current_date}{gap}Time: {current_time}")
            self.printer.textln("*"*48)
            self.printer.textln("PRODUCT                QTY   MRP  DISCNT  TOTAL ")
            self.printer.textln("*"*48)

            temp_total = 0.0
            temp_disc = 0.0
            for item in self.bill_tree.get_children():
                d = self.bill_tree.item(item, 'values')
                # print(d)
                
                p = d[-5].strip()[:22].ljust(22," ")
                q = (d[-4].strip() + " ").rjust(4, " ")
                c = d[-3].strip().rjust(6, " ")
                disc = (str(float(d[-2].strip()) * int(d[-4].strip())) + "  ").rjust(8," ")
                t = d[-1].strip().rjust(8," ")
                temp_total += (int(q)*float(c))
                temp_disc += (float(disc))
                self.printer.textln(p+q+c+disc+t)
            
            self.printer.textln("*"*48)
            temp_total = "TOTAL : " + f"{temp_total:.2f}"
            temp_total = " "*(48-len(temp_total))+ temp_total
            self.printer.textln(temp_total)
            self.printer.set(align='center',font= 1,bold= True,double_height=True,double_width=True)
            total_disc = "TOTAL DISCNT : " + f"{temp_disc:.2f}"
            total_disc = " "*(30-len(total_disc))+ total_disc
            self.printer.textln(total_disc)
            self.printer.set_with_default()
            self.printer.textln("*"*48)
            self.printer.set(align='center',font= 1,bold= True,double_height=True,double_width=True)
            total = "GRAND TOTAL : " + f"{self.total:.2f}"
            total = " "*(30-len(total))+ total
            self.printer.textln(total)
            self.printer.set_with_default()
            self.printer.textln("*"*48)
            self.printer.textln(" "*48)
            amount_intake = "Amount INTAKE : "+ f"{float(self.customer_money.get()):.2f}" + "  "
            amount_intake = " "*(48-len(amount_intake))+ amount_intake
            self.printer.textln(amount_intake)
            return_amount = "Amount RETURN : " + f"{float(self.customer_money.get()) - self.total:.2f}" + "  "
            return_amount = " "*(48-len(return_amount))+ return_amount
            self.printer.textln(return_amount)
            self.printer.textln("*"*48)
            self.printer.cut()

        self.barcode_entry.focus_force()
        self.save_to_json()
        self.load_bills_from_json()

    def save_to_json(self):
        # Read existing data from JSON file if it exists
        # try:
        #     with open('bill_data.json', 'r') as json_file:
        #         existing_data = json.load(json_file)
        # except FileNotFoundError:
        #     existing_data = []

        # temp_new = {}
        # temp_new['Timestamp'] = datetime.now().strftime("%d/%m/%Y - %H:%M")

        new_bill = Bill(id=uuid.uuid4(),date=datetime.now().strftime("%d/%m/%Y - %H:%M"), total=float(self.total), intake_amount=float(self.customer_money.get()))
        session.add(new_bill)
        session.commit()
        # new_data = []
        # with Session(engine) as session:
        #     for child in self.bill_tree.get_children():
        for child in self.bill_tree.get_children():
            values = self.bill_tree.item(child)['values']
            # print(self.bill_tree.item(child)['values'])
            # print(self.bill_tree.item(child))
            # print(type(self.bill_tree.item(child)))
            # for value in self.bill_tree.item(child)['values']:
            bill_item = BillItem(id=uuid.uuid4(), bill_id=new_bill.id, product_details=str(values[1]).strip(), quantity=int(values[2]), unit_price=float(values[3]), discount=float(values[4]), sub_total=float(values[5]))
            session.add(bill_item)
            session.commit()
                # print(value)
                # 0 - barcode
                # 1 - product details
                # 2 - quantity
                # 3 - cost
                # 4 - discount
                # 5 - sub_total
            
            
            # new_data.append(item)
        # temp_new['items'] = new_data
        # temp_new['Total'] = self.total
        # temp_new['amount_intake'] = str(self.customer_money.get())

        # # Append new data to existing data
        # existing_data.append(temp_new)

        # Write combined data to JSON file
        # with open('bill_data.json', 'w') as json_file:
        #     json.dump(existing_data, json_file, indent=4)
    
    def on_tab_pressed(self, event):
        for widget in self.root.winfo_children():
            if widget not in self.tab_0_entries:
                widget.bind("<Shift_R>", lambda event: "break")
                # print("DONE")
        current_tab = self.tabControl.index("current")
        focused_entry = root.focus_get()
        if current_tab == 0:
            if focused_entry not in self.tab_0_entries:
                self.tab_0_entries[0].focus_force()
            else:
                index_of_entry = self.tab_0_entries.index(focused_entry)
                if index_of_entry == 2:
                    self.tab_0_entries[0].focus_force()
                else:
                    self.tab_0_entries[index_of_entry + 1].focus_force()
        if current_tab == 2:
            if focused_entry not in self.tab_2_entries:
                self.tab_2_entries[0].focus_force()
            else:
                index_of_entry = self.tab_2_entries.index(focused_entry)
                if index_of_entry == 1:
                    self.tab_2_entries[0].focus_force()
                else:
                    self.tab_2_entries[index_of_entry + 1].focus_force()
        

        # if current_tab == 0:
        #     focused_entry = root.focus_get()
        #     if focused_entry == entry1:
        #         entry2.focus_set()
        #     elif focused_entry == entry2:
        #         entry3.focus_set()
        #     elif focused_entry == entry3:
        #         entry1.focus_set()
    # def handle_selection(self, event):
    #     # Get the selected item from listbox
    #     selection = self.listbox.get(self.listbox.curselection())
    
    def update_listbox(self, data):
        self.listbox.delete(0, "end")  # Clear existing items
        if data:
            data = [row.product_details for row in data]
            for item in data:
                self.listbox.insert("end", item)
            if self.search_var.get() and data:
                # print("YES")
                self.listbox.place(relx=0.61, rely=0.9, anchor='se')
            else:
                print("NOO")
                self.listbox.delete(0, "end")
                self.listbox.place_forget()
            self.listbox.select_set(0)
            
        else:
            self.listbox.place_forget()
        self.listbox_size = self.listbox.size()
        # print(self.listbox_size)
    
    # Function to search data from database
    def search_data(self,search_term):
        if search_term:
            query = session.query(Product).filter(Product.product_details.like(f"%{search_term}%"))
            # results = [row.product_details for row in query.all()]
            results = query.all()
            return results
        else:
            return None
    
    def focus_on_lbox(self, event):
        # if not self.isListBoxFocused:
                # print(self.isListBoxFocused)
                # listbox_size = self.listbox.size()
                # self.current_index = 0
                # print("YES1")
        self.listbox.focus_set()
        self.isListBoxFocused = True
        self.current_index = self.listbox.curselection()[0]

    def handle_key_press(self, event):
        print("YES")
        
        # listbox_size = self.listbox.size()
        # global self.current_index
        
        
        print(self.isListBoxFocused)
        if event.keysym == 'Up':
            
            # if self.root.focus_get() != self.listbox:
            if not self.isListBoxFocused:
                print(self.isListBoxFocused)
                self.listbox_size = self.listbox.size()
                self.current_index = 0
                print("YES1")
                self.listbox.focus_set()
                self.isListBoxFocused = True
            print("YES2")
            print(self.listbox.selection_get())
            self.listbox.select_clear(self.current_index)
            if 0 < self.current_index < self.listbox_size:
                print(self.current_index)
                self.current_index = self.current_index - 1
            # else:
            #     self.current_index = self.current_index - 1
            
            self.listbox.select_set(self.current_index)
            # self.listbox.selection_anchor()
            self.listbox.select_anchor(self.current_index)
            # self.listbox.
            self.listbox.see(self.current_index)
        elif event.keysym == 'Down':
            # if self.root.focus_get() != self.listbox:
            if not self.isListBoxFocused:
                print(self.root.focus_get())
                self.listbox_size = self.listbox.size()
                self.current_index = 0
                print("YES11")
                self.listbox.focus_set()
                self.isListBoxFocused = True
            print("YES3")
            print(self.listbox.selection_get())
            self.listbox.select_clear(self.current_index)
            if 0 <= self.current_index < self.listbox_size - 1:
                print(self.current_index)
                self.current_index = self.current_index + 1
            # else:
            #     self.current_index = self.current_index + 1
            self.listbox.select_set(self.current_index)
            self.listbox.select_anchor(self.current_index)
            self.listbox.see(self.current_index)
        elif event.keysym == 'Return':
            temp = self.listbox.selection_get()
            print(temp)
            res = self.get_values_by_details(details = temp)
            bill_data_tuple = self.bill_tree.get_children()
            bill_barcode_dict = [str(self.bill_tree.item(item, 'values')[0]).strip() for item in bill_data_tuple]
            bill_product_details_dict = [str(self.bill_tree.item(item, 'values')[1]).strip() for item in bill_data_tuple]
            print(bill_product_details_dict)
            

            if str(res.barcode) not in bill_barcode_dict and str(res.product_details) not in bill_product_details_dict:
                print("NOT iN not in")
                product_quantity = 1
                sub_total = str((res.cost - res.discount) * int(product_quantity)) + (" "*30)
                cost = str(res.cost) + (" "*33)
                discount = str(res.discount) + (" "*33)
                product_quantity =str(product_quantity) + (" "*33)
                self.bill_tree.insert("", "end", text=res.barcode, values=(res.barcode,res.product_details,product_quantity,cost,discount,sub_total))
            elif str(res.barcode) in bill_barcode_dict and str(res.product_details) not in bill_product_details_dict:
                print("IN Not in")
                product_quantity = 1
                sub_total = str((res.cost - res.discount) * int(product_quantity)) + (" "*30)
                cost = str(res.cost) + (" "*33)
                discount = str(res.discount) + (" "*33)
                product_quantity =str(product_quantity) + (" "*33)
                self.bill_tree.insert("", "end",values=(res.barcode,res.product_details,product_quantity,cost,discount,sub_total))
            else:
                print("ABCDEFG")
                if res.barcode:
                    print("ABCDEFG1")
                    values = self.bill_tree.item(bill_data_tuple[bill_barcode_dict.index(str(res.barcode))]).get("values")
                    product_quantity =str(int(values[2]) + 1) + (" "*33)
                    sub_total = str((float(values[3]) - float(values[4])) * int(product_quantity)) + (" "*30)
                    self.bill_tree.item(bill_data_tuple[bill_barcode_dict.index(str(res.barcode))], values=(values[0],values[1],product_quantity,values[3],values[4],sub_total))
                else:
                    print("ABCDEFG2")
                    values = self.bill_tree.item(bill_data_tuple[bill_product_details_dict.index(str(res.product_details))]).get("values")
                    product_quantity =str(int(values[2]) + 1) + (" "*33)
                    sub_total = str((float(values[3]) - float(values[4])) * int(product_quantity)) + (" "*30)
                    self.bill_tree.item(bill_data_tuple[bill_product_details_dict.index(str(res.product_details))], values=(values[0],values[1],product_quantity,values[3],values[4],sub_total))
            # print(type(res))
            # print(res)
            # print(res.product_details)
            # print(res.barcode)
            # print(res.cost)
        elif event.keysym == 'Escape':
            self.listbox.place_forget()
            self.barcode_entry.delete("0","end")
            self.barcode_entry.focus_force()

                
    

    def create_billing_tab(self):
        
        # self.add_pro = True
        # Add widgets for the billing tab
        self.bill_tree = ttk.Treeview(self.billing_tab, columns=("Barcode","Product Name","Quantity","Cost","Discount","Sub Total"), show="headings", height=12)

        style = ttk.Style(self.bill_tree)
        style.configure("Treeview.Heading", font=('Arial', 14))
        style.configure("Treeview", font=('Arial', 14))

        self.bill_tree.heading("Barcode", text="Barcode", anchor=tk.CENTER)
        self.bill_tree.heading("Product Name", text="Product Name", anchor=tk.CENTER)
        self.bill_tree.heading("Quantity", text="Quantity", anchor=tk.CENTER)
        self.bill_tree.heading("Cost", text="Cost", anchor=tk.CENTER)
        self.bill_tree.heading("Discount", text="Discount", anchor=tk.CENTER)
        self.bill_tree.heading("Sub Total", text="Sub Total", anchor=tk.CENTER)

        self.bill_tree.column("Barcode", anchor=tk.CENTER)
        self.bill_tree.column("Product Name", anchor=tk.CENTER)
        self.bill_tree.column("Quantity", anchor=tk.E)
        self.bill_tree.column("Cost", anchor=tk.E)
        self.bill_tree.column("Discount", anchor=tk.E)
        self.bill_tree.column("Sub Total", anchor=tk.E)

        # print(self.bill_tree.column("Barcode")["width"])
        # print(self.bill_tree.column("Product Name")["width"])
        # print(self.bill_tree.column("Quantity")["width"])
        # print(self.bill_tree.column("Cost")["width"])
        # print(self.bill_tree.column("Sub Total")["width"])

        self.bill_tree.bind("<Double-1>", self.on_double_click_bill_tree)
        self.bill_tree.bind("<Delete>", self.on_delete_bill_tree)
        self.bill_tree.bind("<Control_L>", self.clear_bill_tree)
        self.bill_tree.bind("<Control_R>", self.return_amount_popup)
        # self.bill_tree.bind("<Tab>", self.on_tab_pressed)
        

        self.scrollbar = ttk.Scrollbar(self.billing_tab, orient="vertical", command=self.bill_tree.yview)
        self.scrollbar.pack(side="right",fill='y')
        self.bill_tree.configure(yscrollcommand=self.scrollbar.set)
        self.bill_tree.pack(expand=True, fill="both")
        

        # self.bill_tree.pack(side="left", expand=True, fill="both")

        # self.entry_var = tk.StringVar()
        # self.entry_var.trace_add('write', self.add_product_loop)
        self.customer_det = ttk.Entry(self.billing_tab)
        self.customer_det.bind("<Return>", self.create_popup)
        self.customer_det.bind("<Control_L>", self.clear_bill_tree)
        # self.customer_det.bind("<Tab>", self.on_tab_pressed)
        # self.customer_det.bind('<Return>', self.find_customer)
        self.customer_money = ttk.Entry(self.billing_tab)
        self.customer_money.bind("<Return>", self.return_amount_popup)
        self.customer_money.bind("<Control_L>", self.clear_bill_tree)
        self.customer_money.bind("<Control_R>", self.return_amount_popup)
        # self.customer_money.bind("<Tab>", self.on_tab_pressed)
        
        

        # Example: Entry for scanning barcode
        self.search_var = StringVar()
        self.barcode_entry = ttk.Entry(self.billing_tab, textvariable=self.search_var)
        self.listbox = Listbox(self.billing_tab, height=6, selectmode="single", highlightcolor='blue')
        # print(self.barcode_entry.get().isalpha())
        # print(self.barcode_entry.get().isnumeric())
        # if self.barcode_entry.get().isalpha():
        current_index = 0
        self.isListBoxFocused = False
        self.search_var.trace_add("write", lambda *args: self.update_listbox(self.search_data(self.search_var.get())) if not self.barcode_entry.get().isnumeric() else None)
        # self.barcode_entry.bind("<KeyRelease>", lambda *args: self.update_listbox(self.search_data(self.search_var.get())) if not self.barcode_entry.get().isnumeric() else None)
        #  and len(self.barcode_entry.get())!=0 elif len(self.barcode_entry.get())==0 
        # self.listbox.bind("<<ListboxSelect>>", self.handle_selection)
        # self.listbox.bind("<KeyPress>", self.handle_selection)
        self.barcode_entry.bind("<Up>", self.focus_on_lbox)
        self.listbox.bind("<KeyPress>", self.handle_key_press)
        
        
        self.customer_det.pack(side="left",pady=30, padx=350)
        self.barcode_entry.pack(side="left",pady=30, padx=200)
        self.customer_money.pack(side="left",pady=30, padx=0)
        # self.billing_tab.bind("<Control_L>", self.clear_bill_tree)
        # self.barcode_entry.place(relx=0.7, rely=0.98, anchor='se',bordermode='outside')
        self.disc_500 = False
        self.barcode_entry.bind('<Return>', self.add_product_loop)
        self.barcode_entry.bind("<Control_L>", self.clear_bill_tree)
        self.barcode_entry.bind("<Control_R>", self.return_amount_popup)
        # self.barcode_entry.bind("<Tab>", self.on_tab_pressed)
        
        # self.barcode_entry.bind("<Return>", self.add_product_loop)

        # print(self.barcode_entry.winfo_pathname(self.barcode_entry.winfo_id()))
        style1 = ttk.Style()
        style1.configure("elder.TButton", height=6, width=12, font=("Arial", 14, "bold"), foreground='white', background='#33BEFF', padding=10)

        # self.add_product(barcode_entry.get())

        # Example: Button to add product to the table
        self.new_bill_button = ttk.Button(self.billing_tab, text="New Bill", command=lambda: self.clear_bill_tree(None), style="elder.TButton")
        self.new_bill_button.place(relx=0.07, rely=0.98, anchor='sw')
        # self.add_button.pack(pady=10)
        style2 = ttk.Style()
        style2.configure("TButton", height=6, width=12, font=("Arial", 14, "bold"), foreground='white', background='#7433FF', padding=10)
        # self.add_product_running = False
        self.print_bill_button = ttk.Button(self.billing_tab, text="Print Bill", style="TButton", command=lambda: self.return_amount_popup(None))
        self.print_bill_button.place(relx=0.73, rely=0.98, anchor='se')
        

        self.total_label = tk.Label(self.billing_tab, text="Total: 0.00", font=('Arial', 25, 'bold'), foreground='red')
        self.total_label.place(relx=0.98, rely=0.98, anchor='se')


        self.barcode_label = tk.Label(self.billing_tab, text="BARCODE", font=('Arial', 12))
        self.barcode_label.place(relx=0.61, rely=0.94, anchor='se')
        

        # self.customer_num = tk.Label(self.billing_tab, text="Customer Number", font=('Arial', 12))
        # self.customer_num.place(relx=0.19, rely=0.94, anchor='sw')

        # self.customer_num = tk.Label(self.billing_tab, text="Customer Details", font=('Arial', 12))
        # self.customer_num.place(relx=0.35, rely=0.94, anchor='sw')

        self.customer_amount = tk.Label(self.billing_tab, text="Amount INTAKE", font=('Arial', 12))
        self.customer_amount.place(relx=0.82, rely=0.94, anchor='se')
        

        # self.customer_details = tk.Label(self.billing_tab, text="Customer Name : kalyan kalyan Ph : 9494411661", font=('Arial', 12))
        # self.customer_details.place(relx=0.30, rely=0.98, anchor='sw')

        self.img = PhotoImage(file="kk_logo_90p.png")
        # self.img.place(relx=0.1, rely=0.98, anchor='sw',bordermode='outside')
        self.label = tk.Label(self.billing_tab, image=self.img)
        self.label.place(relx=0, rely=1, anchor='sw',bordermode='outside')

        # selected_tab_index = self.tabControl.index(self.tabControl.select())
        # if selected_tab_index == 0:
        #     print(selected_tab_index)
        #     print("ZERO")
        # self.billing_tab.bind("<Tab>", self.on_tab_pressed)

        self.tab_0_entries = [self.customer_det, self.barcode_entry, self.customer_money]

        # Variable to store the currently selected item for editing
        # self.selected_item = None



        # Entry for editing
        # self.edit_entry = None

        # Bind events for cell editing
        # self.bill_tree.bind("<ButtonRelease-1>", self.on_item_click)
        # self.bill_tree.bind("<Return>", self.on_edit_commit)
    
    # def on_enter_pressed1(self, event):
    #     # This function is called when the Enter key is pressed
    #     barcode = self.barcode_entry.get()
    #     print(f"Barcode scanned: {barcode}")

    #     self.barcode_entry.delete("0", "end")
    #     self.barcode_entry.focus_force()
    
    def on_delete_bill_tree(self, event):

        region_clicked = self.bill_tree.identify_region(event.x, event.y)

        if region_clicked not in ("cell"):
            return
        
        # column = self.bill_tree.identify_column(event.x)
        # column_index = int(column[1:]) - 1
        

        selected_iid = self.bill_tree.focus()
        # selected_item = self.bill_tree.item(selected_iid)

        self.bill_tree.delete(selected_iid)
        self.update_total()
        self.barcode_entry.focus_force()

    def on_delete_stock_tree(self, event):

        region_clicked = self.stock_tree.identify_region(event.x, event.y)

        if region_clicked not in ("cell"):
            return
        
        # column = self.bill_tree.identify_column(event.x)
        # column_index = int(column[1:]) - 1
        

        selected_iid = self.stock_tree.focus()
        # selected_item = self.bill_tree.item(selected_iid)

        self.stock_tree.delete(selected_iid)
        # self.update_total()
        self.stock_barcode_entry.focus_force()
        
    def clear_bill_tree(self,event):

        self.bill_tree.delete(*self.bill_tree.get_children())
        self.update_total()
        self.customer_money.delete("0","end")
        self.barcode_entry.focus_force()

    def clear_stock_tree(self):

        self.stock_tree.delete(*self.stock_tree.get_children())
        # self.update_total()
        # self.customer_money.delete("0","end")
        self.stock_barcode_entry.focus_force()
    

    def update_disc(self):

        if self.bill_tree.get_children():
            for item in self.bill_tree.get_children():
                barcode = self.bill_tree.item(item, 'values')[0]
                current_vals = self.bill_tree.item(item).get("values")
                if self.get_values(barcode=barcode):
                    valsFromStock = self.get_values(barcode=barcode)
                    discount = float(valsFromStock.discount)
                    if self.disc_500:
                        current_vals[5] = str(int(current_vals[2]) * (float(current_vals[3]) - discount)) + " "*31
                        current_vals[4] = str(discount) + " "*31
                    else:
                        discount = 0.0
                        current_vals[4] = str(0.0) + " "*31
                        current_vals[5] = str(int(current_vals[2]) * (float(current_vals[3]) - discount)) + " "*31
                    current_vals[2] = str(current_vals[2]) + " "*31
                    self.bill_tree.item(item, values=current_vals)
        
        self.update_total()
        
        self.barcode_entry.focus_force()
    
    def update_total(self):
        # Calculate the total from the values in the tree
        self.total = 0.0
        for item in self.bill_tree.get_children():
            sub_total = float(self.bill_tree.item(item, 'values')[-1]) # Assuming the cost is the last column
            # quantity = int(self.bill_tree.item(item, 'values')[-2]) # Assuming the quantity is the -2 column
            self.total += sub_total
        
        if self.total >= 0 and not self.disc_500:
            self.disc_500 = True
            self.update_disc()
        elif self.total < 0 and self.disc_500:
            self.disc_500 = False
            self.update_disc()
        # Update the total label
        self.total_label.config(text=f"Total: {self.total:.2f}")


    def on_double_click_stock_tree(self, event):

        region_clicked = self.stock_tree.identify_region(event.x, event.y)
        # region_clicked = self.stock_tree.identify_region(event.x, event.y)
        # print(region_clicked)

        if region_clicked not in ("cell"):
            return
        
        column = self.stock_tree.identify_column(event.x)
        column_index = int(column[1:]) - 1
        

        selected_iid = self.stock_tree.focus()
        selected_value = str(self.stock_tree.item(selected_iid).get("values")[column_index]).strip()

        column_box = self.stock_tree.bbox(selected_iid,column)
        # print(column)
        # print(self.bill_tree.bbox(column=column))

        if hasattr(self, 'entry_edit_stock_tree') and isinstance(self.entry_edit_stock_tree, ttk.Entry):
            self.entry_edit_stock_tree.destroy()

        self.entry_edit_stock_tree = ttk.Entry(self.stock_tree,justify='center', font=('Arial', 13))

        self.entry_edit_stock_tree.editing_column_index = column_index
        self.entry_edit_stock_tree.editing_item_iid = selected_iid

        self.entry_edit_stock_tree.insert(0,selected_value)
        self.entry_edit_stock_tree.select_range(0, tk.END)
        self.entry_edit_stock_tree.focus()

        self.entry_edit_stock_tree.bind("<FocusOut>", self.on_focus_out_stock_tree)
        self.entry_edit_stock_tree.bind("<Return>", self.on_enter_pressed_stock_tree)
        self.entry_edit_stock_tree.place(x=column_box[0],y=column_box[1],w=column_box[2],h=column_box[3])


    def on_double_click_bill_tree(self, event):

        region_clicked = self.bill_tree.identify_region(event.x, event.y)
        # region_clicked = self.stock_tree.identify_region(event.x, event.y)
        # print(region_clicked)

        if region_clicked not in ("cell"):
            return
        
        column = self.bill_tree.identify_column(event.x)
        column_index = int(column[1:]) - 1
        

        selected_iid = self.bill_tree.focus()
        selected_value = str(self.bill_tree.item(selected_iid).get("values")[column_index]).strip()

        column_box = self.bill_tree.bbox(selected_iid,column)
        # print(column)
        # print(self.bill_tree.bbox(column=column))

        if hasattr(self, 'entry_edit_bill_tree') and isinstance(self.entry_edit_bill_tree, ttk.Entry):
            self.entry_edit_bill_tree.destroy()

        self.entry_edit_bill_tree = ttk.Entry(self.bill_tree,justify='center', font=('Arial', 13))

        self.entry_edit_bill_tree.editing_column_index = column_index
        self.entry_edit_bill_tree.editing_item_iid = selected_iid

        self.entry_edit_bill_tree.insert(0,selected_value)
        self.entry_edit_bill_tree.select_range(0, tk.END)
        self.entry_edit_bill_tree.focus()

        self.entry_edit_bill_tree.bind("<FocusOut>", self.on_focus_out_bill_tree)
        self.entry_edit_bill_tree.bind("<Return>", self.on_enter_pressed_bill_tree)
        self.entry_edit_bill_tree.place(x=column_box[0],y=column_box[1],w=column_box[2],h=column_box[3])
        # print(column_box)
    
    def create_popup(self,event):
        # print("Popping up")
        popup = tk.Toplevel(self.root)
        popup.title("Popup Window")
        window_width = 400
        window_height = 300
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        popup.geometry(f"{window_width}x{window_height}+{x}+{y}")
        popup_label = tk.Label(popup, text="This is a popup window!")
        popup_label.pack(pady=20)
        popup_button = tk.Button(popup, text="Close", command=popup.destroy)
        popup_button.pack()
        # popup.mainloop()

    def return_amount_popup(self, event):
        # print("Popping up")
        if len(self.customer_money.get()) < 6:
            self.return_amt_popup = tk.Toplevel(self.root)
            self.return_amt_popup.title("Return AMOUNT")
            window_width = 400
            window_height = 300
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2

            self.return_amt_popup.geometry(f"{window_width}x{window_height}+{x}+{y}")
            amount_intake_label = tk.Label(self.return_amt_popup)
            amount_intake_label.config(text = f"Amount Intake : {float(self.customer_money.get())}", font=('Arial', 16, 'bold'))
            amount_intake_label.pack(pady=20)

            self.amount_intake_label = tk.Label(self.return_amt_popup)
            self.amount_intake_label.config(text=f"RETURN : {(float(self.customer_money.get()) - self.total):.2f}", font=('Arial', 18, 'bold'), foreground='green')
            self.amount_intake_label.pack(pady=20)

            self.print_bill()

            # self.amount_intake_entry = tk.Entry(self.return_amt_popup)
            # self.amount_intake_entry.pack(pady=20)
            # self.amount_intake_entry.bind("<Return>", self.show_return_amount)

            popup_button = tk.Button(self.return_amt_popup, text="Close", command=self.return_amt_popup.destroy)
            popup_button.pack()
            # popup.mainloop()
            self.return_amt_popup.bind("<Return>",self.destroy_popup)

    # def show_return_amount(self, event):
    def destroy_popup(self,event):
        event.widget.destroy()

        
    
    def on_enter_pressed_bill_tree(self, event):

        if hasattr(self, 'entry_edit_bill_tree') and isinstance(self.entry_edit_bill_tree, ttk.Entry):

            new_value = self.entry_edit_bill_tree.get()

            selected_iid = self.entry_edit_bill_tree.editing_item_iid
            column_index = self.entry_edit_bill_tree.editing_column_index

            current_values = self.bill_tree.item(selected_iid).get("values")

            # Quantity
            if column_index == 2:
                current_values[column_index] = str(new_value) + (" "*33)
                # SubTot = Q * (Cost - Discount)
                current_values[-1] = str(int(new_value) * (float(current_values[column_index + 1]) - float(current_values[column_index + 2]))) + (" "*30)

            # Discount
            elif column_index == 4:
                current_values[column_index] = str(float(new_value)) + (" "*33)
                # current_values[column_index - 1] = str(current_values[column_index - 1]) + (" "*33)
                # SubTot = Q * (Cost - Discount)
                current_values[-1] = str(int(current_values[column_index - 2]) * (float(current_values[column_index - 1]) - float(new_value))) + (" "*30)
            
            # Cost
            elif column_index == 3:
                current_values[column_index] = str(float(new_value)) + (" "*33)
                # current_values[column_index - 1] = str(current_values[column_index - 1]) + (" "*33)
                # SubTot = Q * (Cost - Discount)
                current_values[-1] = str(int(current_values[column_index - 1]) * (float(new_value) - float(current_values[column_index + 1]))) + (" "*30)

            # Poduct name
            elif column_index == 1:
                current_values[column_index] = new_value
                # current_values[-3] = str(float(current_values[-3])) + (" "*33)
            
            # print(current_values[column_index])

            current_values[-4] = str(current_values[-4]).strip() + (" "*33)
            self.bill_tree.item(selected_iid, values=current_values)

            self.update_total()

            # print(current_values)

            self.entry_edit_bill_tree.destroy()
            self.barcode_entry.focus_force()

    
    def on_enter_pressed_stock_tree(self, event):

        if hasattr(self, 'entry_edit_stock_tree') and isinstance(self.entry_edit_stock_tree, ttk.Entry):

            new_value = self.entry_edit_stock_tree.get()

            selected_iid = self.entry_edit_stock_tree.editing_item_iid
            column_index = self.entry_edit_stock_tree.editing_column_index

            current_values = self.stock_tree.item(selected_iid).get("values")

            # InStock
            if column_index == 2:
                current_values[column_index] = str(new_value) + (" "*26)
                # SubTot = Q * (Cost - Discount)
                # current_values[-1] = str(int(new_value) * (float(current_values[column_index + 1]) - float(current_values[column_index + 2]))) + (" "*30)

            # Discount
            elif column_index == 4:
                current_values[column_index] = str(float(new_value)) + (" "*26)
                # current_values[column_index - 1] = str(current_values[column_index - 1]) + (" "*33)
                # SubTot = Q * (Cost - Discount)
                # current_values[-1] = str(int(current_values[column_index - 2]) * (float(current_values[column_index - 1]) - float(new_value))) + (" "*30)
            
            # Cost
            elif column_index == 3:
                current_values[column_index] = str(float(new_value)) + (" "*26)
                # current_values[column_index - 1] = str(current_values[column_index - 1]) + (" "*33)
                # SubTot = Q * (Cost - Discount)
                # current_values[-1] = str(int(current_values[column_index - 1]) * (float(new_value) - float(current_values[column_index + 1]))) + (" "*30)

            # Poduct name
            elif column_index == 1:
                current_values[column_index] = new_value
                # current_values[-3] = str(float(current_values[-3])) + (" "*33)

            # Barcode
            elif column_index == 0:
                current_values[column_index] = new_value

            # Wholesale Cost
            elif column_index == 5:
                current_values[column_index] = str(float(new_value)) + (" "*26)
            
            # New Stock
            elif column_index == 6:
                current_values[column_index] = str(int(new_value)) + (" "*26)
            
            # print(current_values[column_index])

            # current_values[-4] = str(current_values[-4]).strip() + (" "*33)
            current_values[-4] = str(current_values[-4]).strip() + (" "*26)
            current_values[-1] = str(current_values[-1]).strip() + (" "*26)
            self.stock_tree.item(selected_iid, values=current_values)

            # self.update_total()

            # print(current_values)

            self.entry_edit_stock_tree.destroy()
            self.stock_barcode_entry.focus_force()


    def on_focus_out_bill_tree(self, event):

        if hasattr(self, 'entry_edit_bill_tree') and isinstance(self.entry_edit_bill_tree, ttk.Entry):

            new_value = self.entry_edit_bill_tree.get()

            selected_iid = self.entry_edit_bill_tree.editing_item_iid
            column_index = self.entry_edit_bill_tree.editing_column_index
            # print(column_index)

            current_values = self.bill_tree.item(selected_iid).get("values")
            
            
            # Quantity
            if column_index == 2:
                current_values[column_index] = str(new_value) + (" "*33)
                # SubTot = Q * (Cost - Discount)
                current_values[-1] = str(int(new_value) * (float(current_values[column_index + 1]) - float(current_values[column_index + 2]))) + (" "*30)

            # Discount
            elif column_index == 4:
                current_values[column_index] = str(float(new_value)) + (" "*33)
                # current_values[column_index - 1] = str(current_values[column_index - 1]) + (" "*33)
                # SubTot = Q * (Cost - Discount)
                current_values[-1] = str(int(current_values[column_index - 2]) * (float(current_values[column_index - 1]) - float(new_value))) + (" "*30)
            
            # Cost
            elif column_index == 3:
                current_values[column_index] = str(float(new_value)) + (" "*33)
                # current_values[column_index - 1] = str(current_values[column_index - 1]) + (" "*33)
                # SubTot = Q * (Cost - Discount)
                current_values[-1] = str(int(current_values[column_index - 1]) * (float(new_value) - float(current_values[column_index + 1]))) + (" "*30)

            # Poduct name
            elif column_index == 1:
                current_values[column_index] = new_value
                

            # print(current_values[column_index])

            current_values[-4] = str(current_values[-4]).strip() + (" "*33)
            self.bill_tree.item(selected_iid, values=current_values)

            self.update_total()

            self.entry_edit_bill_tree.destroy()
            self.barcode_entry.focus_force()

    
    def on_focus_out_stock_tree(self, event):

        if hasattr(self, 'entry_edit_stock_tree') and isinstance(self.entry_edit_stock_tree, ttk.Entry):

            new_value = self.entry_edit_stock_tree.get()

            selected_iid = self.entry_edit_stock_tree.editing_item_iid
            column_index = self.entry_edit_stock_tree.editing_column_index
            # print(column_index)

            current_values = self.stock_tree.item(selected_iid).get("values")

            # InStock
            if column_index == 2:
                current_values[column_index] = str(new_value) + (" "*26)
                # SubTot = Q * (Cost - Discount)
                # current_values[-1] = str(int(new_value) * (float(current_values[column_index + 1]) - float(current_values[column_index + 2]))) + (" "*30)

            # Discount
            elif column_index == 4:
                current_values[column_index] = str(float(new_value)) + (" "*26)
                # current_values[column_index - 1] = str(current_values[column_index - 1]) + (" "*33)
                # SubTot = Q * (Cost - Discount)
                # current_values[-1] = str(int(current_values[column_index - 2]) * (float(current_values[column_index - 1]) - float(new_value))) + (" "*30)
            
            # Cost
            elif column_index == 3:
                current_values[column_index] = str(float(new_value)) + (" "*26)
                # current_values[column_index - 1] = str(current_values[column_index - 1]) + (" "*33)
                # SubTot = Q * (Cost - Discount)
                # current_values[-1] = str(int(current_values[column_index - 1]) * (float(new_value) - float(current_values[column_index + 1]))) + (" "*30)

            # Poduct name
            elif column_index == 1:
                current_values[column_index] = new_value
                # current_values[-3] = str(float(current_values[-3])) + (" "*33)

            # Barcode
            elif column_index == 0:
                current_values[column_index] = new_value

            # Wholesale Cost
            elif column_index == 5:
                current_values[column_index] = str(float(new_value)) + (" "*26)
            
            # New Stock
            elif column_index == 6:
                current_values[column_index] = str(int(new_value)) + (" "*26)
            
            # print(current_values[column_index])

            current_values[-4] = str(current_values[-4]).strip() + (" "*26)
            current_values[-1] = str(current_values[-1]).strip() + (" "*26)
            self.stock_tree.item(selected_iid, values=current_values)

            # self.update_total()

            # print(current_values)

            self.entry_edit_stock_tree.destroy()
            self.stock_barcode_entry.focus_force()

    # def toggle_add_product(self):
    #     if not self.add_product_running:
    #         # Set the variable to True to indicate the function is running
    #         self.add_product_running = True
    #         self.add_product_loop()
    #     else:
    #         # Set the variable to False to stop the function
    #         self.add_product_running = False

    def add_product_loop(self, event):
        # print("adding product to bill")
        # while self.add_product_running:
            
        if self.barcode_entry.get().isnumeric():
            barcode = self.barcode_entry.get()
            product_name = ""
            product_quantity = 1
            cost = str(0.0)  + (" "*33) # Replace with actual product cost
            discount = str(0.0) + (" "*33)
            sub_total = product_quantity * (float(cost) - float(discount))

            bill_data_tuple = self.bill_tree.get_children()
            # print(bill_data_tuple)
            bill_barcode_dict = [self.bill_tree.item(item, 'values')[0] for item in bill_data_tuple]
            # print(bill_barcode_dict)

            if barcode in bill_barcode_dict:
                product_name = self.bill_tree.item(bill_data_tuple[bill_barcode_dict.index(barcode)]).get("values")[1]
                cost = float(self.bill_tree.item(bill_data_tuple[bill_barcode_dict.index(barcode)]).get("values")[-3])
                discount = float(self.bill_tree.item(bill_data_tuple[bill_barcode_dict.index(barcode)]).get("values")[-2])
                product_quantity = int(self.bill_tree.item(bill_data_tuple[bill_barcode_dict.index(barcode)]).get("values")[2]) + 1
                sub_total = str(product_quantity * (cost - discount)) + (" "*30)
                cost = str(cost) + (" "*33)
                discount = str(discount) + (" "*33)
                product_quantity =str(product_quantity) + (" "*33)
                values = (barcode,product_name,product_quantity,cost,discount,sub_total)
                self.bill_tree.item(bill_data_tuple[bill_barcode_dict.index(barcode)],values=values)

            else:
                # Insert a new row in the table
                
                # print(type(valsFromStock))
                # print(valsFromStock)
                if self.get_values(barcode=barcode):
                    valsFromStock = self.get_values(barcode=barcode)
                    if int(barcode) == valsFromStock.barcode:
                        product_name = valsFromStock.product_details
                        cost = float(valsFromStock.cost)
                        if self.disc_500:
                            discount = float(valsFromStock.discount)
                        else:
                            discount = 0.0
                        sub_total = str((cost - discount) * int(product_quantity)) + (" "*30)
                        cost = str(cost) + (" "*33)
                        discount = str(discount) + (" "*33)
                        product_quantity =str(product_quantity) + (" "*33)
                        self.bill_tree.insert("", "end", text=barcode, values=(barcode,product_name,product_quantity,cost,discount,sub_total))
                else:
                    self.bill_tree.insert("", "end", text=barcode, values=(barcode,product_name,product_quantity,cost,discount,sub_total))

                # print(valsFromStock)
                
            # print([self.bill_tree.item(item, 'values') for item in self.bill_tree.get_children()])

            
            # self.scrollbar.configure()
            self.update_total()
            
    
            # self.bill_tree.update_idletasks()
            self.bill_tree.yview_moveto(1.0)

            
            self.barcode_entry.delete("0", "end")
            self.barcode_entry.focus_force()
        
        elif self.barcode_entry.get().isalnum():
            barcode = ""
            product_name = self.barcode_entry.get()
            product_quantity = 1
            product_quantity = str(product_quantity) + (" "*33)
            cost = str(0.0)  + (" "*33) # Replace with actual product cost
            discount = str(0.0) + (" "*33)
            sub_total = str(int(product_quantity) * (float(cost) - float(discount))) + (" "*30)
            self.bill_tree.insert("", "end", text=barcode, values=(barcode,product_name,product_quantity,cost,discount,sub_total))

            self.update_total()
            self.bill_tree.yview_moveto(1.0)

            
            self.barcode_entry.delete("0", "end")
            self.barcode_entry.focus_force()

        self.root.update()
            # self.root.after(700)
                
    # def on_item_click(self, event):
    #     item = self.stock_tree.selection()
    #     # print(item)
    #     if item:
    #         self.selected_item = item[0]
    #         self.edit_entry = ttk.Entry(self.tree, justify='center')

    #         # print(self.edit_entry.winfo_pathname(self.edit_entry.winfo_id()))

    #         # print(self.tree.item(self.selected_item, "values")[1])
    #         self.edit_entry.insert(0, self.tree.item(self.selected_item, "values")[0])
    #         self.tree.item(self.selected_item, values=(self.edit_entry, ""))
    #         self.edit_entry.bind("<FocusOut>", self.on_edit_commit)
    #         self.edit_entry.focus_set()

    # def on_edit_commit(self):
        
    #     if self.selected_item and self.edit_entry:
    #         # print("Inside onedit")
    #         updated_value = self.edit_entry.get()
    #         # print(updated_value)
    #         self.tree.item(self.selected_item, values=(updated_value, ""))

    #         # Perform actions with the edited value (you can update your data structure here)

    #         # Reset the selected item and entry
    #         self.selected_item = None
    #         self.edit_entry.destroy()

    def create_stock_tab(self):
        # Add widgets for the stock tab
        # label = ttk.Label(self.stock_tab, text="Stock Tab Content")
        # label.pack(padx=10, pady=10)
        self.stock_barcode_entry = ttk.Entry(self.stock_tab)
        self.stock_barcode_entry.pack(padx=10, pady=10)
        # self.barcode_entry.bind('<Return>', self.add_product_loop)
        selected_tab_index = self.tabControl.index(self.tabControl.select())
        
        # if selected_tab_index == 1:
        #     print(selected_tab_index)
        #     print("ONE")
            
        
        self.stock_barcode_entry.bind('<Return>', self.show_stock_data)

        self.stock_tree = ttk.Treeview(self.stock_tab, columns=("Barcode","Product Name","In Stock","Cost","Discount","Wholesale Cost","New Stock"), show="headings", height=12)

        style = ttk.Style(self.stock_tree)
        style.configure("Treeview.Heading", font=('Arial', 14))
        style.configure("Treeview", font=('Arial', 14))

        self.stock_tree.heading("Barcode", text="Barcode", anchor=tk.CENTER)
        self.stock_tree.heading("Product Name", text="Product Name", anchor=tk.CENTER)
        self.stock_tree.heading("In Stock", text="In Stock", anchor=tk.CENTER)
        self.stock_tree.heading("Cost", text="Cost", anchor=tk.CENTER)
        self.stock_tree.heading("Discount", text="Discount", anchor=tk.CENTER)
        self.stock_tree.heading("Wholesale Cost", text="Wholesale Cost", anchor=tk.CENTER)
        self.stock_tree.heading("New Stock", text="New Stock", anchor=tk.CENTER)

        self.stock_tree.column("Barcode", anchor=tk.CENTER)
        self.stock_tree.column("Product Name", anchor=tk.CENTER)
        self.stock_tree.column("In Stock", anchor=tk.E)
        self.stock_tree.column("Cost", anchor=tk.E)
        self.stock_tree.column("Discount", anchor=tk.E)
        self.stock_tree.column("Wholesale Cost", anchor=tk.E)
        self.stock_tree.column("New Stock", anchor=tk.E)

        self.stock_tree.bind("<Double-1>", self.on_double_click_stock_tree)
        self.stock_tree.bind("<Delete>", self.on_delete_stock_tree)

        style9 = ttk.Style()
        style9.configure("elder.TButton", height=2, width=10, font=("Arial", 14, "bold"), foreground='white', background='#33BEFF', padding=6)

        self.new_stock_button = ttk.Button(self.stock_tab, text="New Stock", command=lambda: self.clear_stock_tree(), style="elder.TButton")
        self.new_stock_button.place(relx=0.8, rely=0, anchor='nw')

        style8 = ttk.Style()
        style8.configure("TButton", height=2, width=10, font=("Arial", 14, "bold"), foreground='white', background='#6a994e', padding=6)

        self.add_stock_button = ttk.Button(self.stock_tab, text="Add Stock", command=lambda: self.add_stock(), style="TButton")
        self.add_stock_button.place(relx=0.9, rely=0, anchor='nw')
        
        self.scrollbar = ttk.Scrollbar(self.stock_tab, orient="vertical", command=self.stock_tree.yview)
        self.scrollbar.pack(side="right",fill='y')
        self.stock_tree.configure(yscrollcommand=self.scrollbar.set)
        self.stock_tree.pack(expand=True, fill="both")
    
    def show_stock_data(self, event):
        # print("adding product to stock")

        if self.stock_barcode_entry.get().isnumeric():
            barcode = self.stock_barcode_entry.get()
            product_name = ""
            product_new_stock = str(1) + " "*26
            cost = str(0.0)  + (" "*26) # Replace with actual product cost
            discount = str(0.0) + (" "*26)
            wholesale_cost = str(0.0) + " "*26
            product_in_stock = 0
            

            stock_data_tuple = self.stock_tree.get_children()
            # print(bill_data_tuple)
            stock_barcode_dict = [self.stock_tree.item(item, 'values')[0] for item in stock_data_tuple]
            # print(bill_barcode_dict)

            if barcode in stock_barcode_dict:
                product_name = self.stock_tree.item(stock_data_tuple[stock_barcode_dict.index(barcode)]).get("values")[1]
                cost = float(self.stock_tree.item(stock_data_tuple[stock_barcode_dict.index(barcode)]).get("values")[3])
                discount = float(self.stock_tree.item(stock_data_tuple[stock_barcode_dict.index(barcode)]).get("values")[4])
                product_in_stock = int(self.stock_tree.item(stock_data_tuple[stock_barcode_dict.index(barcode)]).get("values")[2])
                # print(product_in_stock)
                wholesale_cost = float(self.stock_tree.item(stock_data_tuple[stock_barcode_dict.index(barcode)]).get("values")[5])
                product_new_stock = int(self.stock_tree.item(stock_data_tuple[stock_barcode_dict.index(barcode)]).get("values")[6]) + 1
                cost = str(cost) + (" "*26)
                discount = str(discount) + (" "*26)
                product_in_stock =str(product_in_stock) + (" "*26)
                product_new_stock =str(product_new_stock) + (" "*26)
                wholesale_cost = str(wholesale_cost) + (" "*26)
                values = (barcode,product_name,product_in_stock,cost,discount,wholesale_cost,product_new_stock)
                self.stock_tree.item(stock_data_tuple[stock_barcode_dict.index(barcode)],values=values)

            else:
                # Insert a new row in the table
                
                # print(type(valsFromStock))
                # print(valsFromStock)
                if self.get_values(barcode=barcode):
                    valsFromStock = self.get_values(barcode=barcode)
                    # print(type(valsFromStock))
                    # print(str(valsFromStock))
                    # print(barcode == valsFromStock.barcode)
                    # print(type(barcode))
                    # print(type(valsFromStock.barcode))
                    # print(len(barcode))
                    # print(len(valsFromStock.barcode))
                    if int(barcode) == valsFromStock.barcode:
                        
                        product_name = valsFromStock.product_details
                        cost = float(valsFromStock.cost)
                        discount = float(valsFromStock.discount)
                        # sub_total = str((cost - discount) * int(product_in_stock)) + (" "*30)
                        wholesale_cost = str(float(valsFromStock.wholesale_cost)) + " "*26
                        cost = str(cost) + (" "*26)
                        discount = str(discount) + (" "*26)
                        product_in_stock =str(valsFromStock.in_stock) + (" "*26)
                        self.stock_tree.insert("", "end", text=barcode, values=(barcode,product_name,product_in_stock,cost,discount,wholesale_cost,product_new_stock))
                else:
                    self.stock_tree.insert("", "end", text=barcode, values=(barcode,product_name,product_in_stock,cost,discount,wholesale_cost,product_new_stock))

                # print(valsFromStock)
                
            # print([self.stock_tree.item(item, 'values') for item in self.stock_tree.get_children()])

            
            # self.scrollbar.configure()
            # self.update_total()
            
    
            # self.stock_tree.update_idletasks()
    

        elif self.stock_barcode_entry.get() and "?" in self.stock_barcode_entry.get():
            search_string = self.stock_barcode_entry.get().replace("?","")
            print(search_string)
            res = self.search_data(search_string.lower())
            print(res)
            # search_string = self.stock_barcode_entry.get().lower()
            # filtered_df = self.stock[self.stock['product_details'].str.contains(search_string, case=False)]
            # filtered_dicts = filtered_df.to_dict(orient='records')
            for row in res:
                values = (str(row.barcode),
                          str(row.product_details),
                          str(row.in_stock) + " "*26,
                          str(row.cost) + " "*26,
                          str(row.discount) + " "*26,
                          str(row.wholesale_cost) + " "*26,
                          0

                )
                self.stock_tree.insert("", "end", text=row.barcode, values=values)
        
        elif self.stock_barcode_entry.get().isalnum():
            barcode = ""
            product_name = self.stock_barcode_entry.get()
            in_stock = str(1) + " "*26
            product_quantity = 1
            product_quantity = str(product_quantity) + (" "*26)
            cost = str(0.0)  + (" "*26) # Replace with actual product cost
            product_new_stock = str(1) + " "*26
            wholesale_cost = str(0.0) + " "*26
            discount = str(0.0) + (" "*26)
            self.stock_tree.insert("", "end", text=barcode, values=(barcode,product_name,in_stock,cost,discount,wholesale_cost,product_new_stock))

        
        self.stock_tree.yview_moveto(1.0)

            
        self.stock_barcode_entry.delete("0", "end")
        self.stock_barcode_entry.focus_force()
        self.root.update()


    def add_stock(self):
        if self.stock_tree.get_children():
            for item in self.stock_tree.get_children():
                d = self.stock_tree.item(item, 'values')
                temp_d = {
                    "product_details":str(d[1]).strip(),
                    "barcode":int(str(d[0]).strip()) if d[0] else '',
                    "cost":float(str(d[3]).strip()),
                    "discount":float(str(d[4]).strip()),
                    "wholesale_cost":float(str(float(d[5])).strip()),
                    "in_stock":str(int(d[6]) + int(d[2])),
                    "in_cost":float(0)

                }
                temp_dd = Product(
                    id=uuid.uuid4(),
                    product_details=str(d[1]).strip(),
                    barcode=int(str(d[0]).strip()) if d[0] else "",
                    cost=float(str(d[3]).strip()),
                    discount=float(str(d[4]).strip()),
                    wholesale_cost=float(str(float(d[5])).strip()),
                    in_stock=str(int(d[6]) + int(d[2])),
                    in_cost=float(0)
                )

                # mask = self.stock['barcode'] == d[0]
                if d[0]:
                    query = session.query(Product).filter(getattr(Product, "barcode") == str(d[0]))
                    # matched_indices = self.stock.index[mask]
                    result = query.first()
                else:
                    result = None

                # if not matched_indices.empty:
                #     for index in matched_indices:
                #         for key, value in temp_d.items():
                #             self.stock.at[index, key] = value
                
                # else:
                #     new_index = len(self.stock)
                #     for key, value in temp_d.items():
                #         self.stock.at[new_index, key] = value
                #     # .append(temp_d, ignore_index=True)

                if result:
                    # result.__dict__.update(**temp_d)
                    result.product_details = temp_d['product_details']
                    result.barcode = temp_d['barcode']
                    result.cost = temp_d['cost']
                    result.discount = temp_d['discount']
                    result.wholesale_cost = temp_d['wholesale_cost']
                    result.in_stock = temp_d['in_stock']
                    result.in_cost = temp_d['in_cost']
                    session.commit()
                    # print("UPDATED")
                    # print(d)
                    # print(temp_d)
                else:
                    session.add(temp_dd)
                    session.commit()
                    # print("APPENDED")
                

            
            
            # self.stock.to_csv("9MarBarcodes.csv")
            # self.read_stock()
            session.close()
            self.clear_stock_tree()
            self.stock_barcode_entry.focus_force()
                
    def on_delete_wholesale_bill(self, event):

        region_clicked = self.wholesale_bill_tree.identify_region(event.x, event.y)

        if region_clicked not in ("cell"):
            return
        
        # column = self.wholesale_bill_tree.identify_column(event.x)
        # column_index = int(column[1:]) - 1
        

        selected_iid = self.wholesale_bill_tree.focus()
        # selected_item = self.wholesale_bill_tree.item(selected_iid)

        self.wholesale_bill_tree.delete(selected_iid)
        self.update_wholesale_total()
        self.wholesale_barcode_entry.focus_force()

    def wholesale_add_product_loop(self, event):
        # print("adding product to whole sale bill")
        # while self.add_product_running:
            
        if self.wholesale_barcode_entry.get():
            barcode = self.wholesale_barcode_entry.get()
            product_name = ""
            product_quantity = 1
            cost = str(0.0)  + (" "*33) # Replace with actual product cost
            wholesale_cost = str(0.0) + (" "*33)
            sub_total = product_quantity * float(wholesale_cost)

            bill_data_tuple = self.wholesale_bill_tree.get_children()
            # print(bill_data_tuple)
            bill_barcode_dict = [self.wholesale_bill_tree.item(item, 'values')[0] for item in bill_data_tuple]
            # print(bill_barcode_dict)

            if barcode in bill_barcode_dict:
                product_name = self.wholesale_bill_tree.item(bill_data_tuple[bill_barcode_dict.index(barcode)]).get("values")[1]
                cost = float(self.wholesale_bill_tree.item(bill_data_tuple[bill_barcode_dict.index(barcode)]).get("values")[3])
                wholesale_cost = float(self.wholesale_bill_tree.item(bill_data_tuple[bill_barcode_dict.index(barcode)]).get("values")[4])
                product_quantity = int(self.wholesale_bill_tree.item(bill_data_tuple[bill_barcode_dict.index(barcode)]).get("values")[2]) + 1
                sub_total = str(product_quantity * wholesale_cost) + (" "*30)
                cost = str(cost) + (" "*33)
                wholesale_cost = str(wholesale_cost) + (" "*33)
                product_quantity =str(product_quantity) + (" "*33)
                values = (barcode,product_name,product_quantity,cost,wholesale_cost,sub_total)
                self.wholesale_bill_tree.item(bill_data_tuple[bill_barcode_dict.index(barcode)],values=values)

            else:
                # Insert a new row in the table
                
                # print(type(valsFromStock))
                # print(valsFromStock)
                if self.get_values(barcode=barcode):
                    valsFromStock = self.get_values(barcode=barcode)
                    if int(barcode) == valsFromStock.barcode:
                        product_name = valsFromStock.product_details
                        cost = float(valsFromStock.cost)
                        wholesale_cost = float(valsFromStock.wholesale_cost)
                        sub_total = str(wholesale_cost * int(product_quantity)) + (" "*30)
                        cost = str(cost) + (" "*33)
                        wholesale_cost = str(wholesale_cost) + (" "*33)
                        product_quantity =str(product_quantity) + (" "*33)
                        self.wholesale_bill_tree.insert("", "end", text=barcode, values=(barcode,product_name,product_quantity,cost,wholesale_cost,sub_total))
                else:
                    self.wholesale_bill_tree.insert("", "end", text=barcode, values=(barcode,product_name,product_quantity,cost,wholesale_cost,sub_total))

                # print(valsFromStock)
                
            # print([self.bill_tree.item(item, 'values') for item in self.bill_tree.get_children()])

            
            # self.scrollbar.configure()
            self.update_wholesale_total()
            
    
            # self.bill_tree.update_idletasks()
            self.wholesale_bill_tree.yview_moveto(1.0)

            
            self.wholesale_barcode_entry.delete("0", "end")
            self.wholesale_barcode_entry.focus_force()
        
        
        self.root.update()
    
    def on_double_click_wholesale_bill(self, event):

        region_clicked = self.wholesale_bill_tree.identify_region(event.x, event.y)
        # region_clicked = self.stock_tree.identify_region(event.x, event.y)
        # print(region_clicked)

        if region_clicked not in ("cell"):
            return
        
        column = self.wholesale_bill_tree.identify_column(event.x)
        column_index = int(column[1:]) - 1
        

        selected_iid = self.wholesale_bill_tree.focus()
        selected_value = str(self.wholesale_bill_tree.item(selected_iid).get("values")[column_index]).strip()

        column_box = self.wholesale_bill_tree.bbox(selected_iid,column)
        # print(column)
        # print(self.wholesale_bill_tree.bbox(column=column))

        if hasattr(self, 'entry_edit_wholesale_bill_tree') and isinstance(self.entry_edit_wholesale_bill_tree, ttk.Entry):
            self.entry_edit_wholesale_bill_tree.destroy()

        self.entry_edit_wholesale_bill_tree = ttk.Entry(self.wholesale_bill_tree,justify='center', font=('Arial', 13))

        self.entry_edit_wholesale_bill_tree.editing_column_index = column_index
        self.entry_edit_wholesale_bill_tree.editing_item_iid = selected_iid

        self.entry_edit_wholesale_bill_tree.insert(0,selected_value)
        self.entry_edit_wholesale_bill_tree.select_range(0, tk.END)
        self.entry_edit_wholesale_bill_tree.focus()

        self.entry_edit_wholesale_bill_tree.bind("<FocusOut>", self.on_focus_out_wholesale_bill_tree)
        self.entry_edit_wholesale_bill_tree.bind("<Return>", self.on_enter_pressed_wholesale_bill_tree)
        self.entry_edit_wholesale_bill_tree.place(x=column_box[0],y=column_box[1],w=column_box[2],h=column_box[3])

    def on_enter_pressed_wholesale_bill_tree(self, event):

        
        if hasattr(self, 'entry_edit_wholesale_bill_tree') and isinstance(self.entry_edit_wholesale_bill_tree, ttk.Entry):

            new_value = self.entry_edit_wholesale_bill_tree.get()

            selected_iid = self.entry_edit_wholesale_bill_tree.editing_item_iid
            column_index = self.entry_edit_wholesale_bill_tree.editing_column_index
            # print(column_index)

            current_values = self.wholesale_bill_tree.item(selected_iid).get("values")
            
            
            # Quantity
            if column_index == 2:
                current_values[column_index] = str(new_value) + (" "*33)
                # SubTot = Q * (Cost - Discount)
                current_values[-1] = str(int(new_value) * float(current_values[column_index + 2])) + (" "*30)

            # Wholesale Cost
            elif column_index == 4:
                current_values[column_index] = str(float(new_value)) + (" "*33)
                # current_values[column_index - 1] = str(current_values[column_index - 1]) + (" "*33)
                # SubTot = Q * (Cost - Discount)
                current_values[-1] = str(int(current_values[column_index - 2]) * float(new_value)) + (" "*30)
            
            # Cost
            elif column_index == 3:
                current_values[column_index] = str(float(new_value)) + (" "*33)
                # current_values[column_index - 1] = str(current_values[column_index - 1]) + (" "*33)
                # SubTot = Q * (Cost - Discount)
                # current_values[-1] = str(int(current_values[column_index - 1]) * (float(new_value) - float(current_values[column_index + 1]))) + (" "*30)

            # Poduct name
            elif column_index == 1:
                current_values[column_index] = new_value
                

            # print(current_values[column_index])

            current_values[-4] = str(current_values[-4]).strip() + (" "*33)
            self.wholesale_bill_tree.item(selected_iid, values=current_values)

            self.update_wholesale_total()

            self.entry_edit_wholesale_bill_tree.destroy()
            self.wholesale_barcode_entry.focus_force()

    def on_focus_out_wholesale_bill_tree(self, event):

        if hasattr(self, 'entry_edit_wholesale_bill_tree') and isinstance(self.entry_edit_wholesale_bill_tree, ttk.Entry):

            new_value = self.entry_edit_wholesale_bill_tree.get()

            selected_iid = self.entry_edit_wholesale_bill_tree.editing_item_iid
            column_index = self.entry_edit_wholesale_bill_tree.editing_column_index
            # print(column_index)

            current_values = self.wholesale_bill_tree.item(selected_iid).get("values")
            
            
            # Quantity
            if column_index == 2:
                current_values[column_index] = str(new_value) + (" "*33)
                # SubTot = Q * (Cost - Discount)
                current_values[-1] = str(int(new_value) * float(current_values[column_index + 2])) + (" "*30)

            # Wholesale Cost
            elif column_index == 4:
                current_values[column_index] = str(float(new_value)) + (" "*33)
                # current_values[column_index - 1] = str(current_values[column_index - 1]) + (" "*33)
                # SubTot = Q * (Cost - Discount)
                current_values[-1] = str(int(current_values[column_index - 2]) * float(new_value)) + (" "*30)
            
            # Cost
            elif column_index == 3:
                current_values[column_index] = str(float(new_value)) + (" "*33)
                # current_values[column_index - 1] = str(current_values[column_index - 1]) + (" "*33)
                # SubTot = Q * (Cost - Discount)
                # current_values[-1] = str(int(current_values[column_index - 1]) * (float(new_value) - float(current_values[column_index + 1]))) + (" "*30)

            # Poduct name
            elif column_index == 1:
                current_values[column_index] = new_value
                

            # print(current_values[column_index])

            current_values[-4] = str(current_values[-4]).strip() + (" "*33)
            self.wholesale_bill_tree.item(selected_iid, values=current_values)

            self.update_wholesale_total()

            self.entry_edit_wholesale_bill_tree.destroy()
            self.wholesale_barcode_entry.focus_force()

    def wholesale_return_amount_popup(self, event):
        # print("Popping up")
        if self.wholesale_customer_money.get():
            self.return_amt_popup = tk.Toplevel(self.root)
            self.return_amt_popup.title("Return AMOUNT")
            window_width = 400
            window_height = 300
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2

            self.return_amt_popup.geometry(f"{window_width}x{window_height}+{x}+{y}")
            amount_intake_label = tk.Label(self.return_amt_popup)
            amount_intake_label.config(text = f"Amount Intake : {float(self.wholesale_customer_money.get())}", font=('Arial', 16, 'bold'))
            amount_intake_label.pack(pady=20)

            self.amount_intake_label = tk.Label(self.return_amt_popup)
            self.amount_intake_label.config(text=f"RETURN : {(float(self.wholesale_customer_money.get()) - self.w_total):.2f}", font=('Arial', 18, 'bold'), foreground='green')
            self.amount_intake_label.pack(pady=20)

            self.print_wholesale_bill()

            # self.amount_intake_entry = tk.Entry(self.return_amt_popup)
            # self.amount_intake_entry.pack(pady=20)
            # self.amount_intake_entry.bind("<Return>", self.show_return_amount)

            popup_button = tk.Button(self.return_amt_popup, text="Close", command=self.return_amt_popup.destroy)
            self.return_amt_popup.bind("<Return>", self.destroy_popup)
            popup_button.pack()

    def update_wholesale_total(self):
        # Calculate the total from the values in the tree
        self.w_total = 0.0
        for item in self.wholesale_bill_tree.get_children():
            sub_total = float(self.wholesale_bill_tree.item(item, 'values')[-1]) # Assuming the cost is the last column
            # quantity = int(self.bill_tree.item(item, 'values')[-2]) # Assuming the quantity is the -2 column
            self.w_total += sub_total
        
        
        # Update the total label
        self.wholesale_total_label.config(text=f"Total: {self.w_total:.2f}")

    def print_wholesale_bill(self):
        if self.wholesale_bill_tree.get_children():
            gap = " "*21
            current_date = datetime.now().strftime("%d/%m/%Y")
            current_time = datetime.now().strftime("%H:%M")
            # self.printer.image(img_source="kk_logo_print.png",center=True,)
            # self.printer.textln(" "*48)
            self.printer.textln(f"Date: {current_date}{gap}Time: {current_time}")
            self.printer.textln("*"*48)
            self.printer.textln("PRODUCT                QTY   MRP  W_COST  TOTAL ")
            self.printer.textln("*"*48)
            for item in self.wholesale_bill_tree.get_children():
                d = self.wholesale_bill_tree.item(item, 'values')
                # print(d)
                
                p = d[-5].strip()[:22].ljust(22," ")
                q = (d[-4].strip() + " ").rjust(4, " ")
                c = d[-3].strip().rjust(6, " ")
                w_cost = (d[-2].strip() + "  ").rjust(8," ")
                t = d[-1].strip().rjust(8," ")
                self.printer.textln(p+q+c+w_cost+t)
            
            self.printer.textln("*"*48)
            self.printer.set(align='center',font= 1,bold= True,double_height=True,double_width=True)
            total = "TOTAL : " + f"{self.w_total:.2f}"
            total = " "*(30-len(total))+ total
            self.printer.textln(total)
            self.printer.set_with_default()
            self.printer.textln(" "*48)
            amount_intake = "Amount INTAKE : "+ f"{float(self.wholesale_customer_money.get()):.2f}" + "  "
            amount_intake = " "*(48-len(amount_intake))+ amount_intake
            self.printer.textln(amount_intake)
            return_amount = "Amount RETURN : " + f"{float(self.wholesale_customer_money.get()) - self.w_total:.2f}" + "  "
            return_amount = " "*(48-len(return_amount))+ return_amount
            self.printer.textln(return_amount)
            self.printer.textln("*"*48)
            self.printer.cut()

        self.wholesale_barcode_entry.focus_force()

    def clear_wholesale_bill_tree(self, event):

        self.wholesale_bill_tree.delete(*self.wholesale_bill_tree.get_children())
        self.update_wholesale_total()
        self.wholesale_customer_money.delete("0","end")
        self.wholesale_barcode_entry.focus_force()
        
    def create_wholesale_tab(self):
        # Add widgets for the customer entry tab
        self.wholesale_bill_tree = ttk.Treeview(self.wholesale_tab, columns=("Barcode","Product Name","Quantity","Cost","Wholesale Price","Sub Total"), show="headings", height=12)

        style = ttk.Style(self.wholesale_bill_tree)
        style.configure("Treeview.Heading", font=('Arial', 14))
        style.configure("Treeview", font=('Arial', 14))

        self.wholesale_bill_tree.heading("Barcode", text="Barcode", anchor=tk.CENTER)
        self.wholesale_bill_tree.heading("Product Name", text="Product Name", anchor=tk.CENTER)
        self.wholesale_bill_tree.heading("Quantity", text="Quantity", anchor=tk.CENTER)
        self.wholesale_bill_tree.heading("Cost", text="Cost", anchor=tk.CENTER)
        self.wholesale_bill_tree.heading("Wholesale Price", text="Wholesale Price", anchor=tk.CENTER)
        self.wholesale_bill_tree.heading("Sub Total", text="Sub Total", anchor=tk.CENTER)

        self.wholesale_bill_tree.column("Barcode", anchor=tk.CENTER)
        self.wholesale_bill_tree.column("Product Name", anchor=tk.CENTER)
        self.wholesale_bill_tree.column("Quantity", anchor=tk.E)
        self.wholesale_bill_tree.column("Cost", anchor=tk.E)
        self.wholesale_bill_tree.column("Wholesale Price", anchor=tk.E)
        self.wholesale_bill_tree.column("Sub Total", anchor=tk.E)

        # print(self.bill_tree.column("Barcode")["width"])
        # print(self.bill_tree.column("Product Name")["width"])
        # print(self.bill_tree.column("Quantity")["width"])
        # print(self.bill_tree.column("Cost")["width"])
        # print(self.bill_tree.column("Sub Total")["width"])

        self.wholesale_bill_tree.bind("<Double-1>", self.on_double_click_wholesale_bill)
        self.wholesale_bill_tree.bind("<Delete>", self.on_delete_wholesale_bill)
        

        self.scrollbar = ttk.Scrollbar(self.wholesale_tab, orient="vertical", command=self.wholesale_bill_tree.yview)
        self.scrollbar.pack(side="right",fill='y')
        self.wholesale_bill_tree.configure(yscrollcommand=self.scrollbar.set)
        self.wholesale_bill_tree.pack(expand=True, fill="both")
        self.wholesale_bill_tree.bind('<Control_L>', self.clear_wholesale_bill_tree)
        

        # self.bill_tree.pack(side="left", expand=True, fill="both")

        # self.entry_var = tk.StringVar()
        # self.entry_var.trace_add('write', self.add_product_loop)
        # self.customer_det = ttk.Entry(self.wholesale_tab)
        # self.customer_det.bind("<Return>", self.create_popup)
        # self.customer_det.bind('<Return>', self.find_customer)
        self.wholesale_customer_money = ttk.Entry(self.wholesale_tab)
        self.wholesale_customer_money.bind("<Return>", self.wholesale_return_amount_popup)
        
        

        # Example: Entry for scanning barcode
        self.wholesale_barcode_entry = ttk.Entry(self.wholesale_tab)
        # selected_tab_index = self.tabControl.index(self.tabControl.select())
        # if selected_tab_index == 0:
            
        # self.customer_det.pack(side="left",pady=30, padx=350)
        self.wholesale_barcode_entry.pack(side="left",pady=30, padx=610)
        self.wholesale_customer_money.pack(side="left",pady=30, padx=50)
        self.wholesale_customer_money.bind("<Control_R>", self.wholesale_return_amount_popup)
        # self.wholesale_customer_money.place(relx=0.7, rely=0.98, anchor='se',bordermode='outside')
        # self.disc_500 = False
        self.wholesale_barcode_entry.bind('<Return>', self.wholesale_add_product_loop)
        self.wholesale_customer_money.bind("<Control_L>", self.clear_wholesale_bill_tree)
        self.wholesale_barcode_entry.bind('<Control_L>', self.clear_wholesale_bill_tree)
        
        # self.wholesale_customer_money.bind("<Return>", self.add_product_loop)

        # print(self.wholesale_customer_money.winfo_pathname(self.wholesale_customer_money.winfo_id()))
        style1 = ttk.Style()
        style1.configure("elder.TButton", height=6, width=12, font=("Arial", 14, "bold"), foreground='white', background='#33BEFF', padding=10)

        # self.add_product(wholesale_customer_money.get())

        # Example: Button to add product to the table
        self.new_wholesale_bill_button = ttk.Button(self.wholesale_tab, text="New W Bill", command=lambda: self.clear_wholesale_bill_tree(None), style="elder.TButton")
        self.new_wholesale_bill_button.place(relx=0.07, rely=0.98, anchor='sw')
        # self.add_button.pack(pady=10)
        style2 = ttk.Style()
        style2.configure("TButton", height=6, width=12, font=("Arial", 14, "bold"), foreground='white', background='#7433FF', padding=10)
        # self.add_product_running = False
        self.print_wholesale_bill_button = ttk.Button(self.wholesale_tab, text="Print Bill", style="TButton", command=lambda: self.wholesale_return_amount_popup(None))
        self.print_wholesale_bill_button.place(relx=0.73, rely=0.98, anchor='se')
        

        self.wholesale_total_label = tk.Label(self.wholesale_tab, text="Total: 0.00", font=('Arial', 25, 'bold'), foreground='red')
        self.wholesale_total_label.place(relx=0.98, rely=0.98, anchor='se')

        self.wholesale_barcode_label = tk.Label(self.wholesale_tab, text="BARCODE", font=('Arial', 12))
        self.wholesale_barcode_label.place(relx=0.38, rely=0.94, anchor='se')

        # self.customer_num = tk.Label(self.wholesale_tab, text="Customer Number", font=('Arial', 12))
        # self.customer_num.place(relx=0.19, rely=0.94, anchor='sw')

        # self.customer_num = tk.Label(self.wholesale_tab, text="Customer Details", font=('Arial', 12))
        # self.customer_num.place(relx=0.35, rely=0.94, anchor='sw')

        self.wholesale_customer_amount = tk.Label(self.wholesale_tab, text="Amount INTAKE", font=('Arial', 12))
        self.wholesale_customer_amount.place(relx=0.82, rely=0.94, anchor='se')

        self.tab_2_entries = [self.wholesale_barcode_entry, self.wholesale_customer_money]
        
        

        # self.customer_details = tk.Label(self.wholesale_tab, text="Customer Name : kalyan kalyan Ph : 9494411661", font=('Arial', 12))
        # self.customer_details.place(relx=0.30, rely=0.98, anchor='sw')

        # self.img = PhotoImage(file="kk_logo_90p.png")
        # # self.img.place(relx=0.1, rely=0.98, anchor='sw',bordermode='outside')
        # self.label = tk.Label(self.wholesale_tab, image=self.img)
        # self.label.place(relx=0, rely=1, anchor='sw',bordermode='outside')
    
    def calculate_checksum(self,digits):
        """
        Calculate the checksum digit for the provided digits.
        """
        odd_sum = sum(int(digit) for digit in digits[::2])
        even_sum = sum(int(digit) for digit in digits[1::2]) * 3
        total_sum = odd_sum + even_sum
        checksum_digit = (10 - (total_sum % 10)) % 10
        return checksum_digit

    def generate_ean13_barcode(self,digits):
        """
        Generate the EAN-13 barcode for the provided digits.
        """
        checksum = self.calculate_checksum(digits)
        barcode_digits = digits + str(checksum)
        ean = barcode.get_barcode_class('ean13')
        ean_barcode = ean(barcode_digits, writer=ImageWriter())
        filename = ean_barcode.save('ean13_barcode')
        return filename

    def copy_barcode_to_clipboard(self,event):
        """
        Copy the barcode digits to the clipboard.
        """
        if self.barcode_text.get("1.0", "end-1c"):
            barcode_digits = self.barcode_text.get("1.0", "end-1c")
            if barcode_digits:
                self.barcode_gen_tab.clipboard_clear()
                self.barcode_gen_tab.clipboard_append(barcode_digits)
                messagebox.showinfo("Info", "Barcode copied to clipboard.")
            else:
                messagebox.showwarning("Warning", "No barcode to copy.")

    def generate_and_display_barcode(self,event):
        """
        Generate the barcode and display it in the Tkinter window.
        """
        # chosen_digits = self.custom_barcode_entry.get()chosen_digits = self.custom_barcode_entry.get()
        if self.custom_barcode_entry.get():
            chosen_digits = self.custom_barcode_entry.get()
            if len(chosen_digits) != 12 or not chosen_digits.isdigit():
                messagebox.showerror("Error", "Please enter 12 digits.")
                return

            barcode_digits = chosen_digits + str(self.calculate_checksum(chosen_digits))
            self.barcode_text.delete(1.0, tk.END)
            self.barcode_text.insert(tk.END, barcode_digits)

            barcode_filename = self.generate_ean13_barcode(chosen_digits)
            barcode_img = PhotoImage(file=barcode_filename)

            self.barcode_label.config(image=barcode_img)
            self.barcode_label.image = barcode_img


    def create_barcode_gen_tab(self):

        self.custom_barcode_entry = tk.Entry(self.barcode_gen_tab)
        self.custom_barcode_entry.pack(pady=10)

        # Create and place the button to generate barcode
        generate_button = tk.Button(self.barcode_gen_tab, text="Generate Barcode", command=self.generate_and_display_barcode(None))
        generate_button.pack(pady=5)
        self.custom_barcode_entry.bind("<Return>",self.generate_and_display_barcode)

        # Create and place the text widget to display barcode digits
        self.barcode_text = tk.Text(self.barcode_gen_tab, height=1, width=20)
        self.barcode_text.pack(pady=5)

        # Create and place the label to display barcode image
        self.barcode_label = tk.Label(self.barcode_gen_tab)
        self.barcode_label.pack(pady=10)

        # Create and place the button to copy barcode to clipboard
        copy_button = tk.Button(self.barcode_gen_tab, text="Copy Barcode", command=self.copy_barcode_to_clipboard(None))
        copy_button.pack(pady=5)
        self.custom_barcode_entry.bind("<Control-c>", self.copy_barcode_to_clipboard)

    def create_check_bills_tab(self):

        self.bills = self.load_bills_from_json()
        # self.current_index = len(self.bills) - 1
        self.check_bill_tree = ttk.Treeview(self.check_bills_tab, columns=("Barcode","Product Name","Quantity","Cost","Discount","Sub Total"), show="headings", height=12)
        self.check_bill_tree.pack(fill="both", expand=True)

        style = ttk.Style(self.check_bill_tree)
        style.configure("Treeview.Heading", font=('Arial', 14))
        style.configure("Treeview", font=('Arial', 14))

        self.check_bill_tree.heading("Barcode", text="Barcode", anchor=tk.CENTER)
        self.check_bill_tree.heading("Product Name", text="Product Name", anchor=tk.CENTER)
        self.check_bill_tree.heading("Quantity", text="Quantity", anchor=tk.CENTER)
        self.check_bill_tree.heading("Cost", text="Cost", anchor=tk.CENTER)
        self.check_bill_tree.heading("Discount", text="Discount", anchor=tk.CENTER)
        self.check_bill_tree.heading("Sub Total", text="Sub Total", anchor=tk.CENTER)

        self.check_bill_tree.column("Barcode", anchor=tk.CENTER)
        self.check_bill_tree.column("Product Name", anchor=tk.CENTER)
        self.check_bill_tree.column("Quantity", anchor=tk.E)
        self.check_bill_tree.column("Cost", anchor=tk.E)
        self.check_bill_tree.column("Discount", anchor=tk.E)
        self.check_bill_tree.column("Sub Total", anchor=tk.E)

        self.check_bill_total_label = tk.Label(self.check_bills_tab, text="Total : ", font=('Arial', 25, 'bold'), foreground='red')
        self.check_bill_total_label.place(relx=0.98, rely=0.98, anchor='se')

        # print("-----",self)

        self.scrollbar1 = ttk.Scrollbar(self.check_bills_tab, orient="vertical", command=self.check_bill_tree.yview)
        self.scrollbar1.pack(side="right",fill='y')
        self.check_bill_tree.configure(yscrollcommand=self.scrollbar1.set)
        self.check_bill_tree.pack(expand=True, fill="both")


        
        self.prev_button = tk.Button(self.check_bills_tab, text="Previous Bill", command=self.show_previous_bill)
        self.prev_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.next_button = tk.Button(self.check_bills_tab, text="Next Bill", command=self.show_next_bill)
        self.next_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.print_check_bill_button = ttk.Button(self.check_bills_tab, text="Print Bill", style="TButton", command=lambda: self.print_check_bill(None))
        self.print_check_bill_button.place(relx=0.73, rely=0.98, anchor='se')

        self.display_bill_tree()

        

    def parse_date_string(self,date_str):
        if date_str:
            return datetime.strptime(date_str,"%d/%m/%Y - %H:%M")
        else:
            return None
    def load_bills_from_json(self):
        # try:
        #     with open('bill_data.json', 'r') as json_file:
        #         return json.load(json_file)
        # except FileNotFoundError:
        #     return [] self.parse_date_string(str(Bill.date))
        self.bill_ids =  session.query(Bill).order_by(Bill.date.desc()).all()
        self.bill_id_index = 0

    def show_previous_bill(self):
        self.bill_id_index += 1
        if self.bill_id_index < 0:
            self.bill_id_index = 0
        # self.destroy_current_bill_tree()
        self.display_bill_tree()

    def show_next_bill(self):
        self.bill_id_index -= 1
        if self.bill_id_index >= len(self.bill_ids):
            self.bill_id_index = len(self.bill_ids) - 1
        # self.destroy_current_bill_tree()
        self.display_bill_tree()

    # def destroy_current_bill_tree(self):
    #     for widget in self.winfo_children():
    #         if isinstance(widget, ttk.Treeview):
    #             widget.destroy()

    
    def display_bill_tree(self):
        self.check_bill_tree.delete(*self.check_bill_tree.get_children())
        

        if self.bill_id_index < 0 or self.bill_id_index >= len(self.bill_ids):
            return

        self.current_check_bill = self.bill_ids[self.bill_id_index]

        query = session.query(BillItem).filter(getattr(BillItem, 'bill_id') == self.current_check_bill.id)
        results = query.all()

        # id = Column(Uuid, primary_key = True)
        # bill_id = Column(Uuid, ForeignKey('bills.id'))
        # product_details = Column(String)
        # quantity = Column(Integer)
        # unit_price = Column(Float)
        # discount = Column(Float)
        # sub_total = Column(Float)
        
        

        # self.check_bill_tree["columns"] = tuple(current_check_bill["items"][0].keys())
        # # self.check_bill_tree.heading("#0", text="Timestamp")
        # for column in self.check_bill_tree["columns"]:
        #     self.check_bill_tree.heading(column, text=column)
        # self.check_bill_tree.pack(fill="both", expand=True)

        for row in results:
            self.check_bill_tree.insert("", "end", values=("",row.product_details,row.quantity,row.unit_price,row.discount,row.sub_total))
        
        self.update_check_bill_total(self.current_check_bill)
        

    def update_check_bill_total(self,temp):

        # print(type(self))
        # print(self)

        self.check_bill_total_label.config(text=f"Total: {temp.total}")

    def print_check_bill(self,event):
        if self.check_bill_tree.get_children():
            self.printer.set_with_default()
            gap = " "*21
            current_date = self.current_check_bill['Timestamp'].split(" - ")[0]
            current_time = self.current_check_bill['Timestamp'].split(" - ")[1]
            self.printer.image(img_source="kk_logo_print.png",center=True,)
            self.printer.textln(" "*48)
            self.printer.textln(f"Date: {current_date}{gap}Time: {current_time}")
            self.printer.textln("*"*48)
            self.printer.textln("PRODUCT                QTY   MRP  DISCNT  TOTAL ")
            self.printer.textln("*"*48)
            for item in self.check_bill_tree.get_children():
                d = self.check_bill_tree.item(item, 'values')
                # print(d)
                
                p = d[-5].strip()[:22].ljust(22," ")
                q = (d[-4].strip() + " ").rjust(4, " ")
                c = d[-3].strip().rjust(6, " ")
                disc = (d[-2].strip() + "  ").rjust(8," ")
                t = d[-1].strip().rjust(8," ")
                self.printer.textln(p+q+c+disc+t)
            
            self.printer.textln("*"*48)
            self.printer.set(align='center',font= 1,bold= True,double_height=True,double_width=True)
            total = "TOTAL : " + f"{float(self.check_bill_total_label['text'].split(':')[-1].strip())}"
            total = " "*(30-len(total))+ total
            self.printer.textln(total)
            self.printer.set_with_default()
            self.printer.textln(" "*48)
            # amount_intake
            amount_intake = "Amount INTAKE : "+ f"{float(self.current_check_bill['amount_intake'])}" + "  "
            amount_intake = " "*(48-len(amount_intake))+ amount_intake
            self.printer.textln(amount_intake)
            return_amount = "Amount RETURN : " + f"{float(self.current_check_bill['amount_intake']) - float(self.check_bill_total_label['text'].split(':')[-1].strip())}" + "  "
            return_amount = " "*(48-len(return_amount))+ return_amount
            self.printer.textln(return_amount)
            self.printer.textln("*"*48)
            self.printer.cut()
        

if __name__ == "__main__":
    create_db()
    root = tk.Tk()
    app = BillingApp(root)
    root.mainloop()
