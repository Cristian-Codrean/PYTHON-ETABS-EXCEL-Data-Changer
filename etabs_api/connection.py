import comtypes.client

def connect_to_etabs():
    """Conexiune simplă directă la ETABS"""
    try:
        # Creează obiect helper
        helper = comtypes.client.CreateObject('ETABSv1.Helper')
        helper = helper.QueryInterface(comtypes.gen.ETABSv1.cHelper)

        # Obține obiectul ETABS
        myETABSObject = helper.GetObject("CSI.ETABS.API.ETABSObject")

        if myETABSObject is None:
            raise Exception("⮽⮽ Nu s-a găsit nicio instanță ETABS rulează")

        # Obține SapModel
        SapModel = myETABSObject.SapModel

        print("✓✓ Conectat la instanța ETABS care rulează")
        return SapModel

    except Exception as e:
        print(f"⮽⮽ Conexiune ETABS eșuată: {e}")
        raise

# Variabilă globală pentru a stoca conexiunea
_sap_model = None

def get_sap_model():
    """Obține SapModel - se conectează dacă nu este deja conectat"""
    global _sap_model
    if _sap_model is None:
        _sap_model = connect_to_etabs()
    return _sap_model

if __name__ == "__main__":
    sap_model = connect_to_etabs()
    sap_model.SetModelIsLocked(False)

