import frappe
import json
from dateutil.parser import parse
from datetime import datetime
import pytz


def get_data_ok(request):
    data = json.loads(frappe.request.data)
    event = data["event"]
    lista_errori = ""

    if event == "customer-notification":
        uuid = data["data"]["notification"]["invoice_uuid"]
        data_notifica = data["data"]["notification"]["created_at"]
        stato = data["data"]["notification"]["type"]
        # Check if "lista_errori" exists
        lista_errori = data["data"]["notification"]["message"].get("lista_errori", "")

    elif event == "customer-invoice":
        uuid = data["data"]["invoice"]["uuid"]
        data_notifica = data["data"]["invoice"]["created_at"]
        stato = "Inviata"

    lista_fatture = frappe.get_list(
        "Sales Invoice", filters={"custom_uuid": uuid}, fields=["name"]
    )
    if len(lista_fatture) > 0:
        fattura = frappe.get_doc("Sales Invoice", lista_fatture[0]["name"])

        data_ok = {
            "doc_fattura": fattura,
            "event": event,
            "uuid": uuid,
            "original_data": data,
            "data_notifica": data_notifica,
            "stato": stato,
            "lista_errori": lista_errori,
        }

        return data_ok
    else:
        frappe.throw(f"Fattura non trovata: {uuid}")


def save_notifica(data_ok):
    doc = data_ok["doc_fattura"]
    data_notifica_str = data_ok["data_notifica"]
    data_notifica = parse(data_notifica_str)
    # Convertire `data_notifica` in UTC
    rome_tz = pytz.timezone("Europe/Rome")
    # Convertire `data_notifica` al fuso orario di Roma
    data_notifica_rome = data_notifica.astimezone(rome_tz)

    # Formattare la data in un formato compatibile con il database SQL
    formatted_data_notifica = data_notifica_rome.strftime("%Y-%m-%d %H:%M:%S")

    # Convertire `original_data` in un oggetto Python e poi in una stringa JSON indentata
    formatted_original_data = json.dumps(data_ok["original_data"], indent=2)

    doc.append(
        "custom_notifiche_sdi",
        {
            "notifica": data_ok["event"],
            "data": formatted_original_data,
            "data_notifica": formatted_data_notifica,
        },
    )
    doc.custom_ultima_notifica = formatted_original_data
    doc.save()


@frappe.whitelist(allow_guest=False)
def supplier_invoice():
    print(frappe.request.data)
    return "OK from supplier_invoice"


@frappe.whitelist(allow_guest=False)
def cutomer_invoice():
    data_ok = get_data_ok(frappe.request.data)
    data_ok["doc_fattura"].custom_stato_invio = data_ok["stato"]
    data_ok["doc_fattura"].save()

    save_notifica(data_ok)

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
    data_ok = get_data_ok(frappe.request.data)
    data_ok["doc_fattura"].custom_stato_invio = data_ok["stato"]
    data_ok["doc_fattura"].save()

    save_notifica(data_ok)

    return "OK from customer_notification"


@frappe.whitelist(allow_guest=False)
def legal_storage_missing_vat():
    print(frappe.request.data)
    return "OK from legal_storage_missing_vat"


@frappe.whitelist(allow_guest=False)
def legal_storage_receipt():
    print(frappe.request.data)
    return "OK from legal_storage_receipt"
