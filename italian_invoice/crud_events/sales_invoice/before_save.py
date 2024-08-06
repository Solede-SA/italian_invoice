import frappe


def execute(doc, method=None):
    customer = frappe.get_doc("Customer", doc.customer)
    # if doc.is_return:
    #     return

    # if customer.is_public_administration and doc.naming_series != "PAINIV/.YY./":
    #     frappe.throw(
    #         (
    #             "La fattura è stata creata per un utente privato. Puoi midificare il cliente associando solo un altro cliente privato"
    #         )
    #     )

    # if not customer.is_public_administration and doc.naming_series != "SINV/.YY./":
    #     frappe.throw(
    #         (
    #             "La fattura è stata creata per un utente pubblico. Puoi midificare il cliente associando solo un altro cliente pubblico"
    #         )
    #     )
