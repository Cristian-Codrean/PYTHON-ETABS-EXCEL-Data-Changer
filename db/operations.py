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

    # Creează tabelă cu TOATE coloanele noi
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Frames (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        UniqueName TEXT NOT NULL,
        Label TEXT,
        GUID TEXT,
        Section TEXT,
        RealStory TEXT,
        SelectedStory TEXT,
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
        SelectionTime TEXT,
        ExcelColumn TEXT,      
        ExcelRow INTEGER,      
        SheetName TEXT,
        Length REAL,
        iJointName TEXT,
        jJointName TEXT,
        ModelOverwrites TEXT,
        MaterialOverwrites TEXT,
        Material TEXT,
        fck REAL,
        SectionType TEXT,
        Depth REAL,
        Width REAL,
        beff REAL,
        FlangeThickness REAL,
        ceffTOP REAL,
        ceffBOTTOM REAL,
        LongitudinalSteel TEXT,
        TransversalSteel TEXT,
        SectionOverwrites TEXT,
        iEndReleases TEXT,
        jEndReleases TEXT,
        iEndLengthOffset TEXT,
        jEndLengthOffset TEXT,
        AslReqGF TEXT,
        AslReqGS TEXT,
        AslEff TEXT,
        AslEffPlate TEXT,
        AslSupp TEXT,
        MEdGF TEXT,
        MEdGS TEXT,
        VEdGF TEXT,
        VEdGS TEXT,
        AstEff TEXT,
        AstSupp TEXT,
        AstReqGF TEXT,
        AstReqGS TEXT,
        MRdPoz TEXT,
        MRdNeg TEXT,
        PhiMaxNeg TEXT,
        PhiCapNeg TEXT,
        PhiMaxPoz TEXT,
        PhiCapPoz TEXT,
        TopColumnMRd TEXT,
        BottColumnMRd TEXT,
        iTopColumnReleases TEXT,
        iBottColumnReleases TEXT,
        jTopColumnReleases TEXT,
        jBottColumnReleases TEXT,
        TopColName TEXT,
        BottColName TEXT,
        NodeCheck TEXT,
        TopFiberCheck TEXT,
        BottFiberCheck TEXT,
        ShearCheck TEXT
    )
    """)
    print("-- Am creat tabela Frames cu toate coloanele noi!")

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
                label, real_story = get_label_and_story(frame_name)
                guid = get_frame_guid(frame_name)
                section_name = get_section_name(frame_name)

                # FIXED: Added section_name parameter
                design_data = get_design_data_from_group_settings(group_settings, frame_name, group_number,
                                                                  order_in_group, scenario, real_story, section_name)

                # Obține toate datele noi din ETABS API
                beam_properties = get_all_beam_properties(frame_name)

                # FIXED: Counted columns and values - there are 74 columns and 74 values
                # FIXED: Updated to 75 columns and 75 values
                sql, params = build_insert_sql_and_params(
                    frame_name, label, guid, section_name, real_story,
                    design_data, beam_properties, group_number, order_in_group, scenario
                )
                cursor.execute(sql, params)

                print(f"-- Grinda {frame_name} adăugată (Scenariu {scenario}, Grup {group_number}, Poziția {order_in_group})")
                total_beams += 1

            except Exception as e:
                print(f"⮽⮽ EROARE la procesarea grinzii {frame_name}: {e}")
                import traceback
                traceback.print_exc()

    return total_beams


# def process_beam_groups_from_json(cursor, beam_groups, scenario):
#     """Procesează toate grupurile de grinzi pentru un scenariu cu setările individuale din JSON"""
#     total_beams = 0
#
#     if not beam_groups:
#         print(f"-- Niciun grup de grinzi găsit pentru scenariul {scenario}")
#         return 0
#
#     print(f"-- Procesare {len(beam_groups)} grupuri pentru scenariul {scenario}")
#
#     for group_data in beam_groups:
#         group_number = group_data.get("group_number", 1)
#
#         if not isinstance(group_data, dict):
#             print(f"⮽⮽ Format neașteptat pentru grupul {group_number}: {type(group_data)}")
#             continue
#
#         beams_in_group = group_data.get("beams", [])
#         group_settings = group_data.get("settings", {})
#
#         print(f"-- Procesare grup {group_number} cu {len(beams_in_group)} grinzi")
#
#         for order_in_group, frame_name in enumerate(beams_in_group, 1):
#             try:
#                 label, real_story = get_label_and_story(frame_name)
#                 guid = get_frame_guid(frame_name)
#
#                 design_data = get_design_data_from_group_settings(group_settings, frame_name, group_number,
#                                                                   order_in_group, scenario, real_story)
#
#                 # Inserează datele în baza de date cu NOUA STRUCTURĂ
#                 cursor.execute("""
#                 INSERT INTO Frames (
#                     UniqueName, Label, GUID, RealStory, SelectedStory, GroupID, OrderID, Scenario,
#                     Rezistente, DCL, DCM, DCH, Secundare, DirX, DirY,
#                     CombUpper, CombLower, SelectionTime,
#                     ExcelColumn, ExcelRow, SheetName
#                 ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#                 """, (
#                     frame_name,
#                     label,
#                     guid,
#                     real_story,  # RealStory - din ETABS
#                     design_data["selected_story"],  # SelectedStory - din setările grupului
#                     group_number,
#                     order_in_group,
#                     scenario,
#                     design_data["rezistente"],
#                     design_data["dcl"],
#                     design_data["dcm"],
#                     design_data["dch"],
#                     design_data["secundare"],
#                     design_data["dir_x"],
#                     design_data["dir_y"],
#                     design_data["comb_upper"],
#                     design_data["comb_lower"],
#                     design_data["selection_time"],
#                     None,  # ExcelColumn - va fi populat mai târziu
#                     None,  # ExcelRow - va fi populat mai târziu
#                     None   # SheetName - va fi populat mai târziu
#                 ))
#
#                 print(f"-- Grinda {frame_name} adăugată (Scenariu {scenario}, Grup {group_number}, Poziția {order_in_group})")
#                 total_beams += 1
#
#             except Exception as e:
#                 print(f"⮽⮽ EROARE la procesarea grinzii {frame_name}: {e}")
#                 import traceback
#                 traceback.print_exc()
#
#     return total_beams
#

def get_design_data_from_group_settings(group_settings, frame_name, group_id, order_id, scenario, real_story, section_name):
    """Extrage datele de design din setările specifice grupului"""
    try:
        button_states = group_settings.get("button_states", {})
        rezistente_type = group_settings.get("rezistente_type", "Normale")
        selected_story = group_settings.get("etaj", real_story)  # Folosește real_story ca fallback

        # Combinațiile selectate
        comb_upper_list = group_settings.get("selected_combinations_upper", [])
        comb_lower_list = group_settings.get("selected_combinations_lower", [])

        # Convert lists to strings
        comb_upper = ", ".join(comb_upper_list) if isinstance(comb_upper_list, list) else str(comb_upper_list)
        comb_lower = ", ".join(comb_lower_list) if isinstance(comb_lower_list, list) else str(comb_lower_list)

        # Debug logging
        print(f"   - Button states pentru {frame_name}: {button_states}")
        print(f"   - Rezistente: {rezistente_type}")
        print(f"   - Section: {section_name}")
        print(f"   - Real Story: {real_story}")
        print(f"   - Selected Story: {selected_story}")
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
            "selected_story": selected_story,
            "selection_time": datetime.now().isoformat()
        }

    except Exception as e:
        print(f"⮽⮽ Eroare la extragerea datelor de design pentru {frame_name}: {e}")
        return get_default_design_data(group_id, order_id, real_story, section_name)


def get_default_design_data(group_id, order_id, real_story, section_name):
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
        "selected_story": real_story,  # Folosește real_story ca SelectedStory default
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


def get_all_beam_properties(frame_name):
    """Obține toate proprietățile grinzii din ETABS API (funcții placeholder pentru acum)"""
    try:
        # Folosește funcțiile existente și adaugă funcțiile noi
        from etabs_api.operations import (
            get_frame_length, get_prop_modifiers, get_end_releases, get_end_length_offsets,
            get_material_overwrite, get_section_name, get_section_material
        )

        # Funcții placeholder pentru noile proprietăți
        def get_joint_names(name):
            return {"i": "N/A", "j": "N/A"}

        def get_section_properties(name):
            return {
                "section_type": "N/A", "depth": 0.0, "width": 0.0, "beff": 0.0,
                "flange_thickness": 0.0, "ceff_top": 0.0, "ceff_bottom": 0.0
            }

        def get_steel_properties(name):
            return {
                "longitudinal": {"fyk": 0.0, "fuk": 0.0, "fym": 0.0, "fum": 0.0},
                "transversal": {"fyk": 0.0, "fuk": 0.0, "fym": 0.0, "fum": 0.0}
            }

        def get_design_results(name):
            return {
                "asl_req_gf": {"i": 0.0, "mid": 0.0, "j": 0.0},
                "asl_req_gs": {"i": 0.0, "mid": 0.0, "j": 0.0},
                "asl_eff": {"i": 0.0, "mid": 0.0, "j": 0.0},
                "asl_eff_plate": {"i": 0.0, "mid": 0.0, "j": 0.0},
                "asl_supp": {"i": 0.0, "mid": 0.0, "j": 0.0},
                "med_gf": {"i": 0.0, "mid": 0.0, "j": 0.0},
                "med_gs": {"i": 0.0, "mid": 0.0, "j": 0.0},
                "ved_gf": {"i": 0.0, "mid": 0.0, "j": 0.0},
                "ved_gs": {"i": 0.0, "mid": 0.0, "j": 0.0},
                "ast_eff": {"i": 0.0, "mid": 0.0, "j": 0.0},
                "ast_supp": {"i": 0.0, "mid": 0.0, "j": 0.0},
                "ast_req_gf": {"i": 0.0, "mid": 0.0, "j": 0.0},
                "ast_req_gs": {"i": 0.0, "mid": 0.0, "j": 0.0}
            }

        def get_capacity_results(name):
            return {
                "mrd_poz": {"i": 0.0, "j": 0.0},
                "mrd_neg": {"i": 0.0, "j": 0.0},
                "phi_max_neg": {"i": 0.0, "j": 0.0},
                "phi_cap_neg": {"i": 0.0, "j": 0.0},
                "phi_max_poz": {"i": 0.0, "j": 0.0},
                "phi_cap_poz": {"i": 0.0, "j": 0.0}
            }

        def get_column_connections(name):
            return {
                "top_column_mrd": {"i": 0.0, "j": 0.0},
                "bott_column_mrd": {"i": 0.0, "j": 0.0},
                "i_top_column_releases": {"Nx": 0.0, "V2": 0.0, "V3": 0.0, "T": 0.0, "M22": 0.0, "M33": 0.0},
                "i_bott_column_releases": {"Nx": 0.0, "V2": 0.0, "V3": 0.0, "T": 0.0, "M22": 0.0, "M33": 0.0},
                "j_top_column_releases": {"Nx": 0.0, "V2": 0.0, "V3": 0.0, "T": 0.0, "M22": 0.0, "M33": 0.0},
                "j_bott_column_releases": {"Nx": 0.0, "V2": 0.0, "V3": 0.0, "T": 0.0, "M22": 0.0, "M33": 0.0},
                "top_col_name": {"i": "N/A", "j": "N/A"},
                "bott_col_name": {"i": "N/A", "j": "N/A"}
            }

        def get_checks(name):
            return {
                "node_check": {"i": "N/A", "j": "N/A"},
                "top_fiber_check": {"i": "N/A", "mid": "N/A", "j": "N/A"},
                "bott_fiber_check": {"i": "N/A", "mid": "N/A", "j": "N/A"},
                "shear_check": {"i": "N/A", "mid": "N/A", "j": "N/A"}
            }

        # Obține toate proprietățile
        length = get_frame_length(frame_name) or 0.0
        joint_names = get_joint_names(frame_name)
        model_overwrites = get_prop_modifiers(frame_name) or {"A": 0.0, "Av2": 0.0, "Av3": 0.0, "T": 0.0, "M2": 0.0,
                                                              "M3": 0.0, "M": 0.0, "W": 0.0}
        material_overwrites = get_material_overwrite(frame_name) or "N/A"
        material = get_section_material(frame_name) or "N/A"
        section_props = get_section_properties(frame_name)
        steel_props = get_steel_properties(frame_name)
        end_releases = get_end_releases(frame_name) or {
            "i": {"Nx": 0.0, "V2": 0.0, "V3": 0.0, "T": 0.0, "M22": 0.0, "M33": 0.0},
            "j": {"Nx": 0.0, "V2": 0.0, "V3": 0.0, "T": 0.0, "M22": 0.0, "M33": 0.0}}
        end_offsets = get_end_length_offsets(frame_name) or {"i": {"Length": 0.0, "RigidZoneFactor": 0.0},
                                                             "j": {"Length": 0.0, "RigidZoneFactor": 0.0}}
        design_results = get_design_results(frame_name)
        capacity_results = get_capacity_results(frame_name)
        column_connections = get_column_connections(frame_name)
        checks = get_checks(frame_name)

        return {
            "length": length,
            "i_joint_name": joint_names["i"],
            "j_joint_name": joint_names["j"],
            "model_overwrites": json.dumps(model_overwrites),
            "material_overwrites": material_overwrites,
            "material": material,
            "fck": 0.0,  # Placeholder
            "section_type": section_props["section_type"],
            "depth": section_props["depth"],
            "width": section_props["width"],
            "beff": section_props["beff"],
            "flange_thickness": section_props["flange_thickness"],
            "ceff_top": section_props["ceff_top"],
            "ceff_bottom": section_props["ceff_bottom"],
            "longitudinal_steel": json.dumps(steel_props["longitudinal"]),
            "transversal_steel": json.dumps(steel_props["transversal"]),
            "section_overwrites": json.dumps(model_overwrites),  # Same as model_overwrites for now
            "i_end_releases": json.dumps(end_releases["i"]),
            "j_end_releases": json.dumps(end_releases["j"]),
            "i_end_length_offset": json.dumps(end_offsets["i"]),
            "j_end_length_offset": json.dumps(end_offsets["j"]),
            "asl_req_gf": json.dumps(design_results["asl_req_gf"]),
            "asl_req_gs": json.dumps(design_results["asl_req_gs"]),
            "asl_eff": json.dumps(design_results["asl_eff"]),
            "asl_eff_plate": json.dumps(design_results["asl_eff_plate"]),
            "asl_supp": json.dumps(design_results["asl_supp"]),
            "med_gf": json.dumps(design_results["med_gf"]),
            "med_gs": json.dumps(design_results["med_gs"]),
            "ved_gf": json.dumps(design_results["ved_gf"]),
            "ved_gs": json.dumps(design_results["ved_gs"]),
            "ast_eff": json.dumps(design_results["ast_eff"]),
            "ast_supp": json.dumps(design_results["ast_supp"]),
            "ast_req_gf": json.dumps(design_results["ast_req_gf"]),
            "ast_req_gs": json.dumps(design_results["ast_req_gs"]),
            "mrd_poz": json.dumps(capacity_results["mrd_poz"]),
            "mrd_neg": json.dumps(capacity_results["mrd_neg"]),
            "phi_max_neg": json.dumps(capacity_results["phi_max_neg"]),
            "phi_cap_neg": json.dumps(capacity_results["phi_cap_neg"]),
            "phi_max_poz": json.dumps(capacity_results["phi_max_poz"]),
            "phi_cap_poz": json.dumps(capacity_results["phi_cap_poz"]),
            "top_column_mrd": json.dumps(column_connections["top_column_mrd"]),
            "bott_column_mrd": json.dumps(column_connections["bott_column_mrd"]),
            "i_top_column_releases": json.dumps(column_connections["i_top_column_releases"]),
            "i_bott_column_releases": json.dumps(column_connections["i_bott_column_releases"]),
            "j_top_column_releases": json.dumps(column_connections["j_top_column_releases"]),
            "j_bott_column_releases": json.dumps(column_connections["j_bott_column_releases"]),
            "top_col_name": json.dumps(column_connections["top_col_name"]),
            "bott_col_name": json.dumps(column_connections["bott_col_name"]),
            "node_check": json.dumps(checks["node_check"]),
            "top_fiber_check": json.dumps(checks["top_fiber_check"]),
            "bott_fiber_check": json.dumps(checks["bott_fiber_check"]),
            "shear_check": json.dumps(checks["shear_check"])
        }

    except Exception as e:
        print(f"⮽⮽ Eroare la obținerea proprietăților grinzii {frame_name}: {e}")
        # Returnează valori default în caz de eroare
        return get_default_beam_properties()


def get_default_beam_properties():
    """Returnează proprietăți default pentru grindă"""
    default_dict = {"i": 0.0, "mid": 0.0, "j": 0.0}
    default_release = {"Nx": 0.0, "V2": 0.0, "V3": 0.0, "T": 0.0, "M22": 0.0, "M33": 0.0}
    default_offset = {"Length": 0.0, "RigidZoneFactor": 0.0}
    default_steel = {"fyk": 0.0, "fuk": 0.0, "fym": 0.0, "fum": 0.0}
    default_overwrites = {"A": 0.0, "Av2": 0.0, "Av3": 0.0, "T": 0.0, "M2": 0.0, "M3": 0.0, "M": 0.0, "W": 0.0}

    return {
        "length": 0.0,
        "i_joint_name": "N/A",
        "j_joint_name": "N/A",
        "model_overwrites": json.dumps(default_overwrites),
        "material_overwrites": "N/A",
        "material": "N/A",
        "fck": 0.0,
        "section_type": "N/A",
        "depth": 0.0,
        "width": 0.0,
        "beff": 0.0,
        "flange_thickness": 0.0,
        "ceff_top": 0.0,
        "ceff_bottom": 0.0,
        "longitudinal_steel": json.dumps(default_steel),
        "transversal_steel": json.dumps(default_steel),
        "section_overwrites": json.dumps(default_overwrites),
        "i_end_releases": json.dumps(default_release),
        "j_end_releases": json.dumps(default_release),
        "i_end_length_offset": json.dumps(default_offset),
        "j_end_length_offset": json.dumps(default_offset),
        "asl_req_gf": json.dumps(default_dict),
        "asl_req_gs": json.dumps(default_dict),
        "asl_eff": json.dumps(default_dict),
        "asl_eff_plate": json.dumps(default_dict),
        "asl_supp": json.dumps(default_dict),
        "med_gf": json.dumps(default_dict),
        "med_gs": json.dumps(default_dict),
        "ved_gf": json.dumps(default_dict),
        "ved_gs": json.dumps(default_dict),
        "ast_eff": json.dumps(default_dict),
        "ast_supp": json.dumps(default_dict),
        "ast_req_gf": json.dumps(default_dict),
        "ast_req_gs": json.dumps(default_dict),
        "mrd_poz": json.dumps({"i": 0.0, "j": 0.0}),
        "mrd_neg": json.dumps({"i": 0.0, "j": 0.0}),
        "phi_max_neg": json.dumps({"i": 0.0, "j": 0.0}),
        "phi_cap_neg": json.dumps({"i": 0.0, "j": 0.0}),
        "phi_max_poz": json.dumps({"i": 0.0, "j": 0.0}),
        "phi_cap_poz": json.dumps({"i": 0.0, "j": 0.0}),
        "top_column_mrd": json.dumps({"i": 0.0, "j": 0.0}),
        "bott_column_mrd": json.dumps({"i": 0.0, "j": 0.0}),
        "i_top_column_releases": json.dumps(default_release),
        "i_bott_column_releases": json.dumps(default_release),
        "j_top_column_releases": json.dumps(default_release),
        "j_bott_column_releases": json.dumps(default_release),
        "top_col_name": json.dumps({"i": "N/A", "j": "N/A"}),
        "bott_col_name": json.dumps({"i": "N/A", "j": "N/A"}),
        "node_check": json.dumps({"i": "N/A", "j": "N/A"}),
        "top_fiber_check": json.dumps(default_dict),
        "bott_fiber_check": json.dumps(default_dict),
        "shear_check": json.dumps(default_dict)
    }


def build_insert_sql_and_params(frame_name, label, guid, section_name, real_story, design_data, beam_properties,
                                group_number, order_in_group, scenario):
    """Construiește SQL-ul și parametrii pentru INSERT"""
    columns = [
        "UniqueName", "Label", "GUID", "Section", "RealStory", "SelectedStory", "GroupID", "OrderID", "Scenario",
        "Rezistente", "DCL", "DCM", "DCH", "Secundare", "DirX", "DirY",
        "CombUpper", "CombLower", "SelectionTime",
        "ExcelColumn", "ExcelRow", "SheetName",
        "Length", "iJointName", "jJointName", "ModelOverwrites", "MaterialOverwrites", "Material", "fck",
        "SectionType", "Depth", "Width", "beff", "FlangeThickness", "ceffTOP", "ceffBOTTOM",
        "LongitudinalSteel", "TransversalSteel", "SectionOverwrites",
        "iEndReleases", "jEndReleases", "iEndLengthOffset", "jEndLengthOffset",
        "AslReqGF", "AslReqGS", "AslEff", "AslEffPlate", "AslSupp",
        "MEdGF", "MEdGS", "VEdGF", "VEdGS", "AstEff", "AstSupp", "AstReqGF", "AstReqGS",
        "MRdPoz", "MRdNeg", "PhiMaxNeg", "PhiCapNeg", "PhiMaxPoz", "PhiCapPoz",
        "TopColumnMRd", "BottColumnMRd",
        "iTopColumnReleases", "iBottColumnReleases", "jTopColumnReleases", "jBottColumnReleases",
        "TopColName", "BottColName", "NodeCheck", "TopFiberCheck", "BottFiberCheck", "ShearCheck"
    ]

    params = [
        frame_name,  # 1
        label,  # 2
        guid,  # 3
        section_name,  # 4
        real_story,  # 5
        design_data["selected_story"],  # 6
        group_number,  # 7
        order_in_group,  # 8
        scenario,  # 9
        design_data["rezistente"],  # 10
        design_data["dcl"],  # 11
        design_data["dcm"],  # 12
        design_data["dch"],  # 13
        design_data["secundare"],  # 14
        design_data["dir_x"],  # 15
        design_data["dir_y"],  # 16
        design_data["comb_upper"],  # 17
        design_data["comb_lower"],  # 18
        design_data["selection_time"],  # 19
        None,  # 20 ExcelColumn
        None,  # 21 ExcelRow
        None,  # 22 SheetName
        # Noile coloane cu date din ETABS
        beam_properties["length"],  # 23
        beam_properties["i_joint_name"],  # 24
        beam_properties["j_joint_name"],  # 25
        beam_properties["model_overwrites"],  # 26
        beam_properties["material_overwrites"],  # 27
        beam_properties["material"],  # 28
        beam_properties["fck"],  # 29
        beam_properties["section_type"],  # 30
        beam_properties["depth"],  # 31
        beam_properties["width"],  # 32
        beam_properties["beff"],  # 33
        beam_properties["flange_thickness"],  # 34
        beam_properties["ceff_top"],  # 35
        beam_properties["ceff_bottom"],  # 36
        beam_properties["longitudinal_steel"],  # 37
        beam_properties["transversal_steel"],  # 38
        beam_properties["section_overwrites"],  # 39
        beam_properties["i_end_releases"],  # 40
        beam_properties["j_end_releases"],  # 41
        beam_properties["i_end_length_offset"],  # 42
        beam_properties["j_end_length_offset"],  # 43
        beam_properties["asl_req_gf"],  # 44
        beam_properties["asl_req_gs"],  # 45
        beam_properties["asl_eff"],  # 46
        beam_properties["asl_eff_plate"],  # 47
        beam_properties["asl_supp"],  # 48
        beam_properties["med_gf"],  # 49
        beam_properties["med_gs"],  # 50
        beam_properties["ved_gf"],  # 51
        beam_properties["ved_gs"],  # 52
        beam_properties["ast_eff"],  # 53
        beam_properties["ast_supp"],  # 54
        beam_properties["ast_req_gf"],  # 55
        beam_properties["ast_req_gs"],  # 56
        beam_properties["mrd_poz"],  # 57
        beam_properties["mrd_neg"],  # 58
        beam_properties["phi_max_neg"],  # 59
        beam_properties["phi_cap_neg"],  # 60
        beam_properties["phi_max_poz"],  # 61
        beam_properties["phi_cap_poz"],  # 62
        beam_properties["top_column_mrd"],  # 63
        beam_properties["bott_column_mrd"],  # 64
        beam_properties["i_top_column_releases"],  # 65
        beam_properties["i_bott_column_releases"],  # 66
        beam_properties["j_top_column_releases"],  # 67
        beam_properties["j_bott_column_releases"],  # 68
        beam_properties["top_col_name"],  # 69
        beam_properties["bott_col_name"],  # 70
        beam_properties["node_check"],  # 71
        beam_properties["top_fiber_check"],  # 72
        beam_properties["bott_fiber_check"],  # 73
        beam_properties["shear_check"]  # 74
    ]

    # Verify counts match
    if len(columns) != len(params):
        print(f"⮽⮽ MISMATCH: {len(columns)} columns but {len(params)} parameters")
        # Add missing parameter
        if len(columns) > len(params):
            params.extend([None] * (len(columns) - len(params)))

    placeholders = ",".join(["?"] * len(columns))
    sql = f"INSERT INTO Frames ({','.join(columns)}) VALUES ({placeholders})"

    return sql, params