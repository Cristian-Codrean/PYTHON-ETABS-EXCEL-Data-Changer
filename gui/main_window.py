import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sys
import os
import json
import sqlite3
from datetime import datetime

# ==================== IMPORTURI FIXATE ====================
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
    from excel.operations import copy_excel_file
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
        self.root.title("Design Comparison Tool")
        self.root.resizable(True, True)

        # Testează conexiunea ETABS făcând un apel API simplu
        print("-- Testare conexiune ETABS")
        try:
            from etabs_api.connection import get_sap_model
            sap_model = get_sap_model()

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
        """Creează baza de date locală, apoi copiază Excel și DB în folderul specificat"""

        # Verifică folderul de rezultate
        result_folder = self.file_frame.result_folder_var.get()
        if not result_folder:
            messagebox.showerror("⮽⮽ Eroare", "Selectează un folder de rezultate!")
            return

        # Verifică fișierul template
        default_file = self.file_frame.default_file_var.get()
        if not default_file:
            messagebox.showerror("⮽⮽ Eroare", "Selectează un fișier template!")
            return

        try:
            # Creează nume de fișier cu timestamp
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            excel_filename = f"beam_analysis_{timestamp}.xlsx"
            excel_path = os.path.join(result_folder, excel_filename)

            # Creează nume pentru baza de date cu același timestamp
            db_filename = f"beam_database_{timestamp}.db"
            db_path = os.path.join(result_folder, db_filename)

            print(f"-- Încep procesul de creare Excel și DB...")
            print(f"-- Template Excel: {default_file}")
            print(f"-- Destinație Excel: {excel_path}")
            print(f"-- Destinație DB: {db_path}")

            # Pas 1: Creează baza de date LOCALĂ cu toate grinzile selectate
            print("-- Creare bază de date locală cu grinzile selectate...")
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

            # Pas 2: Functii pentru popularea bazei de date mari
            print("-- Populare baza de date cu informații detaliate")
            self.populate_database_with_details()

            # Pas 3: Functii pentru procesarea excel
            print("-- Procesare fișier Excel cu date din baza de date locala")
            excel_success = self.process_excel_with_database(default_file, excel_path)

            if not excel_success:
                messagebox.showerror("⮽⮽ Eroare", "Nu s-a putut procesa fișierul Excel!")
                return

            # Pas 4: Copiază baza de date detailata în folderul de rezultate
            if os.path.exists("frames.db"):
                try:
                    import shutil
                    shutil.copy2("frames.db", db_path)
                    print(f"✓✓ Bază de date copiată în: {db_path}")
                except Exception as e:
                    print(f"⮽⮽ Eroare la copierea bazei de date: {e}")
                    messagebox.showerror("⮽⮽ Eroare", f"Eroare la copierea bazei de date: {e}")
                    return
            else:
                print("⮽⮽ Baza de date locală nu există pentru copiere")
                messagebox.showerror("⮽⮽Eroare", "Baza de date locală nu a fost creată!")
                return

            # Afișează mesaj de succes
            print(f"✓✓ Proces completat cu succes!")
            messagebox.showinfo("✓✓ Succes",
                                f"Proces completat cu succes!\n\n"
                                f"Fișier Excel creat:\n{excel_path}\n\n"
                                f"Bază de date creată:\n{db_path}")

        except Exception as e:
            print(f"⮽⮽ Eroare la crearea Excel-ului: {e}")
            messagebox.showerror("Eroare", f"Eroare: {e}")

    def populate_database_with_details(self):
        """Populează baza de date cu informații detaliate din ETABS"""
        try:
            # Conectează-te la baza de date locală
            conn = sqlite3.connect("frames.db")
            cursor = conn.cursor()

            # Obține toate grinzile din baza de date
            cursor.execute("SELECT UniqueName FROM Frames")
            beams = cursor.fetchall()

            print(f"-- Populare detalii pentru {len(beams)} grinzi...")

            for (beam_name,) in beams:
                try:
                    # Obține informații detaliate din ETABS
                    label, story = etabs_api.operations.get_label_and_story(beam_name)
                    guid = etabs_api.operations.get_frame_guid(beam_name)
                    section_name = etabs_api.operations.get_section_name(beam_name)

                    # Obține geometria
                    geometry = etabs_api.operations.get_geometry(beam_name)
                    length = geometry['length'] if geometry else 0

                    # Actualizează înregistrarea în baza de date
                    cursor.execute("""
                    UPDATE Frames 
                    SET Label = ?, Story = ?, GUID = ?, SectionName = ?, Length = ?
                    WHERE UniqueName = ?
                    """, (label, story, guid, section_name, length, beam_name))

                    print(f"✓✓ Actualizat: {beam_name}")

                except Exception as e:
                    print(f"⮽⮽️ Eroare la actualizarea grinzii {beam_name}: {e}")
                    continue

            # Salvează schimbările
            conn.commit()
            conn.close()
            print("✓✓ Baza de date a fost populată cu informații detaliate!")

        except Exception as e:
            print(f"⮽⮽ Eroare la popularea bazei de date: {e}")

    def process_excel_with_database(self, template_path, output_path):
        """Procesează fișierul Excel folosind datele din baza de date"""
        try:
            # Pas 1: Copiază template-ul Excel
            print(f"-- Copiiere template-ul Excel...")
            success = copy_excel_file(template_path, output_path)

            if not success:
                print("⮽⮽ Eroare la copierea template-ului Excel")
                return False

            # Pas 2: Aici vor fi adăugate funcțiile pentru popularea Excel-ului
            # cu date din baza de date
            print(f"-- Populare Excel-ul cu date din baza de date...")

            # Exemplu simplu - poți extinde această funcție mai târziu
            # pentru a popula fișierul Excel cu date din baza de date

            print(f"✓✓ Excel procesat cu succes: {output_path}")
            return True

        except Exception as e:
            print(f"⮽⮽ Eroare la procesarea Excel-ului: {e}")
            return False

    def close_application(self):
        """Închide aplicația și șterge fișierele temporare locale"""
        print("-- Închidere aplicația...")

        # Șterge fișierul temporar JSON
        if os.path.exists("beam_selection_temp.json"):
            try:
                os.remove("beam_selection_temp.json")
                print("-- Fișier temporar JSON șters")
            except Exception as e:
                print(f"⮽⮽ Nu am putut șterge fișierul temporar JSON: {e}")

        # Șterge baza de date locală
        if os.path.exists("frames.db"):
            try:
                os.remove("frames.db")
                print("✓✓ Baza de date locală ștearsă")
            except Exception as e:
                print(f"⮽⮽ Nu am putut șterge baza de date locală: {e}")

        # Oprește tracking
        if hasattr(self, 'beam_selection_active') and self.beam_selection_active:
            self.stop_beam_selection()

        print("-- Aplicația se închide...")
        self.root.destroy()

    def unselect_all(self):
        """Șterge TOATE datele inclusiv baza de date locală"""
        print("Ștergere selctii inclusiv baza de date locală")

        # Șterge grupurile de grinzi
        self.all_beam_groups_a = []
        self.all_beam_groups_b = []
        self.current_beam_group = []

        # Șterge fișierul temporar
        if os.path.exists("beam_selection_temp.json"):
            os.remove("beam_selection_temp.json")
            print("-- Fișier temporar șters")

        # Șterge fișierul bazei de date locale
        if os.path.exists("frames.db"):
            os.remove("frames.db")
            print("-- Baza de date locală ștearsă")

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
            print("-- Selectarea grinzilor este deja activă!")
            return

        self.current_scenario = scenario
        self.beam_selection_active = True
        self.current_beam_group = []

        # Șterge orice selecție anterioară în ETABS
        etabs_api.operations.clear_frame_selection()

        print(f"-- Început selecție grinzi pentru {scenario}")
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
            # Salvează grupul curent în scenariul corespunzător
            if self.current_scenario == "A":
                self.all_beam_groups_a.append(self.current_beam_group.copy())
                current_groups = self.all_beam_groups_a
            else:
                self.all_beam_groups_b.append(self.current_beam_group.copy())
                current_groups = self.all_beam_groups_b

            print(
                f"-- Grupul {len(current_groups)} confirmat pentru scenariul {self.current_scenario}: {self.current_beam_group}")

            # Salvează în fișier temporar
            self.save_temp_data(self.current_scenario, current_groups)

            # Ascunde grinzile
            success = etabs_api.operations.hide_specific_frames(self.current_beam_group)
            if success:
                print("-- Grinzi ascunse cu succes în ETABS")
            else:
                print("⮽⮽ Metoda de ascundere a eșuat")

            # Șterge selecția pentru următorul grup
            etabs_api.operations.clear_frame_selection()
            self.current_beam_group = []

            print("-- Gata pentru selecția următorului grup de grinzi...")
            return True
        else:
            print("-- Nu sunt grinzi selectate în grupul curent!")
            return False

    def confirm_and_stop(self):
        """Confirmă grupul curent și oprește selecția"""
        if self.current_beam_group:
            # Salvează grupul curent
            if self.current_scenario == "A":
                self.all_beam_groups_a.append(self.current_beam_group.copy())
                current_groups = self.all_beam_groups_a
            else:
                self.all_beam_groups_b.append(self.current_beam_group.copy())
                current_groups = self.all_beam_groups_b

            print(f"-- Grupul final confirmat pentru scenariul {self.current_scenario}")

            # Salvează în fișier temporar
            self.save_temp_data(self.current_scenario, current_groups)

            # Ascunde grinzile
            etabs_api.operations.hide_specific_frames(self.current_beam_group)

        # Șterge selecția și oprește
        etabs_api.operations.clear_frame_selection()
        self.stop_beam_selection()
        return True

    def cancel_selection(self):
        """Anulează selecția curentă fără salvare"""
        print("-- Selecție anulată")

        # Șterge selecția în ETABS
        etabs_api.operations.clear_frame_selection()
        self.current_beam_group = []
        self.stop_beam_selection()
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
        """Salvează datele temporare pentru un scenariu"""
        data = {
            "timestamp": datetime.now().isoformat(),
            f"scenario_{scenario.lower()}": {
                "beam_groups": beam_groups,
                "rezistente_type": self.top_radio_state,
                "etaj": self.etaj_value,
                "selected_combinations_upper": self.selected_combinations[f"{scenario}_upper"],
                "selected_combinations_lower": self.selected_combinations[f"{scenario}_lower"],
                "button_states": {k[1]: v for k, v in self.button_states.items() if k[0] == scenario}
            }
        }

        with open("beam_selection_temp.json", 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"-- Date salvate pentru scenariul {scenario}")

    def get_detailed_summary_data(self):
        """Returnează datele detaliate pentru verificare"""
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
                    group_info["beams"].append({
                        "unique_name": beam_name,
                        "label": beam_info["Label"],
                        "story": beam_info["Story"],
                        "length": beam_info["Length"],
                        "section_name": beam_info["SectionName"],
                        "material": beam_info["Material"]
                    })
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
                    group_info["beams"].append({
                        "unique_name": beam_name,
                        "label": beam_info["Label"],
                        "story": beam_info["Story"],
                        "length": beam_info["Length"],
                        "section_name": beam_info["SectionName"],
                        "material": beam_info["Material"]
                    })
                summary["scenarios"]["Suprastructura"]["beam_groups"].append(group_info)

        return summary

    def get_beam_info(self, beam_name):
        """Extrage informații despre o grindă din ETABS"""
        try:
            label, story = etabs_api.operations.get_label_and_story(beam_name)
            guid = etabs_api.operations.get_frame_guid(beam_name)
            section_name = etabs_api.operations.get_section_name(beam_name)

            return {
                "UniqueName": beam_name,
                "Label": label,
                "Story": story,
                "GUID": guid,
                "SectionName": section_name,
                "Length": 0,  # Poți adăuga lungimea dacă este necesar
                "Material": "Concrete"
            }
        except Exception as e:
            print(f"Eroare la obținerea informațiilor pentru {beam_name}: {e}")
            return {
                "UniqueName": beam_name,
                "Label": "N/A",
                "Story": "N/A",
                "GUID": "N/A",
                "SectionName": "N/A",
                "Length": 0,
                "Material": "Concrete"
            }

    def run(self):
        """Rulează aplicația principală"""
        self.root.mainloop()


if __name__ == "__main__":
    app = DesignApp()
    app.run()