import frappe
from frappe import _


def handle_rounding(doc, method):
    rounded_amount = 0

    # se unallocated_amount > 1.0, reounded_amount = unallocated_amount
    if doc.unallocated_amount <= 1.0:
        rounded_amount = doc.unallocated_amount
        doc.unallocated_amount = 0

    if doc.difference_amount:
        rounded_amount = doc.difference_amount
        doc.difference_amount = 0

    if rounded_amount > 0:
        rounding_account = frappe.get_value("Company", doc.company, "round_off_account")
        default_cost_center = frappe.get_value("Company", doc.company, "cost_center")

        if not rounding_account:
            frappe.throw(_("Please set Round Off Account in Company"))
        if not default_cost_center:
            frappe.throw(_("Please set Default Cost Center in Company"))

        doc.append(
            "deductions",
            {
                "account": rounding_account,
                "amount": rounded_amount,
                "cost_center": default_cost_center,
            },
        )

        doc._rounding_details = {
            "original_amount": doc.total_allocated_amount,
            "rounded_amount": doc.paid_amount,
            "difference": rounded_amount,
            "reference_invoice": (
                doc.references[0].reference_name if doc.references else None
            ),
        }


def after_insert(doc, method):
    if hasattr(doc, "_rounding_details"):
        frappe.get_doc(
            {
                "doctype": "Payment Rounding Log",
                "payment_entry": doc.name,
                "reference_invoice": doc._rounding_details.get("reference_invoice"),
                "original_amount": doc._rounding_details["original_amount"],
                "rounded_amount": doc._rounding_details["rounded_amount"],
                "difference": doc._rounding_details["difference"],
                "date": doc.posting_date,
            }
        ).insert(ignore_permissions=True)
