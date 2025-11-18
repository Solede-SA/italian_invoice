import frappe


def after_install():
    """Create default document types for e-invoicing after app installation"""
    create_default_document_types()


def create_default_document_types():
    """Create default Tipologia di documento e-Invoice records"""

    document_types = [
        {"codice": "TD01", "descrizione": "Fattura", "tipologia": "Fattura"},
        {
            "codice": "TD02",
            "descrizione": "Acconto/Anticipo su fattura",
            "tipologia": "Fattura",
        },
        {
            "codice": "TD03",
            "descrizione": "Acconto/Anticipo su parcella",
            "tipologia": "Fattura",
        },
        {"codice": "TD04", "descrizione": "Nota di credito", "tipologia": "Fattura"},
        {"codice": "TD05", "descrizione": "Nota di debito", "tipologia": "Fattura"},
        {"codice": "TD06", "descrizione": "Parcella", "tipologia": "Fattura"},
        {
            "codice": "TD16",
            "descrizione": "Integrazione fattura reverse charge interno",
            "tipologia": "Fattura",
        },
        {
            "codice": "TD17",
            "descrizione": "Integrazione/autofattura per acquisto servizi dall'estero",
            "tipologia": "AutoFattura",
        },
        {
            "codice": "TD18",
            "descrizione": "Integrazione per acquisto di beni intracomunitari",
            "tipologia": "AutoFattura",
        },
        {
            "codice": "TD19",
            "descrizione": "Integrazione/autofattura per acquisto di beni ex art.17 c.2 DPR 633/72",
            "tipologia": "AutoFattura",
        },
        {
            "codice": "TD20",
            "descrizione": "Autofattura per regolarizzazione e integrazione delle fatture (art.6 c.8 d.lgs. 471/97 o art.46 c.5 D.L. 331/93)",
            "tipologia": "AutoFattura",
        },
        {
            "codice": "TD21",
            "descrizione": "Autofattura per splafonamento",
            "tipologia": "AutoFattura",
        },
        {
            "codice": "TD22",
            "descrizione": "Estrazione beni da Deposito IVA",
            "tipologia": "Fattura",
        },
        {
            "codice": "TD23",
            "descrizione": "Estrazione beni da Deposito IVA con versamento dell'IVA",
            "tipologia": "Fattura",
        },
        {
            "codice": "TD24",
            "descrizione": "Fattura differita di cui all'art.21, comma 4, lett. a)",
            "tipologia": "Fattura",
        },
        {
            "codice": "TD25",
            "descrizione": "Fattura differita di cui all'art.21, comma 4, terzo periodo lett. b)",
            "tipologia": "Fattura",
        },
        {
            "codice": "TD26",
            "descrizione": "Cessione di beni ammortizzabili e per passaggi interni (ex art.36 DPR 633/72)",
            "tipologia": "Fattura",
        },
        {
            "codice": "TD27",
            "descrizione": "Fattura per autoconsumo o per cessioni gratuite senza rivalsa",
            "tipologia": "Fattura",
        },
    ]

    for doc_type in document_types:
        # Check if record already exists
        if not frappe.db.exists(
            "Tipologia di documento e-Invoice", {"codice": doc_type["codice"]}
        ):
            doc = frappe.get_doc(
                {
                    "doctype": "Tipologia di documento e-Invoice",
                    "codice": doc_type["codice"],
                    "descrizione": doc_type["descrizione"],
                    "tipologia": doc_type["tipologia"],
                }
            )
            doc.insert(ignore_permissions=True)
            frappe.db.commit()

    frappe.msgprint("Default document types created successfully", alert=True)
