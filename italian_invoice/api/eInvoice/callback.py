import frappe


@frappe.whitelist(allow_guest=False)
def supplier_invoice():
    print(frappe.request.data)
    return "OK from supplier_invoice"


@frappe.whitelist(allow_guest=False)
def customer_invoice():
    print(frappe.request.data)
    return "OK from customer_invoice"


@frappe.whitelist(allow_guest=False)
def invoice_status_quarantena():
    print(frappe.request.data)
    return "OK from invoice_status_quarantena"


@frappe.whitelist(allow_guest=False)
def invoice_status_invoice_error():
    print(frappe.request.data)
    return "OK from invoice_status_invoice_error"


@frappe.whitelist(allow_guest=False)
def customer_notification():
    print(frappe.request.data)
    return "OK from customer_notification"


@frappe.whitelist(allow_guest=False)
def legal_storage_missing_vat():
    print(frappe.request.data)
    return "OK from legal_storage_missing_vat"


@frappe.whitelist(allow_guest=False)
def legal_storage_receipt():
    print(frappe.request.data)
    return "OK from legal_storage_receipt"
