# -*- coding: utf-8 -*-
"""
Gestione fatture passive (fornitori) per Italian Invoice
Indipendente dal provider SDI utilizzato
"""

import frappe
import json
from frappe import _


def get_or_create_supplier(supplier_vat_id, invoice_data):
    """
    Controlla se esiste un fornitore con la partita IVA data, altrimenti lo crea

    Args:
        supplier_vat_id: Partita IVA del fornitore
        invoice_data: Dati fattura per recuperare info fornitore

    Returns:
        dict: Dati del fornitore (esistente o appena creato)
    """
    try:
        # Cerca fornitore esistente
        supplier = frappe.db.exists("Supplier", {"tax_id": supplier_vat_id})

        if supplier:
            # Ritorna i dati del fornitore esistente
            supplier_doc = frappe.get_doc("Supplier", supplier)
            return {
                "success": True,
                "supplier_name": supplier_doc.name,
                "supplier_data": supplier_doc.as_dict(),
                "is_new": False,
            }

        # Estrai dati fornitore dal JSON/XML
        supplier_data = extract_supplier_data(invoice_data)

        # Crea nuovo fornitore
        new_supplier = create_supplier(supplier_data, invoice_data.get("company"))

        supplier_doc = frappe.get_doc("Supplier", new_supplier)
        return {
            "success": True,
            "supplier_name": supplier_doc.name,
            "supplier_data": supplier_doc.as_dict(),
            "is_new": True,
        }

    except Exception as e:
        frappe.log_error(f"Errore in get_or_create_supplier: {str(e)}", "Italian Invoice Passive")
        return {"success": False, "error": str(e)}


def extract_supplier_data(invoice_data):
    """
    Estrae dati fornitore dal formato JSON/XML della fattura
    Supporta diversi formati di input
    """
    # Se è una stringa JSON, parsala
    if isinstance(invoice_data, str):
        invoice_data = json.loads(invoice_data)

    # Cerca il cedente_prestatore nei vari formati possibili
    if "data" in invoice_data and "invoice" in invoice_data["data"]:
        # Formato OpenAPI
        payload = invoice_data["data"]["invoice"]["payload"]
        return payload["fattura_elettronica_header"]["cedente_prestatore"]
    elif "fattura_elettronica_header" in invoice_data:
        # Formato diretto
        return invoice_data["fattura_elettronica_header"]["cedente_prestatore"]
    elif "cedente_prestatore" in invoice_data:
        # Formato semplificato
        return invoice_data["cedente_prestatore"]
    else:
        frappe.throw("Formato fattura non riconosciuto")


def create_supplier(supplier_data, company):
    """
    Crea un nuovo fornitore

    Args:
        supplier_data: Dizionario con i dati del fornitore
        company: Nome della company

    Returns:
        Il nome del documento del fornitore creato
    """
    supplier = frappe.get_doc({
        "doctype": "Supplier",
        "supplier_name": supplier_data["dati_anagrafici"]["anagrafica"].get(
            "denominazione",
            supplier_data["dati_anagrafici"]["anagrafica"].get("nome", "")
        ),
        "tax_id": supplier_data["dati_anagrafici"]["id_fiscale_iva"]["id_codice"],
        "supplier_group": get_default_supplier_group(),
        "supplier_type": "Company",
        "tax_country": supplier_data["dati_anagrafici"]["id_fiscale_iva"]["id_paese"],
        "is_frozen": 0,
        "status": "Passive",
    })

    # Aggiungi indirizzo se presente
    if "sede" in supplier_data:
        sede = supplier_data["sede"]
        supplier.address_line1 = sede.get("indirizzo", "")
        supplier.address_line2 = sede.get("numero_civico", "")
        supplier.city = sede.get("comune", "")
        supplier.state = sede.get("provincia", "")
        supplier.pincode = sede.get("cap", "")
        supplier.country = get_country_name(sede.get("nazione", "IT"))

    # Gestione contatti opzionali
    if supplier_data.get("contatti"):
        contatti = supplier_data["contatti"]
        if contatti.get("telefono"):
            supplier.phone = contatti["telefono"]
        if contatti.get("fax"):
            supplier.fax = contatti["fax"]
        if contatti.get("email"):
            supplier.email_id = contatti["email"]

    # Se ha codice fiscale persona fisica
    if supplier_data["dati_anagrafici"].get("codice_fiscale"):
        cf = supplier_data["dati_anagrafici"]["codice_fiscale"]
        if len(cf) != 11:  # Non è un CF temporaneo
            supplier.supplier_type = "Individual"
            supplier.fiscal_code = cf

    supplier.insert()
    supplier.save()
    return supplier.name


@frappe.whitelist()
def process_supplier_invoice(invoice_data, fattura_fornitori_sdi=None, item_mappings=None):
    """
    Processa una fattura fornitore e crea una Purchase Invoice

    Args:
        invoice_data: JSON string o dict con dati fattura
        fattura_fornitori_sdi: Nome doc Fattura Fornitori SDI (opzionale)
        item_mappings: Mapping articoli personalizzato (opzionale)

    Returns:
        Nome della Purchase Invoice creata
    """
    try:
        frappe.db.begin()

        # Parse dati se necessario
        if isinstance(invoice_data, str):
            invoice_data = json.loads(invoice_data)

        if item_mappings and isinstance(item_mappings, str):
            item_mappings = json.loads(item_mappings)

        # Estrai dati fattura
        payload = extract_invoice_payload(invoice_data)

        # Ottieni o crea fornitore
        supplier_vat = extract_supplier_vat(payload)
        supplier_result = get_or_create_supplier(supplier_vat, invoice_data)

        if not supplier_result["success"]:
            frappe.db.rollback()
            frappe.throw(f"Errore fornitore: {supplier_result['error']}")

        supplier = supplier_result["supplier_name"]

        # Determina company
        if fattura_fornitori_sdi:
            fattura_sdi_doc = frappe.get_doc("Fattura Fornitori SDI", fattura_fornitori_sdi)
            company = fattura_sdi_doc.company
        else:
            company = invoice_data.get("company", frappe.defaults.get_user_default("Company"))

        # Estrai dati documento
        doc_data = extract_document_data(payload)

        # Estrai righe fattura
        invoice_lines = extract_invoice_lines(payload)

        # Verifica se è una nota di credito
        tipo_documento = doc_data.get("tipo_documento")
        is_return = is_credit_note(tipo_documento)

        # Crea Purchase Invoice
        purchase_invoice = frappe.get_doc({
            "doctype": "Purchase Invoice",
            "supplier": supplier,
            "posting_date": doc_data["data"],
            "company": company,
            "currency": doc_data.get("divisa", "EUR"),
            "is_paid": 0,
            "is_return": 1 if is_return else 0,
            "status": "Draft",
            "from_xml": 1,
            "bill_no": doc_data["numero"],
            "bill_date": doc_data["data"],
            "items": prepare_invoice_items(
                invoice_lines,
                item_mappings,
                company,
                is_return
            ),
            "taxes": prepare_invoice_taxes(
                extract_tax_summary(payload),
                company,
                is_return
            ),
        })

        # Aggiungi riferimento file se presente
        if invoice_data.get("data", {}).get("invoice", {}).get("file_id"):
            purchase_invoice.scan_field = invoice_data["data"]["invoice"]["file_id"]

        purchase_invoice.insert()
        purchase_invoice.save()

        # Aggiorna Fattura Fornitori SDI se presente
        if fattura_fornitori_sdi:
            fattura_sdi_doc.fattura = purchase_invoice.name
            fattura_sdi_doc.stato = "Importata"
            fattura_sdi_doc.save()

        frappe.db.commit()
        return purchase_invoice.name

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Errore importazione: {str(e)}", "Italian Invoice Passive")
        frappe.throw(f"Errore importazione fattura: {str(e)}")


def extract_invoice_payload(invoice_data):
    """Estrae il payload dalla struttura dati"""
    if "data" in invoice_data and "invoice" in invoice_data["data"]:
        return invoice_data["data"]["invoice"]["payload"]
    elif "payload" in invoice_data:
        return invoice_data["payload"]
    elif "fattura_elettronica_body" in invoice_data:
        return invoice_data
    else:
        return invoice_data


def extract_supplier_vat(payload):
    """Estrae partita IVA fornitore dal payload"""
    if "fattura_elettronica_header" in payload:
        return payload["fattura_elettronica_header"]["cedente_prestatore"]["dati_anagrafici"]["id_fiscale_iva"]["id_codice"]
    elif "cedente_prestatore" in payload:
        return payload["cedente_prestatore"]["dati_anagrafici"]["id_fiscale_iva"]["id_codice"]
    else:
        frappe.throw("Impossibile trovare partita IVA fornitore")


def is_credit_note(tipo_documento):
    """Verifica se il tipo documento è una nota di credito"""
    return tipo_documento in ["TD04", "TD05", "TD08", "TD09"]


def invert_sign_for_credit_note(value, is_return):
    """Inverte il segno di un valore se è una nota di credito"""
    if not is_return:
        return value
    return -abs(float(value)) if value else 0


def link_item_to_purchase_document(item_dict, purchase_doc_name, purchase_doctype):
    """
    Collega una riga di Purchase Invoice a un Purchase Order o Purchase Receipt

    Args:
        item_dict: Dizionario della riga item
        purchase_doc_name: Nome del documento PO/PR
        purchase_doctype: "Purchase Order" o "Purchase Receipt"
    """
    if not purchase_doc_name or purchase_doctype not in ["Purchase Order", "Purchase Receipt"]:
        return

    # Campi da popolare in base al doctype
    if purchase_doctype == "Purchase Order":
        item_dict["purchase_order"] = purchase_doc_name
        # Trova la riga specifica nel PO che corrisponde all'item
        po_item = frappe.db.get_value(
            "Purchase Order Item",
            {
                "parent": purchase_doc_name,
                "item_code": item_dict.get("item_code"),
                "docstatus": 1
            },
            "name"
        )
        if po_item:
            item_dict["po_detail"] = po_item
    else:  # Purchase Receipt
        item_dict["purchase_receipt"] = purchase_doc_name
        # Trova la riga specifica nel PR che corrisponde all'item
        pr_item = frappe.db.get_value(
            "Purchase Receipt Item",
            {
                "parent": purchase_doc_name,
                "item_code": item_dict.get("item_code"),
                "docstatus": 1
            },
            "name"
        )
        if pr_item:
            item_dict["pr_detail"] = pr_item


@frappe.whitelist()
def get_open_purchase_documents_summary(supplier_vat):
    """
    Recupera sommario di PO/PR aperti per un fornitore (per alert nel form)

    Args:
        supplier_vat: Partita IVA fornitore

    Returns:
        dict: {"purchase_orders": [...], "purchase_receipts": [...]}
    """
    result = {
        "purchase_orders": [],
        "purchase_receipts": []
    }

    # Trova fornitore dalla partita IVA
    supplier_list = frappe.get_list("Supplier", filters={"tax_id": supplier_vat}, fields=["name"])
    if not supplier_list:
        return result

    supplier = supplier_list[0]["name"]

    # Purchase Orders aperti
    pos = frappe.db.sql("""
        SELECT DISTINCT
            parent.name,
            parent.transaction_date,
            parent.grand_total
        FROM `tabPurchase Order` parent
        INNER JOIN `tabPurchase Order Item` item ON item.parent = parent.name
        WHERE parent.supplier = %(supplier)s
        AND parent.docstatus = 1
        AND parent.status NOT IN ('Closed', 'Completed', 'Cancelled')
        AND (item.billed_amt < item.amount OR item.billed_amt IS NULL)
        ORDER BY parent.transaction_date DESC
        LIMIT 10
    """, {"supplier": supplier}, as_dict=True)
    result["purchase_orders"] = pos

    # Purchase Receipts aperti
    prs = frappe.db.sql("""
        SELECT DISTINCT
            parent.name,
            parent.posting_date,
            parent.grand_total
        FROM `tabPurchase Receipt` parent
        INNER JOIN `tabPurchase Receipt Item` item ON item.parent = parent.name
        WHERE parent.supplier = %(supplier)s
        AND parent.docstatus = 1
        AND parent.status NOT IN ('Closed', 'Completed', 'Cancelled')
        AND (item.billed_amt < item.amount OR item.billed_amt IS NULL)
        ORDER BY parent.posting_date DESC
        LIMIT 10
    """, {"supplier": supplier}, as_dict=True)
    result["purchase_receipts"] = prs

    return result


@frappe.whitelist()
def create_purchase_invoice_from_document(doc_name, doctype, bill_no, fattura_sdi_name):
    """
    Crea una Purchase Invoice da un Purchase Order o Purchase Receipt

    Args:
        doc_name: Nome del PO/PR
        doctype: "Purchase Order" o "Purchase Receipt"
        bill_no: Numero fattura da impostare
        fattura_sdi_name: Nome della Fattura Fornitori SDI

    Returns:
        Nome della Purchase Invoice creata
    """
    if doctype == "Purchase Order":
        from erpnext.buying.doctype.purchase_order.purchase_order import make_purchase_invoice
        pi = make_purchase_invoice(doc_name)
    elif doctype == "Purchase Receipt":
        from erpnext.stock.doctype.purchase_receipt.purchase_receipt import make_purchase_invoice
        pi = make_purchase_invoice(doc_name)
    else:
        frappe.throw(f"Doctype non supportato: {doctype}")

    # Imposta bill_no
    pi.bill_no = bill_no

    # Estrai data fattura dalla Fattura Fornitori SDI
    fattura_sdi = frappe.get_doc("Fattura Fornitori SDI", fattura_sdi_name)
    bill_date = _get_bill_date_from_fattura_sdi(fattura_sdi)
    if bill_date:
        pi.bill_date = bill_date

    # Salva (ma non submit)
    pi.insert()
    frappe.db.commit()

    return pi.name


def _get_bill_date_from_fattura_sdi(fattura_sdi):
    """Estrae la data fattura dai dati JSON della Fattura Fornitori SDI"""
    from italian_invoice.italian_invoice.doctype.fattura_fornitori_sdi.fattura_fornitori_sdi import _get_fattura_body_from_json

    body = _get_fattura_body_from_json(fattura_sdi.dati_fattura)
    if not body:
        return None

    return body.get("dati_generali", {}).get("dati_generali_documento", {}).get("data")


@frappe.whitelist()
def prepare_purchase_document_for_invoice(doc_name, doctype, bill_no):
    """
    Popola bill_no in un PO/PR per prepararlo alla creazione della PI

    Args:
        doc_name: Nome del PO/PR
        doctype: "Purchase Order" o "Purchase Receipt"
        bill_no: Numero fattura da settare

    Returns:
        dict: URL del documento
    """
    if doctype not in ["Purchase Order", "Purchase Receipt"]:
        frappe.throw("Doctype non valido")

    # Il bill_no verrà copiato automaticamente quando si crea la PI dal PO/PR
    # Non serve modificare il PO/PR qui, lo gestiamo nella creazione PI

    return {
        "success": True,
        "url": f"/app/{doctype.lower().replace(' ', '-')}/{doc_name}"
    }


def find_fattura_sdi_by_bill_no(bill_no, supplier=None):
    """
    Trova una Fattura Fornitori SDI dal numero fattura (DRY)

    Args:
        bill_no: Numero fattura
        supplier: Partita IVA fornitore (opzionale)

    Returns:
        Nome della Fattura Fornitori SDI o None
    """
    filters = {"dati_fattura": ["like", f'%"numero": "{bill_no}"%']}
    if supplier:
        filters["partita_iva_fornitore"] = supplier

    fatture = frappe.get_list(
        "Fattura Fornitori SDI",
        filters=filters,
        fields=["name"],
        limit=1
    )

    return fatture[0]["name"] if fatture else None


def link_purchase_invoice_to_fattura_sdi(purchase_invoice_name, fattura_sdi_name):
    """
    Collega una Purchase Invoice a una Fattura SDI (DRY)

    Args:
        purchase_invoice_name: Nome Purchase Invoice
        fattura_sdi_name: Nome Fattura Fornitori SDI
    """
    fattura_sdi = frappe.get_doc("Fattura Fornitori SDI", fattura_sdi_name)
    fattura_sdi.fattura = purchase_invoice_name
    fattura_sdi.stato = "Importata"
    fattura_sdi.save(ignore_permissions=True)
    frappe.db.commit()


def unlink_purchase_invoice_from_fattura_sdi(purchase_invoice_name):
    """
    Scollega una Purchase Invoice da Fattura SDI (DRY)

    Args:
        purchase_invoice_name: Nome Purchase Invoice
    """
    fatture = frappe.get_list(
        "Fattura Fornitori SDI",
        filters={"fattura": purchase_invoice_name},
        fields=["name"]
    )

    for fattura in fatture:
        doc = frappe.get_doc("Fattura Fornitori SDI", fattura["name"])
        doc.fattura = None
        doc.stato = "Da importare"
        doc.save(ignore_permissions=True)

    frappe.db.commit()


def on_purchase_invoice_submit(doc, method):
    """
    Hook chiamato quando una Purchase Invoice viene submitted
    Collega automaticamente alla Fattura Fornitori SDI se esiste

    Args:
        doc: Purchase Invoice document
        method: Nome del metodo (on_submit)
    """
    if not doc.bill_no:
        return

    # Ottieni partita IVA del fornitore
    supplier_tax_id = frappe.db.get_value("Supplier", doc.supplier, "tax_id")
    if not supplier_tax_id:
        return

    # Cerca Fattura SDI con questo numero per questo fornitore
    fattura_sdi_name = find_fattura_sdi_by_bill_no(doc.bill_no, supplier_tax_id)

    if fattura_sdi_name:
        link_purchase_invoice_to_fattura_sdi(doc.name, fattura_sdi_name)
        frappe.msgprint(
            f"Fattura collegata automaticamente a Fattura Fornitori SDI: {fattura_sdi_name}",
            alert=True,
            indicator="green"
        )


def on_purchase_invoice_cancel(doc, method):
    """
    Hook chiamato quando una Purchase Invoice viene cancellata
    Scollega dalla Fattura Fornitori SDI

    Args:
        doc: Purchase Invoice document
        method: Nome del metodo (on_cancel)
    """
    unlink_purchase_invoice_from_fattura_sdi(doc.name)


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_open_purchase_documents(doctype, txt, searchfield, start, page_len, filters):
    """
    Query function per Link field - recupera PO/PR aperti per un fornitore

    Args:
        doctype: Doctype target (viene passato automaticamente da Frappe)
        txt: Testo di ricerca
        searchfield: Campo di ricerca
        start: Offset per paginazione
        page_len: Numero risultati per pagina
        filters: Filtri aggiuntivi (supplier, doctype)

    Returns:
        Lista di tuple [[name, details], ...]
    """
    target_doctype = filters.get("doctype")
    supplier = filters.get("supplier")

    if not target_doctype or target_doctype not in ["Purchase Order", "Purchase Receipt"]:
        return []

    # Campi diversi per PO e PR (DRY)
    date_field = "transaction_date" if target_doctype == "Purchase Order" else "posting_date"
    item_doctype = f"{target_doctype} Item"

    # Query per trovare documenti con righe non completamente fatturate
    return frappe.db.sql("""
        SELECT DISTINCT
            parent.name,
            CONCAT(parent.name, ' (', DATE_FORMAT(parent.{date_field}, '%%d/%%m/%%Y'), ' - ',
                   FORMAT(parent.grand_total, 2), ' EUR)')
        FROM `tab{doctype}` parent
        INNER JOIN `tab{item_doctype}` item ON item.parent = parent.name
        WHERE parent.supplier = %(supplier)s
        AND parent.docstatus = 1
        AND parent.status NOT IN ('Closed', 'Completed', 'Cancelled')
        AND (item.billed_amt < item.amount OR item.billed_amt IS NULL)
        AND parent.name LIKE %(txt)s
        ORDER BY parent.{date_field} DESC
        LIMIT %(start)s, %(page_len)s
    """.format(doctype=target_doctype, item_doctype=item_doctype, date_field=date_field), {
        "supplier": supplier,
        "txt": f"%{txt}%",
        "start": start,
        "page_len": page_len
    })


def extract_document_data(payload):
    """Estrae dati generali documento"""
    if "fattura_elettronica_body" in payload:
        return payload["fattura_elettronica_body"][0]["dati_generali"]["dati_generali_documento"]
    elif "dati_generali" in payload:
        return payload["dati_generali"]["dati_generali_documento"]
    else:
        return payload.get("dati_generali_documento", {})


def extract_invoice_lines(payload):
    """Estrae righe fattura"""
    if "fattura_elettronica_body" in payload:
        return payload["fattura_elettronica_body"][0]["dati_beni_servizi"]["dettaglio_linee"]
    elif "dati_beni_servizi" in payload:
        return payload["dati_beni_servizi"]["dettaglio_linee"]
    else:
        return payload.get("dettaglio_linee", [])


def extract_tax_summary(payload):
    """Estrae riepilogo IVA"""
    if "fattura_elettronica_body" in payload:
        return payload["fattura_elettronica_body"][0]["dati_beni_servizi"]["dati_riepilogo"]
    elif "dati_beni_servizi" in payload:
        return payload["dati_beni_servizi"]["dati_riepilogo"]
    else:
        return payload.get("dati_riepilogo", [])


def calculate_total_discount(invoice_lines):
    """
    Calcola lo sconto totale dalle righe con importo negativo

    Args:
        invoice_lines: Lista righe fattura

    Returns:
        float: Totale sconti (valore positivo)
    """
    total_discount = 0.0

    for line in invoice_lines:
        try:
            prezzo_totale = float(line.get("prezzo_totale", 0))
            if prezzo_totale < 0:
                total_discount += abs(prezzo_totale)
        except (ValueError, TypeError):
            continue

    return total_discount


def prepare_invoice_items(invoice_lines, item_mappings=None, company=None, is_return=False):
    """
    Prepara le righe della fattura di acquisto

    Args:
        invoice_lines: Lista di righe della fattura
        item_mappings: Mapping personalizzato articoli
        company: Nome della società
        is_return: True se è una nota di credito (inverte i segni)

    Returns:
        Lista di dizionari per le righe Purchase Invoice
    """
    items = []

    for line in invoice_lines:
        # Verifica validità riga
        if not is_valid_invoice_line(line):
            continue

        # Calcola quantità
        quantity = get_line_quantity(line)
        rate = float(line.get("prezzo_unitario", 0))

        # Per note di credito, inverti il segno della quantità
        quantity = invert_sign_for_credit_note(quantity, is_return)
        if is_return:
            rate = abs(rate)

        if item_mappings and str(line.get("numero_linea")) in item_mappings:
            # Usa mapping personalizzato
            mapping = item_mappings[str(line["numero_linea"])]
            uom = frappe.db.get_value("Item", mapping["item_code"], "stock_uom") or "Nr"

            item_dict = {
                "item_code": mapping["item_code"],
                "description": mapping.get("description", line.get("descrizione", "")),
                "qty": quantity,
                "rate": rate,
                "expense_account": mapping.get("account"),
                "uom": uom,
                "price_list_rate": rate,
                "tax_rate": line.get("aliquota_iva", 0),
                "tax_nature": line.get("natura"),
            }

            # Collega a Purchase Order se specificato
            if mapping.get("purchase_order"):
                link_item_to_purchase_document(item_dict, mapping["purchase_order"], "Purchase Order")

            # Collega a Purchase Receipt se specificato
            if mapping.get("purchase_receipt"):
                link_item_to_purchase_document(item_dict, mapping["purchase_receipt"], "Purchase Receipt")

            items.append(item_dict)
        else:
            # Crea riga automatica
            items.append({
                "item_code": get_or_create_item_code(line),
                "description": line.get("descrizione", ""),
                "qty": quantity,
                "rate": rate,
                "uom": get_default_uom(),
                "price_list_rate": rate,
                "tax_rate": line.get("aliquota_iva", 0),
                "tax_nature": line.get("natura"),
            })

    return items


def is_valid_invoice_line(line):
    """Verifica se una riga fattura è valida per l'importazione"""
    return line.get("prezzo_totale") is not None or line.get("quantita") is not None


def get_line_quantity(line):
    """Ottiene la quantità per una riga, con default a 1 per servizi"""
    try:
        if line.get("quantita") and float(line.get("quantita", 0)) > 0:
            return float(line["quantita"])
        elif line.get("prezzo_totale") and float(line.get("prezzo_totale", 0)) > 0:
            # Servizio senza quantità
            return 1
    except (ValueError, TypeError):
        pass
    return 1


def prepare_invoice_taxes(invoice_summary, company, is_return=False):
    """
    Prepara le tasse per la fattura di acquisto

    Args:
        invoice_summary: Lista di riepiloghi IVA
        company: Nome della società
        is_return: True se è una nota di credito (inverte i segni)

    Returns:
        Lista di dizionari per le tasse
    """
    taxes = []

    for summary in invoice_summary:
        tax_rate = float(summary.get("aliquota_iva", 0))
        tax_account = get_tax_account(tax_rate, company)

        tax_amount = invert_sign_for_credit_note(summary.get("imposta", 0), is_return)
        total = invert_sign_for_credit_note(summary.get("imponibile_importo", 0), is_return)

        taxes.append({
            "charge_type": "Actual",
            "account_head": tax_account,
            "tax_amount": tax_amount,
            "rate": tax_rate,
            "description": f"IVA {tax_rate}%",
            "total": total,
        })

    return taxes


def get_tax_account(tax_rate, company):
    """
    Restituisce l'account IVA in base all'aliquota

    Args:
        tax_rate: Aliquota IVA
        company: Nome company

    Returns:
        Nome dell'account IVA
    """
    tax_rate = round(float(tax_rate), 2)

    # Cerca account con quella tax_rate
    if tax_rate > 0:
        tax_account = frappe.db.get_all(
            "Account",
            {"company": company, "tax_rate": tax_rate, "account_type": "Tax"},
            ["name"],
            limit=1
        )
        if tax_account:
            return tax_account[0]["name"]

    # Fallback all'account IVA default della company
    default_tax = frappe.db.get_value(
        "Company",
        company,
        "default_income_account"
    )

    if default_tax:
        return default_tax

    frappe.throw(f"Account IVA non trovato per aliquota {tax_rate}% in {company}")


def get_or_create_item_code(line):
    """
    Ottiene o crea un item code per la riga

    Args:
        line: Riga fattura

    Returns:
        Item code
    """
    # Cerca per descrizione
    descrizione = line.get("descrizione", "")

    if descrizione:
        item_code = frappe.db.get_value("Item", {"item_name": descrizione}, "name")
        if item_code:
            return item_code

    # Usa item generico di default
    return get_default_item_code()


def get_default_supplier_group():
    """Restituisce il gruppo fornitori di default"""
    # Prima prova a prendere il default dal sistema
    default = frappe.db.get_single_value("Buying Settings", "supplier_group")
    if default:
        return default

    # Altrimenti usa "All Supplier Groups" che esiste sempre
    return "All Supplier Groups"


def get_default_uom():
    """Restituisce l'UOM di default"""
    default = frappe.db.get_single_value("Stock Settings", "stock_uom")
    return default or "Nos"


def get_default_item_code():
    """Restituisce l'item code di default per articoli generici"""
    # Verifica se esiste un item generico
    if frappe.db.exists("Item", "Servizi Generici"):
        return "Servizi Generici"

    # Altrimenti prendine uno qualsiasi di tipo servizio
    service_item = frappe.db.get_value(
        "Item",
        {"is_stock_item": 0, "disabled": 0},
        "name"
    )

    if service_item:
        return service_item

    frappe.throw("Nessun articolo di tipo servizio trovato. Creare almeno un articolo generico.")


def get_country_name(country_code):
    """
    Converte codice paese in nome

    Args:
        country_code: Codice paese a 2 lettere

    Returns:
        Nome paese completo
    """
    if not country_code:
        return "Italy"  # Default

    country_code = country_code.upper()

    # Mappa i codici speciali
    if country_code == "UK":
        country_code = "GB"

    # Cerca nel database di ERPNext
    country = frappe.db.get_value("Country", {"code": country_code}, "name")

    if country:
        return country

    # Fallback a mapping statico per i più comuni
    country_mapping = {
        "IT": "Italy",
        "DE": "Germany",
        "FR": "France",
        "ES": "Spain",
        "GB": "United Kingdom",
        "US": "United States",
        "CH": "Switzerland",
        "AT": "Austria",
    }

    return country_mapping.get(country_code, "Italy")


@frappe.whitelist()
def check_document_type(document_type_code):
    """
    Verifica il tipo di documento e avvisa se è un'autofattura

    Args:
        document_type_code: Codice tipo documento (es. "TD01")

    Returns:
        True se è un'autofattura, False altrimenti
    """
    try:
        doc_type = frappe.get_doc(
            "Tipologia di documento e-Invoice", document_type_code
        )
        if doc_type.tipologia == "AutoFattura":
            frappe.msgprint(
                f"Attenzione: Il documento {document_type_code} è un'autofattura",
                title="Autofattura rilevata",
                indicator="orange"
            )
            return True
    except frappe.DoesNotExistError:
        frappe.log_error(
            f"Tipo documento {document_type_code} non trovato",
            "Italian Invoice Passive"
        )

    return False