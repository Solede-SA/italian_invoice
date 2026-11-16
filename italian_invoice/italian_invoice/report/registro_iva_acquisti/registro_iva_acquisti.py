from collections import defaultdict

import frappe
from frappe import _

# Le aliquote con le loro colonne di imponibile e imposta.
RATES = (22, 10, 5, 4)
# Le colonne degli importi, a zero prima di sommare le righe IVA della fattura.
ZERI = dict.fromkeys([f"{k}_{r}" for r in RATES for k in ("imponibile", "imposta")] + ["esente", "non_imponibile", "indetraibile"], 0)


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	"""Definisce le colonne del registro IVA acquisti"""
	return [
		{
			"fieldname": "progressive",
			"label": _("N. Progr."),
			"fieldtype": "Int",
			"width": 80,
		},
		{
			"fieldname": "posting_date",
			"label": _("Data"),
			"fieldtype": "Date",
			"width": 100,
		},
		{
			"fieldname": "bill_no",
			"label": _("N. Documento"),
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"fieldname": "name",
			"label": _("Fattura Acquisto"),
			"fieldtype": "Link",
			"options": "Purchase Invoice",
			"width": 150,
		},
		{
			"fieldname": "supplier_name",
			"label": _("Fornitore"),
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"fieldname": "tax_id",
			"label": _("P.IVA/CF"),
			"fieldtype": "Data",
			"width": 130,
		},
		{
			"fieldname": "imponibile_22",
			"label": _("Imponibile 22%"),
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"fieldname": "imposta_22",
			"label": _("Imposta 22%"),
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"fieldname": "imponibile_10",
			"label": _("Imponibile 10%"),
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"fieldname": "imposta_10",
			"label": _("Imposta 10%"),
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"fieldname": "imponibile_5",
			"label": _("Imponibile 5%"),
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"fieldname": "imposta_5",
			"label": _("Imposta 5%"),
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"fieldname": "imponibile_4",
			"label": _("Imponibile 4%"),
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"fieldname": "imposta_4",
			"label": _("Imposta 4%"),
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"fieldname": "esente",
			"label": _("Esente"),
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"fieldname": "non_imponibile",
			"label": _("Non Imponibile"),
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"fieldname": "indetraibile",
			"label": _("Non Detraibile"),
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"fieldname": "totale",
			"label": _("Totale"),
			"fieldtype": "Currency",
			"width": 120,
		},
		{"fieldname": "note", "label": _("Note"), "fieldtype": "Data", "width": 150},
	]


def get_data(filters):
	"""Recupera i dati delle fatture di acquisto e li raggruppa per aliquota IVA"""
	conditions = get_conditions(filters)

	invoices = frappe.db.sql(
		f"""
		SELECT
			pi.name,
			pi.posting_date,
			pi.bill_no,
			pi.bill_date,
			pi.supplier,
			pi.supplier_name,
			pi.tax_id,
			pi.grand_total,
			pi.status
		FROM `tabPurchase Invoice` pi
		WHERE pi.docstatus = 1
		{conditions}
		ORDER BY pi.posting_date, pi.name
	""",
		filters,
		as_dict=1,
	)

	if not invoices:
		return []

	data = []
	progressive = 1
	taxes = get_tax_breakdown([invoice.name for invoice in invoices])

	for invoice in invoices:
		row = {
			"progressive": progressive,
			"posting_date": invoice.posting_date,
			"bill_no": invoice.bill_no or "",
			"name": invoice.name,
			"supplier_name": invoice.supplier_name,
			"tax_id": invoice.tax_id or "",
			**ZERI,
			"totale": invoice.grand_total,
			"note": "",
		}

		missing = add_taxes(row, taxes[invoice.name])

		# Aggiungi note per operazioni speciali
		notes = []
		if row["esente"]:
			notes.append("Esente")
		if row["non_imponibile"]:
			notes.append("Non Imp.")
		if row["indetraibile"]:
			notes.append("IVA Indetr.")
		if missing:
			notes.append(_("Riga IVA senza aliquota: da completare"))

		# Verifica se è reverse charge
		if is_reverse_charge(invoice.name):
			notes.append("Rev. Charge")

		row["note"] = ", ".join(notes)

		data.append(row)
		progressive += 1

	return data


def add_taxes(row, taxes):
	"""Somma le righe IVA della fattura nelle colonne del registro; restituisce quante righe IVA non hanno l'aliquota."""
	missing = 0
	for tax in taxes:
		if tax.add_deduct_tax == "Deduct":
			continue  # ritenuta d'acconto, IVA a debito dell'inversione contabile: non sono IVA a credito
		if tax.charge_type == "Actual":
			# ERPNext azzera l'aliquota delle righe a importo fisso: quelle importate la portano in custom_aliquota_iva
			if not (tax.aliquota or tax.imponibile):
				if tax.account_type == "Tax" and tax.tax_amount:
					missing += 1  # IVA inserita a mano: da completare
				continue  # bollo e altre spese: non sono IVA
			rate, base = tax.aliquota, tax.imponibile
		elif tax.rate:
			rate, base = tax.rate, tax.tax_amount * 100 / tax.rate
		else:
			continue
		if rate in RATES:
			row[f"imponibile_{rate:g}"] += base
			# IVA fuori dai conti d'imposta: indetraibile, sul conto del costo (studio Milesi) o del cespite
			row[f"imposta_{rate:g}" if tax.account_type == "Tax" else "indetraibile"] += tax.tax_amount
		elif rate == 0:
			description = (tax.description or "").lower()
			row["esente" if "esent" in description or "esclus" in description else "non_imponibile"] += base
	return missing


def get_tax_breakdown(invoice_names):
	"""Le righe tasse delle fatture, raggruppate per fattura, con gli importi nella valuta della società."""
	taxes = defaultdict(list)
	for tax in frappe.db.sql(
		"""
		SELECT
			t.parent,
			t.description,
			t.add_deduct_tax,
			t.charge_type,
			t.rate,
			t.base_tax_amount AS tax_amount,
			t.custom_aliquota_iva AS aliquota,
			t.custom_imponibile * p.conversion_rate AS imponibile,
			a.account_type
		FROM `tabPurchase Taxes and Charges` t
		JOIN `tabAccount` a ON a.name = t.account_head
		JOIN `tabPurchase Invoice` p ON p.name = t.parent
		WHERE t.parent IN %(names)s AND t.parenttype = 'Purchase Invoice'
		ORDER BY t.parent, t.idx
	""",
		{"names": invoice_names},
		as_dict=1,
	):
		taxes[tax.parent].append(tax)
	return taxes


def is_reverse_charge(invoice_name):
	"""Verifica se la fattura è in reverse charge"""
	result = frappe.db.sql(
		"""
		SELECT COUNT(*) as count
		FROM `tabPurchase Taxes and Charges`
		WHERE parent = %s
		AND (
			description LIKE '%%reverse%%charge%%'
			OR description LIKE '%%invers%%contab%%'
			OR account_head LIKE '%%reverse%%charge%%'
		)
	""",
		invoice_name,
		as_dict=1,
	)

	return result[0].count > 0 if result else False


def get_conditions(filters):
	"""Costruisce le condizioni WHERE per la query"""
	conditions = []

	if filters.get("company"):
		conditions.append("pi.company = %(company)s")

	if filters.get("from_date"):
		conditions.append("pi.posting_date >= %(from_date)s")

	if filters.get("to_date"):
		conditions.append("pi.posting_date <= %(to_date)s")

	if filters.get("supplier"):
		conditions.append("pi.supplier = %(supplier)s")

	return " AND " + " AND ".join(conditions) if conditions else ""
