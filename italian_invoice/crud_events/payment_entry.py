import frappe
from frappe import _
from frappe.utils import flt


def adjust_allocated_amount_for_rounding(doc, method):
    """
    Aggiusta l'allocated_amount nelle references se la differenza tra paid_amount
    e outstanding_amount è entro la soglia di arrotondamento.
    Questo permette di allocare l'intero importo della fattura anche se pagato leggermente meno.
    """
    if not doc.references or doc.docstatus == 1:
        return

    # Ottieni la soglia dalla Company
    threshold = flt(
        frappe.get_value("Company", doc.company, "payment_rounding_threshold") or 0.50
    )

    adjusted = False

    for ref in doc.references:
        outstanding = flt(ref.outstanding_amount)
        allocated = flt(ref.allocated_amount)

        # Calcola quanto manca da allocare su questa specifica fattura
        remaining = outstanding - allocated

        # Se c'è un importo non allocato positivo (pagato di meno) ed è entro la soglia
        if remaining > 0 and remaining <= threshold:
            # Alloca l'intero importo outstanding
            ref.allocated_amount = outstanding
            adjusted = True

            frappe.msgprint(
                _(
                    "Arrotondamento automatico applicato su fattura {0}: allocati {1} invece di {2} (differenza: {3})"
                ).format(
                    ref.reference_name,
                    frappe.format_value(outstanding, {"fieldtype": "Currency"}),
                    frappe.format_value(allocated, {"fieldtype": "Currency"}),
                    frappe.format_value(remaining, {"fieldtype": "Currency"}),
                ),
                title=_("Allocazione con Arrotondamento"),
                indicator="blue",
            )

    # Forza il ricalcolo di total_allocated_amount, unallocated_amount e difference_amount
    if adjusted:
        doc.set_total_allocated_amount()
        doc.set_unallocated_amount()
        doc.set_difference_amount()


def handle_rounding(doc, method):
    """
    Gestisce l'arrotondamento automatico durante il validate.
    Aggiunge una riga in deductions se la differenza è entro la soglia configurata.
    """
    # DEBUG: Se il documento è già submitted, non fare nulla
    if doc.docstatus == 1:
        return

    # Ottieni la soglia dalla Company
    threshold = flt(
        frappe.get_value("Company", doc.company, "payment_rounding_threshold") or 0.50
    )

    # Determina quale campo gestire: unallocated_amount O difference_amount (non entrambi!)
    total_rounding = 0
    deduction_sign = 0

    if flt(doc.unallocated_amount) > 0:
        # Hanno pagato di più: gestiamo unallocated_amount
        total_rounding = flt(doc.unallocated_amount)
        # Le deductions vengono SOMMATE a unallocated, quindi usiamo negativo per sottrarre
        deduction_sign = -1
    elif abs(flt(doc.difference_amount)) > 0:
        # C'è una differenza da gestire
        total_rounding = abs(flt(doc.difference_amount))
        # Le deductions vengono SOTTRATTE da difference, quindi usiamo positivo per sottrarre
        deduction_sign = 1

    if total_rounding == 0:
        # Rimuovi eventuali righe di arrotondamento precedenti se non servono più
        _remove_existing_rounding_deduction(doc)
        return

    # Se la differenza è entro la soglia, applica l'arrotondamento
    if total_rounding > 0 and total_rounding <= threshold:
        # Ottieni gli account necessari
        rounding_account = frappe.get_value("Company", doc.company, "round_off_account")
        default_cost_center = frappe.get_value("Company", doc.company, "cost_center")

        if not rounding_account:
            frappe.throw(
                _(
                    "Imposta Round Off Account in Company per abilitare l'arrotondamento automatico"
                )
            )
        if not default_cost_center:
            frappe.throw(_("Imposta Default Cost Center in Company"))

        # Cerca o crea la riga di deduzione per l'arrotondamento
        rounding_row = _find_or_create_rounding_deduction(
            doc, rounding_account, default_cost_center
        )
        rounding_row.amount = total_rounding * deduction_sign

        # Forza il ricalcolo di unallocated_amount e difference_amount
        doc.set_unallocated_amount()
        doc.set_difference_amount()

        # Salva i dettagli per il log
        doc._rounding_details = {
            "original_amount": doc.total_allocated_amount,
            "rounded_amount": doc.paid_amount,
            "difference": total_rounding,
            "reference_invoice": (
                doc.references[0].reference_name if doc.references else None
            ),
        }

        # Mostra messaggio informativo all'utente
        frappe.msgprint(
            _(
                "Arrotondamento automatico applicato: {0}<br>Account utilizzato: {1}<br>La differenza di pagamento è stata gestita automaticamente."
            ).format(
                frappe.format_value(total_rounding, {"fieldtype": "Currency"}),
                rounding_account,
            ),
            title=_("Arrotondamento Automatico"),
            indicator="blue",
        )

    elif total_rounding > threshold:
        # Mostra warning se supera la soglia ma non bloccare in validate
        frappe.msgprint(
            _(
                "Attenzione: differenza di {0} supera la soglia di arrotondamento automatico ({1}).<br>Verifica l'importo del pagamento prima del submit."
            ).format(
                frappe.format_value(total_rounding, {"fieldtype": "Currency"}),
                frappe.format_value(threshold, {"fieldtype": "Currency"}),
            ),
            title=_("Differenza Elevata"),
            indicator="orange",
        )


def _find_or_create_rounding_deduction(doc, rounding_account, cost_center):
    """
    Trova la riga di deduzione esistente per l'arrotondamento o ne crea una nuova.
    """
    # Cerca una riga esistente con lo stesso account
    for deduction in doc.deductions:
        if deduction.account == rounding_account:
            # Marca questa riga come arrotondamento automatico
            deduction._is_auto_rounding = True
            return deduction

    # Se non esiste, creane una nuova
    new_row = doc.append(
        "deductions",
        {"account": rounding_account, "cost_center": cost_center, "amount": 0},
    )
    # Marca questa riga come arrotondamento automatico
    new_row._is_auto_rounding = True
    return new_row


def _remove_existing_rounding_deduction(doc):
    """
    Rimuove eventuali righe di arrotondamento se non sono più necessarie.
    """
    rounding_account = frappe.get_value("Company", doc.company, "round_off_account")
    if not rounding_account:
        return

    rows_to_remove = []
    for idx, deduction in enumerate(doc.deductions):
        if deduction.account == rounding_account:
            rows_to_remove.append(idx)

    # Rimuovi le righe in ordine inverso per non alterare gli indici
    for idx in reversed(rows_to_remove):
        doc.remove(doc.deductions[idx])


def validate_rounding_on_submit(doc, method):
    """
    Validazione e preservazione delle deductions prima del submit.
    """
    # Ottieni il round_off_account per identificare le nostre deductions
    rounding_account = frappe.get_value("Company", doc.company, "round_off_account")

    # Conta quante deductions di arrotondamento abbiamo
    rounding_deductions = (
        [d for d in doc.deductions if d.account == rounding_account]
        if rounding_account
        else []
    )

    # Se non ci sono deductions di arrotondamento ma dovrebbero esserci, riapplicale
    if not rounding_deductions:
        # Verifica se serve un arrotondamento
        threshold = flt(
            frappe.get_value("Company", doc.company, "payment_rounding_threshold")
            or 0.50
        )
        total_rounding = 0

        if flt(doc.unallocated_amount) > 0:
            total_rounding = flt(doc.unallocated_amount)
        elif abs(flt(doc.difference_amount)) > 0:
            total_rounding = abs(flt(doc.difference_amount))

        if total_rounding > 0 and total_rounding <= threshold:
            # Le deductions sono state rimosse! Riapplicale
            handle_rounding(doc, method)

    # Validazione finale: blocca se la differenza supera la soglia
    threshold = flt(
        frappe.get_value("Company", doc.company, "payment_rounding_threshold") or 0.50
    )
    total_difference = abs(flt(doc.difference_amount))

    if total_difference > threshold:
        frappe.throw(
            _(
                "Impossibile procedere: differenza di {0} supera la soglia di arrotondamento automatico ({1}).<br>Verifica l'importo del pagamento o le allocazioni."
            ).format(
                frappe.format_value(total_difference, {"fieldtype": "Currency"}),
                frappe.format_value(threshold, {"fieldtype": "Currency"}),
            ),
            title=_("Differenza Troppo Elevata"),
        )

    # Crea il Payment Rounding Log se necessario
    if hasattr(doc, "_rounding_details") and rounding_deductions:
        _create_payment_rounding_log(doc)


def _create_payment_rounding_log(doc):
    """
    Crea il Payment Rounding Log.
    """
    if not hasattr(doc, "_rounding_details"):
        return

    reference_invoice = doc._rounding_details.get("reference_invoice")
    reference_type = None

    if reference_invoice:
        if frappe.db.exists("Sales Invoice", reference_invoice):
            reference_type = "Sales Invoice"
        elif frappe.db.exists("Purchase Invoice", reference_invoice):
            reference_type = "Purchase Invoice"

    frappe.get_doc(
        {
            "doctype": "Payment Rounding Log",
            "payment_entry": doc.name,
            "reference_invoice": reference_invoice,
            "reference_type": reference_type,
            "original_amount": doc._rounding_details["original_amount"],
            "rounded_amount": doc._rounding_details["rounded_amount"],
            "difference": doc._rounding_details["difference"],
        }
    ).insert(ignore_permissions=True)


def after_insert(doc, method):
    """
    Crea il log dopo l'inserimento di un nuovo Payment Entry.
    """
    if hasattr(doc, "_rounding_details"):
        _create_payment_rounding_log(doc)
