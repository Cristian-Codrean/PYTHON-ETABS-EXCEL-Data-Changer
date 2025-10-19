import sqlite3
import os
import json
from datetime import datetime  # Add missing import


def create_database(frame_list):
    """ Creează baza de date pentru elementele de tip frame (grinzi) din toate grupurile."""

    # Calea către baza de date în folderul root
    db_path = "frames.db"

    # Verifică dacă baza de date există deja și o șterge
    if os.path.exists(db_path):
        os.remove(db_path)
        print("-- Am șters baza de date veche pentru a o recrea!")

    # Încarcă datele din fișierul JSON temporar
    json_data = load_temp_json_data()
    if not json_data:
        print("⮽⮽ Nu s-au putut încărca datele din fișierul JSON temporar!")
        return False

    # Conectează-te la baza de date
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Creează tabelă cu noile coloane pentru poziția Excel
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Frames (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        UniqueName TEXT NOT NULL,
        Label TEXT,
        GUID TEXT,
        GroupID INTEGER,
        OrderID INTEGER,
        Scenario TEXT,
        Rezistente TEXT,
        DCL TEXT,
        DCM TEXT,
        DCH TEXT,
        Secundare TEXT,
        DirX TEXT,
        DirY TEXT,
        CombUpper TEXT,
        CombLower TEXT,
        Etaj TEXT,
        SelectionTime TEXT,
        ExcelColumn TEXT,      
        ExcelRow INTEGER,      
        SheetName TEXT         
    )
    """)
    print("-- Am creat tabela Frames cu noile coloane Excel!")

    # Procesează TOATE grupurile de grinzi din ambele scenarii
    total_beams_added = 0

    # Procesează scenariul A (Infrastructura)
    if "scenario_a" in json_data:
        scenario_a_data = json_data["scenario_a"]
        beam_groups_a = scenario_a_data.get("beam_groups", [])
        print(f"-- Procesare scenariu A (Infrastructura) cu {len(beam_groups_a)} grupuri")
        total_beams_added += process_beam_groups_from_json(cursor, beam_groups_a, "A")
    else:
        print("-- Niciun scenariu A găsit în JSON")

    # Procesează scenariul B (Suprastructura)
    if "scenario_b" in json_data:
        scenario_b_data = json_data["scenario_b"]
        beam_groups_b = scenario_b_data.get("beam_groups", [])
        print(f"-- Procesare scenariu B (Suprastructura) cu {len(beam_groups_b)} grupuri")
        total_beams_added += process_beam_groups_from_json(cursor, beam_groups_b, "B")
    else:
        print("-- Niciun scenariu B găsit în JSON")

    # Salvează schimbările
    conn.commit()

    print(f"-- S-au adăugat {total_beams_added} grinzi în baza de date din toate grupurile!")

    # Închide conexiunea
    conn.close()
    print("-- Conexiunea la baza de date a fost închisă!")
    return True


def process_beam_groups_from_json(cursor, beam_groups, scenario):
    """Procesează toate grupurile de grinzi pentru un scenariu cu setările individuale din JSON"""
    total_beams = 0

    if not beam_groups:
        print(f"-- Niciun grup de grinzi găsit pentru scenariul {scenario}")
        return 0

    print(f"-- Procesare {len(beam_groups)} grupuri pentru scenariul {scenario}")

    for group_data in beam_groups:
        group_number = group_data.get("group_number", 1)

        if not isinstance(group_data, dict):
            print(f"⮽⮽ Format neașteptat pentru grupul {group_number}: {type(group_data)}")
            continue

        beams_in_group = group_data.get("beams", [])
        group_settings = group_data.get("settings", {})

        print(f"-- Procesare grup {group_number} cu {len(beams_in_group)} grinzi")

        for order_in_group, frame_name in enumerate(beams_in_group, 1):
            try:
                label, story = get_label_and_story(frame_name)
                guid = get_frame_guid(frame_name)

                design_data = get_design_data_from_group_settings(group_settings, frame_name, group_number,
                                                                  order_in_group, scenario)

                # Inserează datele în baza de date cu noile coloane (inițial NULL)
                cursor.execute("""
                INSERT INTO Frames (
                    UniqueName, Label, GUID, GroupID, OrderID, Scenario,
                    Rezistente, DCL, DCM, DCH, Secundare, DirX, DirY,
                    CombUpper, CombLower, Etaj, SelectionTime,
                    ExcelColumn, ExcelRow, SheetName
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    frame_name,
                    label,
                    guid,
                    group_number,
                    order_in_group,
                    scenario,
                    design_data["rezistente"],
                    design_data["dcl"],
                    design_data["dcm"],
                    design_data["dch"],
                    design_data["secundare"],
                    design_data["dir_x"],
                    design_data["dir_y"],
                    design_data["comb_upper"],
                    design_data["comb_lower"],
                    design_data["etaj"],
                    design_data["selection_time"],
                    None,  # ExcelColumn - va fi populat mai târziu
                    None,  # ExcelRow - va fi populat mai târziu
                    None   # SheetName - va fi populat mai târziu
                ))

                print(f"-- Grinda {frame_name} adăugată (Scenariu {scenario}, Grup {group_number}, Poziția {order_in_group})")
                total_beams += 1

            except Exception as e:
                print(f"⮽⮽ EROARE la procesarea grinzii {frame_name}: {e}")
                import traceback
                traceback.print_exc()

    return total_beams


def get_design_data_from_group_settings(group_settings, frame_name, group_id, order_id, scenario):
    """Extrage datele de design din setările specifice grupului"""
    try:
        button_states = group_settings.get("button_states", {})
        rezistente_type = group_settings.get("rezistente_type", "Normale")
        etaj_value = group_settings.get("etaj", "N/A")

        # Combinațiile selectate
        comb_upper_list = group_settings.get("selected_combinations_upper", [])
        comb_lower_list = group_settings.get("selected_combinations_lower", [])

        # Convert lists to strings
        comb_upper = ", ".join(comb_upper_list) if isinstance(comb_upper_list, list) else str(comb_upper_list)
        comb_lower = ", ".join(comb_lower_list) if isinstance(comb_lower_list, list) else str(comb_lower_list)

        # Debug logging
        print(f"   - Button states pentru {frame_name}: {button_states}")
        print(f"   - Rezistente: {rezistente_type}")
        print(f"   - Etaj: {etaj_value}")
        print(f"   - Comb Upper: {comb_upper}")
        print(f"   - Comb Lower: {comb_lower}")

        return {
            "group_id": group_id,
            "order_id": order_id,
            "rezistente": rezistente_type,
            "dcl": str(button_states.get("DCL", False)),
            "dcm": str(button_states.get("DCM", False)),
            "dch": str(button_states.get("DCH", False)),
            "secundare": str(button_states.get("Secundare", False)),
            "dir_x": str(button_states.get("Dir X", False)),
            "dir_y": str(button_states.get("Dir Y", False)),
            "comb_upper": comb_upper,
            "comb_lower": comb_lower,
            "etaj": etaj_value,
            "selection_time": datetime.now().isoformat()
        }

    except Exception as e:
        print(f"⮽⮽ Eroare la extragerea datelor de design pentru {frame_name}: {e}")
        return get_default_design_data(group_id, order_id)


def get_default_design_data(group_id, order_id):
    """Returnează date de design default"""
    return {
        "group_id": group_id,
        "order_id": order_id,
        "rezistente": "Normale",
        "dcl": "False",
        "dcm": "False",
        "dch": "False",
        "secundare": "False",
        "dir_x": "False",
        "dir_y": "False",
        "comb_upper": "N/A",
        "comb_lower": "N/A",
        "etaj": "N/A",
        "selection_time": datetime.now().isoformat()
    }


def load_temp_json_data():
    """Încarcă datele din fișierul JSON temporar"""
    try:
        json_path = "beam_selection_temp.json"
        if not os.path.exists(json_path):
            print(f"⮽⮽ Fișierul JSON temporar nu există: {json_path}")
            return None

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print("-- Datele din fișierul JSON temporar au fost încărcate")

            # Debug detaliat: afișează toată structura JSON-ului
            print(f"-- Chei principale în JSON: {list(data.keys())}")

            # Verifică structura pentru fiecare scenariu
            for scenario_key in ["scenario_a", "scenario_b"]:
                if scenario_key in data:
                    scenario_data = data[scenario_key]
                    beam_groups = scenario_data.get("beam_groups", [])
                    print(f"-- Scenariul {scenario_key}:")
                    print(f"   - Număr grupuri: {len(beam_groups)}")
                    print(f"   - Tip beam_groups: {type(beam_groups)}")

                    total_beams_in_scenario = 0
                    for i, group in enumerate(beam_groups):
                        if isinstance(group, dict):
                            beams_in_group = group.get("beams", [])
                            group_number = group.get("group_number", i + 1)
                            print(f"   - Grup {group_number}: {len(beams_in_group)} grinzi")
                            if beams_in_group:  # Dacă grupul nu este gol
                                print(f"     Primele 3 grinzi: {beams_in_group[:3]}")
                                # Afișează setările grupului pentru debugging
                                settings = group.get("settings", {})
                                print(
                                    f"     Setări: Rezistente={settings.get('rezistente_type')}, Etaj={settings.get('etaj')}")
                                print(f"     Button States: {settings.get('button_states', {})}")
                            total_beams_in_scenario += len(beams_in_group)
                        else:
                            print(f"   - Grup {i + 1}: format neașteptat: {type(group)}")

                    print(f"   - Total grinzi în scenariu: {total_beams_in_scenario}")
                else:
                    print(f"-- Scenariul {scenario_key} nu există în JSON")

            return data

    except Exception as e:
        print(f"⮽⮽ Eroare la încărcarea fișierului JSON: {e}")
        import traceback
        traceback.print_exc()
        return None


# Funcții helper pentru a evita erorile de import
def get_label_and_story(name):
    """Funcție helper pentru a obține label și story"""
    try:
        from etabs_api.operations import get_label_and_story as get_label_story
        return get_label_story(name)
    except Exception as e:
        return [f"Label-{name}", "Story1"]


def get_frame_guid(name):
    """Funcție helper pentru a obține GUID"""
    try:
        from etabs_api.operations import get_frame_guid as get_guid
        return get_guid(name)
    except Exception as e:
        return f"guid-{name}"


def get_section_name(name):
    """Funcție helper pentru a obține numele secțiunii"""
    try:
        from etabs_api.operations import get_section_name as get_section
        return get_section(name)
    except Exception as e:
        return "Section1"

