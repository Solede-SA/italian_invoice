import frappe
from frappe import _
from frappe.utils import flt, now

@frappe.whitelist()
def calculate_billing_gap(delivery_note_name):
    """Calcola la differenza di fatturazione per un DDT"""
    dn = frappe.get_doc("Delivery Note", delivery_note_name)

    if dn.docstatus != 1:
        return {
            'billing_gap': 0,
            'can_force_complete': False
        }

    # Calcola il totale da fatturare
    total_amount = sum(flt(item.amount) for item in dn.items)

    # Calcola il totale già fatturato
    total_billed = sum(flt(item.billed_amt) for item in dn.items)

    # Calcola la differenza
    billing_gap = total_amount - total_billed

    # Può essere forzato se la differenza è tra 0 e 1 (non negativa e sotto la soglia)
    can_force_complete = 0 < billing_gap < 1.0

    # Aggiorna il campo custom
    if dn.billing_gap != billing_gap:
        frappe.db.set_value("Delivery Note", delivery_note_name, "billing_gap", billing_gap)

    return {
        'total_amount': total_amount,
        'total_billed': total_billed,
        'billing_gap': billing_gap,
        'per_billed': dn.per_billed,
        'can_force_complete': can_force_complete
    }

@frappe.whitelist()
def force_billing_complete(delivery_note_name, reason):
    """Forza il completamento della fatturazione per piccole differenze"""

    # Verifica permessi
    if not frappe.has_permission("Delivery Note", "write", delivery_note_name):
        frappe.throw(_("You don't have permission to perform this operation"))

    # Calcola il gap attuale
    gap_info = calculate_billing_gap(delivery_note_name)

    if not gap_info['can_force_complete']:
        frappe.throw(_("The billing difference is too large or negative. Cannot force completion."))

    # Crea il log per tracciabilità
    log = frappe.get_doc({
        "doctype": "Delivery Note Billing Adjustment Log",
        "delivery_note": delivery_note_name,
        "adjustment_amount": gap_info['billing_gap'],
        "reason": reason,
        "adjusted_by": frappe.session.user,
        "adjustment_date": now()
    })
    log.insert()

    # Aggiorna il Delivery Note
    dn = frappe.get_doc("Delivery Note", delivery_note_name)

    # Imposta per_billed a 100
    dn.per_billed = 100

    # Aggiorna lo status
    dn.status = "Completed"

    # Salva senza validazione per evitare controlli standard
    dn.flags.ignore_validate_update_after_submit = True
    dn.save(ignore_permissions=True)

    # Aggiungi commento per tracciabilità
    dn.add_comment(
        "Comment",
        f"Billing forced to complete. Gap amount: {gap_info['billing_gap']:.2f}. Reason: {reason}"
    )

    frappe.db.commit()

    frappe.msgprint(
        _("Delivery Note marked as fully billed. Difference: {0}").format(gap_info['billing_gap']),
        alert=True
    )

    return True

@frappe.whitelist()
def revert_billing_adjustment(delivery_note_name):
    """Annulla l'aggiustamento di fatturazione"""

    # Verifica permessi
    if not frappe.has_permission("Delivery Note", "write", delivery_note_name):
        frappe.throw(_("You don't have permission to perform this operation"))

    # Verifica se esiste un aggiustamento
    adjustments = frappe.get_all(
        "Delivery Note Billing Adjustment Log",
        filters={"delivery_note": delivery_note_name},
        order_by="adjustment_date desc",
        limit=1
    )

    if not adjustments:
        frappe.throw(_("No billing adjustment found for this Delivery Note"))

    # Ricalcola il per_billed originale
    dn = frappe.get_doc("Delivery Note", delivery_note_name)

    total_amount = sum(flt(item.amount) for item in dn.items)
    total_billed = sum(flt(item.billed_amt) for item in dn.items)

    if total_amount > 0:
        actual_per_billed = (total_billed / total_amount) * 100
    else:
        actual_per_billed = 0

    # Ripristina il valore originale
    dn.per_billed = actual_per_billed

    # Aggiorna lo status
    if actual_per_billed < 100:
        dn.status = "To Bill"

    # Salva senza validazione
    dn.flags.ignore_validate_update_after_submit = True
    dn.save(ignore_permissions=True)

    # Cancella il log di aggiustamento
    frappe.delete_doc("Delivery Note Billing Adjustment Log", adjustments[0].name)

    # Aggiungi commento
    dn.add_comment(
        "Comment",
        f"Billing adjustment reverted. Restored per_billed to {actual_per_billed:.2f}%"
    )

    frappe.db.commit()

    frappe.msgprint(_("Billing adjustment has been reverted"), alert=True)

    return True

def update_billing_gap_on_save(doc, method):
    """Hook per aggiornare il billing gap quando viene salvato un Delivery Note"""
    if doc.docstatus == 1:
        calculate_billing_gap(doc.name)