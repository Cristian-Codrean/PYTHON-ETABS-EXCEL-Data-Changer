import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sys
import os
import json
import sqlite3
from datetime import datetime
from etabs_api.connection import get_sap_model
sap_model = get_sap_model()


current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Încercă să importe API-ul ETABS
try:
    import etabs_api.operations
except ImportError as e:
    print(f"⮽⮽ Avertisment de import operatiuni API ETABS: {e}")

# Importă widget-uri
try:
    from .widgets import ScenarioFrame, FileSelectionFrame, ControlButtons, SelectionConfirmationDialog, \
        SimpleSummaryPopup
except ImportError:
    try:
        from widgets import ScenarioFrame, FileSelectionFrame, ControlButtons, SelectionConfirmationDialog, \
            SimpleSummaryPopup
    except ImportError:
        try:
            sys.path.insert(0, current_dir)
            from widgets import ScenarioFrame, FileSelectionFrame, ControlButtons, SelectionConfirmationDialog, \
                SimpleSummaryPopup
        except ImportError as e:
            print(f"⮽⮽ Eșuat import widget-uri: {e}")
            sys.exit(1)

# Importă operațiuni Excel direct
try:
    from excel.operations import *
except ImportError:
    print(f"⮽⮽ Avertisment de import operatiuni EXCEL: {e}")

# Importă operațiuni bază de date direct
try:
    from db.operations import create_database
except ImportError:
    print(f"⮽⮽ Avertisment de import operatiuni Baza de Date : {e}")


class DesignApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Beam Design by CCO")
        self.root.resizable(True, True)

        # Testează conexiunea ETABS făcând un apel API simplu
        print("-- Testare conexiune ETABS")
        try:
            # Testează conexiunea cu un apel simplu
            test_result = sap_model.GetModelFilename()
            print(f"✓✓ Conexiune ETABS SUCCES. Model: {test_result}")

        except Exception as e:
            print(f"⮽⮽ Test conexiune ETABS eșuat: {e}")
            print(">> Te rog asigură-te că ETABS rulează cu un model deschis.")
            self.root.destroy()
            return

        # Dacă ajungem aici, conexiunea este bună - inițializează GUI
        self.initialize_gui()

    def initialize_gui(self):
        """Inițializează componentele GUI"""
        print("-- Inițializare GUI")

        # ==================== URĂRIRE STARE ====================
        # Starea butoanelor pentru ambele scenarii
        self.button_states = {
            ("A", "DCL"): False, ("A", "DCM"): False, ("A", "DCH"): False,
            ("A", "Secundare"): False, ("A", "Dir X"): False, ("A", "Dir Y"): False,
            ("B", "DCL"): False, ("B", "DCM"): False, ("B", "DCH"): False,
            ("B", "Secundare"): False, ("B", "Dir X"): False, ("B", "Dir Y"): False,
        }

        # Starea radio butoanelor de sus
        self.top_radio_state = "Normale"

        # Combinațiile selectate
        self.selected_combinations = {
            "A_upper": [], "A_lower": [], "B_upper": [], "B_lower": []
        }

        # Valoarea etajului selectat
        self.etaj_value = None

        # ==================== URĂRIRE SELECȚIE GRINZI ====================
        self.beam_selection_active = False
        self.current_beam_group = []
        self.all_beam_groups_a = []  # Pentru Infrastructură
        self.all_beam_groups_b = []  # Pentru Suprastructură
        self.current_scenario = None
        self.tracking_id = None

        # ==================== CONTAINER PRINCIPAL ====================
        container = ttk.Frame(self.root)
        container.pack(expand=True, fill="both")

        # --- Switch top pentru rezistențe ---
        switches_frame = ttk.Frame(container)
        switches_frame.pack(pady=10)
        self.rezistente_var = tk.StringVar(value="Normale")
        switch1 = ttk.Frame(switches_frame)
        switch1.pack()
        tk.Radiobutton(switch1, text="Rezistențe Normale", variable=self.rezistente_var, value="Normale",
                       command=self.update_top_radio_state).pack(side="left", padx=20)
        tk.Radiobutton(switch1, text="Rezistențe Medii", variable=self.rezistente_var, value="Medii",
                       command=self.update_top_radio_state).pack(side="left", padx=20)

        # --- Dropdown etaj ---
        ttk.Label(container, text="Etaj:").pack()
        self.story_var = tk.StringVar()
        self.story_dropdown = ttk.Combobox(container, textvariable=self.story_var, state="readonly")

        # Umple dropdown cu etaje din ETABS
        try:
            stories = etabs_api.operations.get_story_names()
            self.story_dropdown['values'] = stories
            print(f"-- Încărcat {len(stories)} etaje din ETABS")
        except Exception as e:
            print(f"⮽⮽ Eroare la încărcarea etajelor: {e}")
            self.story_dropdown['values'] = []

        self.story_dropdown.pack(pady=5)
        self.story_dropdown.bind('<<ComboboxSelected>>', self.update_etaj_value)

        # --- Container frame-uri scenarii ---
        frame_scenarios = ttk.Frame(container)
        frame_scenarios.pack()

        # ==================== FRAME-URI SCENARII ====================
        # Scenariul A - Infrastructura
        self.scenario_a = ScenarioFrame(
            parent=frame_scenarios,
            scenario_name="Infrastructura",
            scenario_id="A",
            button_states=self.button_states,
            button_command=self.set_variant,
            clear_command=self.clear_scenario_a,
            action_command=lambda: self.start_beam_selection("A")
        )
        self.scenario_a.frame.grid(row=0, column=0, padx=20, pady=10, sticky="n")

        # Scenariul B - Suprastructura
        self.scenario_b = ScenarioFrame(
            parent=frame_scenarios,
            scenario_name="Suprastructura",
            scenario_id="B",
            button_states=self.button_states,
            button_command=self.set_variant,
            clear_command=self.clear_scenario_b,
            action_command=lambda: self.start_beam_selection("B")
        )
        self.scenario_b.frame.grid(row=0, column=1, padx=20, pady=10, sticky="n")

        # Umple listbox-uri cu combinații
        self.fill_listbox(self.scenario_a.list_upper)
        self.fill_listbox(self.scenario_a.list_lower)
        self.fill_listbox(self.scenario_b.list_upper)
        self.fill_listbox(self.scenario_b.list_lower)

        # ==================== BUTOANE CONTROL ====================
        self.control_buttons = ControlButtons(
            parent=container,
            check_command=self.check_selection,
            clear_command=self.unselect_all
        )
        self.control_buttons.pack(pady=5)

        # ==================== SELECȚIE FIȘIERE ====================
        self.file_frame = FileSelectionFrame(
            parent=container,
            browse_default_command=self.browse_default_file,
            browse_result_command=self.browse_result_folder
        )
        self.file_frame.pack(pady=10, fill=tk.X, padx=20)

        # ==================== FRAME BUTOANE JOS ====================
        # Creează un frame pentru butoanele de jos să fie aliniate
        bottom_frame = ttk.Frame(container)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=20)

        # Butonul Create Excel
        ttk.Button(bottom_frame, text="Create Excel", command=self.create_excel, width=40).pack(
            side=tk.LEFT, ipadx=20, ipady=10
        )

        # Butonul Close
        ttk.Button(bottom_frame, text="Close", command=self.close_application, width=10).pack(
            side=tk.RIGHT, ipadx=10, ipady=5
        )

    def create_excel(self):
        """Creează baza de date temporara, apoi populeaza un fisier excel nou cu inforamtii detaileate despre
        frameurile selectate"""

        # Verifică folderul de rezultate
        result_folder = self.file_frame.result_folder_var.get()
        if not result_folder:
            messagebox.showerror("⮽⮽ Eroare", "Selectează un folder de rezultate!")
            return

        # Verifică dacă folderul există
        if not os.path.exists(result_folder):
            messagebox.showerror("⮽⮽ Eroare", f"Folderul de rezultate nu există: {result_folder}")
            return

        # Verifică fișierul template
        default_file = self.file_frame.default_file_var.get()
        if not default_file:
            messagebox.showerror("⮽⮽ Eroare", "Selectează un fișier template!")
            return

        # Verifică dacă fișierul template există
        if not os.path.exists(default_file):
            messagebox.showerror("⮽⮽ Eroare", f"Fișierul template nu există: {default_file}")
            return

        try:
            # Creează nume de fișier cu timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Obține numele modelului ETABS
            try:
                model_name = sap_model.GetModelFilename()
                # Extrage doar numele fișierului fără cale
                model_basename = os.path.basename(model_name)
                model_basename = model_basename.replace('.edb', '')
            except Exception as e:
                print(f"⮽⮽ Eroare la obținerea numelui modelului: {e}")
                model_basename = "ETABS_Model"

            excel_filename = f"{model_basename} - grinzi ({timestamp}).xlsx"
            excel_path = os.path.join(result_folder, excel_filename)

            # Creează nume pentru baza de date cu același timestamp
            db_filename = f"{model_basename} - grinzi DB - ({timestamp}).db"
            db_path = os.path.join(result_folder, db_filename)

            print(f"-- Folder rezultate: {result_folder}")
            print(f"-- Cale Excel finală: {excel_path}")
            print(f"-- Cale DB finală: {db_path}")

            # Pas 1: Creează baza de date LOCALĂ cu toate grinzile selectate
            print("-- Creare bază de date locală cu grinzile selectate")
            all_beams = []
            for group in self.all_beam_groups_a:
                all_beams.extend(group)
            for group in self.all_beam_groups_b:
                all_beams.extend(group)

            if not all_beams:
                messagebox.showerror("⮽⮽ Eroare", "Nu sunt grinzi selectate pentru a crea baza de date!")
                return

            # Creează baza de date locală
            success = create_database(all_beams)
            if not success:
                messagebox.showerror("⮽⮽ Eroare", "Nu s-a putut crea baza de date locală!")
                return

            print("✓✓ Bază de date locală creată cu succes!")

            # Pas 2: Copy the template file to new location with preserved formatting
            print("-- Copiere fișier template la locația nouă (cu păstrarea formatărilor)")
            try:
                from excel.operations import copy_excel_file_with_column_widths
                copy_success = copy_excel_file_with_column_widths(default_file, excel_path)
                if not copy_success:
                    messagebox.showerror("⮽⮽ Eroare", "Nu s-a putut copia fișierul template!")
                    return
            except ImportError:
                # Fallback to original method if new function is not available
                from excel.operations import copy_excel_file
                copy_success = copy_excel_file(default_file, excel_path)
                if not copy_success:
                    messagebox.showerror("⮽⮽ Eroare", "Nu s-a putut copia fișierul template!")
                    return

            # Pas 3: Create Excel with structured layout (THIS WILL POPULATE ExcelColumn, ExcelRow, SheetName)
            print("-- Creare schelet Excel cu datele grinzilor")
            try:
                # Use the new structured layout
                from excel.operations import create_structured_excel_layout
                excel_success = create_structured_excel_layout(
                    excel_path=excel_path,
                    template_excel_path=default_file,  # Use the default file as template
                    db_path="frames.db"
                )
                if not excel_success:
                    messagebox.showerror("⮽⮽ Eroare", "Nu s-a putut crea structura Excel!")
                    return
            except Exception as e:
                print(f"⮽⮽ Eroare la crearea Excel-ului structurat: {e}")
                messagebox.showerror("⮽⮽ Eroare", f"Eroare la crearea Excel-ului: {e}")
                return

            # PAS NOU: Creează backup-ul bazei de date DUPĂ ce Excel-ul a fost creat
            # Acum baza de date conține și informațiile despre pozițiile Excel
            print("-- Creare backup baza de date (după popularea pozițiilor Excel)...")
            backup_success = self.backup_database_before_excel_creation(excel_path, "frames.db")
            if backup_success:
                print("✓✓ Backup baza de date creat cu succes (cu pozițiile Excel populate)")
            else:
                print("⮽⮽ Backup baza de date eșuat")

            # Afișează mesaj de succes
            print(f"✓✓ Proces completat cu succes!")
            messagebox.showinfo("✓✓ Succes",
                                f"Proces completat cu succes!\n\n"
                                f"Fișier Excel creat:\n{excel_path}\n\n"
                                f"Bază de date creată:\n{db_path}\n\n"
                                f"Backup baza de date cu pozițiile Excel a fost salvat în același folder.")

        except Exception as e:
            print(f"⮽⮽ Eroare la crearea Excel-ului: {e}")
            messagebox.showerror("Eroare", f"Eroare: {e}")

    def close_application(self):
        """Închide aplicația și șterge doar fișierele temporare locale, NU și backup-urile"""
        print("-- Închidere aplicația...")

        # Șterge fișierul temporar JSON
        if os.path.exists("beam_selection_temp.json"):
            try:
                os.remove("beam_selection_temp.json")
                print("-- Fișier temporar JSON șters")
            except Exception as e:
                print(f"⮽⮽ Nu am putut șterge fișierul temporar JSON: {e}")

        # Șterge doar baza de date locală (frames.db), NU și backup-urile
        if os.path.exists("frames.db"):
            try:
                os.remove("frames.db")
                print("✓✓ Baza de date locală ștearsă (frames.db)")
            except Exception as e:
                print(f"⮽⮽ Nu am putut șterge baza de date locală: {e}")

        # Oprește tracking
        if hasattr(self, 'beam_selection_active') and self.beam_selection_active:
            self.stop_beam_selection()

        print("-- Aplicația se închide...")
        print("-- NOTĂ: Backup-urile bazei de date au fost păstrate în folderul cu fișierul Excel")
        self.root.destroy()

    def unselect_all(self):
        """Șterge TOATE datele inclusiv baza de date locală, dar NU și backup-urile"""
        print("Ștergere selctii inclusiv baza de date locală")

        # Șterge grupurile de grinzi
        self.all_beam_groups_a = []
        self.all_beam_groups_b = []
        self.current_beam_group = []

        # Șterge fișierul temporar
        if os.path.exists("beam_selection_temp.json"):
            os.remove("beam_selection_temp.json")
            print("-- Fișier temporar șters")

        # Șterge doar fișierul bazei de date locale (frames.db), NU și backup-urile
        if os.path.exists("frames.db"):
            os.remove("frames.db")
            print("-- Baza de date locală ștearsă (frames.db)")

        # Șterge selecțiile GUI
        self.clear_scenario_a()
        self.clear_scenario_b()

        # Resetează starea butoanelor
        for key in list(self.button_states.keys()):
            self.button_states[key] = False

        # Resetează alte stări
        self.rezistente_var.set("Normale")
        self.top_radio_state = "Normale"
        self.story_var.set("")
        self.etaj_value = None
        self.selected_combinations = {
            "A_upper": [], "A_lower": [], "B_upper": [], "B_lower": []
        }

        # Șterge selecția ETABS
        etabs_api.operations.clear_frame_selection()

        # Actualizează butoanele
        self.update_scenario_buttons("A")
        self.update_scenario_buttons("B")

        print("✓✓ Toate datele au fost șterse. Gata pentru selecție nouă.")
        print("-- NOTĂ: Backup-urile bazei de date au fost păstrate")

    def check_selection(self):
        """Afișează sumarul tuturor grinzilor selectate"""
        print("-- Verificare date grinzi...")
        summary_data = self.get_detailed_summary_data()
        if summary_data and summary_data.get("scenarios"):
            SimpleSummaryPopup(self.root, summary_data)
        else:
            print("⮽⮽ Nu am date de grinzi pentru verificare")

    def start_beam_selection(self, scenario):
        """Începe procesul de selectare a grinzilor pentru scenariul dat"""
        if self.beam_selection_active:
            print("-- Selectarea grinzilor este deja activă! Opriți mai întâi selecția curentă.")
            return

        # CAPTURE CURRENT STATE AT THE MOMENT OF STARTING SELECTION
        current_state = self.get_current_state_at_selection_start()

        # Ensure etaj_value is not None, use a default if needed
        if self.etaj_value is None:
            print("-- Avertisment: Niciun etaj selectat, se va folosi 'Unknown'")
            self.etaj_value = "Unknown"

        self.current_scenario = scenario
        self.beam_selection_active = True
        self.current_beam_group = []  # RESET current beam group for new selection

        # STORE THE CAPTURED STATE FOR THIS SELECTION SESSION
        self.current_selection_state = current_state

        # Rest of the method remains the same...
        # Șterge orice selecție anterioară în ETABS
        etabs_api.operations.clear_frame_selection()

        print(f"-- Început selecție grinzi pentru {scenario}")
        print(f"-- Stare butoane la începutul selecției: {current_state['button_states']}")
        print("-- Te rog selectează grinzi în ETABS...")

        # Afișează dialogul de confirmare
        self.show_selection_confirmation(scenario, is_first_group=True)

        # Începe urmărirea selecțiilor de grinzi în background
        self.start_tracking()

    def start_tracking(self):
        """Începe urmărirea selecțiilor de grinzi"""
        if self.beam_selection_active:
            self.track_beam_selections()

    # def track_beam_selections(self):
    #     """Urmărește selecțiile de grinzi în ETABS în timp real"""
    #     if not self.beam_selection_active:
    #         return
    #
    #     try:
    #         # Obține frame-urile selectate din ETABS
    #         selected_frames = etabs_api.operations.get_selected_frames_live()
    #
    #         # Actualizează grupul curent cu toate frame-urile selectate
    #         self.current_beam_group = selected_frames.copy()
    #
    #         if selected_frames:
    #             print(f"-- Grinzi selectate curent ({len(selected_frames)}): {selected_frames}")
    #
    #         # Continuă urmărirea
    #         self.tracking_id = self.root.after(500, self.track_beam_selections)
    #
    #     except Exception as e:
    #         print(f"⮽⮽ Eroare la urmărirea grinzilor: {e}")
    #         self.tracking_id = self.root.after(500, self.track_beam_selections)
    def track_beam_selections(self):
        """Urmărește selecțiile de grinzi în ETABS în timp real"""
        if not self.beam_selection_active:
            return

        try:
            # Obține frame-urile selectate din ETABS
            selected_frames = etabs_api.operations.get_selected_frames_live()

            # Verifică dacă selecția s-a schimbat față de ultima apelare
            if set(selected_frames) != set(self.current_beam_group):
                # Actualizează grupul curent doar dacă s-a schimbat
                self.current_beam_group = selected_frames.copy()

                if selected_frames:
                    print(f"-- Grinzi selectate curent ({len(selected_frames)}): {selected_frames}")
                else:
                    print("-- Nicio grindă selectată")

            # Continuă urmărirea
            self.tracking_id = self.root.after(500, self.track_beam_selections)

        except Exception as e:
            print(f"⮽⮽ Eroare la urmărirea grinzilor: {e}")
            self.tracking_id = self.root.after(500, self.track_beam_selections)

    def stop_tracking(self):
        """Oprește urmărirea selecției grinzilor"""
        if self.tracking_id:
            self.root.after_cancel(self.tracking_id)
            self.tracking_id = None

    def stop_beam_selection(self):
        """Oprește complet procesul de selectare a grinzilor"""
        self.beam_selection_active = False
        self.stop_tracking()
        print("-- Selectarea grinzilor oprită")

    def show_selection_confirmation(self, scenario, is_first_group=False):
        """Afișează dialogul de confirmare pentru selecția grinzilor"""
        scenario_name = "Infrastructura" if scenario == "A" else "Suprastructura"

        self.confirmation_dialog = SelectionConfirmationDialog(
            parent=self.root,
            scenario_name=scenario_name,
            confirm_continue_callback=self.handle_confirm_continue,
            confirm_stop_callback=self.handle_confirm_stop,
            cancel_callback=self.handle_cancel,
            is_first_group=is_first_group
        )

    def handle_confirm_continue(self):
        """Gestionează apăsarea butonului 'Confirmă și continuă'"""
        print("Confirmă și continuă")
        if self.confirm_and_continue():
            if self.confirmation_dialog:
                group_count = len(self.all_beam_groups_a if self.current_scenario == "A" else self.all_beam_groups_b)
                self.confirmation_dialog.update_message(
                    f"-- Grupul {group_count} confirmat!\n"
                    f"-- Selectează următorul grup de grinzi în ETABS..."
                )
        else:
            if self.confirmation_dialog:
                self.confirmation_dialog.update_message(
                    "⮽⮽ EROARE: Nici o grindă selectată!\n"
                    "Selectează grinzi în ETABS înainte de confirmare."
                )

    def handle_confirm_stop(self):
        """Gestionează apăsarea butonului 'Confirmă și oprește'"""
        print("Confirmă și oprește")
        if self.confirm_and_stop():
            if self.confirmation_dialog:
                self.confirmation_dialog.close_dialog()

    def handle_cancel(self):
        """Gestionează apăsarea butonului 'Anulează'"""
        print("Anulează")
        if self.cancel_selection():
            if self.confirmation_dialog:
                self.confirmation_dialog.close_dialog()

    def confirm_and_continue(self):
        """Confirmă grupul curent și continuă cu următorul grup"""
        if self.current_beam_group:
            # Folosește starea capturată LA ÎNCEPUTUL SELECȚIEI
            if hasattr(self, 'current_selection_state'):
                selection_state = self.current_selection_state
            else:
                # Fallback: capture current state
                selection_state = self.get_current_state_at_selection_start()

            # Salvează grupul curent în scenariul corespunzător
            if self.current_scenario == "A":
                self.all_beam_groups_a.append(self.current_beam_group.copy())
                current_groups = self.all_beam_groups_a
            else:
                self.all_beam_groups_b.append(self.current_beam_group.copy())
                current_groups = self.all_beam_groups_b

            print(
                f"-- Grupul {len(current_groups)} confirmat pentru scenariul {self.current_scenario}: {len(self.current_beam_group)} grinzi")
            print(f"-- Grinzi în grup: {self.current_beam_group}")

            # Salvează în fișier temporar CU STARE CAPTURATĂ LA ÎNCEPUT
            self.save_temp_data_with_selection_state(self.current_scenario, current_groups, selection_state)

            # # Ascunde grinzile
            # success = etabs_api.operations.hide_specific_frames(self.current_beam_group)
            # if success:
            #     print("-- Grinzi ascunse cu succes în ETABS")
            # else:
            #     print("⮽⮽ Metoda de ascundere a eșuat")
            #
            # # Șterge selecția pentru următorul grup
            # etabs_api.operations.clear_frame_selection()
            self.current_beam_group = []

            print("-- Gata pentru selecția următorului grup de grinzi...")
            return True
        else:
            print("-- Nu sunt grinzi selectate în grupul curent!")
            return False

    def confirm_and_stop(self):
        """Confirmă grupul curent și oprește selecția"""
        if self.current_beam_group:
            # Folosește starea capturată LA ÎNCEPUTUL SELECȚIEI
            if hasattr(self, 'current_selection_state'):
                selection_state = self.current_selection_state
            else:
                # Fallback: capture current state
                selection_state = self.get_current_state_at_selection_start()

            # Salvează grupul curent
            if self.current_scenario == "A":
                self.all_beam_groups_a.append(self.current_beam_group.copy())
                current_groups = self.all_beam_groups_a
            else:
                self.all_beam_groups_b.append(self.current_beam_group.copy())
                current_groups = self.all_beam_groups_b

            print(
                f"-- Grupul final confirmat pentru scenariul {self.current_scenario}: {len(self.current_beam_group)} grinzi")
            print(f"-- Grinzi în grup final: {self.current_beam_group}")

            # Salvează în fișier temporar CU STARE CAPTURATĂ LA ÎNCEPUT
            self.save_temp_data_with_selection_state(self.current_scenario, current_groups, selection_state)

            # # Ascunde grinzile
            # etabs_api.operations.hide_specific_frames(self.current_beam_group)

        # Șterge selecția și oprește
        etabs_api.operations.clear_frame_selection()
        self.stop_beam_selection()

        # Clean up the stored selection state
        if hasattr(self, 'current_selection_state'):
            del self.current_selection_state

        return True

    def cancel_selection(self):
        """Anulează selecția curentă fără salvare"""
        print("-- Selecție anulată")

        # Șterge selecția în ETABS
        etabs_api.operations.clear_frame_selection()
        self.current_beam_group = []
        self.stop_beam_selection()

        # Clean up the stored selection state
        if hasattr(self, 'current_selection_state'):
            del self.current_selection_state

        return True

    def fill_listbox(self, listbox):
        """Umple listbox-ul dat cu combinații de proiectare"""
        for i in etabs_api.operations.get_comb_names():
            listbox.insert(tk.END, f"{i}")

    def set_variant(self, scenario, variant):
        """Gestionează apăsarea butoanelor de variantă"""
        scenario_obj = self.scenario_a if scenario == "A" else self.scenario_b
        buttons = scenario_obj.variant_buttons
        states = self.button_states

        if variant in ["DCL", "DCM", "DCH"]:
            # Apăsarea DCL/DCM/DCH
            for v in ["DCL", "DCM", "DCH"]:
                pressed = (v == variant)
                buttons[v].config(relief="sunken" if pressed else "raised",
                                  background="lightblue" if pressed else "SystemButtonFace")
                states[(scenario, v)] = pressed
            # Deselectează Secundare automat
            buttons["Secundare"].config(relief="raised", background="SystemButtonFace")
            states[(scenario, "Secundare")] = False

        elif variant == "Secundare":
            # Secundare șterge DCL/DCM/DCH și Dir X/Y
            for v in ["DCL", "DCM", "DCH", "Secundare"]:
                pressed = (v == "Secundare")
                buttons[v].config(relief="sunken" if pressed else "raised",
                                  background="lightblue" if pressed else "SystemButtonFace")
                states[(scenario, v)] = pressed
            # Șterge butoanele Dir
            for dir_btn in ["Dir X", "Dir Y"]:
                buttons[dir_btn].config(relief="raised", background="SystemButtonFace")
                states[(scenario, dir_btn)] = False

        else:  # Dir X / Dir Y
            other = "Dir X" if variant == "Dir Y" else "Dir Y"
            if states[(scenario, "Secundare")]:
                # Șterge butoanele Dir dacă Secundare este activ
                for dir_btn in ["Dir X", "Dir Y"]:
                    buttons[dir_btn].config(relief="raised", background="SystemButtonFace")
                    states[(scenario, dir_btn)] = False
            else:
                # Comută butonul curent, asigură-te că doar un buton Dir este apăsat
                buttons[variant].config(relief="sunken", background="lightgreen")
                buttons[other].config(relief="raised", background="SystemButtonFace")
                states[(scenario, variant)] = True
                states[(scenario, other)] = False

    def update_top_radio_state(self):
        """Actualizează starea radio butoanelor de sus"""
        self.top_radio_state = self.rezistente_var.get()

    def update_etaj_value(self, event=None):
        """Actualizează valoarea etajului când se schimbă dropdown-ul"""
        self.etaj_value = self.story_var.get()
        print(f"-- Etaj selectat: {self.etaj_value}")

    def update_selected_combinations(self):
        """Actualizează combinațiile selectate din listbox-uri"""
        self.selected_combinations["A_upper"] = [self.scenario_a.list_upper.get(i) for i in
                                                 self.scenario_a.list_upper.curselection()]
        self.selected_combinations["A_lower"] = [self.scenario_a.list_lower.get(i) for i in
                                                 self.scenario_a.list_lower.curselection()]
        self.selected_combinations["B_upper"] = [self.scenario_b.list_upper.get(i) for i in
                                                 self.scenario_b.list_upper.curselection()]
        self.selected_combinations["B_lower"] = [self.scenario_b.list_lower.get(i) for i in
                                                 self.scenario_b.list_lower.curselection()]

    def get_current_state(self):
        """Returnează un snapshot complet al tuturor stărilor"""
        self.update_top_radio_state()
        self.update_selected_combinations()
        return {
            "button_states": self.button_states.copy(),
            "top_radio_state": self.top_radio_state,
            "selected_combinations": self.selected_combinations.copy(),
            "etaj": self.etaj_value,
            "beam_groups_a": self.all_beam_groups_a.copy(),
            "beam_groups_b": self.all_beam_groups_b.copy()
        }

    def clear_scenario_a(self):
        """Deselectează doar selecțiile scenariului A"""
        self.scenario_a.list_upper.selection_clear(0, tk.END)
        self.scenario_a.list_lower.selection_clear(0, tk.END)
        self.update_selected_combinations()

    def clear_scenario_b(self):
        """Deselectează doar selecțiile scenariului B"""
        self.scenario_b.list_upper.selection_clear(0, tk.END)
        self.scenario_b.list_lower.selection_clear(0, tk.END)
        self.update_selected_combinations()

    def update_scenario_buttons(self, scenario):
        """Actualizează aspectul butoanelor pentru un scenariu"""
        scenario_obj = self.scenario_a if scenario == "A" else self.scenario_b
        buttons = scenario_obj.variant_buttons

        for variant, btn in buttons.items():
            state = self.button_states.get((scenario, variant), False)
            if variant in ["DCL", "DCM", "DCH", "Secundare"]:
                btn.config(relief="sunken" if state else "raised",
                           background="lightblue" if state else "SystemButtonFace")
            else:  # Dir X / Dir Y
                btn.config(relief="sunken" if state else "raised",
                           background="lightgreen" if state else "SystemButtonFace")

    def browse_default_file(self):
        """Deschide dialogul pentru selectarea fișierului default"""
        filename = filedialog.askopenfilename(title="Selectează fișierul default",
                                              filetypes=[("Fișiere Excel", "*.xlsx"), ("Toate fișierele", "*.*")])
        if filename:
            self.file_frame.default_file_var.set(filename)

    def browse_result_folder(self):
        """Deschide dialogul pentru selectarea folderului de rezultate"""
        folder = filedialog.askdirectory(title="Selectează folderul de rezultate")
        if folder:
            self.file_frame.result_folder_var.set(folder)

    def save_temp_data(self, scenario, beam_groups):
        """Salvează datele temporare pentru un scenariu cu setările specifice fiecărui grup"""
        try:
            # Încarcă datele existente sau creează structură nouă
            if os.path.exists("beam_selection_temp.json"):
                with open("beam_selection_temp.json", 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {
                    "timestamp": datetime.now().isoformat(),
                    "scenario_a": {"beam_groups": []},
                    "scenario_b": {"beam_groups": []}
                }

            # Actualizează doar scenariul curent
            scenario_key = f"scenario_{scenario.lower()}"

            # Obține setările curente (la momentul selecției)
            current_settings = {
                "rezistente_type": self.top_radio_state,
                "etaj": self.etaj_value,
                "selected_combinations_upper": self.selected_combinations[f"{scenario}_upper"].copy(),
                "selected_combinations_lower": self.selected_combinations[f"{scenario}_lower"].copy(),
                "button_states": {k[1]: v for k, v in self.button_states.items() if k[0] == scenario}
            }

            # Pentru fiecare grup de grinzi, salvează și setările aferente
            detailed_beam_groups = []
            for i, beam_group in enumerate(beam_groups):
                detailed_group = {
                    "beams": beam_group,
                    "settings": current_settings.copy(),  # Salvează setările pentru acest grup
                    "group_number": i + 1,
                    "selection_timestamp": datetime.now().isoformat()
                }
                detailed_beam_groups.append(detailed_group)

            data[scenario_key] = {
                "beam_groups": detailed_beam_groups,
                "last_updated": datetime.now().isoformat()
            }

            with open("beam_selection_temp.json", 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"-- Date salvate pentru scenariul {scenario} cu {len(detailed_beam_groups)} grupuri")

        except Exception as e:
            print(f"⮽⮽ Eroare la salvarea datelor temporare: {e}")

    def get_detailed_summary_data(self):
        """Returnează datele detaliate pentru verificare - folosește setările din JSON"""
        try:
            # Încarcă datele din fișierul temporar pentru a obține setările corecte per grup
            if os.path.exists("beam_selection_temp.json"):
                with open("beam_selection_temp.json", 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
            else:
                json_data = {}

            summary = {
                "timestamp": datetime.now().isoformat(),
                "scenarios": {}
            }

            # Procesează scenariul A din JSON
            if "scenario_a" in json_data:
                scenario_a_data = json_data["scenario_a"]
                beam_groups_a = scenario_a_data.get("beam_groups", [])

                summary["scenarios"]["Infrastructura"] = {
                    "group_count": len(beam_groups_a),
                    "total_beams": sum(len(group.get("beams", [])) for group in beam_groups_a),
                    "beam_groups": []
                }

                for group_idx, group_data in enumerate(beam_groups_a, 1):
                    group_settings = group_data.get("settings", {})
                    beams_in_group = group_data.get("beams", [])

                    group_info = {
                        "group_number": group_idx,
                        "settings": group_settings,
                        "beams": []
                    }

                    for beam_name in beams_in_group:
                        beam_info = self.get_beam_info(beam_name)
                        group_info["beams"].append(beam_info)

                    summary["scenarios"]["Infrastructura"]["beam_groups"].append(group_info)

            # Procesează scenariul B din JSON
            if "scenario_b" in json_data:
                scenario_b_data = json_data["scenario_b"]
                beam_groups_b = scenario_b_data.get("beam_groups", [])

                summary["scenarios"]["Suprastructura"] = {
                    "group_count": len(beam_groups_b),
                    "total_beams": sum(len(group.get("beams", [])) for group in beam_groups_b),
                    "beam_groups": []
                }

                for group_idx, group_data in enumerate(beam_groups_b, 1):
                    group_settings = group_data.get("settings", {})
                    beams_in_group = group_data.get("beams", [])

                    group_info = {
                        "group_number": group_idx,
                        "settings": group_settings,
                        "beams": []
                    }

                    for beam_name in beams_in_group:
                        beam_info = self.get_beam_info(beam_name)
                        group_info["beams"].append(beam_info)

                    summary["scenarios"]["Suprastructura"]["beam_groups"].append(group_info)

            return summary

        except Exception as e:
            print(f"⮽⮽ Eroare la obținerea datelor sumar din JSON: {e}")
            # Fallback to empty summary if JSON reading fails
            return {
                "timestamp": datetime.now().isoformat(),
                "scenarios": {}
            }

        except Exception as e:
            print(f"⮽⮽ Eroare la obținerea datelor sumar: {e}")
            # Fallback to old method if there's an error
            return self._get_detailed_summary_data_fallback()

    # def get_detailed_summary_data(self):
    #     """Returnează datele detaliate pentru verificare - folosește setările din JSON"""
    #     try:
    #         # Încarcă datele din fișierul temporar pentru a obține setările corecte per grup
    #         if os.path.exists("beam_selection_temp.json"):
    #             with open("beam_selection_temp.json", 'r', encoding='utf-8') as f:
    #                 json_data = json.load(f)
    #         else:
    #             json_data = {}
    #
    #         summary = {
    #             "timestamp": datetime.now().isoformat(),
    #             "scenarios": {}
    #         }
    #
    #         # Procesează scenariul A din JSON
    #         if "scenario_a" in json_data:
    #             scenario_a_data = json_data["scenario_a"]
    #             beam_groups_a = scenario_a_data.get("beam_groups", [])
    #
    #             summary["scenarios"]["Infrastructura"] = {
    #                 "group_count": len(beam_groups_a),
    #                 "total_beams": sum(len(group.get("beams", [])) for group in beam_groups_a),
    #                 "beam_groups": []
    #             }
    #
    #             for group_idx, group_data in enumerate(beam_groups_a, 1):
    #                 group_settings = group_data.get("settings", {})
    #                 beams_in_group = group_data.get("beams", [])
    #
    #                 group_info = {
    #                     "group_number": group_idx,
    #                     "settings": group_settings,
    #                     "beams": []
    #                 }
    #
    #                 for beam_name in beams_in_group:
    #                     beam_info = self.get_beam_info(beam_name)
    #                     group_info["beams"].append(beam_info)
    #
    #                 summary["scenarios"]["Infrastructura"]["beam_groups"].append(group_info)
    #
    #         # Procesează scenariul B din JSON
    #         if "scenario_b" in json_data:
    #             scenario_b_data = json_data["scenario_b"]
    #             beam_groups_b = scenario_b_data.get("beam_groups", [])
    #
    #             summary["scenarios"]["Suprastructura"] = {
    #                 "group_count": len(beam_groups_b),
    #                 "total_beams": sum(len(group.get("beams", [])) for group in beam_groups_b),
    #                 "beam_groups": []
    #             }
    #
    #             for group_idx, group_data in enumerate(beam_groups_b, 1):
    #                 group_settings = group_data.get("settings", {})
    #                 beams_in_group = group_data.get("beams", [])
    #
    #                 group_info = {
    #                     "group_number": group_idx,
    #                     "settings": group_settings,
    #                     "beams": []
    #                 }
    #
    #                 for beam_name in beams_in_group:
    #                     beam_info = self.get_beam_info(beam_name)
    #                     group_info["beams"].append(beam_info)
    #
    #                 summary["scenarios"]["Suprastructura"]["beam_groups"].append(group_info)
    #
    #         return summary
    #
    #     except Exception as e:
    #         print(f"⮽⮽ Eroare la obținerea datelor sumar din JSON: {e}")
    #         # Fallback to the original method if JSON reading fails
    #         return self.get_detailed_summary_data_original()

    def get_detailed_summary_data_original(self):
        """Versiunea originală a metodei de sumar (ca fallback)"""
        summary = {
            "timestamp": datetime.now().isoformat(),
            "scenarios": {}
        }

        # Procesează scenariul A
        if self.all_beam_groups_a:
            summary["scenarios"]["Infrastructura"] = {
                "group_count": len(self.all_beam_groups_a),
                "total_beams": sum(len(group) for group in self.all_beam_groups_a),
                "beam_groups": [],
                "settings": {
                    "rezistente_type": self.top_radio_state,
                    "etaj": self.etaj_value,
                    "combinations_upper": self.selected_combinations["A_upper"],
                    "combinations_lower": self.selected_combinations["A_lower"],
                    "button_states": {k[1]: v for k, v in self.button_states.items() if k[0] == "A"}
                }
            }

            for group_idx, group in enumerate(self.all_beam_groups_a, 1):
                group_info = {
                    "group_number": group_idx,
                    "beams": []
                }
                for beam_name in group:
                    beam_info = self.get_beam_info(beam_name)
                    group_info["beams"].append(beam_info)
                summary["scenarios"]["Infrastructura"]["beam_groups"].append(group_info)

        # Procesează scenariul B
        if self.all_beam_groups_b:
            summary["scenarios"]["Suprastructura"] = {
                "group_count": len(self.all_beam_groups_b),
                "total_beams": sum(len(group) for group in self.all_beam_groups_b),
                "beam_groups": [],
                "settings": {
                    "rezistente_type": self.top_radio_state,
                    "etaj": self.etaj_value,
                    "combinations_upper": self.selected_combinations["B_upper"],
                    "combinations_lower": self.selected_combinations["B_lower"],
                    "button_states": {k[1]: v for k, v in self.button_states.items() if k[0] == "B"}
                }
            }

            for group_idx, group in enumerate(self.all_beam_groups_b, 1):
                group_info = {
                    "group_number": group_idx,
                    "beams": []
                }
                for beam_name in group:
                    beam_info = self.get_beam_info(beam_name)
                    group_info["beams"].append(beam_info)
                summary["scenarios"]["Suprastructura"]["beam_groups"].append(group_info)

        return summary

    def _get_global_settings_from_groups(self, beam_groups, scenario):
        """Extrage setări globale din grupurile existente pentru compatibilitate"""
        if not beam_groups:
            return {
                "rezistente_type": "N/A",
                "etaj": "N/A",
                "combinations_upper": [],
                "combinations_lower": [],
                "button_states": {}
            }

        # Folosește setările din primul grup ca setări globale
        first_group_settings = beam_groups[0].get("settings", {})

        return {
            "rezistente_type": first_group_settings.get("rezistente_type", "N/A"),
            "etaj": first_group_settings.get("etaj", "N/A"),
            "combinations_upper": first_group_settings.get("selected_combinations_upper", []),
            "combinations_lower": first_group_settings.get("selected_combinations_lower", []),
            "button_states": first_group_settings.get("button_states", {})
        }

    def get_beam_info(self, beam_name):
        """Extrage informații despre o grindă din ETABS pentru popup"""
        try:
            print(f"-- Obținere informații pentru grindă: {beam_name}")

            label, story = etabs_api.operations.get_label_and_story(beam_name)
            section_name = etabs_api.operations.get_section_name(beam_name)
            material = etabs_api.operations.get_section_material(beam_name)
            length = etabs_api.operations.get_frame_length(beam_name)

            beam_info = {
                "unique_name": beam_name,
                "label": label if label else "N/A",
                "story": story if story else "N/A",
                "section_name": section_name if section_name else "N/A",
                "material": material if material else "N/A",
                "length": length if length else 0.0
            }

            print(f"-- Informații obținute pentru {beam_name}:")
            print(f"   Label: {beam_info['label']}")
            print(f"   Story: {beam_info['story']}")
            print(f"   Section: {beam_info['section_name']}")
            print(f"   Material: {beam_info['material']}")
            print(f"   Length: {beam_info['length']:.3f}")

            return beam_info

        except Exception as e:
            print(f"⮽⮽ Eroare critică la obținerea informațiilor pentru {beam_name}: {e}")
            return {
                "unique_name": beam_name,
                "label": "N/A",
                "story": "N/A",
                "section_name": "N/A",
                "material": "N/A",
                "length": 0.0
            }

    def get_current_state_at_confirmation(self):
        """Capturează starea curentă la momentul confirmării selecției"""
        self.update_top_radio_state()
        self.update_selected_combinations()

        return {
            "button_states": self.button_states.copy(),
            "top_radio_state": self.top_radio_state,
            "selected_combinations": self.selected_combinations.copy(),
            "etaj": self.etaj_value
        }

    def save_temp_data_with_current_state(self, scenario, beam_groups, current_state):
        """Salvează datele temporare cu starea capturată la momentul selecției"""
        try:
            # Încarcă datele existente sau creează structură nouă
            if os.path.exists("beam_selection_temp.json"):
                with open("beam_selection_temp.json", 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {
                    "timestamp": datetime.now().isoformat(),
                    "scenario_a": {"beam_groups": []},
                    "scenario_b": {"beam_groups": []}
                }

            # Actualizează doar scenariul curent
            scenario_key = f"scenario_{scenario.lower()}"

            # Reconstruim lista de grupuri cu setările corespunzătoare
            detailed_beam_groups = []

            # Pentru grupurile existente, păstrăm setările originale
            if scenario_key in data and "beam_groups" in data[scenario_key]:
                existing_groups = data[scenario_key]["beam_groups"]
                detailed_beam_groups.extend(existing_groups)

            # Adaugă noul grup CU SETĂRILE CAPTURATE
            new_group = {
                "beams": beam_groups[-1] if beam_groups else [],  # Ultimul grup adăugat
                "settings": {
                    "rezistente_type": current_state["top_radio_state"],
                    "etaj": current_state["etaj"],
                    "selected_combinations_upper": current_state["selected_combinations"][f"{scenario}_upper"],
                    "selected_combinations_lower": current_state["selected_combinations"][f"{scenario}_lower"],
                    "button_states": {k[1]: v for k, v in current_state["button_states"].items() if k[0] == scenario}
                },
                "group_number": len(detailed_beam_groups) + 1,
                "selection_timestamp": datetime.now().isoformat()
            }
            detailed_beam_groups.append(new_group)

            data[scenario_key] = {
                "beam_groups": detailed_beam_groups,
                "last_updated": datetime.now().isoformat()
            }

            with open("beam_selection_temp.json", 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"-- Date salvate pentru scenariul {scenario} cu {len(detailed_beam_groups)} grupuri")

        except Exception as e:
            print(f"⮽⮽ Eroare la salvarea datelor temporare: {e}")

    def get_current_state_at_selection_start(self):
        """Capturează starea curentă la momentul începerii selecției"""
        self.update_top_radio_state()
        self.update_selected_combinations()

        return {
            "button_states": self.button_states.copy(),
            "top_radio_state": self.top_radio_state,
            "selected_combinations": self.selected_combinations.copy(),
            "etaj": self.etaj_value,
            "selection_start_time": datetime.now().isoformat()
        }

    def save_temp_data_with_selection_state(self, scenario, beam_groups, selection_state):
        """Salvează datele temporare cu starea capturată la începutul selecției"""
        try:
            # Încarcă datele existente sau creează structură nouă
            if os.path.exists("beam_selection_temp.json"):
                with open("beam_selection_temp.json", 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {
                    "timestamp": datetime.now().isoformat(),
                    "scenario_a": {"beam_groups": []},
                    "scenario_b": {"beam_groups": []}
                }

            # Actualizează doar scenariul curent
            scenario_key = f"scenario_{scenario.lower()}"

            # Reconstruim lista de grupuri cu setările corespunzătoare
            detailed_beam_groups = []

            # Pentru grupurile existente, păstrăm setările originale
            if scenario_key in data and "beam_groups" in data[scenario_key]:
                existing_groups = data[scenario_key]["beam_groups"]
                detailed_beam_groups.extend(existing_groups)

            # Adaugă toate grupurile curente CU SETĂRILE CAPTURATE LA ÎNCEPUTUL SELECȚIEI
            # Ultimul grup este cel tocmai adăugat
            if beam_groups:  # Dacă există grupurile
                # Obține doar grupurile noi care nu sunt deja în detailed_beam_groups
                existing_group_count = len(detailed_beam_groups)
                new_groups_count = len(beam_groups) - existing_group_count

                if new_groups_count > 0:
                    # Adaugă noile grupuri
                    for i in range(new_groups_count):
                        group_index = existing_group_count + i
                        if group_index < len(beam_groups):
                            new_group = {
                                "beams": beam_groups[group_index],
                                "settings": {
                                    "rezistente_type": selection_state["top_radio_state"],
                                    "etaj": selection_state["etaj"],
                                    "selected_combinations_upper": selection_state["selected_combinations"][
                                        f"{scenario}_upper"],
                                    "selected_combinations_lower": selection_state["selected_combinations"][
                                        f"{scenario}_lower"],
                                    "button_states": {k[1]: v for k, v in selection_state["button_states"].items() if
                                                      k[0] == scenario}
                                },
                                "group_number": len(detailed_beam_groups) + 1,
                                "selection_start_time": selection_state["selection_start_time"],
                                "confirmation_time": datetime.now().isoformat()
                            }
                            detailed_beam_groups.append(new_group)

            data[scenario_key] = {
                "beam_groups": detailed_beam_groups,
                "last_updated": datetime.now().isoformat()
            }

            with open("beam_selection_temp.json", 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"-- Date salvate pentru scenariul {scenario} cu {len(detailed_beam_groups)} grupuri")
            print(f"-- Stare salvată: Rezistente={selection_state['top_radio_state']}, Etaj={selection_state['etaj']}")

        except Exception as e:
            print(f"⮽⮽ Eroare la salvarea datelor temporare: {e}")

    def run(self):
        """Rulează aplicația principală"""
        self.root.mainloop()

    # def get_current_state_at_selection_start(self):
    #     """Capturează starea curentă la momentul începerii selecției"""
    #     self.update_top_radio_state()
    #     self.update_selected_combinations()
    #
    #     return {
    #         "button_states": self.button_states.copy(),
    #         "top_radio_state": self.top_radio_state,
    #         "selected_combinations": self.selected_combinations.copy(),
    #         "etaj": self.etaj_value,
    #         "selection_start_time": datetime.now().isoformat()
    #     }

    # def save_temp_data_with_selection_state(self, scenario, beam_groups, selection_state):
    #     """Salvează datele temporare cu starea capturată la începutul selecției"""
    #     try:
    #         # Încarcă datele existente sau creează structură nouă
    #         if os.path.exists("beam_selection_temp.json"):
    #             with open("beam_selection_temp.json", 'r', encoding='utf-8') as f:
    #                 data = json.load(f)
    #         else:
    #             data = {
    #                 "timestamp": datetime.now().isoformat(),
    #                 "scenario_a": {"beam_groups": []},
    #                 "scenario_b": {"beam_groups": []}
    #             }
    #
    #         # Actualizează doar scenariul curent
    #         scenario_key = f"scenario_{scenario.lower()}"
    #
    #         # Reconstruim lista de grupuri cu setările corespunzătoare
    #         detailed_beam_groups = []
    #
    #         # Pentru grupurile existente, păstrăm setările originale
    #         if scenario_key in data and "beam_groups" in data[scenario_key]:
    #             existing_groups = data[scenario_key]["beam_groups"]
    #             detailed_beam_groups.extend(existing_groups)
    #
    #         # Adaugă noul grup CU SETĂRILE CAPTURATE LA ÎNCEPUTUL SELECȚIEI
    #         new_group = {
    #             "beams": beam_groups[-1] if beam_groups else [],  # Ultimul grup adăugat
    #             "settings": {
    #                 "rezistente_type": selection_state["top_radio_state"],
    #                 "etaj": selection_state["etaj"],
    #                 "selected_combinations_upper": selection_state["selected_combinations"][f"{scenario}_upper"],
    #                 "selected_combinations_lower": selection_state["selected_combinations"][f"{scenario}_lower"],
    #                 "button_states": {k[1]: v for k, v in selection_state["button_states"].items() if k[0] == scenario}
    #             },
    #             "group_number": len(detailed_beam_groups) + 1,
    #             "selection_start_time": selection_state["selection_start_time"],
    #             "confirmation_time": datetime.now().isoformat()
    #         }
    #         detailed_beam_groups.append(new_group)
    #
    #         data[scenario_key] = {
    #             "beam_groups": detailed_beam_groups,
    #             "last_updated": datetime.now().isoformat()
    #         }
    #
    #         with open("beam_selection_temp.json", 'w', encoding='utf-8') as f:
    #             json.dump(data, f, indent=2, ensure_ascii=False)
    #         print(f"-- Date salvate pentru scenariul {scenario} cu {len(detailed_beam_groups)} grupuri")
    #         print(f"-- Stare salvată: Rezistente={selection_state['top_radio_state']}, Etaj={selection_state['etaj']}")
    #
    #     except Exception as e:
    #         print(f"⮽⮽ Eroare la salvarea datelor temporare: {e}")

    def backup_database_before_excel_creation(self, excel_path, db_path="frames.db"):
        """
        Creates a backup copy of the database in the same folder as the Excel file
        before the local database is deleted.
        """
        try:
            print(f"-- Backup: Checking if database exists at {db_path}")
            if not os.path.exists(db_path):
                print(f"⮽⮽ Database file not found for backup: {db_path}")
                return False

            # Get the directory of the Excel file
            excel_dir = os.path.dirname(excel_path)
            if not excel_dir:
                excel_dir = os.getcwd()

            print(f"-- Backup: Excel directory is {excel_dir}")

            # Create backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"frames_backup_{timestamp}.db"
            backup_path = os.path.join(excel_dir, backup_filename)

            print(f"-- Backup: Creating backup at {backup_path}")

            # Copy the database file
            import shutil
            shutil.copy2(db_path, backup_path)

            # Verify the backup was created
            if os.path.exists(backup_path):
                backup_size = os.path.getsize(backup_path)
                print(f"✓✓ Database backup created successfully: {backup_path}")
                print(f"-- Backup file size: {backup_size} bytes")
                return True
            else:
                print(f"⮽⮽ Database backup failed - file not created")
                return False

        except Exception as e:
            print(f"⮽⮽ Error creating database backup: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    app = DesignApp()
    app.run()