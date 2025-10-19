import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sqlite3

class AlternativeWindow:
    def __init__(self, db_file_path):
        self.db_file_path = db_file_path

        self.root = tk.Tk()
        self.root.title("BEAM DESIGN BY CCO")  # Small title in window frame
        self.root.geometry("500x550")  # Taller window (increased height)

        # Initialize Tkinter variables AFTER creating the root window
        self.excel_work_file = tk.StringVar()
        self.excel_default_file = tk.StringVar()

        # Center window
        self.center_window()

        self.create_widgets()

    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = 500
        height = 560
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def create_widgets(self):
        """Create alternative window widgets"""
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # File info frame - Only DB file info
        info_frame = ttk.LabelFrame(main_container, text="Fisier selectat")
        info_frame.pack(fill="x", pady=10)

        # DB file info
        db_info_frame = ttk.Frame(info_frame)
        db_info_frame.pack(fill="x", padx=10, pady=8)

        ttk.Label(db_info_frame, text="Fisier Baza de Date:", font=("Arial", 9, "bold")).pack(anchor="w")
        ttk.Label(db_info_frame, text=self.db_file_path).pack(anchor="w", padx=20)

        # Operations buttons frame - Vertical layout
        operations_frame = ttk.LabelFrame(main_container, text="Operatiuni")
        operations_frame.pack(fill="x", pady=15)

        # Create buttons in vertical layout
        buttons_container = ttk.Frame(operations_frame)
        buttons_container.pack(fill="x", padx=10, pady=10)

        # Button 1: View DB Data
        btn_view = ttk.Button(
            buttons_container,
            text="Vizualizare DB",
            command=self.view_db_data,
            width=30
        )
        btn_view.pack(pady=5)

        # Button 2: Inject Excel to DB
        btn_inject = ttk.Button(
            buttons_container,
            text="Injectare date EXCEL ==> DB",
            command=self.inject_excel_to_db,
            width=30
        )
        btn_inject.pack(pady=5)

        # Button 3: Overwrite DB to Excel
        btn_overwrite = ttk.Button(
            buttons_container,
            text="Suprascriere date DB ==> EXCEL",
            command=self.overwrite_db_to_excel,
            width=30
        )
        btn_overwrite.pack(pady=5)

        # Button 4: Create new Excel from DB
        btn_create_excel = ttk.Button(
            buttons_container,
            text="Creare fisier excel nou dupa DB",
            command=self.create_excel_from_db,
            width=30
        )
        btn_create_excel.pack(pady=5)

        # Excel file selectors frame
        excel_frame = ttk.LabelFrame(main_container, text="Fisiere Excel")
        excel_frame.pack(fill="x", pady=15)

        # Excel work file selector
        work_file_frame = ttk.Frame(excel_frame)
        work_file_frame.pack(fill="x", padx=10, pady=8)

        ttk.Label(work_file_frame, text="Fisier Excel in lucru:", width=20).pack(side="left")
        ttk.Entry(work_file_frame, textvariable=self.excel_work_file, width=30).pack(side="left", padx=5)
        ttk.Button(work_file_frame, text="Browse", command=self.browse_work_excel, width=8).pack(side="left")

        # Excel default file selector
        default_file_frame = ttk.Frame(excel_frame)
        default_file_frame.pack(fill="x", padx=10, pady=8)

        ttk.Label(default_file_frame, text="Fisier Excel Default:", width=20).pack(side="left")
        ttk.Entry(default_file_frame, textvariable=self.excel_default_file, width=30).pack(side="left", padx=5)
        ttk.Button(default_file_frame, text="Browse", command=self.browse_default_excel, width=8).pack(side="left")

        # Bottom frame for Close button - RIGHT side with more space
        bottom_frame = ttk.Frame(main_container)
        bottom_frame.pack(side="bottom", fill="x", pady=20)  # Increased padding

        # Small Close button in RIGHT bottom corner - more visible
        ttk.Button(
            bottom_frame,
            text="Close",
            command=self.close_window,
            width=10  # Slightly wider for better visibility
        ).pack(side="right", padx=10, pady=10)  # Added padding for visibility

    def browse_work_excel(self):
        """Browse for Excel work file"""
        filename = filedialog.askopenfilename(
            title="Selecteaza fisierul Excel in lucru",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        if filename:
            self.excel_work_file.set(filename)

    def browse_default_excel(self):
        """Browse for Excel default file"""
        filename = filedialog.askopenfilename(
            title="Selecteaza fisierul Excel default",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        if filename:
            self.excel_default_file.set(filename)

    def view_db_data(self):
        """Show all DB data in an interactive table"""
        try:
            # Connect to database
            conn = sqlite3.connect(self.db_file_path)
            cursor = conn.cursor()

            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()

            if not tables:
                messagebox.showinfo("Info", "⮽⮽ Nu exista tabele in baza de date.")
                return

            # For simplicity, show data from the first table
            table_name = tables[0][0]
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()

            # Get column names
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [column[1] for column in cursor.fetchall()]

            conn.close()

            # Show interactive table
            self.show_interactive_table(columns, rows, f"Date din tabelul: {table_name}")

        except Exception as e:
            messagebox.showerror("⮽⮽ Eroare", f"Eroare la citirea bazei de date: {e}")

    def show_interactive_table(self, columns, rows, title):
        """Show an interactive table"""
        try:
            # Create new window for table
            table_window = tk.Toplevel(self.root)
            table_window.title(title)
            table_window.geometry("900x500")

            # Create frame for table
            table_frame = ttk.Frame(table_window)
            table_frame.pack(fill="both", expand=True, padx=10, pady=10)

            # Create treeview
            tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=20)

            # Configure columns
            for col in columns:
                tree.heading(col, text=col, command=lambda _col=col: self.treeview_sort_column(tree, _col, False))
                tree.column(col, width=100)

            # Add data
            for row in rows:
                tree.insert('', 'end', values=row)

            # Add scrollbars
            v_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
            h_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
            tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

            # Pack everything
            tree.pack(side='left', fill='both', expand=True)
            v_scrollbar.pack(side='right', fill='y')
            h_scrollbar.pack(side='bottom', fill='x')

        except Exception as e:
            messagebox.showerror("⮽⮽ Eroare", f"Eroare la afisarea tabelului: {e}")

    def treeview_sort_column(self, tree, col, reverse):
        """Sort treeview column when clicked"""
        try:
            data = [(tree.set(k, col), k) for k in tree.get_children('')]
            data.sort(reverse=reverse)

            for index, (val, k) in enumerate(data):
                tree.move(k, '', index)

            tree.heading(col, command=lambda: self.treeview_sort_column(tree, col, not reverse))
        except:
            pass

    def inject_excel_to_db(self):
        """Inject data from Excel to Database"""
        messagebox.showinfo("Info", "Functia 'Injectare date EXCEL ==> DB' va fi implementata.")
        # Placeholder for Excel injection functionality

    def overwrite_db_to_excel(self):
        """Overwrite Excel file with DB data"""
        messagebox.showinfo("Info", "Functia 'Suprascriere date DB ==> EXCEL' va fi implementata.")
        # Placeholder for DB to Excel overwrite functionality

    def create_excel_from_db(self):
        """Create new Excel file from DB data"""
        messagebox.showinfo("Info", "Functia 'Creare fisier excel nou dupa DB' va fi implementata.")
        # Placeholder for Excel creation functionality

    def close_window(self):
        """Close the alternative window"""
        print("-- Inchidere fereastra baza de date existenta")
        self.root.destroy()

    def run(self):
        """Run the alternative window"""
        print("-- Pornire fereastra baza de date existenta")
        self.root.mainloop()
