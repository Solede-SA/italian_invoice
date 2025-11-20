import frappe
from frappe import _
from frappe.utils import flt


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

	for invoice in invoices:
		row = {
			"progressive": progressive,
			"posting_date": invoice.posting_date,
			"bill_no": invoice.bill_no or "",
			"name": invoice.name,
			"supplier_name": invoice.supplier_name,
			"tax_id": invoice.tax_id or "",
			"imponibile_22": 0,
			"imposta_22": 0,
			"imponibile_10": 0,
			"imposta_10": 0,
			"imponibile_5": 0,
			"imposta_5": 0,
			"imponibile_4": 0,
			"imposta_4": 0,
			"esente": 0,
			"non_imponibile": 0,
			"indetraibile": 0,
			"totale": invoice.grand_total,
			"note": "",
		}

		# Recupera le righe delle tasse
		tax_breakdown = get_tax_breakdown(invoice.name)

		# Raggruppa per aliquota
		for tax in tax_breakdown:
			rate = flt(tax.get("rate"))
			base_amount = flt(tax.get("base_amount"))
			tax_amount = flt(tax.get("tax_amount"))

			# Gestione IVA non detraibile
			if tax.get("add_deduct_tax") == "Deduct":
				row["indetraibile"] += tax_amount
				continue

			if rate == 22:
				row["imponibile_22"] += base_amount
				row["imposta_22"] += tax_amount
			elif rate == 10:
				row["imponibile_10"] += base_amount
				row["imposta_10"] += tax_amount
			elif rate == 5:
				row["imponibile_5"] += base_amount
				row["imposta_5"] += tax_amount
			elif rate == 4:
				row["imponibile_4"] += base_amount
				row["imposta_4"] += tax_amount
			elif rate == 0:
				# Gestione operazioni esenti/non imponibili
				description = tax.get("description", "")
				if description and ("esent" in description.lower() or "esclus" in description.lower()):
					row["esente"] += base_amount
				else:
					row["non_imponibile"] += base_amount

		# Aggiungi note per operazioni speciali
		notes = []
		if row["esente"] > 0:
			notes.append("Esente")
		if row["non_imponibile"] > 0:
			notes.append("Non Imp.")
		if row["indetraibile"] > 0:
			notes.append("IVA Indetr.")

		# Verifica se è reverse charge
		if is_reverse_charge(invoice.name):
			notes.append("Rev. Charge")

		row["note"] = ", ".join(notes)

		data.append(row)
		progressive += 1

	return data


def get_tax_breakdown(invoice_name):
	"""Recupera il dettaglio delle tasse per una fattura con calcolo imponibile"""
	taxes = frappe.db.sql(
		"""
		SELECT
			account_head,
			description,
			rate,
			base_tax_amount as tax_amount,
			item_wise_tax_detail,
			add_deduct_tax,
			charge_type
		FROM `tabPurchase Taxes and Charges`
		WHERE parent = %s
		ORDER BY idx
	""",
		invoice_name,
		as_dict=1,
	)

	result = []
	for tax in taxes:
		base_amount = 0
		tax_amount = flt(tax.get("tax_amount"))

		# Prova prima con item_wise_tax_detail
		if tax.get("item_wise_tax_detail"):
			import json

			try:
				item_wise = json.loads(tax.item_wise_tax_detail)
				for item_code, tax_data in item_wise.items():
					if isinstance(tax_data, list) and len(tax_data) >= 2:
						base_amount += flt(tax_data[1])
			except (json.JSONDecodeError, ValueError):
				pass

		# Se non c'è item_wise_tax_detail, calcola l'imponibile dalla tax_amount e rate
		if base_amount == 0 and tax_amount != 0 and flt(tax.get("rate")) != 0:
			base_amount = tax_amount / (flt(tax.get("rate")) / 100)

		# Aggiungi solo se c'è almeno un valore
		if base_amount > 0 or tax_amount > 0:
			result.append(
				{
					"account_head": tax.account_head,
					"description": tax.description,
					"rate": flt(tax.get("rate")),
					"base_amount": base_amount,
					"tax_amount": tax_amount,
					"add_deduct_tax": tax.add_deduct_tax,
				}
			)

	return result


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
