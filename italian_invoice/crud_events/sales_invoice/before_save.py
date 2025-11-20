import frappe


def execute(doc, method=None):
	if doc.is_return:
		return

	if doc.is_new():
		return

	customer = frappe.get_doc("Customer", doc.customer)
	old_doc = doc.get_doc_before_save()
	old_customer = frappe.get_doc("Customer", old_doc.customer)

	if old_customer.is_public_administration and not customer.is_public_administration:
		frappe.throw("Non puoi modificare un cliente PA con uno privato. Crea una nuova fattura")

	if not old_customer.is_public_administration and customer.is_public_administration:
		frappe.throw("Non puoi modificare un cliente privato con uno PA. Crea una nuova fattura")
