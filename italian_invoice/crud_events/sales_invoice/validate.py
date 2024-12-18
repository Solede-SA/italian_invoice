import frappe


def get_original_invoice(doc):
    if doc.return_against:
        original_invoice = frappe.get_doc("Sales Invoice", doc.return_against)
        return original_invoice
    else:
        return None


# se il cliente è soggetto a lettera di intento restituisce true
def is_subject_to_letter_of_intent(doc):
    if doc.customer:
        customer = frappe.get_doc("Customer", doc.customer)
        if customer.custom_abilita_lettera_dintento:
            return True
    return False


def execute(doc, method=None):
    if doc.is_return:
        original_invoice = get_original_invoice(doc)

        if original_invoice:
            if original_invoice.payment_schedule:
                for payment_schedule in original_invoice.payment_schedule:

                    payment_schedule.name = None
                    payment_schedule.parent = None

                    doc.append("payment_schedule", payment_schedule)
            doc.payment_terms_template = original_invoice.payment_terms_template

    if is_subject_to_letter_of_intent(doc):
        # per ogni item della fattura setta il campo custom_motivo_esenzione_iva con il valore "N3.5 se tax_rate è 0"
        for item in doc.items:
            if item.tax_rate == 0:
                item.custom_motivo_esenzione_iva = "N3.5"

        # genera in alert che dice che il cliente è soggetto a lettera di intento e quindi il motivo esenzione iva è stato settato a N3.5
        frappe.msgprint(
            "Il cliente è soggetto a lettera di intento. Il motivo esenzione IVA è stato settato a N3.5"
        )
