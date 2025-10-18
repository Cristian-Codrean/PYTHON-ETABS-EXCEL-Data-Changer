import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sys
import os


class StartupWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("BEAM DESIGN BY CCO")
        self.root.geometry("450x400")  # Înălțime crescută la 400
        self.root.resizable(False, False)

        # Centrează fereastra pe ecran
        self.center_window()

        # Va stoca alegerea utilizatorului
        self.choice = None

        # Doar stocarea căii fișierului DB (fișierul ETABS eliminat)
        self.db_file_path = tk.StringVar()

        self.create_widgets()

    def center_window(self):
        """Centrează fereastra pe ecran"""
        self.root.update_idletasks()
        width = 450
        height = 400
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def create_widgets(self):
        """Creează widget-urile ferestrei de start"""
        # Container principal cu mai mult padding
        main_container = ttk.Frame(self.root)
        main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Frame pentru butoane mari
        buttons_frame = ttk.Frame(main_container)
        buttons_frame.pack(fill="x", pady=15)

        # Buton 1: Creează bază de date nouă - ÎNTOTDEAUNA DISPONIBIL
        self.btn_create_db = ttk.Button(
            buttons_frame,
            text="Creează o bază de date nouă",
            command=self.create_new_database,
            width=40,
            style="Big.TButton"
        )
        self.btn_create_db.pack(pady=10)

        # Buton 2: Conectează-te la bază de date existentă
        self.btn_connect_db = ttk.Button(
            buttons_frame,
            text="Conectează-te la o bază de date existentă",
            command=self.connect_to_existing_database,
            width=40,
            style="Big.TButton",
            state="disabled"  # Inițial dezactivat până când fișierul DB este selectat
        )
        self.btn_connect_db.pack(pady=10)

        # Selector fișier DB doar - ÎNTOTDEAUNA VIZIBIL - Făcut mai înalt
        file_selectors_frame = ttk.LabelFrame(main_container, text="Fișier bază de date")
        file_selectors_frame.pack(fill="x", pady=15, ipady=10)  # Padding intern crescut

        # Selector fișier DB cu mai mult spațiu vertical
        db_frame = ttk.Frame(file_selectors_frame)
        db_frame.pack(fill="x", padx=15, pady=12)  # Padding crescut

        ttk.Label(db_frame, text="Fișier DB:", width=10).pack(side="left")
        db_entry = ttk.Entry(db_frame, textvariable=self.db_file_path, width=25)
        db_entry.pack(side="left", padx=5)
        ttk.Button(db_frame, text="Browse", command=self.browse_db_file, width=8).pack(side="left")

        # Etichetă status pentru validare fișier DB
        self.db_status = ttk.Label(main_container, text="❌ Selectează fișier bază de date", foreground="red")
        self.db_status.pack(anchor="w", pady=8)

        # Frame pentru butonul Close - Asigură-te că este în partea de jos
        bottom_frame = ttk.Frame(main_container)
        bottom_frame.pack(side="bottom", fill="x", pady=10)

        # Buton Close - MIC în colțul stânga jos
        ttk.Button(
            bottom_frame,
            text="Close",
            command=self.close_application,
            width=8
        ).pack(side="left", anchor="sw")

        # Configurează stilul butoanelor mari
        style = ttk.Style()
        style.configure("Big.TButton", font=("Arial", 10, "bold"), padding=8)

        # Setează trace pentru a monitoriza modificările căii fișierului DB
        self.db_file_path.trace('w', self.update_buttons_state)

    def update_buttons_state(self, *args):
        """Actualizează starea butoanelor în funcție de selecția fișierului DB"""
        db_file = self.db_file_path.get()

        # Actualizează eticheta de status
        if db_file and os.path.exists(db_file):
            self.db_status.config(text="✅ Fișier bază de date selectat", foreground="green")
            self.btn_connect_db.config(state="normal")  # Activează al doilea buton
        elif db_file:
            self.db_status.config(text="❌ Fișier bază de date nu există", foreground="red")
            self.btn_connect_db.config(state="disabled")  # Dezactivează al doilea buton
        else:
            self.db_status.config(text="❌ Selectează fișier bază de date", foreground="red")
            self.btn_connect_db.config(state="disabled")  # Dezactivează al doilea buton

        # Primul buton este ÎNTOTDEAUNA activat (nu este necesară validare fișier)
        self.btn_create_db.config(state="normal")

    def browse_db_file(self):
        """Caută fișierul bazei de date"""
        filename = filedialog.askopenfilename(
            title="Selectează fișierul bazei de date",
            filetypes=[("Fișiere Database", "*.db"), ("Fișiere SQLite", "*.sqlite"), ("Toate fișierele", "*.*")]
        )
        if filename:
            self.db_file_path.set(filename)

    def create_new_database(self):
        """Gestionează apăsarea butonului 'Creează bază de date nouă'"""
        print("Utilizatorul a selectat: Creează bază de date nouă")
        self.choice = "main_app"
        self.root.quit()
        self.root.destroy()

    def connect_to_existing_database(self):
        """Gestionează apăsarea butonului 'Conectează-te la bază de date existentă'"""
        # Validează dacă fișierul DB există
        db_file = self.db_file_path.get()

        if not db_file:
            messagebox.showerror("Eroare", "Te rog selectează un fișier bază de date!")
            return

        if not os.path.exists(db_file):
            messagebox.showerror("Eroare", f"Fișierul bazei de date nu există:\n{db_file}")
            return

        print(f"Conectare la bază de date existentă: {db_file}")
        self.choice = "alternative"
        self.root.quit()
        self.root.destroy()

    def close_application(self):
        """Închide complet aplicația"""
        self.choice = "exit"
        self.root.quit()
        self.root.destroy()

    def get_choice(self):
        """Returnează alegerea utilizatorului"""
        return self.choice

    def get_file_paths(self):
        """Returnează căile fișierelor selectate (doar fișierul DB acum)"""
        return {
            "db_file": self.db_file_path.get()
        }

    def run(self):
        """Rulează fereastra de start și returnează alegerea"""
        self.root.mainloop()
        return self.choice