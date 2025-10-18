import sys
import os
import traceback

# Adaugă directorul curent în Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Adaugă și folderul gui specific
gui_dir = os.path.join(current_dir, 'gui')
sys.path.insert(0, gui_dir)

print(f"Python path: {sys.path}")


def main():
    """Punctul principal de intrare în aplicație cu fereastra de start"""

    try:
        # Importă și afișează fereastra de start
        from gui.startup_window import StartupWindow
        print("✅ Fereastra de start importată cu succes")

        # Afișează fereastra de start și obține alegerea utilizatorului
        print("🚀 Pornire BEAM DESIGN BY CCO...")
        startup = StartupWindow()
        user_choice = startup.run()

        # Obține căile fișierelor (doar fișierul DB acum)
        file_paths = startup.get_file_paths()

        print(f"📋 Utilizatorul a selectat: {user_choice}")
        print(f"🗃️ Fișier DB: {file_paths['db_file']}")

        # Gestionează alegerea utilizatorului
        if user_choice == "main_app":
            # Deschide aplicația principală (crează bază de date nouă)
            from gui.main_window import DesignApp
            print("✅ Deschid aplicația principală...")
            app = DesignApp()
            app.run()

        elif user_choice == "alternative":
            # Deschide fereastra alternativă (conectare la bază de date existentă)
            from gui.alternative_window import AlternativeWindow
            print("✅ Deschid fereastra bază de date existentă...")
            alt_window = AlternativeWindow(
                db_file_path=file_paths["db_file"]
            )
            alt_window.run()

        elif user_choice == "exit":
            # Închide aplicația
            print("👋 Aplicație închisă de utilizator")
            sys.exit(0)

        else:
            # Fallback implicit
            print("⚠️ Selecție invalidă, închidere aplicație")
            sys.exit(0)

    except Exception as e:
        print(f"❌ Eroare aplicație: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()