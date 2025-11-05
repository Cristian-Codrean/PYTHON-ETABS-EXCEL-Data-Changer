import math
# Importă funcția de conexiune
from etabs_api.connection import get_sap_model
# Get sap_model at module level for all functions to use
sap_model = get_sap_model()

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

        if ret[2] == 0:
            section_name = ret[0]
            print(f"-- Secțiune obținută pentru {frame_name}: {section_name}")
            return section_name
    except Exception as e:
        print(f"⮽⮽ Eroare la obținerea numelui secțiunii pentru {frame_name}: {e}")
        return "N/A"

def get_model_modifiers(name):
    SapModel = get_sap_model()
    modifiers, ret = SapModel.FrameObj.GetModifiers(name)
    if ret != 0:
        return None
    keys = ["A", "Av2", "Av3", "T", "M2", "M3", "M", "W"]
    return dict(zip(keys, modifiers))

def get_section_modifiers(sec_name):
    """Returneaza overwriteurile pentru sectiunea unui elem. de tip frame (input = frame unique name"""
    try:
        SapModel = get_sap_model()
        modifiers, ret = SapModel.PropFrame.GetModifiers(sec_name)
        if ret == 0:
            keys = ["A", "Av2", "Av3", "T", "M2", "M3", "M", "W"]
            return dict(zip(keys, modifiers))
    except Exception as e:
        print(f"⮽⮽ Eroare la obținerea modificatorilor de sectiune {sec_name}: {e}")
        return None

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

def get_material_overwrite(sect_name):
    """Returneaza material overwrite pt un elem. de tip frame (input = frame unique name"""
    try:
        SapModel = get_sap_model()
        material, ret = SapModel.FrameObj.GetMaterialOverwrite(sect_name)
        return material
    except Exception as e:
        print(f"⮽⮽ Eroare la extragerea overwriteului de material pt {sect_name} : {e}")
        return None

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


# def get_section_material(frame_name):
#     """Obține numele materialului pentru secțiunea unei grinzi"""
#     try:
#         # Obține numele secțiunii
#         section_name = sap_model.FrameObj.GetSection(frame_name)[0]
#         ret = sap_model.cPropFrame.GetMaterial(section_name)
#         if section_name != None and ret[1] == 0:
#             return ret[0]
#     except Exception as e:
#         print(f"⮽⮽ Eroare la obținerea materialului pentru {frame_name}: {e}")
#         return None
#
# # rett = get_section_material("GT 30x70")
# # print(rett)
# section_name = sap_model.cPropFrame.GetMaterial("GT 30X70")
# print(section_name)

def get_frame_length(frame_name):
    """Obține lungimea unei grinzi"""
    try:
        # Get start and end joints
        point_i, point_j = sap_model.FrameObj.GetPoints(frame_name)[0:2]
        # Get coordinates for each joint
        xi, yi, zi = sap_model.PointObj.GetCoordCartesian(point_i)[0:3]
        xj, yj, zj = sap_model.PointObj.GetCoordCartesian(point_j)[0:3]
        # Calculate length
        length = math.sqrt((xj - xi) ** 2 + (yj - yi) ** 2 + (zj - zi) ** 2)
        return length
    except Exception as e:
        print(f"⮽⮽ Eroare la obținerea lungimii pentru {frame_name}: {e}")
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

def get_i_joint_name(frame_name):
    """Returneaza numele jointului i (input = frame unique name)"""
    try:
        # Get start and end joints
        point_i, point_j = sap_model.FrameObj.GetPoints(frame_name)[0:2]
        return {"i":point_i}
    except Exception as e:
        print(f"""⮽⮽ Eroare la obținerea numelui jointului "i" pentru {frame_name}: {e}""")
        return {"i":None}

def get_j_joint_name(frame_name):
    """Returneaza numele jointului j (input = frame unique name)"""
    try:
        # Get start and end joints
        point_i, point_j = sap_model.FrameObj.GetPoints(frame_name)[0:2]
        return {"j":point_j}
    except Exception as e:
        print(f"""⮽⮽ Eroare la obținerea numelui jointului "j" pentru {frame_name}: {e}""")
        return {"j":None}


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