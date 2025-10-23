# Importă funcția de conexiune
from etabs_api.connection import get_sap_model
# Get sap_model at module level for all functions to use
sap_model = get_sap_model()

def hide_specific_frames(frame_list):
    """Ascunde frame-urile specificate folosind funcția Make Objects Invisible din ETABS"""
    sap_model = get_sap_model()
    if not frame_list:
        print("-- Nu sunt frame-uri de ascuns")
        return True

    print(f"-- Încerc să ascund {len(frame_list)} frame-uri: {frame_list}")

    try:
        # Mai întâi, șterge orice selecție existentă
        sap_model.SelectObj.ClearSelection()

        # Selectează toate frame-urile pe care vrem să le ascundem
        selected_count = 0
        for frame_name in frame_list:
            try:
                ret = sap_model.FrameObj.SetSelected(frame_name, True)
                if ret == 0:
                    selected_count += 1
                else:
                    print(f"Avertisment:⮽⮽ Nu sa putut selecta frame-ul {frame_name}, eroare: {ret}")
            except Exception as e:
                print(f"⮽⮽ Eroare la selectarea frame-ului {frame_name}: {e}")

        print(f"-- Selectat {selected_count} frame-uri pentru ascundere")

        if selected_count > 0:
            # Metoda 1: Încearcă să folosească interfața Display pentru a ascunde obiecte
            try:
                # Obține toate obiectele selectate și le ascunde folosind opțiuni de display
                ret = sap_model.Display.SetObjectSelected(False)  # Deselectează toate
                if ret == 0:
                    print(f"-- Ascuns cu succes {selected_count} frame-uri")
                    return True
                else:
                    print(f"⮽⮽ Display.SetObjectSelected a returnat eroare: {ret}")
            except Exception as e:
                print(f"⮽⮽ Metoda Display a eșuat: {e}")

        # Șterge selecția indiferent de rezultat
        sap_model.SelectObj.ClearSelection()
        return selected_count > 0

    except Exception as e:
        print(f"⮽⮽ Eroare în hide_specific_frames: {e}")
        # Șterge selecția la eroare
        try:
            sap_model.SelectObj.ClearSelection()
        except:
            pass
        return False


def show_all_frames():
    """Arată toate frame-urile din model"""
    sap_model = get_sap_model()
    try:
        # Metoda 1: Încearcă să arate toate obiectele folosind interfața Display
        ret = sap_model.Display.SetObjectSelected(True)  # Selectează toate pentru a le face vizibile
        if ret == 0:
            print("-- Toate frame-urile ar trebui să fie vizibile acum")
            # Deselectează după ce le face vizibile
            sap_model.SelectObj.ClearSelection()
            return True
        else:
            print(f"⮽⮽ Display.SetObjectSelected a returnat eroare: {ret}")
            return False
    except Exception as e:
        print(f"⮽⮽ Eroare la afișarea frame-urilor: {e}")
        return False


def get_story_names():
    """Returnează numele nivelurilor într-o listă"""
    sap_model = get_sap_model()
    try:
        # Apel direct fără variabile intermediare
        return list(sap_model.Story.GetStories()[1])
    except Exception as e:
        print(f"⮽⮽ Eroare la obținerea numelor etajelor: {e}")
        return []


def get_comb_names():
    """Returnează numele tuturor combinațiilor într-o listă"""
    sap_model = get_sap_model()
    try:
        number_names = 0
        my_name = []
        return list(sap_model.RespCombo.GetNameList(number_names, my_name)[1])
    except Exception as e:
        print(f"⮽⮽ Eroare la obținerea numelor combinațiilor: {e}")
        return []


def get_selected_frames_live():
    """Returnează obiectele de tip frame (unique name) care sunt selectate în model în mod live"""
    sap_model = get_sap_model()
    try:
        name_list = list(sap_model.FrameObj.GetNameList()[1])
        selected_list = []
        for frame_name in name_list:
            if sap_model.FrameObj.GetSelected(frame_name)[0] == True:
                selected_list.append(frame_name)
        return selected_list
    except Exception as e:
        print(f"⮽⮽ Eroare la obținerea frame-urilor selectate live: {e}")
        return []


def clear_frame_selection():
    """Deselectează toate frame-urile din model"""
    sap_model = get_sap_model()
    try:
        sap_model.SelectObj.ClearSelection()
        return True
    except Exception as e:
        print(f"⮽⮽ Eroare la ștergerea selecției frame-urilor: {e}")
        return False


def get_frame_guid(frame_name):
    """Returnează GUID pentru elementul de tip frame introdus (Unique Name)"""
    sap_model = get_sap_model()
    try:
        result = sap_model.FrameObj.GetGUID(frame_name)
        return result[0] if result else None
    except Exception as e:
        print(f"⮽⮽ Eroare la obținerea GUID frame: {e}")
        return None


def get_label_and_story(name):
    """Returnează label și story de la inputul (unique name) ca o listă de stringuri"""
    try:
        result = sap_model.FrameObj.GetLabelFromName(name)
        if result and len(result) >= 2:
            return result[0:2]
        else:
            print(f"⮽⮽ Rezultat neașteptat GetLabelFromName pentru {name}: {result}")
            return ["N/A", "N/A"]
    except Exception as e:
        print(f"⮽⮽ Eroare la obținerea label și story pentru {name}: {e}")
        return ["N/A", "N/A"]


def get_section_name(frame_name):
    """Obține numele secțiunii pentru o grindă"""
    try:
        ret = sap_model.FrameObj.GetSection(frame_name)
        print(f"-- GetSection pentru {frame_name}: ret={ret}")

        if ret[0] == 0:
            section_name = ret[1]
            print(f"-- Secțiune obținută pentru {frame_name}: {section_name}")
            return section_name
        else:
            # În ETABS, uneori returnează numele secțiunii direct în ret[0]
            if isinstance(ret[0], str) and ret[0]:
                print(f"-- Secțiune obținută (alternativ) pentru {frame_name}: {ret[0]}")
                return ret[0]
            else:
                print(f"⮽⮽ Eroare GetSection pentru {frame_name}: cod {ret[0]}")
                return "N/A"
    except Exception as e:
        print(f"⮽⮽ Eroare la obținerea numelui secțiunii pentru {frame_name}: {e}")
        return "N/A"

def get_prop_modifiers(name):
    SapModel = get_sap_model()
    ret, modifiers = SapModel.FrameObj.GetModifiers(name)
    if ret != 0:
        return None
    keys = ["Area", "As2", "As3", "Torsion", "I22", "I33", "Mass", "Weight"]
    return dict(zip(keys, modifiers))

def get_end_releases(name):
    SapModel = get_sap_model()
    ret, i_releases, j_releases = SapModel.FrameObj.GetReleases(name)
    if ret != 0:
        return None
    keys = ["Axial", "Shear2", "Shear3", "Torsion", "Moment22", "Moment33"]
    return {
        "i": dict(zip(keys, i_releases)),
        "j": dict(zip(keys, j_releases))
    }

def get_end_length_offsets(name):
    SapModel = get_sap_model()
    ret, offset_i, offset_j, rigid_zone = SapModel.FrameObj.GetEndLengthOffset(name)
    if ret != 0:
        return None
    return {"i": offset_i, "j": offset_j, "RigidZoneFactor": rigid_zone}

def get_insertion_point(name):
    SapModel = get_sap_model()
    ret, card, justify, rotation = SapModel.FrameObj.GetInsertionPoint(name)
    if ret != 0:
        return None
    return {"CardinalPoint": card, "Justification": justify, "Rotation": rotation}

def get_output_stations(name):
    SapModel = get_sap_model()
    ret, sta_type, num = SapModel.FrameObj.GetOutputStations(name)
    if ret != 0:
        return None
    return {"OutputStationsBy": sta_type, "Number": num}

def get_local_axis_angle(name):
    SapModel = get_sap_model()
    ret, angle = SapModel.FrameObj.GetLocalAxes(name)
    return angle if ret == 0 else None

def get_springs(name):
    SapModel = get_sap_model()
    ret, spring = SapModel.FrameObj.GetSpringAssignment(name)
    return spring if ret == 0 else None

def get_line_mass(name):
    SapModel = get_sap_model()
    ret, mass, weight = SapModel.FrameObj.GetMass(name)
    if ret != 0:
        return None
    return mass

def get_tc_limits(name):
    SapModel = get_sap_model()
    ret, tension, compression = SapModel.FrameObj.GetTCLimits(name)
    if ret != 0:
        return None
    return {"Tension": tension, "Compression": compression}

def get_spandrel(name):
    SapModel = get_sap_model()
    ret, spandrel = SapModel.FrameObj.GetSpandrel(name)
    return spandrel if ret == 0 else None

def get_material_overwrite(name):
    SapModel = get_sap_model()
    ret, material = SapModel.FrameObj.GetMaterialOverwrite(name)
    return material if ret == 0 else None

def get_rebar_ratio(name):
    SapModel = get_sap_model()
    ret, ratio = SapModel.FrameObj.GetRebarRatio(name)
    return ratio if ret == 0 else None

def get_auto_mesh(name):
    SapModel = get_sap_model()
    ret, automesh = SapModel.FrameObj.GetAutoMesh(name)
    return automesh if ret == 0 else None

def get_groups(name):
    SapModel = get_sap_model()
    ret, number, group_names = SapModel.FrameObj.GetGroupAssign(name)
    if ret != 0:
        return None
    return {"Count": number, "Names": group_names}


def get_section_material(frame_name):
    """Obține numele materialului pentru secțiunea unei grinzi"""
    try:
        # Obține numele secțiunii
        section_name = get_section_name(frame_name)
        if section_name == "N/A":
            return "N/A"

        print(f"-- Obținere material pentru secțiunea: {section_name}")

        # Încearcă să obțină materialul direct folosind GetMaterial
        ret = sap_model.PropFrame.GetMaterial(section_name)
        print(f"-- GetMaterial pentru {section_name}: ret={ret}")

        if ret[0] == 0:
            material_name = ret[1]
            print(f"-- Material obținut direct: {material_name}")
            return material_name

        # Dacă direct nu funcționează, încearcă pentru diferite tipuri de secțiuni
        ret = sap_model.PropFrame.GetRectangle(section_name)
        if ret[0] == 0:
            material_name = ret[3]
            print(f"-- Material pentru secțiune rectangulară: {material_name}")
            return material_name

        ret = sap_model.PropFrame.GetISection(section_name)
        if ret[0] == 0:
            material_name = ret[8]
            print(f"-- Material pentru secțiune I: {material_name}")
            return material_name

        ret = sap_model.PropFrame.GetTube(section_name)
        if ret[0] == 0:
            material_name = ret[6]
            print(f"-- Material pentru secțiune tub: {material_name}")
            return material_name

        ret = sap_model.PropFrame.GetCircle(section_name)
        if ret[0] == 0:
            material_name = ret[3]
            print(f"-- Material pentru secțiune circulară: {material_name}")
            return material_name

        print(f"⮽⮽ Nu s-a putut determina materialul pentru secțiunea {section_name}")
        return "N/A"

    except Exception as e:
        print(f"⮽⮽ Eroare la obținerea materialului pentru {frame_name}: {e}")
        return "N/A"


def get_frame_length(frame_name):
    """Obține lungimea unei grinzi"""
    try:
        ret = sap_model.FrameObj.GetLength(frame_name)
        print(f"-- GetLength pentru {frame_name}: ret={ret}")

        if ret[0] == 0:
            length = ret[1]
            print(f"-- Lungime obținută pentru {frame_name}: {length:.3f}")
            return length
        else:
            print(f"⮽⮽ Eroare GetLength pentru {frame_name}: cod {ret[0]}")
            # Încearcă o metodă alternativă pentru a obține lungimea
            return get_frame_length_alternative(frame_name)
    except Exception as e:
        print(f"⮽⮽ Eroare la obținerea lungimii pentru {frame_name}: {e}")
        return 0.0


def get_frame_length_alternative(frame_name):
    """Metodă alternativă pentru a obține lungimea unei grinzi"""
    try:
        # Obține coordonatele punctelor de capăt
        ret = sap_model.FrameObj.GetPoints(frame_name)
        if ret[0] == 0:
            point1, point2 = ret[1], ret[2]
            # Obține coordonatele punctelor
            ret1 = sap_model.PointObj.GetCoordCartesian(point1)
            ret2 = sap_model.PointObj.GetCoordCartesian(point2)

            if ret1[0] == 0 and ret2[0] == 0:
                x1, y1, z1 = ret1[1], ret1[2], ret1[3]
                x2, y2, z2 = ret2[1], ret2[2], ret2[3]
                # Calculează distanța euclidiană
                length = ((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2) ** 0.5
                print(f"-- Lungime calculată pentru {frame_name}: {length:.3f}")
                return length

        print(f"⮽⮽ Nu s-a putut calcula lungimea pentru {frame_name}")
        return 0.0

    except Exception as e:
        print(f"⮽⮽ Eroare la calculul alternativ al lungimii pentru {frame_name}: {e}")
        return 0.0

def get_section_properties(frame_name):
    """Obține proprietățile secțiunii unei grinzi (simplificat)"""
    try:
        ret = sap_model.FrameObj.GetSection(frame_name)
        if ret[0] != 0:
            return "N/A"

        section_name = ret[1]

        # Încearcă să obții proprietăți pentru diferite tipuri de secțiuni
        ret = sap_model.PropFrame.GetRectangle(section_name)
        if ret[0] == 0:
            return f"Rect: {ret[4]}x{ret[5]}"  # Width x Height

        ret = sap_model.PropFrame.GetISection(section_name)
        if ret[0] == 0:
            return f"I-Sec: {ret[4]}x{ret[5]}"  # Depth x Width

        ret = sap_model.PropFrame.GetTube(section_name)
        if ret[0] == 0:
            return f"Tube: {ret[4]}x{ret[5]}"  # Depth x Width

        return section_name  # Return section name if no specific properties found

    except Exception as e:
        print(f"Eroare la obținerea proprietăților secțiunii pentru {frame_name}: {e}")
        return "N/A"

# Add these placeholder functions to etabs_api/operations.py

def get_joint_names(frame_name):
    """Placeholder function - returns joint names"""
    return {"i": "N/A", "j": "N/A"}

# def get_section_properties(frame_name):
#     """Placeholder function - returns section properties"""
#     return {
#         "section_type": "N/A", "depth": 0.0, "width": 0.0, "beff": 0.0,
#         "flange_thickness": 0.0, "ceff_top": 0.0, "ceff_bottom": 0.0
#     }

def get_steel_properties(frame_name):
    """Placeholder function - returns steel properties"""
    return {
        "longitudinal": {"fyk": 0.0, "fuk": 0.0, "fym": 0.0, "fum": 0.0},
        "transversal": {"fyk": 0.0, "fuk": 0.0, "fym": 0.0, "fum": 0.0}
    }

def get_design_results(frame_name):
    """Placeholder function - returns design results"""
    default_dict = {"i": 0.0, "mid": 0.0, "j": 0.0}
    return {
        "asl_req_gf": default_dict.copy(),
        "asl_req_gs": default_dict.copy(),
        "asl_eff": default_dict.copy(),
        "asl_eff_plate": default_dict.copy(),
        "asl_supp": default_dict.copy(),
        "med_gf": default_dict.copy(),
        "med_gs": default_dict.copy(),
        "ved_gf": default_dict.copy(),
        "ved_gs": default_dict.copy(),
        "ast_eff": default_dict.copy(),
        "ast_supp": default_dict.copy(),
        "ast_req_gf": default_dict.copy(),
        "ast_req_gs": default_dict.copy()
    }

def get_capacity_results(frame_name):
    """Placeholder function - returns capacity results"""
    default_dict = {"i": 0.0, "j": 0.0}
    return {
        "mrd_poz": default_dict.copy(),
        "mrd_neg": default_dict.copy(),
        "phi_max_neg": default_dict.copy(),
        "phi_cap_neg": default_dict.copy(),
        "phi_max_poz": default_dict.copy(),
        "phi_cap_poz": default_dict.copy()
    }

def get_column_connections(frame_name):
    """Placeholder function - returns column connection data"""
    default_release = {"Nx": 0.0, "V2": 0.0, "V3": 0.0, "T": 0.0, "M22": 0.0, "M33": 0.0}
    default_name = {"i": "N/A", "j": "N/A"}
    return {
        "top_column_mrd": {"i": 0.0, "j": 0.0},
        "bott_column_mrd": {"i": 0.0, "j": 0.0},
        "i_top_column_releases": default_release.copy(),
        "i_bott_column_releases": default_release.copy(),
        "j_top_column_releases": default_release.copy(),
        "j_bott_column_releases": default_release.copy(),
        "top_col_name": default_name.copy(),
        "bott_col_name": default_name.copy()
    }

def get_checks(frame_name):
    """Placeholder function - returns check results"""
    default_dict = {"i": "N/A", "mid": "N/A", "j": "N/A"}
    return {
        "node_check": {"i": "N/A", "j": "N/A"},
        "top_fiber_check": default_dict.copy(),
        "bott_fiber_check": default_dict.copy(),
        "shear_check": default_dict.copy()
    }