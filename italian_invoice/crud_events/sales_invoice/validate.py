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


def manage_split_payment(doc, method):
    # Controlla se il cliente ha il flag dello split payment
    is_split = frappe.get_value("Customer", doc.customer, "is_public_administration")
    if not is_split:
        return

    # Identifica la riga di tassa relativa all'IVA in split payment
    # Assumiamo che il conto per l'IVA in split payment sia "Split Payment VAT - AC"
    vat_account = "05041007 - Iva Split Payment - CBM"
    vat_tax_row = None
    for tax in doc.taxes:
        if tax.account_head == vat_account:
            vat_tax_row = tax
            break

    if not vat_tax_row:
        # Se non troviamo la riga IVA, non facciamo nulla
        return

    # La tax_amount di questa riga rappresenta l'IVA che non deve essere incassata dal cliente.
    # Creiamo quindi una riga di tasse "negativa" che riduce l'importo dovuto dal cliente
    # di pari ammontare.
    offset_amount = vat_tax_row.tax_amount

    # Aggiungiamo una riga tasse di tipo Actual negativa per compensare l'IVA dall'importo dovuto
    doc.append(
        "taxes",
        {
            "charge_type": "Actual",
            "account_head": "05041009 - Split Payment Offset - CBM",  # Crea un account ad hoc se necessario
            "description": "Offset IVA per split payment",
            "tax_amount": -offset_amount,
        },
    )

    # Ricalcoliamo i totali dopo aver inserito la riga offset
    doc.calculate_taxes_and_totals()


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
        # setto il campo custom_bollo_virtuale a 1
        doc.custom_bollo_virtuale = 1

        # per ogni item della fattura setta il campo custom_motivo_esenzione_iva con il valore "N3.5 se tax_rate è 0"
        for item in doc.items:
            if item.tax_rate == 0:
                item.custom_motivo_esenzione_iva = "N3.5"

        # genera in alert che dice che il cliente è soggetto a lettera di intento e quindi il motivo esenzione iva è stato settato a N3.5
        frappe.msgprint(
            "Il cliente è soggetto a lettera di intento. Il motivo esenzione IVA è stato settato a N3.5 e il bollo virtuale è stato settato a 1"
        )

    manage_split_payment(doc, method)
