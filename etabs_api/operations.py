import math

# Importă funcția de conexiune
from etabs_api.connection import get_sap_model


def hide_specific_frames(frame_list):
    """Ascunde frame-urile specificate folosind funcția Make Objects Invisible din ETABS"""
    sap_model = get_sap_model()
    if not frame_list:
        print("Nu sunt frame-uri de ascuns")
        return True

    print(f"Încerc să ascund {len(frame_list)} frame-uri: {frame_list}")

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
                    print(f"Avertisment: Nu am putut selecta frame-ul {frame_name}, eroare: {ret}")
            except Exception as e:
                print(f"Eroare la selectarea frame-ului {frame_name}: {e}")

        print(f"Selectat {selected_count} frame-uri pentru ascundere")

        if selected_count > 0:
            # Metoda 1: Încearcă să folosească interfața Display pentru a ascunde obiecte
            try:
                # Obține toate obiectele selectate și le ascunde folosind opțiuni de display
                ret = sap_model.Display.SetObjectSelected(False)  # Deselectează toate
                if ret == 0:
                    print(f"Ascuns cu succes {selected_count} frame-uri")
                    return True
                else:
                    print(f"Display.SetObjectSelected a returnat eroare: {ret}")
            except Exception as e:
                print(f"Metoda Display a eșuat: {e}")

        # Șterge selecția indiferent de rezultat
        sap_model.SelectObj.ClearSelection()
        return selected_count > 0

    except Exception as e:
        print(f"Eroare în hide_specific_frames: {e}")
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
            print("Toate frame-urile ar trebui să fie vizibile acum")
            # Deselectează după ce le face vizibile
            sap_model.SelectObj.ClearSelection()
            return True
        else:
            print(f"Display.SetObjectSelected a returnat eroare: {ret}")
            return False
    except Exception as e:
        print(f"Eroare la afișarea frame-urilor: {e}")
        return False


def get_story_names():
    """Returnează numele nivelurilor într-o listă"""
    sap_model = get_sap_model()
    try:
        # Apel direct fără variabile intermediare
        return list(sap_model.Story.GetStories()[1])
    except Exception as e:
        print(f"Eroare la obținerea numelor etajelor: {e}")
        return []


def get_comb_names():
    """Returnează numele tuturor combinațiilor într-o listă"""
    sap_model = get_sap_model()
    try:
        number_names = 0
        my_name = []
        return list(sap_model.RespCombo.GetNameList(number_names, my_name)[1])
    except Exception as e:
        print(f"Eroare la obținerea numelor combinațiilor: {e}")
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
        print(f"Eroare la obținerea frame-urilor selectate live: {e}")
        return []


def clear_frame_selection():
    """Deselectează toate frame-urile din model"""
    sap_model = get_sap_model()
    try:
        sap_model.SelectObj.ClearSelection()
        return True
    except Exception as e:
        print(f"Eroare la ștergerea selecției frame-urilor: {e}")
        return False


def get_frame_guid(frame_name):
    """Returnează GUID pentru elementul de tip frame introdus (Unique Name)"""
    sap_model = get_sap_model()
    try:
        result = sap_model.FrameObj.GetGUID(frame_name)
        return result[0] if result else None
    except Exception as e:
        print(f"Eroare la obținerea GUID frame: {e}")
        return None


def get_label_and_story(name):
    """Returnează label și story de la inputul (unique name) ca o listă de stringuri"""
    sap_model = get_sap_model()
    try:
        result = sap_model.FrameObj.GetLabelFromName(name)
        return result[0:2] if result else [None, None]
    except Exception as e:
        print(f"Eroare la obținerea label și story: {e}")
        return [None, None]


def get_section_name(name):
    """Returnează numele secțiunii pentru un frame"""
    SapModel = get_sap_model()
    result = SapModel.FrameObj.GetSection(name)
    return result[1] if result and result[0] == 0 else None


def get_section_name(name):
    SapModel = get_sap_model()
    result = SapModel.FrameObj.GetSection(name)
    return result[1] if result and result[0] == 0 else None


def get_prop_modifiers(name):
    SapModel = get_sap_model()
    result = SapModel.FrameObj.GetModifiers(name)
    if not result or result[0] != 0:
        return None
    keys = ["Area", "As2", "As3", "Torsion", "I22", "I33", "Mass", "Weight"]
    return dict(zip(keys, result[1]))

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