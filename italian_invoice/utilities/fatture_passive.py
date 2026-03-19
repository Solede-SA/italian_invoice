"""
Gestione fatture passive (fornitori) per Italian Invoice
Indipendente dal provider SDI utilizzato
"""

import json
from difflib import SequenceMatcher

import frappe


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
	Usa la funzione centralizzata per gestire diversi formati
	"""
	from italian_invoice.utilities.fatture import get_cedente_prestatore_from_json

	return get_cedente_prestatore_from_json(invoice_data)


def create_supplier(supplier_data, company):
	"""
	Crea un nuovo fornitore

	Args:
	    supplier_data: Dizionario con i dati del fornitore
	    company: Nome della company

	Returns:
	    Il nome del documento del fornitore creato
	"""
	supplier = frappe.get_doc(
		{
			"doctype": "Supplier",
			"supplier_name": supplier_data["dati_anagrafici"]["anagrafica"].get(
				"denominazione",
				supplier_data["dati_anagrafici"]["anagrafica"].get("nome", ""),
			),
			"tax_id": supplier_data["dati_anagrafici"]["id_fiscale_iva"]["id_codice"],
			"supplier_group": get_default_supplier_group(),
			"supplier_type": "Company",
			"tax_country": supplier_data["dati_anagrafici"]["id_fiscale_iva"]["id_paese"],
			"is_frozen": 0,
			"status": "Passive",
		}
	)

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
	return supplier.name


@frappe.whitelist()
def get_items_by_supplier(doctype, txt, searchfield, start, page_len, filters):
	"""Query per ottenere tutti gli Item, prioritizzando quelli associati al fornitore
	tramite Item Supplier o Item Default."""
	supplier = filters.get("default_supplier")
	if not supplier:
		return frappe.get_list(
			"Item",
			filters={"name": ["like", f"%{txt}%"]},
			fields=["name", "item_name"],
			as_list=True,
			limit_start=start,
			limit_page_length=page_len,
		)

	return frappe.db.sql(
		"""
		SELECT i.name, i.item_name
		FROM `tabItem` i
		LEFT JOIN `tabItem Supplier` isup ON isup.parent = i.name AND isup.supplier = %(supplier)s
		LEFT JOIN `tabItem Default` idef ON idef.parent = i.name AND idef.default_supplier = %(supplier)s
		WHERE (i.name LIKE %(txt)s OR i.item_name LIKE %(txt)s)
		AND i.disabled = 0
		GROUP BY i.name
		ORDER BY (isup.name IS NOT NULL OR idef.name IS NOT NULL) DESC, i.name
		LIMIT %(start)s, %(page_len)s
		""",
		{"supplier": supplier, "txt": f"%{txt}%", "start": int(start), "page_len": int(page_len)},
	)


@frappe.whitelist()
def save_item_supplier_mappings(mappings, supplier_name):
	"""
	Salva le associazioni fornitore-articolo nella child table Item Supplier.
	Chiamata dopo che l'utente conferma il dialog con 'Ricorda associazione'.
	"""
	if isinstance(mappings, str):
		mappings = json.loads(mappings)

	# Filtra mappings validi e raccogli item_code unici
	valid = [(m["item_code"], m["supplier_part_no"]) for m in mappings if m.get("item_code") and m.get("supplier_part_no")]
	if not valid:
		return

	item_codes = list(set(ic for ic, _ in valid))

	# Bulk check: trova tutte le associazioni già esistenti per questi item e fornitore
	existing_keys = set()
	for row in frappe.get_all(
		"Item Supplier",
		filters={"parent": ["in", item_codes], "supplier": supplier_name},
		fields=["parent", "supplier_part_no"],
	):
		existing_keys.add((row["parent"], (row["supplier_part_no"] or "").strip().lower()))

	# Raggruppa per item_code per caricare ogni Item una volta sola
	from collections import defaultdict
	items_to_update = defaultdict(list)
	for item_code, part_no in valid:
		if (item_code, part_no.strip().lower()) not in existing_keys:
			items_to_update[item_code].append(part_no)

	for item_code, part_nos in items_to_update.items():
		item_doc = frappe.get_doc("Item", item_code)
		for part_no in part_nos:
			item_doc.append("supplier_items", {
				"supplier": supplier_name,
				"supplier_part_no": part_no,
			})
		item_doc.save(ignore_permissions=True)


def _get_supplier_items(supplier_name):
	"""Ottieni tutti gli Item associati al fornitore (via Item Supplier + Item Default)."""
	# Item da Item Supplier
	from_supplier = frappe.get_all(
		"Item Supplier",
		filters={"supplier": supplier_name},
		fields=["parent as item_code", "supplier_part_no"],
	)

	# Item da Item Default
	from_default = frappe.get_all(
		"Item Default",
		filters={"default_supplier": supplier_name},
		fields=["parent as item_code"],
	)

	return from_supplier, from_default


@frappe.whitelist()
def find_matching_items(supplier_name, invoice_lines):
	"""
	Cerca item matching per le righe della fattura con strategia a cascata:
	1. codice_articolo XML → Item Supplier.supplier_part_no
	2. descrizione → Item Supplier.supplier_part_no (match esatto)
	3. SequenceMatcher su item_name/description degli Item del fornitore
	4. Nessun match → lascia vuoto

	Args:
	    supplier_name: Nome del fornitore
	    invoice_lines: Lista di righe fattura

	Returns:
	    dict: {numero_linea: {"item_code": "...", "expense_account": "..."}}
	"""
	if isinstance(invoice_lines, str):
		invoice_lines = json.loads(invoice_lines)

	from italian_invoice.utilities.fatture import get_codice_articolo_from_line

	matches = {}
	from_supplier, from_default = _get_supplier_items(supplier_name)

	# Indice supplier_part_no → item_code per lookup rapido
	part_no_map = {}
	for entry in from_supplier:
		pn = (entry.get("supplier_part_no") or "").strip().lower()
		if pn:
			part_no_map[pn] = entry["item_code"]

	# Tutti gli item_code del fornitore (da entrambe le fonti)
	all_item_codes = list(set(
		[e["item_code"] for e in from_supplier] + [e["item_code"] for e in from_default]
	))

	# Dettagli degli item per il matching per similarità
	items_details = []
	# Bulk fetch expense accounts per tutti gli item del fornitore
	expense_accounts = {}
	if all_item_codes:
		items_details = frappe.get_all(
			"Item",
			filters={"name": ["in", all_item_codes]},
			fields=["name", "item_name", "description"],
		)
		for row in frappe.get_all(
			"Item Default",
			filters={"parent": ["in", all_item_codes]},
			fields=["parent", "default_supplier", "expense_account"],
		):
			if not row.get("expense_account"):
				continue
			# Priorità: account specifico per questo fornitore
			if row["default_supplier"] == supplier_name:
				expense_accounts[row["parent"]] = row["expense_account"]
			elif row["parent"] not in expense_accounts:
				expense_accounts[row["parent"]] = row["expense_account"]

	for line in invoice_lines:
		line_desc = (line.get("descrizione") or "").strip()
		line_desc_lower = line_desc.lower()
		codice = get_codice_articolo_from_line(line)
		matched_item = None

		# 1. Match per codice articolo XML → supplier_part_no
		if codice:
			codice_lower = codice.strip().lower()
			if codice_lower in part_no_map:
				matched_item = part_no_map[codice_lower]

		# 2. Match esatto descrizione → supplier_part_no
		if not matched_item and line_desc_lower:
			if line_desc_lower in part_no_map:
				matched_item = part_no_map[line_desc_lower]

		# 3. Match per similarità su item_name/description
		if not matched_item and line_desc_lower and items_details:
			best_ratio = 0.0
			for item in items_details:
				for field in ("item_name", "description"):
					val = (item.get(field) or "").strip().lower()
					if not val:
						continue
					if line_desc_lower == val:
						matched_item = item["name"]
						break
					ratio = SequenceMatcher(None, line_desc_lower, val).ratio()
					if ratio > best_ratio and ratio > 0.7:
						best_ratio = ratio
						matched_item = item["name"]
				if matched_item and line_desc_lower == (item.get("item_name") or "").strip().lower():
					break

		if matched_item:
			matches[line.get("numero_linea")] = {
				"item_code": matched_item,
				"expense_account": expense_accounts.get(matched_item),
			}

	return matches


@frappe.whitelist()
def process_supplier_invoice(
	invoice_data, fattura_fornitori_sdi=None, item_mappings=None, remember_mappings=None
):
	"""
	Processa una fattura fornitore e crea una Purchase Invoice

	Args:
	    invoice_data: JSON string o dict con dati fattura
	    fattura_fornitori_sdi: Nome doc Fattura Fornitori SDI (opzionale)
	    item_mappings: Mapping articoli personalizzato (opzionale)
	    remember_mappings: Lista di {item_code, supplier_part_no} da salvare in Item Supplier

	Returns:
	    Nome della Purchase Invoice creata
	"""
	try:
		# Parse dati se necessario
		if isinstance(invoice_data, str):
			invoice_data = json.loads(invoice_data)

		if item_mappings and isinstance(item_mappings, str):
			item_mappings = json.loads(item_mappings)

		if remember_mappings and isinstance(remember_mappings, str):
			remember_mappings = json.loads(remember_mappings)

		# Estrai dati fattura
		from italian_invoice.utilities.fatture import (
			get_invoice_payload,
			get_supplier_vat_from_json,
		)

		payload = get_invoice_payload(invoice_data)

		# Ottieni o crea fornitore
		supplier_vat = get_supplier_vat_from_json(payload)
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
		purchase_invoice = frappe.get_doc(
			{
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
				"items": prepare_invoice_items(invoice_lines, item_mappings, company, is_return),
				"taxes": prepare_invoice_taxes(extract_tax_summary(payload), company, is_return),
			}
		)

		# Aggiungi riferimento file se presente
		if invoice_data.get("data", {}).get("invoice", {}).get("file_id"):
			purchase_invoice.scan_field = invoice_data["data"]["invoice"]["file_id"]

		purchase_invoice.insert()

		# Aggiorna Fattura Fornitori SDI se presente
		if fattura_fornitori_sdi:
			fattura_sdi_doc.fattura = purchase_invoice.name
			fattura_sdi_doc.stato = "Importata"
			fattura_sdi_doc.save()

		# Salva associazioni Item Supplier per auto-apprendimento
		if remember_mappings:
			save_item_supplier_mappings(remember_mappings, supplier)

		return purchase_invoice.name

	except Exception as e:
		frappe.log_error(f"Errore importazione: {str(e)}", "Italian Invoice Passive")
		frappe.throw(f"Errore importazione fattura: {str(e)}")


def is_credit_note(tipo_documento):
	"""Verifica se il tipo documento è una nota di credito"""
	return tipo_documento in ["TD04", "TD05", "TD08", "TD09"]


def invert_sign_for_credit_note(value, is_return):
	"""Inverte il segno di un valore se è una nota di credito"""
	if not is_return:
		return value
	return -abs(float(value)) if value else 0


@frappe.whitelist()
def get_open_purchase_documents_summary(supplier_vat):
	"""
	Recupera sommario di PO/PR aperti per un fornitore (per alert nel form)

	Args:
	    supplier_vat: Partita IVA fornitore

	Returns:
	    dict: {"purchase_orders": [...], "purchase_receipts": [...]}
	"""
	result = {"purchase_orders": [], "purchase_receipts": []}

	# Trova fornitore dalla partita IVA
	supplier_list = frappe.get_list("Supplier", filters={"tax_id": supplier_vat}, fields=["name"])
	if not supplier_list:
		return result

	supplier = supplier_list[0]["name"]

	# Purchase Orders aperti
	pos = frappe.db.sql(
		"""
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
    """,
		{"supplier": supplier},
		as_dict=True,
	)
	result["purchase_orders"] = pos

	# Purchase Receipts aperti
	prs = frappe.db.sql(
		"""
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
    """,
		{"supplier": supplier},
		as_dict=True,
	)
	result["purchase_receipts"] = prs

	return result


@frappe.whitelist()
def create_purchase_invoice_from_document(doc_name, doctype, bill_no, fattura_sdi_name):
	"""
	Crea una Purchase Invoice da un Purchase Order o Purchase Receipt,
	applicando l'IVA dalla Fattura Fornitori SDI.

	Args:
	    doc_name: Nome del PO/PR
	    doctype: "Purchase Order" o "Purchase Receipt"
	    bill_no: Numero fattura da impostare
	    fattura_sdi_name: Nome della Fattura Fornitori SDI

	Returns:
	    Nome della Purchase Invoice creata
	"""
	from italian_invoice.utilities.fatture import get_fattura_body

	if doctype == "Purchase Order":
		from erpnext.buying.doctype.purchase_order.purchase_order import (
			make_purchase_invoice,
		)

		pi = make_purchase_invoice(doc_name)
	elif doctype == "Purchase Receipt":
		from erpnext.stock.doctype.purchase_receipt.purchase_receipt import (
			make_purchase_invoice,
		)

		pi = make_purchase_invoice(doc_name)
	else:
		frappe.throw(f"Doctype non supportato: {doctype}")

	# Imposta bill_no
	pi.bill_no = bill_no

	# Estrai dati dalla Fattura Fornitori SDI
	fattura_sdi = frappe.get_doc("Fattura Fornitori SDI", fattura_sdi_name)

	# Estrai data fattura e allinea posting_date e bill_date
	bill_date = _get_bill_date_from_fattura_sdi(fattura_sdi)
	if bill_date:
		pi.bill_date = bill_date
		pi.posting_date = bill_date

	# Estrai e applica l'IVA dalla fattura SDI
	body = get_fattura_body(fattura_sdi.dati_fattura)
	if body:
		# Verifica se è una nota di credito
		tipo_documento = (
			body.get("dati_generali", {}).get("dati_generali_documento", {}).get("tipo_documento", "")
		)
		is_return = is_credit_note(tipo_documento)

		# Estrai riepilogo IVA e prepara le tasse
		tax_summary = extract_tax_summary(body)
		if tax_summary:
			# Rimuovi le tasse esistenti (copiate dal PO/PR)
			pi.taxes = []
			# Aggiungi le tasse dalla fattura SDI
			taxes = prepare_invoice_taxes(tax_summary, pi.company, is_return)
			for tax in taxes:
				pi.append("taxes", tax)

	# Salva (ma non submit)
	pi.insert()
	frappe.db.commit()

	return pi.name


def _get_bill_date_from_fattura_sdi(fattura_sdi):
	"""Estrae la data fattura dai dati JSON della Fattura Fornitori SDI"""
	from italian_invoice.utilities.fatture import get_fattura_body

	body = get_fattura_body(fattura_sdi.dati_fattura)
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
		"url": f"/app/{doctype.lower().replace(' ', '-')}/{doc_name}",
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

	fatture = frappe.get_list("Fattura Fornitori SDI", filters=filters, fields=["name"], limit=1)

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
		fields=["name"],
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
			indicator="green",
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


def _extract_from_payload(payload, body_path, default=None):
	"""Helper DRY per estrarre dati dal payload navigando la struttura a cascata."""
	if default is None:
		default = {}
	if "fattura_elettronica_body" in payload:
		obj = payload["fattura_elettronica_body"][0]
		for key in body_path:
			obj = obj[key]
		return obj
	# Naviga il percorso diretto (senza fattura_elettronica_body)
	obj = payload
	for key in body_path[:-1]:
		if key in obj:
			obj = obj[key]
		else:
			return payload.get(body_path[-1], default)
	return obj.get(body_path[-1], default)


def extract_document_data(payload):
	"""Estrae dati generali documento"""
	return _extract_from_payload(payload, ["dati_generali", "dati_generali_documento"])


def extract_invoice_lines(payload):
	"""Estrae righe fattura"""
	return _extract_from_payload(payload, ["dati_beni_servizi", "dettaglio_linee"], default=[])


def extract_tax_summary(payload):
	"""Estrae riepilogo IVA"""
	return _extract_from_payload(payload, ["dati_beni_servizi", "dati_riepilogo"], default=[])


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

			items.append(item_dict)
		else:
			# Crea riga automatica
			items.append(
				{
					"item_code": get_or_create_item_code(line),
					"description": line.get("descrizione", ""),
					"qty": quantity,
					"rate": rate,
					"uom": get_default_uom(),
					"price_list_rate": rate,
					"tax_rate": line.get("aliquota_iva", 0),
					"tax_nature": line.get("natura"),
				}
			)

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
	Prepara le tasse per la fattura di acquisto.
	Gestisce sia aliquote standard che righe con IVA 0% + natura (N1-N6).
	Per reverse charge (N6) crea doppia riga: IVA credito + IVA debito.

	Args:
	    invoice_summary: Lista di riepiloghi IVA (dati_riepilogo)
	    company: Nome della società
	    is_return: True se è una nota di credito

	Returns:
	    Lista di dizionari per le tasse
	"""
	taxes = []

	for summary in invoice_summary:
		tax_rate = float(summary.get("aliquota_iva", 0))
		natura = summary.get("natura") or ""
		esigibilita = summary.get("esigibilita_iva") or "I"
		rif_normativo = summary.get("riferimento_normativo") or ""

		tax_amount = invert_sign_for_credit_note(summary.get("imposta", 0), is_return)
		total = invert_sign_for_credit_note(summary.get("imponibile_importo", 0), is_return)

		if tax_rate == 0 and natura:
			# IVA 0% con natura: crea riga tax con importo 0 e conto specifico
			tax_account = get_tax_account_by_natura(natura, company)
			description = rif_normativo or f"Natura {natura}"

			taxes.append({
				"charge_type": "Actual",
				"account_head": tax_account,
				"tax_amount": 0,
				"rate": 0,
				"description": description,
				"total": total,
			})

			# Reverse charge (N6.x): crea anche riga IVA a debito speculare
			if natura.startswith("N6"):
				rc_tax_rate = _get_reverse_charge_rate(natura)
				if rc_tax_rate > 0:
					rc_credit_account = get_tax_account(rc_tax_rate, company, root_type="Asset")
					rc_debit_account = get_tax_account(rc_tax_rate, company, root_type="Liability")
					rc_amount = round(float(total) * rc_tax_rate / 100, 2)
					rc_amount = invert_sign_for_credit_note(rc_amount, is_return)

					taxes.append({
						"charge_type": "Actual",
						"account_head": rc_credit_account,
						"tax_amount": rc_amount,
						"rate": rc_tax_rate,
						"description": f"IVA {rc_tax_rate}% RC credito ({natura})",
						"total": total,
					})
					taxes.append({
						"charge_type": "Actual",
						"account_head": rc_debit_account,
						"tax_amount": -rc_amount,
						"rate": rc_tax_rate,
						"description": f"IVA {rc_tax_rate}% RC debito ({natura})",
						"total": total,
					})
		elif tax_rate == 0:
			# IVA 0% senza natura: ignora (non è significativo)
			continue
		else:
			# Aliquota standard (22%, 10%, 4%, ecc.)
			tax_account = get_tax_account(tax_rate, company)

			description = f"IVA {tax_rate}%"
			if esigibilita == "S":
				description += " (Split Payment)"
			elif esigibilita == "D":
				description += " (Differita)"

			taxes.append({
				"charge_type": "Actual",
				"account_head": tax_account,
				"tax_amount": tax_amount,
				"rate": tax_rate,
				"description": description,
				"total": total,
			})

	return taxes


def _get_reverse_charge_rate(natura):
	"""Determina l'aliquota IVA per reverse charge in base alla natura."""
	# N6.1-N6.9: in Italia l'aliquota standard per RC è 22%
	# Può essere personalizzata in futuro
	return 22.0


def get_tax_account(tax_rate, company, root_type=None):
	"""
	Restituisce l'account IVA ACQUISTI in base all'aliquota.

	Args:
	    tax_rate: Aliquota IVA
	    company: Nome company
	    root_type: Se specificato, cerca solo in quel root_type

	Returns:
	    Nome dell'account IVA acquisti
	"""
	tax_rate = round(float(tax_rate), 2)

	root_types = [root_type] if root_type else ["Asset", "Liability"]

	for rt in root_types:
		tax_account = frappe.db.get_all(
			"Account",
			{
				"company": company,
				"tax_rate": tax_rate,
				"account_type": "Tax",
				"root_type": rt,
			},
			["name"],
			limit=1,
		)
		if tax_account:
			return tax_account[0]["name"]

	frappe.throw(
		f"Account IVA Acquisti non trovato per aliquota {tax_rate}% (root_type={root_type or 'Asset/Liability'}) in {company}. "
		f"Assicurarsi che esista un account con tax_rate={tax_rate} e account_type='Tax'."
	)


def get_tax_account_by_natura(natura, company):
	"""
	Restituisce l'account contabile per operazioni con natura (IVA 0%).
	Cerca un Account con account_name che contenga il codice natura.

	Args:
	    natura: Codice natura (N1, N2.2, N3.5, N4, N6.1, ecc.)
	    company: Nome company

	Returns:
	    Nome dell'account
	"""
	# Cerca account con nome che contiene il codice natura (es. "N4" o "N6")
	natura_base = natura.split(".")[0] if "." in natura else natura

	for search_term in (natura, natura_base):
		accounts = frappe.db.get_all(
			"Account",
			{
				"company": company,
				"account_name": ["like", f"%{search_term}%"],
				"account_type": "Tax",
				"is_group": 0,
			},
			["name"],
			limit=1,
		)
		if accounts:
			return accounts[0]["name"]

	frappe.throw(
		f"Account non trovato per natura '{natura}' in {company}. "
		f"Creare un account di tipo Tax con il codice natura nel nome (es. 'IVA Acquisti {natura}')."
	)


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

	# Cerca il primo gruppo disponibile (gestisce multilingua)
	groups = frappe.get_all("Supplier Group", fields=["name"], limit=1)
	if groups:
		return groups[0]["name"]

	frappe.throw("Nessun Supplier Group trovato nel sistema")


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
	service_item = frappe.db.get_value("Item", {"is_stock_item": 0, "disabled": 0}, "name")

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
		doc_type = frappe.get_doc("Tipologia di documento e-Invoice", document_type_code)
		if doc_type.tipologia == "AutoFattura":
			frappe.msgprint(
				f"Attenzione: Il documento {document_type_code} è un'autofattura",
				title="Autofattura rilevata",
				indicator="orange",
			)
			return True
	except frappe.DoesNotExistError:
		frappe.log_error(
			f"Tipo documento {document_type_code} non trovato",
			"Italian Invoice Passive",
		)

	return False
