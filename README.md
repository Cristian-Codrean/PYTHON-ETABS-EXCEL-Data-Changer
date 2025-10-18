## Nume Aplicație și Destinație
**BEAM DESIGN BY CCO** este o aplicație pentru proiectarea și analiza grinzilor structurale, integrată cu ETABS si Excel. Aplicația permite selectarea grinzilor din modele ETABS, gestionarea acestora în baze de date și introducerea acestora intr-un fisier EXCEL intr-o anumita ordine. Utilizatorul poate interactiona usor cu fisierul EXCEL dupa care poate injecta anumite valori in baza de date si in ETABS.

## Funcționalități Principale
- Conexiune cu ETABS pentru extragerea datelor structurale
- Selectare interactivă a grinzilor din modelul ETABS
- Creare bază de date SQLite cu proprietățile grinzilor
- Două scenarii de proiectare: Infrastructură și Suprastructură
- Generare fișiere Excel pentru rapoarte și analize
- Interfață grafică intuitivă
- Gestionare baze de date existente
- Injectarea valorilor in ETABS

## Biblioteci și Programe Utilizate
** Biblioteci Python:
- `tkinter` - Interfață grafică
- `sqlite3` - Baze de date
- `comtypes` - Conexiune cu ETABS API
- `os`, `sys` - Operațiuni sistem
- `shutil` - Operațiuni fișiere
- `xlwings` - Operațiuni cu fisiere EXCEL

## Programe Licențiate:
- **ETABS** - Software de analiză structurală (licență necesară)
- **Microsoft Excel** - Pentru rapoarte (licență necesară)

## Schema Aplicației
```text
BEAM-DESIGN-BY-CCO/
├── run.py
├── gui/
│ ├── main_window.py
│ ├── startup_window.py
│ ├── alternative_window.py
│ └── widgets.py
├── etabs_api/
│ ├── connection.py
│ └── operations.py
├── excel/
│ └── operations.py
└── db/
└── operations.py
```

## Instalare și Utilizare
### I Cerințe Preliminare:
1. Python 3.8 sau superior
2. ETABS instalat și licențiat
3. Microsoft Excel (pentru rapoarte)

### II Instalare:

### Clonează repository-ul
git clone https://github.com/Cristian-Codrean/PYTHON-ETABS-EXCEL-Data-Changer.git

#### Intră în directorul proiectului
cd BEAM-DESIGN-BY-CCO

### Instalează dependențele
pip install comtypes

### Utilizare:
Pornește ETABS și deschide un model structural
Rulează aplicația: python run.py
Selectează "Creează o bază de date nouă"
Alege fișierul bazei de date
În fereastra principală:
Selectează etajul dorit
Configurează scenariile (Infrastructură/Suprastructură)
Selectează grinzile în ETABS
Generează raportul Excel

### Drepturi de autor si disclaimer:
Drepturi de Autor:
© 2025 BEAM DESIGN BY CCO. Toate drepturile rezervate.

Disclaimer Important:
Această aplicație este un proiect independent și NU este afiliată, autorizată, sponsorizată sau aprobată în vreun fel de:

Computers and Structures, Inc. (CSI) - producătorii ETABS

Microsoft Corporation - producătorii Excel

ETABS este o marcă înregistrată a Computers and Structures, Inc.
Microsoft Excel este o marcă înregistrată a Microsoft Corporation.

Această aplicație este dezvoltată pentru scopuri educaționale și de cercetare. Utilizatorii sunt responsabili pentru obținerea licențelor necesare pentru ETABS și Microsoft Excel.

Dezvoltator:
Aplicația a fost dezvoltată pentru nevoi interne de proiectare structurală.

Pentru întrebări sau suport, contactați dezvoltatorul.