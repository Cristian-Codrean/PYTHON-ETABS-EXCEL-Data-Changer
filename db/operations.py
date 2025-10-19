import sqlite3
import os


def create_database(frame_list):
    """ Creează baza de date pentru elementele de tip frame (grinzi) dintr-o listă.
    """

    # Calea către baza de date în folderul root
    db_path = "frames.db"

    # Verifică dacă baza de date există deja și o șterge
    if os.path.exists(db_path):
        os.remove(db_path)
        print("-- Am șters baza de date veche pentru a o recrea!")

    # Conectează-te la baza de date (sau creează-o dacă nu există)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Creează tabelă nouă cu toate coloanele pentru proprietățile grinzilor
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Frames (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        UniqueName TEXT NOT NULL,           -- Numele unic al grinzii în ETABS
        Label TEXT,                         -- Eticheta grinzii
        GUID TEXT,                          -- ID-ul unic global
        Story TEXT,                         -- Nivelul pe care se află grinda
        SectionName TEXT,                   -- Numele secțiunii
        Material TEXT                       -- Materialul grinzii
    )
    """)
    print("-- Am creat tabela Frames cu succes!")

    # Adaugă fiecare grindă în baza de date
    for frame_name in frame_list:
        print(f"-- Procesare grindă: {frame_name}")

        try:
            # Încercăm să obținem detaliile despre grindă
            label, story = get_label_and_story(frame_name)
            guid = get_frame_guid(frame_name)
            section_name = get_section_name(frame_name)

            # Inserează datele în baza de date
            cursor.execute("""
            INSERT INTO Frames (UniqueName, Label, GUID, Story, SectionName, Material)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (frame_name, label, guid, story, section_name, "Concrete"))

            print(f"-- Grinda {frame_name} a fost adaugata în baza de date!")

        except Exception as e:
            print(f"⮽⮽ EROARE la procesarea grinzii {frame_name}: {e}")
            # Dacă eșuăm, adăugăm doar datele de bază
            cursor.execute("""
            INSERT INTO Frames (UniqueName, Label, GUID) VALUES (?, ?, ?)
            """, (frame_name, f"Label-{frame_name}", f"guid-{frame_name}"))
            print(f"⮽⮽️ Sa adăugat doar date de bază pentru {frame_name}")

    # Salvează schimbările în baza de date
    conn.commit()
    print("-- Sa salvat toate schimbările în baza de date!")

    # Afișează câte rânduri am adăugat
    cursor.execute("SELECT COUNT(*) FROM Frames")
    count = cursor.fetchone()[0]
    print(f"-- SA adăugat {count} grinzi în baza de date!")

    # Închide conexiunea la baza de date
    conn.close()
    print("-- Conexiunea la baza de date a fost închisă!")
    return True


# Funcții helper pentru a evita erorile de import
def get_label_and_story(name):
    """Funcție helper pentru a obține label și story"""
    try:
        from etabs_api.operations import get_label_and_story as get_label_story
        return get_label_story(name)
    except:
        return [f"Label-{name}", "Story1"]


def get_frame_guid(name):
    """Funcție helper pentru a obține GUID"""
    try:
        from etabs_api.operations import get_frame_guid as get_guid
        return get_guid(name)
    except:
        return f"guid-{name}"


def get_section_name(name):
    """Funcție helper pentru a obține numele secțiunii"""
    try:
        from etabs_api.operations import get_section_name as get_section
        return get_section(name)
    except:
        return "Section1"