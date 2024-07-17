import frappe


@frappe.whitelist(allow_guest=False)
def receive_supplier_invoice():
    print(frappe.request.data)
