import frappe
from frappe import _
from frappe.utils import add_days, add_months, get_last_day, getdate


@frappe.whitelist()
def recalculate_payment_schedule(sales_invoice_name):
	"""Recalculate payment schedule for submitted Sales Invoice"""
	doc = frappe.get_doc("Sales Invoice", sales_invoice_name)

	if not doc.payment_terms_template:
		frappe.throw(_("No Payment Terms Template found"))

	# Get payment terms template
	template = frappe.get_doc("Payment Terms Template", doc.payment_terms_template)

	if not template.terms:
		frappe.throw(_("Payment Terms Template has no terms"))

	# Delete existing payment schedule
	frappe.db.delete(
		"Payment Schedule",
		{"parent": sales_invoice_name, "parenttype": "Sales Invoice"},
	)

	# Create new payment schedule
	for term_detail in template.terms:
		due_date = calculate_due_date(doc.posting_date, term_detail)

		payment_amount = (doc.grand_total * (term_detail.invoice_portion or 100)) / 100

		payment_schedule = frappe.new_doc("Payment Schedule")
		payment_schedule.parent = sales_invoice_name
		payment_schedule.parenttype = "Sales Invoice"
		payment_schedule.parentfield = "payment_schedule"
		payment_schedule.payment_term = term_detail.payment_term
		payment_schedule.description = term_detail.description
		payment_schedule.due_date = due_date
		payment_schedule.invoice_portion = term_detail.invoice_portion or 100
		payment_schedule.mode_of_payment = term_detail.mode_of_payment
		payment_schedule.payment_amount = payment_amount
		payment_schedule.base_payment_amount = payment_amount
		payment_schedule.outstanding = payment_amount
		payment_schedule.paid_amount = 0

		payment_schedule.insert(ignore_permissions=True)

	# Update main due_date with the last payment schedule date
	max_due_date = frappe.db.sql(
		"""
        SELECT MAX(due_date)
        FROM `tabPayment Schedule`
        WHERE parent = %s AND parenttype = 'Sales Invoice'
    """,
		sales_invoice_name,
	)[0][0]

	if max_due_date:
		frappe.db.set_value("Sales Invoice", sales_invoice_name, "due_date", max_due_date)

	frappe.db.commit()

	return {"success": True, "message": _("Payment schedule recalculated successfully")}


def calculate_due_date(posting_date, term):
	"""Calculate due date based on payment term settings"""
	posting_date = getdate(posting_date)

	if term.due_date_based_on == "Day(s) after invoice date":
		return add_days(posting_date, term.credit_days or 0)
	elif term.due_date_based_on == "Day(s) after the end of the invoice month":
		end_of_month = get_last_day(posting_date)
		return add_days(end_of_month, term.credit_days or 0)
	elif term.due_date_based_on == "Month(s) after the end of the invoice month":
		end_of_month = get_last_day(posting_date)
		return add_months(end_of_month, term.credit_months or 0)
	else:
		return posting_date
