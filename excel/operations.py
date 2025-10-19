import os
import shutil


def copy_excel_file(source_excel_path, destination_excel_path):
    """Creează o copie a unui fișier Excel.
    Args:
        source_excel_path (str): Calea către fișierul Excel sursă
        destination_excel_path (str): Calea unde se salvează copia
    Returns:
        bool: True dacă copierea a reușit, False dacă a eșuat
    """
    try:
        print(f"-- Copiez fișier Excel...")
        print(f"-- Sursa: {source_excel_path}")
        print(f"-- Destinație: {destination_excel_path}")

        # Verifică dacă fișierul sursă există
        if not os.path.exists(source_excel_path):
            print(f"⮽⮽ Fișierul sursă nu există: {source_excel_path}")
            return False

        # Creează directorul dacă nu există
        destination_dir = os.path.dirname(destination_excel_path)
        if not os.path.exists(destination_dir):
            os.makedirs(destination_dir)
            print(f"-- Am creat directorul: {destination_dir}")

        # Copiază fișierul
        shutil.copy2(source_excel_path, destination_excel_path)

        # Verifică dacă copia a fost creată
        if os.path.exists(destination_excel_path):
            print(f"✓✓ Fișier Excel copiat cu succes: {destination_excel_path}")
            return True
        else:
            print(f"⮽⮽ Eroare la copiere")
            return False

    except Exception as e:
        print(f"⮽⮽ Eroare la copierea fișierului Excel: {e}")
        return False