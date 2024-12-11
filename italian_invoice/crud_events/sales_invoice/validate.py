import frappe


def get_original_invoice(doc):
    if doc.return_against:
        original_invoice = frappe.get_doc("Sales Invoice", doc.return_against)
        return original_invoice
    else:
        return None


def execute(doc, method=None):
    if doc.is_return:
        original_invoice = get_original_invoice(doc)

        print("original_invoice", original_invoice.payment_schedule)
        print("isList", isinstance(original_invoice.payment_schedule, list))

        if original_invoice:
            if original_invoice.payment_schedule:
                for payment_schedule in original_invoice.payment_schedule:

                    payment_schedule.name = None
                    payment_schedule.parent = None

                    doc.append("payment_schedule", payment_schedule)
            doc.payment_terms_template = original_invoice.payment_terms_template
