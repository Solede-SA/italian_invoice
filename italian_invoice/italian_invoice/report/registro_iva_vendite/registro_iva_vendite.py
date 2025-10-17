import frappe
from frappe import _
from frappe.utils import flt, getdate


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	"""Definisce le colonne del registro IVA vendite"""
	return [
		{
			"fieldname": "progressive",
			"label": _("N. Progr."),
			"fieldtype": "Int",
			"width": 80
		},
		{
			"fieldname": "posting_date",
			"label": _("Data"),
			"fieldtype": "Date",
			"width": 100
		},
		{
			"fieldname": "name",
			"label": _("N. Fattura"),
			"fieldtype": "Link",
			"options": "Sales Invoice",
			"width": 150
		},
		{
			"fieldname": "customer_name",
			"label": _("Cliente"),
			"fieldtype": "Data",
			"width": 200
		},
		{
			"fieldname": "tax_id",
			"label": _("P.IVA/CF"),
			"fieldtype": "Data",
			"width": 130
		},
		{
			"fieldname": "imponibile_22",
			"label": _("Imponibile 22%"),
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "imposta_22",
			"label": _("Imposta 22%"),
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "imponibile_10",
			"label": _("Imponibile 10%"),
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "imposta_10",
			"label": _("Imposta 10%"),
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "imponibile_5",
			"label": _("Imponibile 5%"),
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "imposta_5",
			"label": _("Imposta 5%"),
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "imponibile_4",
			"label": _("Imponibile 4%"),
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "imposta_4",
			"label": _("Imposta 4%"),
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "esente",
			"label": _("Esente"),
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "non_imponibile",
			"label": _("Non Imponibile"),
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "totale",
			"label": _("Totale"),
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "note",
			"label": _("Note"),
			"fieldtype": "Data",
			"width": 150
		}
	]


def get_data(filters):
	"""Recupera i dati delle fatture di vendita e li raggruppa per aliquota IVA"""
	conditions = get_conditions(filters)

	invoices = frappe.db.sql(f"""
		SELECT
			si.name,
			si.posting_date,
			si.customer,
			si.customer_name,
			si.tax_id,
			si.grand_total,
			si.status
		FROM `tabSales Invoice` si
		WHERE si.docstatus = 1
		{conditions}
		ORDER BY si.posting_date, si.name
	""", filters, as_dict=1)

	if not invoices:
		return []

	data = []
	progressive = 1

	for invoice in invoices:
		row = {
			"progressive": progressive,
			"posting_date": invoice.posting_date,
			"name": invoice.name,
			"customer_name": invoice.customer_name,
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
			"totale": invoice.grand_total,
			"note": ""
		}

		# Recupera le righe delle tasse
		tax_breakdown = get_tax_breakdown(invoice.name)

		# Raggruppa per aliquota
		for tax in tax_breakdown:
			rate = flt(tax.get("rate"))
			base_amount = flt(tax.get("base_amount"))
			tax_amount = flt(tax.get("tax_amount"))

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

		row["note"] = ", ".join(notes)

		data.append(row)
		progressive += 1

	return data


def get_tax_breakdown(invoice_name):
	"""Recupera il dettaglio delle tasse per una fattura con calcolo imponibile da item_wise_tax_detail"""
	taxes = frappe.db.sql("""
		SELECT
			account_head,
			description,
			rate,
			base_tax_amount as tax_amount,
			item_wise_tax_detail
		FROM `tabSales Taxes and Charges`
		WHERE parent = %s
		ORDER BY idx
	""", invoice_name, as_dict=1)

	result = []
	for tax in taxes:
		if not tax.item_wise_tax_detail:
			continue

		import json
		try:
			item_wise = json.loads(tax.item_wise_tax_detail)
			base_amount = 0

			for item_code, tax_data in item_wise.items():
				if isinstance(tax_data, list) and len(tax_data) >= 2:
					base_amount += flt(tax_data[1])

			if base_amount > 0 or flt(tax.tax_amount) > 0:
				result.append({
					"account_head": tax.account_head,
					"description": tax.description,
					"rate": flt(tax.rate),
					"base_amount": base_amount,
					"tax_amount": flt(tax.tax_amount)
				})
		except (json.JSONDecodeError, ValueError):
			continue

	return result


def get_conditions(filters):
	"""Costruisce le condizioni WHERE per la query"""
	conditions = []

	if filters.get("company"):
		conditions.append("si.company = %(company)s")

	if filters.get("from_date"):
		conditions.append("si.posting_date >= %(from_date)s")

	if filters.get("to_date"):
		conditions.append("si.posting_date <= %(to_date)s")

	if filters.get("customer"):
		conditions.append("si.customer = %(customer)s")

	return " AND " + " AND ".join(conditions) if conditions else ""
