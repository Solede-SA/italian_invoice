import frappe


@frappe.whitelist()
def get_default_bank_account(**kwargs):
    lista = frappe.get_list(
        "Bank Account",
        filters={
            "company": kwargs["company"],
            "is_default": 1,
            "is_company_account": 1,
        },
        fields=["name"],
    )

    if len(lista) > 0:
        return lista[0]
    else:
        return None
