"""Righe IVA delle fatture ricevute (16/11/2026). Il conto IVA sugli acquisti di ogni società: quello che le sue
fatture hanno usato di più, finora scelto per aliquota (e a volte su un conto delle vendite). Aliquota e imponibile del
documento sulle righe già registrate: ERPNext li azzera nelle righe a importo fisso e il registro IVA acquisti
mostrava imposta 0. Le righe che non si abbinano al documento si stampano e si completano a mano."""

import frappe
from frappe.utils import flt
from frappe.utils.fixtures import sync_fixtures

from italian_invoice.utilities.fatture import get_invoice_payload
from italian_invoice.utilities.fatture_passive import extract_tax_summary, iva_significativa

CONTO = "custom_account_iva_acquisti"


def execute():
	sync_fixtures("italian_invoice")  # i campi nuovi servono qui: il migrate sincronizza le fixture dopo le patch
	for company in frappe.get_all("Company", filters={CONTO: ["is", "not set"]}, pluck="name"):
		conto = conto_piu_usato(company)
		if conto:
			frappe.db.set_value("Company", company, CONTO, conto)
		print(f"{company}: conto IVA sugli acquisti {conto or 'NON IMPOSTATO (nessuna fattura ricevuta con IVA)'}")

	for sdi in frappe.get_all("Fattura Fornitori SDI", filters={"fattura": ["is", "set"]}, fields=["name", "fattura"]):
		pi = frappe.db.get_value("Purchase Invoice", {"name": sdi.fattura, "docstatus": ["<", 2]}, ["name", "is_return"], as_dict=True)
		if not pi:
			continue
		righe = frappe.get_all(
			"Purchase Taxes and Charges",
			filters={"parent": pi.name, "parenttype": "Purchase Invoice"},
			fields=["name", "add_deduct_tax", "tax_amount", "custom_aliquota_iva", "custom_imponibile"],
			order_by="idx",
		)
		documento = get_invoice_payload(frappe.db.get_value("Fattura Fornitori SDI", sdi.name, "dati_fattura"))
		abbinate, senza_riga = abbina(extract_tax_summary(documento), righe, pi.is_return)
		for nome, valori in abbinate.items():
			frappe.db.set_value("Purchase Taxes and Charges", nome, valori, update_modified=False)
		for voce in senza_riga:
			print(f"{pi.name} ({sdi.name}): nessuna riga IVA per {voce}, da completare a mano")


def conto_piu_usato(company):
	"""Il conto d'imposta più usato dalle righe IVA aggiunte, con importo, delle fatture ricevute confermate."""
	conti = frappe.db.sql(
		"""select t.account_head from `tabPurchase Taxes and Charges` t
		join `tabPurchase Invoice` p on p.name = t.parent
		join `tabAccount` a on a.name = t.account_head
		where p.company = %s and p.docstatus = 1 and t.add_deduct_tax = 'Add' and t.tax_amount != 0 and a.account_type = 'Tax'
		group by t.account_head order by count(*) desc limit 1""",
		company,
		pluck=True,
	)
	return conti[0] if conti else None


def abbina(riepiloghi, righe, is_return):
	"""Ogni voce IVA del riepilogo va sulla riga aggiunta, ancora senza aliquota, con la stessa imposta (al 0% con
	natura: una riga a importo 0). Restituisce {riga: campi} e le voci rimaste senza riga; nelle note di credito
	l'imponibile prende il segno negativo delle righe."""
	libere = [r for r in righe if r.add_deduct_tax == "Add" and not (r.custom_aliquota_iva or r.custom_imponibile)]
	abbinate, senza_riga = {}, []
	for voce in filter(iva_significativa, riepiloghi):
		aliquota, imposta = flt(voce.get("aliquota_iva")), abs(flt(voce.get("imposta")))
		riga = next((r for r in libere if abs(flt(r.tax_amount)) == imposta), None)
		if not riga:
			senza_riga.append(f"{aliquota:g}% imposta {imposta:.2f}")
			continue
		libere.remove(riga)
		imponibile = abs(flt(voce.get("imponibile_importo")))
		abbinate[riga.name] = {"custom_aliquota_iva": aliquota, "custom_imponibile": -imponibile if is_return else imponibile}
	return abbinate, senza_riga
