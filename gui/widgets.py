import tkinter as tk
from tkinter import ttk

# Add this import section at the top of widgets.py
try:
    from .startup_window import StartupWindow, AlternativeWindow
except ImportError:
    try:
        from startup_window import StartupWindow, AlternativeWindow
    except ImportError:
        # Fallback for when the file doesn't exist yet
        class StartupWindow:
            def __init__(self):
                pass
        class AlternativeWindow:
            def __init__(self):
                pass

class ScenarioFrame:
    def __init__(self, parent, scenario_name, scenario_id, button_states, button_command, clear_command,
                 action_command):
        self.scenario_id = scenario_id
        self.frame = ttk.LabelFrame(parent, text=scenario_name)

        # Upper list
        ttk.Label(self.frame, text="Grupari Fundamentale:").pack(pady=5)
        self.list_upper = tk.Listbox(self.frame, height=6, selectmode=tk.MULTIPLE, exportselection=False)
        self.list_upper.pack(pady=5, fill=tk.X)

        # Lower list
        ttk.Label(self.frame, text="Grupari Seismice:").pack(pady=5)
        self.list_lower = tk.Listbox(self.frame, height=6, selectmode=tk.MULTIPLE, exportselection=False)
        self.list_lower.pack(pady=5, fill=tk.X)

        # Variant buttons
        self.variant_buttons = {}
        for v in ["DCL", "DCM", "DCH", "Secundare"]:
            btn = tk.Button(self.frame, text=v, command=lambda val=v: button_command(scenario_id, val))
            btn.pack(fill="x", padx=5, pady=2)
            self.variant_buttons[v] = btn

        # Unselect all button
        ttk.Button(self.frame, text="Unselect All", command=clear_command).pack(pady=5, fill="x")

        # Extra buttons (Dir X / Dir Y)
        frame_horizontal = ttk.Frame(self.frame)
        frame_horizontal.pack(pady=2, fill="x")
        self.variant_buttons['Dir X'] = tk.Button(frame_horizontal, text="Dir X",
                                                  command=lambda: button_command(scenario_id, "Dir X"))
        self.variant_buttons['Dir Y'] = tk.Button(frame_horizontal, text="Dir Y",
                                                  command=lambda: button_command(scenario_id, "Dir Y"))
        self.variant_buttons['Dir X'].pack(side="left", expand=True, fill="x")
        self.variant_buttons['Dir Y'].pack(side="left", expand=True, fill="x")

        # Main action button
        button_text = f"Selecteaza Grinzi {scenario_name}"
        ttk.Button(self.frame, text=button_text, command=action_command).pack(
            pady=10, ipadx=20, ipady=10
        )


class ControlButtons:
    def __init__(self, parent, check_command, clear_command):
        self.frame = ttk.Frame(parent)

        ttk.Button(self.frame, text="Verificare Date Grinzi", command=check_command, width=40).pack(pady=5)
        ttk.Button(self.frame, text="Clear All Selection", command=clear_command, width=40).pack(pady=5)

    def pack(self, **kwargs):
        self.frame.pack(**kwargs)


class FileSelectionFrame:
    def __init__(self, parent, browse_default_command, browse_result_command):
        self.frame = ttk.Frame(parent)

        # Default file selection
        ttk.Label(self.frame, text="Default File:").grid(row=0, column=0, sticky="w")
        self.default_file_var = tk.StringVar()
        ttk.Entry(self.frame, textvariable=self.default_file_var, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(self.frame, text="Browse", command=browse_default_command).grid(row=0, column=2, padx=5)

        # Result folder selection
        ttk.Label(self.frame, text="Result Folder:").grid(row=1, column=0, sticky="w", pady=5)
        self.result_folder_var = tk.StringVar()
        ttk.Entry(self.frame, textvariable=self.result_folder_var, width=50).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(self.frame, text="Browse", command=browse_result_command).grid(row=1, column=2, padx=5, pady=5)

    def pack(self, **kwargs):
        self.frame.pack(**kwargs)


class SelectionConfirmationDialog:
    def __init__(self, parent, scenario_name, confirm_continue_callback, confirm_stop_callback, cancel_callback,
                 is_first_group=False):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Confirmare Selectie - {scenario_name}")
        self.dialog.geometry("500x300")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center the dialog
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (500 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (300 // 2)
        self.dialog.geometry(f"+{x}+{y}")

        # Message
        if is_first_group:
            message = f"Selectati grinzi in ETABS pentru {scenario_name}\nApoi confirmati selectia:"
        else:
            message = f"Selectati urmatorul grup de grinzi in ETABS pentru {scenario_name}\nApoi confirmati selectia:"

        self.message_label = ttk.Label(self.dialog, text=message, font=("Arial", 12), justify=tk.CENTER)
        self.message_label.pack(pady=20)

        # Buttons frame
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(pady=20)

        # Confirma si continua button
        ttk.Button(button_frame, text="Confirma selectia si continua",
                   command=confirm_continue_callback, width=30).pack(pady=10)

        # Confirma si opreste button
        ttk.Button(button_frame, text="Confirma selectia si Opreste",
                   command=confirm_stop_callback, width=30).pack(pady=10)

        # Anuleaza button
        ttk.Button(button_frame, text="Anuleaza",
                   command=cancel_callback, width=30).pack(pady=10)

    def update_message(self, new_message):
        """Update the dialog message"""
        self.message_label.config(text=new_message)

    def close_dialog(self):
        """Close the dialog window"""
        self.dialog.destroy()


class SimpleSummaryPopup:
    def __init__(self, parent, summary_data):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Verificare Date Grinzi - Summary")
        self.dialog.geometry("1400x600")

        # Create notebook for tabs
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Add tabs for each scenario
        for scenario_name, scenario_data in summary_data.get("scenarios", {}).items():
            self.create_scenario_tab(notebook, scenario_name, scenario_data)

        # Close button
        ttk.Button(self.dialog, text="Close", command=self.dialog.destroy).pack(pady=10)

    def create_scenario_tab(self, notebook, scenario_name, scenario_data):
        tab = ttk.Frame(notebook)
        notebook.add(tab, text=scenario_name)

        # Create frame for table
        table_frame = ttk.Frame(tab)
        table_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Create treeview for simple beam table
        columns = ('Group', 'Order', 'UniqueName', 'Story', 'SectionName', 'SectionProps', 'Material', 'Length',
                   'Rezistente', 'Etaj', 'DCL', 'DCM', 'DCH', 'Secundare', 'DirX', 'DirY')

        tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=20)

        # Configure columns
        column_widths = {
            'Group': 60, 'Order': 60, 'UniqueName': 120, 'Story': 80,
            'SectionName': 120, 'SectionProps': 150, 'Material': 80, 'Length': 80,
            'Rezistente': 100, 'Etaj': 80, 'DCL': 50, 'DCM': 50, 'DCH': 50,
            'Secundare': 80, 'DirX': 50, 'DirY': 50
        }

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=column_widths.get(col, 100))

        # Add data
        settings = scenario_data['settings']
        button_states = settings['button_states']

        for group_info in scenario_data['beam_groups']:
            for beam in group_info['beams']:
                tree.insert('', 'end', values=(
                    group_info['group_number'],
                    group_info['beams'].index(beam) + 1,
                    beam['unique_name'],
                    beam['story'],
                    beam['section_name'],
                    beam.get('section_props', 'N/A'),
                    beam.get('material', 'Concrete'),
                    f"{beam['length']:.3f}",
                    settings['rezistente_type'] or "Not set",
                    settings['etaj'] or "Not set",
                    "✓" if button_states.get('DCL') else "✗",
                    "✓" if button_states.get('DCM') else "✗",
                    "✓" if button_states.get('DCH') else "✗",
                    "✓" if button_states.get('Secundare') else "✗",
                    "✓" if button_states.get('Dir X') else "✗",
                    "✓" if button_states.get('Dir Y') else "✗"
                ))

        # Add scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Pack everything
        tree.pack(side='left', fill='both', expand=True)
        v_scrollbar.pack(side='right', fill='y')
        h_scrollbar.pack(side='bottom', fill='x')