"""Blocchi della fattura elettronica ricevuta che la Purchase Invoice di base non copriva: ritenuta d'acconto,
bollo, cassa previdenziale, condizioni di pagamento. Ogni blocco agisce solo se presente nel documento; i conti
e l'articolo della cassa sono impostazioni della società (campi su Company), assenti = errore esplicito quando
servono. Nessun valore dedotto: ciò che non torna con il documento ferma l'importazione con il motivo."""

import frappe
from frappe import _
from frappe.utils import add_days, flt, getdate

TOLLERANZA = 0.01
# Tipi di ritenuta registrati sul conto ritenute della società; gli altri (contributi INPS, ENASARCO, ENPAM)
# hanno conti propri e per ora fermano l'importazione.
TIPI_RITENUTA_GESTITI = {"RT01": "persone fisiche", "RT02": "persone giuridiche"}
TIPI_CASSA = {
	"TC01": "Cassa avvocati", "TC02": "Cassa dottori commercialisti", "TC03": "Cassa geometri",
	"TC04": "Cassa ingegneri e architetti", "TC05": "Cassa notariato", "TC06": "Cassa ragionieri",
	"TC07": "ENASARCO", "TC08": "ENPACL consulenti del lavoro", "TC09": "ENPAM medici", "TC10": "ENPAF farmacisti",
	"TC11": "ENPAV veterinari", "TC12": "ENPAIA agricoltura", "TC13": "Fondo spedizionieri", "TC14": "INPGI giornalisti",
	"TC15": "ONAOSI", "TC16": "CASAGIT", "TC17": "EPPI periti industriali", "TC18": "EPAP", "TC19": "ENPAB biologi",
	"TC20": "ENPAPI infermieri", "TC21": "ENPAP psicologi", "TC22": "INPS",
}


def integra_blocchi(doc_data, invoice_lines, company, is_return):
	"""Righe articolo, righe tasse e campi in più per la Purchase Invoice dai blocchi del documento."""
	base_ritenuta = sum(flt(line.get("prezzo_totale")) for line in invoice_lines if line.get("ritenuta") == "SI")
	items, taxes = [], []
	for cassa in doc_data.get("dati_cassa_previdenziale") or []:
		items.append(_riga_cassa(cassa, company, is_return))
		if cassa.get("ritenuta") == "SI":
			base_ritenuta += flt(cassa.get("importo_contributo_cassa"))
	ritenute = doc_data.get("dati_ritenuta") or []
	for ritenuta in ritenute:
		taxes.append(_riga_ritenuta(ritenuta, base_ritenuta, company, is_return))
	bollo = doc_data.get("dati_bollo")
	if bollo and bollo.get("bollo_virtuale") == "SI" and flt(bollo.get("importo_bollo")):
		conto = _impostazione(company, "custom_account_bollo", "il conto del bollo")
		taxes.append(_riga_tassa(conto, flt(bollo["importo_bollo"]), is_return, deduci=False, descrizione="Imposta di bollo"))
	campi = {
		"custom_ritenuta_tipo": ", ".join(r.get("tipo_ritenuta") or "" for r in ritenute),
		"custom_ritenuta_causale": ", ".join(r.get("causale_pagamento") or "" for r in ritenute),
		"custom_ritenuta_importo": sum(flt(r.get("importo_ritenuta")) for r in ritenute),
	} if ritenute else {}
	return items, taxes, campi


def _impostazione(company, campo, etichetta):
	valore = frappe.get_cached_value("Company", company, campo)
	if not valore:
		frappe.throw(
			_("La fattura ha {0} ma la società {1} non ha «{2}» nelle impostazioni (campo {3}).").format(
				etichetta, company, etichetta, campo
			)
		)
	return valore


def _riga_cassa(cassa, company, is_return):
	tipo = cassa.get("tipo_cassa")
	if tipo not in TIPI_CASSA:
		frappe.throw(_("Tipo di cassa previdenziale non previsto: {0}.").format(tipo))
	item_code = _impostazione(company, "custom_item_cassa_previdenziale", "l'articolo della cassa previdenziale")
	return {
		"item_code": item_code,
		"description": f"{TIPI_CASSA[tipo]} {flt(cassa.get('al_cassa'))}% su {flt(cassa.get('imponibile_cassa')):.2f}",
		"qty": -1 if is_return else 1,
		"rate": abs(flt(cassa.get("importo_contributo_cassa"))),
		"uom": frappe.get_cached_value("Item", item_code, "stock_uom"),
		"expense_account": _impostazione(company, "custom_account_cassa_previdenziale", "il conto della cassa previdenziale"),
		"tax_rate": cassa.get("aliquota_iva", 0),
		"tax_nature": cassa.get("natura"),
	}


def _riga_ritenuta(ritenuta, base, company, is_return):
	tipo = ritenuta.get("tipo_ritenuta")
	if tipo not in TIPI_RITENUTA_GESTITI:
		frappe.throw(_("Tipo di ritenuta non gestito: {0}.").format(tipo))
	importo = flt(ritenuta.get("importo_ritenuta"))
	aliquota = flt(ritenuta.get("aliquota_ritenuta"))
	attesa = round(base * aliquota / 100, 2)
	if abs(importo - attesa) > TOLLERANZA:
		frappe.throw(
			_("Ritenuta {0} non torna: il documento dice {1:.2f}, ma {2}% di {3:.2f} fa {4:.2f}.").format(
				tipo, importo, aliquota, base, attesa
			)
		)
	conto = _impostazione(company, "custom_account_ritenuta", "il conto delle ritenute d'acconto")
	return _riga_tassa(conto, importo, is_return, deduci=True, aliquota=aliquota,
		descrizione=f"Ritenuta d'acconto {aliquota}% ({TIPI_RITENUTA_GESTITI[tipo]})")


def _riga_tassa(conto, importo, is_return, *, deduci, descrizione, aliquota=0):
	"""Riga tasse a importo fisso sul totale; nelle note di credito il segno si inverte."""
	return {
		"charge_type": "Actual",
		"add_deduct_tax": "Deduct" if deduci else "Add",
		"category": "Total",
		"account_head": conto,
		"tax_amount": -importo if is_return else importo,
		"rate": aliquota,
		"description": descrizione,
	}


def scadenze(dati_pagamento, bill_date, netto_da_pagare, totale_documento):
	"""Righe del piano dei pagamenti dai DatiPagamento: una per rata, scadenza dal documento. Le rate possono
	essere espresse al lordo della ritenuta (totale documento) o al netto: in entrambi i casi il piano va
	espresso al netto, che è quanto ERPNext richiede. Lista vuota se il documento non ha DatiPagamento."""
	rate = [d for p in dati_pagamento for d in (p.get("dettaglio_pagamento") or [])]
	if not rate:
		return []
	somma = round(sum(flt(r.get("importo_pagamento")) for r in rate), 2)
	if not somma or (abs(somma - totale_documento) > TOLLERANZA and abs(somma - netto_da_pagare) > TOLLERANZA):
		frappe.throw(
			_("Le rate del documento sommano {0:.2f}, ma il totale è {1:.2f} e il netto da pagare {2:.2f}.").format(
				somma, totale_documento, netto_da_pagare
			)
		)
	fattore = netto_da_pagare / somma
	modi = {codice: modo_di_pagamento(codice) for codice in {r.get("modalita_pagamento") for r in rate}}
	righe = []
	for rata in rate:
		scadenza = rata.get("data_scadenza_pagamento") or add_days(
			rata.get("data_riferimento_termini_pagamento") or bill_date, int(rata.get("giorni_termini_pagamento") or 0)
		)
		if getdate(scadenza) < getdate(bill_date):
			frappe.throw(
				_("Scadenza {0} precedente alla data del documento {1}: da controllare a mano.").format(scadenza, bill_date)
			)
		importo = round(flt(rata.get("importo_pagamento")) * fattore, 2)
		righe.append({
			"due_date": scadenza,
			"payment_amount": importo,
			"invoice_portion": importo / netto_da_pagare * 100,
			"mode_of_payment": modi[rata.get("modalita_pagamento")],
			"description": rata.get("modalita_pagamento") or "",
		})
	# gli arrotondamenti delle rate scalate si assorbono sull'ultima, così la somma è esattamente il netto
	differenza = round(netto_da_pagare - sum(r["payment_amount"] for r in righe), 2)
	if differenza:
		righe[-1]["payment_amount"] = round(righe[-1]["payment_amount"] + differenza, 2)
	return righe


def modo_di_pagamento(codice):
	"""Il Mode of Payment con il codice della fattura elettronica (campo di ERPNext Italia). Senza codice nessun
	modo; con più modi sullo stesso codice la configurazione è ambigua e va corretta."""
	if not codice:
		return None
	modi = frappe.get_all("Mode of Payment", filters={"mode_of_payment_code": ["like", f"{codice}-%"], "enabled": 1}, pluck="name")
	if len(modi) > 1:
		frappe.throw(_("Più modalità di pagamento hanno il codice {0}: {1}. Lasciane una sola.").format(codice, ", ".join(modi)))
	return modi[0] if modi else None


def iban_fornitore(dati_pagamento):
	"""Il primo IBAN nei DatiPagamento, per i pagamenti e per accorgersi di un cambio di coordinate."""
	for pagamento in dati_pagamento:
		for rata in pagamento.get("dettaglio_pagamento") or []:
			if rata.get("iban"):
				return rata["iban"]
	return None
