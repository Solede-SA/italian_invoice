import io
import json
import re

import frappe
from frappe import _
from frappe.utils import cstr, flt
from frappe.utils.file_manager import remove_file
from frappe.utils import today
from xmlschema import validate

from erpnext.controllers.taxes_and_totals import get_itemised_tax
from erpnext.regional.italy import state_codes


def get_prefixed_company_tax_id(company_tax_id):
    return company_tax_id if company_tax_id.startswith("IT") else "IT" + company_tax_id


def clean_phone(s):
    if s is None:
        return s
    # Rimuove le parentesi mantenendo gli spazi
    s = re.sub(r"[()]", "", s)
    # Rimuove i numeri tra + e il primo spazio successivo
    s = re.sub(r"\+\d+\s", "", s)
    # Rimuove tutti i caratteri non numerici
    s = re.sub(r"\D", "", s)
    return s


def get_billing_address(doc, invoice):
    if doc.doctype == "Customer":
        return frappe.get_doc("Address", invoice.customer_address)

    if doc.doctype == "Supplier":
        return frappe.get_doc("Address", invoice.supplier_address)

    if doc.doctype == "Company":
        address = frappe.db.get_values(
            "Address",
            {"is_primary_address": 1, "is_your_company_address": 1},
            ["*"],
            as_dict=True,
        )

        return address[0]


def get_company_data(doc):
    company = frappe.get_doc("Company", doc.company, as_dict=True)
    billing_address = get_billing_address(company, doc)

    company_data = {
        "country_code": "IT",
        "tax_id": company.tax_id,
        "fiscal_code": company.fiscal_code,
        "fiscal_regime": company.fiscal_regime,
        "contact": {
            "phone": clean_phone(company.phone_no),
            "email": company.email,
        },
        "registration_data": {
            "registration_number": company.registration_number,
            "registrar_office_province": company.registrar_office_province,
            "share_capital_amount": company.share_capital_amount,
            "no_of_members": company.no_of_members,
            "liquidation_state": company.liquidation_state,
        },
        "address": {
            "address_line1": billing_address.address_line1,
            "pincode": billing_address.pincode,
            "city": billing_address.city,
            "state_code": billing_address.state,
            "country_code": billing_address.country_code,
        },
    }

    return company_data


def get_codice_destinatario(party):
    codice_destinatario = None
    if party.doctype == "Company":
        codice_destinatario = party.custom_codice_sistema_interscambio

    if party.doctype == "Customer":
        codice_destinatario = party.custom_codice_univoco

    return codice_destinatario


def get_party_name(party):
    name = None
    if party.doctype == "Company":
        name = party.company_name

    if party.doctype == "Customer":
        name = party.customer_name

    if party.doctype == "Supplier":
        name = party.supplier_name

    return name


def get_party_data(party, invoice):
    billing_address = get_billing_address(party, invoice)

    party_data = {
        "doctype": party.doctype,
        "fiscal_code": party.fiscal_code,
        "tax_id": party.tax_id,
        "recipient_code": get_codice_destinatario(party),
        "name": get_party_name(party),
        "type": "Company" if party.tax_id else "Individual",
        "fiscal_regime": party.fiscal_regime if party.doctype == "Company" else None,
        "is_public_administration": (
            party.is_public_administration if party.doctype == "Customer" else None
        ),
        "address": {
            "address_line1": billing_address.address_line1,
            "pincode": billing_address.pincode,
            "city": billing_address.city,
            "state_code": billing_address.state,
            "country_code": billing_address.country_code,
        },
        "contact": {
            "phone": clean_phone(billing_address.phone),
            "email": billing_address.email_id,
        },
    }

    return party_data


def get_cessionario_committente(doc):
    doctype = doc.doctype
    cessionario = None

    if doctype == "Sales Invoice":
        cessionario = frappe.get_doc("Customer", doc.customer, as_dict=True)
    elif doctype == "Purchase Invoice":
        cessionario = frappe.get_doc("Company", doc.company, as_dict=True)

    cessionario_committente = get_party_data(cessionario, doc)
    return cessionario_committente


def get_cedente_prestatore(doc):
    doctype = doc.doctype
    cedente = None

    if doctype == "Sales Invoice":
        cedente = frappe.get_doc("Company", doc.company, as_dict=True)
    elif doctype == "Purchase Invoice":
        cedente = frappe.get_doc("Supplier", doc.supplier, as_dict=True)

    cedente_prestatore = get_party_data(cedente, doc)
    return cedente_prestatore


def get_invoice_data(doc):
    company_data = get_company_data(doc)
    cessionario_committente = get_cessionario_committente(doc)
    cedente_prestatore = get_cedente_prestatore(doc)
    e_invoice_items = [item for item in doc.items]

    tipo_di_documento = frappe.get_doc(
        "Tipologia di documento e-Invoice", doc.custom_tipo_di_documento
    )

    if doc.return_against:
        returned_against_doc = frappe.get_doc("Sales Invoice", doc.return_against)

    transmission_format_code = "FPR12"
    if cessionario_committente["is_public_administration"] == 1:
        transmission_format_code = "FPA12"

    data = {
        "causale": doc.doctype,
        "transmission_format_code": transmission_format_code,
        "progressive_number": get_progressive_name(doc),
        "type_of_document": tipo_di_documento.codice,
        "currency": "EUR",
        "posting_date": str(today()),
        "unamended_name": get_unamended_name(doc),
        "return_against_unamended": (
            get_unamended_name(returned_against_doc) if doc.return_against else None
        ),
        "return_against_date": (
            returned_against_doc.posting_date if doc.return_against else None
        ),
        "grand_total": doc.grand_total,
        "rounded_total": doc.rounded_total,
        "additional_discount_percentage": doc.additional_discount_percentage,
        "discount_amount": doc.discount_amount,
        "net_total": doc.net_total,
        "total_taxes_and_charges": doc.total_taxes_and_charges,
        "company_data": company_data,
        "cessionario_committente": cessionario_committente,
        "cedente_prestatore": cedente_prestatore,
        "e_invoice_items": e_invoice_items,
        "tax_data": get_invoice_summary(e_invoice_items, doc.taxes),
        "payment_schedule": doc.payment_schedule,
        "apply_discount_on": doc.apply_discount_on,
        # "stamp_duty": doc.stamp_duty,
    }

    if doc.doctype == "Purchase Invoice":
        data["soggetto_emittente"] = "CC"
        data["bill_no"] = doc.bill_no
        data["bill_date"] = str(doc.bill_date)

    return data


# def update_itemised_tax_data(doc):
#     if not doc.taxes:
#         return

#     if doc.doctype == "Purchase Invoice":
#         return

#     itemised_tax = get_itemised_tax(doc.taxes)

#     for row in doc.items:
#         tax_rate = 0.0
#         if itemised_tax.get(row.item_code):
#             tax_rate = sum(
#                 [
#                     tax.get("tax_rate", 0)
#                     for d, tax in itemised_tax.get(row.item_code).items()
#                 ]
#             )

#         row.tax_rate = flt(tax_rate, row.precision("tax_rate"))
#         row.tax_amount = flt(
#             (row.net_amount * tax_rate) / 100, row.precision("net_amount")
#         )
#         row.total_amount = flt(
#             (row.net_amount + row.tax_amount), row.precision("total_amount")
#         )


# @frappe.whitelist()
# def export_invoices(filters=None):
#     frappe.has_permission("Sales Invoice", throw=True)

#     invoices = frappe.get_all(
#         "Sales Invoice",
#         filters=get_conditions(filters),
#         fields=["name", "company_tax_id"],
#     )

#     attachments = get_e_invoice_attachments(invoices)

#     zip_filename = "{0}-einvoices.zip".format(
#         frappe.utils.get_datetime().strftime("%Y%m%d_%H%M%S")
#     )

#     download_zip(attachments, zip_filename)


# def prepare_invoice(invoice, progressive_number):
#     # set CEDENTE information
#     cedente = get_cedente_prestatore(invoice)
#     cedenteAddress = get_billing_address (cedente)

#     invoice.progressive_number = progressive_number
#     invoice.unamended_name = get_unamended_name(invoice)
#     invoice.company_data = cedente
#     invoice.company_address_data = cedenteAddress
#     invoice.type_of_document = invoice.custom_tipo_di_documento

#     # # set cessionario information
#     cessionario = get_cessionario_committente(invoice)
#     cessionarioAddress = get_billing_address(cessionario)
#     invoice.customer_data = cessionario
#     invoice.customer_address_data = cessionarioAddress
#     invoice.transmission_format_code = "FPR12"

#     if invoice.doctype == "Sales Invoice":
#         if invoice.shipping_address_name:
#             invoice.shipping_address_data = frappe.get_doc(
#                 "Address", invoice.shipping_address_name
#             )

#         if invoice.customer_data.is_public_administration:
#             invoice.transmission_format_code = "FPA12"

#     invoice.e_invoice_items = [item for item in invoice.items]
#     tax_data = get_invoice_summary(invoice.e_invoice_items, invoice.taxes)
#     invoice.tax_data = tax_data

#     # Check if stamp duty (Bollo) of 2 EUR exists.
#     stamp_duty_charge_row = next(
#         (
#             tax
#             for tax in invoice.taxes
#             if tax.charge_type == "Actual" and tax.tax_amount == 2.0
#         ),
#         None,
#     )
#     if stamp_duty_charge_row:
#         invoice.stamp_duty = stamp_duty_charge_row.tax_amount

#     for item in invoice.e_invoice_items:
#         if item.tax_rate == 0.0 and item.tax_amount == 0.0 and tax_data.get("0.0"):
#             item.tax_exemption_reason = tax_data["0.0"]["tax_exemption_reason"]

#     if invoice.doctype == "Sales Invoice":
#         customer_po_data = {}
#         for d in invoice.e_invoice_items:
#             if (
#                 d.customer_po_no
#                 and d.customer_po_date
#                 and d.customer_po_no not in customer_po_data
#             ):
#                 customer_po_data[d.customer_po_no] = d.customer_po_date

#         invoice.customer_po_data = customer_po_data

#     return invoice


# def get_conditions(filters):
#     filters = json.loads(filters)

#     conditions = {"docstatus": 1, "company_tax_id": ("!=", "")}

#     if filters.get("company"):
#         conditions["company"] = filters["company"]
#     if filters.get("customer"):
#         conditions["customer"] = filters["customer"]

#     if filters.get("from_date"):
#         conditions["posting_date"] = (">=", filters["from_date"])
#     if filters.get("to_date"):
#         conditions["posting_date"] = ("<=", filters["to_date"])

#     if filters.get("from_date") and filters.get("to_date"):
#         conditions["posting_date"] = (
#             "between",
#             [filters.get("from_date"), filters.get("to_date")],
#         )

#     return conditions


# def download_zip(files, output_filename):
#     import zipfile

#     zip_stream = io.BytesIO()
#     with zipfile.ZipFile(zip_stream, "w", zipfile.ZIP_DEFLATED) as zip_file:
#         for file in files:
#             file_path = frappe.utils.get_files_path(
#                 file.file_name, is_private=file.is_private
#             )

#             zip_file.write(file_path, arcname=file.file_name)

#     frappe.local.response.filename = output_filename
#     frappe.local.response.filecontent = zip_stream.getvalue()
#     frappe.local.response.type = "download"
#     zip_stream.close()


def get_invoice_summary(items, taxes):
    summary_data = frappe._dict()
    for tax in taxes:
        # Include only VAT charges.
        if tax.charge_type == "Actual":
            continue

        # Charges to appear as items in the e-invoice.
        if tax.charge_type in ["On Previous Row Total", "On Previous Row Amount"]:
            reference_row = next(
                (row for row in taxes if row.idx == int(tax.row_id or 0)), None
            )
            if reference_row:
                items.append(
                    frappe._dict(
                        idx=len(items) + 1,
                        item_code=reference_row.description,
                        item_name=reference_row.description,
                        description=reference_row.description,
                        rate=reference_row.tax_amount,
                        qty=1.0,
                        amount=reference_row.tax_amount,
                        stock_uom=frappe.db.get_single_value(
                            "Stock Settings", "stock_uom"
                        )
                        or _("Nos"),
                        tax_rate=tax.rate * 1,
                        tax_amount=(reference_row.tax_amount * tax.rate) / 100,
                        net_amount=reference_row.tax_amount,
                        taxable_amount=reference_row.tax_amount,
                        item_tax_rate={tax.account_head: tax.rate * 1},
                        charges=True,
                    )
                )

        # Check item tax rates if tax rate is zero.
        if tax.rate == 0:
            for item in items:
                item_tax_rate = item.item_tax_rate
                if isinstance(item.item_tax_rate, str):
                    item_tax_rate = json.loads(item.item_tax_rate)

                if item_tax_rate and tax.account_head in item_tax_rate:
                    key = cstr(item_tax_rate[tax.account_head])
                    if key not in summary_data:
                        summary_data.setdefault(
                            key,
                            {
                                "tax_amount": 0.0,
                                "taxable_amount": 0.0,
                                "tax_exemption_reason": "",
                                "tax_exemption_law": "",
                            },
                        )

                    summary_data[key]["tax_amount"] += item.tax_amount
                    summary_data[key]["taxable_amount"] += item.net_amount
                    if key == "0.0":
                        summary_data[key][
                            "tax_exemption_reason"
                        ] = tax.tax_exemption_reason
                        summary_data[key]["tax_exemption_law"] = tax.tax_exemption_law

            if summary_data.get("0.0") and tax.charge_type in [
                "On Previous Row Total",
                "On Previous Row Amount",
            ]:
                summary_data[key]["taxable_amount"] = tax.total

            if (
                summary_data == {}
            ):  # Implies that Zero VAT has not been set on any item.
                summary_data.setdefault(
                    "0.0",
                    {
                        "tax_amount": 0.0,
                        "taxable_amount": tax.total,
                        "tax_exemption_reason": tax.tax_exemption_reason,
                        "tax_exemption_law": tax.tax_exemption_law,
                    },
                )

        else:
            print("add_deduct_tax", tax.add_deduct_tax)
            if tax.add_deduct_tax == "Add":
                item_wise_tax_detail = json.loads(tax.item_wise_tax_detail)
                for rate_item in [
                    tax_item
                    for tax_item in item_wise_tax_detail.items()
                    if tax_item[1][0] == tax.rate
                ]:
                    key = cstr(tax.rate)
                    if not summary_data.get(key):
                        summary_data.setdefault(
                            key, {"tax_amount": 0.0, "taxable_amount": 0.0}
                        )
                    summary_data[key]["tax_amount"] += rate_item[1][1]
                    summary_data[key]["taxable_amount"] += sum(
                        [
                            item.net_amount
                            for item in items
                            if item.item_code == rate_item[0]
                        ]
                    )

                for item in items:
                    key = cstr(tax.rate)
                    if item.get("charges"):
                        if not summary_data.get(key):
                            summary_data.setdefault(key, {"taxable_amount": 0.0})
                        summary_data[key]["taxable_amount"] += item.taxable_amount

    return summary_data


# # Ensure payment details are valid for e-invoice.
# def sales_invoice_on_submit(doc, method):
#     # Validate payment details
#     if get_company_country(doc.company) not in [
#         "Italy",
#         "Italia",
#         "Italian Republic",
#         "Repubblica Italiana",
#     ]:
#         return

#     if not len(doc.payment_schedule):
#         frappe.throw(
#             _("Please set the Payment Schedule"),
#             title=_("E-Invoicing Information Missing"),
#         )
#     else:
#         for schedule in doc.payment_schedule:
#             if not schedule.mode_of_payment:
#                 frappe.throw(
#                     _(
#                         "Row {0}: Please set the Mode of Payment in Payment Schedule"
#                     ).format(schedule.idx),
#                     title=_("E-Invoicing Information Missing"),
#                 )
#             elif not frappe.db.get_value(
#                 "Mode of Payment", schedule.mode_of_payment, "mode_of_payment_code"
#             ):
#                 frappe.throw(
#                     _(
#                         "Row {0}: Please set the correct code on Mode of Payment {1}"
#                     ).format(schedule.idx, schedule.mode_of_payment),
#                     title=_("E-Invoicing Information Missing"),
#                 )

#     prepare_and_attach_invoice(doc)


# @frappe.whitelist()
# def generate_single_invoice(docname, doctype):
#     doc = frappe.get_doc(doctype, docname)
#     frappe.has_permission(doctype, doc=doc, throw=True)
#     e_invoice = prepare_and_attach_invoice(doc)

#     return e_invoice


# Delete e-invoice attachment on cancel.
# def sales_invoice_on_cancel(doc, method):
#     if get_company_country(doc.company) not in [
#         "Italy",
#         "Italia",
#         "Italian Republic",
#         "Repubblica Italiana",
#     ]:
#         return

#     for attachment in get_e_invoice_attachments(doc):
#         remove_file(
#             attachment.name, attached_to_doctype=doc.doctype, attached_to_name=doc.name
#         )


# def get_company_country(company):
#     return frappe.get_cached_value("Company", company, "country")


def get_e_invoice_attachments(doc):
    company_data = get_company_data(doc)
    company_tax_id = get_prefixed_company_tax_id(company_data["tax_id"])

    attachments = frappe.get_all(
        "File",
        fields=("name", "file_name", "attached_to_name", "is_private"),
        filters={
            "attached_to_name": doc.name,
            "attached_to_doctype": doc.doctype,
        },
    )

    out = []
    for attachment in attachments:
        if (
            attachment.file_name
            and attachment.file_name.endswith(".xml")
            and attachment.file_name.startswith(company_tax_id)
        ):
            out.append(attachment)

    return out


# def validate_address(address_name):
#     fields = ["pincode", "city", "country_code"]
#     data = frappe.get_cached_value("Address", address_name, fields, as_dict=1) or {}

#     for field in fields:
#         if not data.get(field):
#             frappe.throw(
#                 _("Please set {0} for address {1}").format(
#                     field.replace("-", ""), address_name
#                 ),
#                 title=_("E-Invoicing Information Missing"),
#             )


def get_unamended_name(doc):
    attributes = ["naming_series", "amended_from"]
    for attribute in attributes:
        if not hasattr(doc, attribute):
            return doc.name

    unamended_name = doc.name

    if doc.amended_from:
        unamended_name = doc.amended_from.split("-")[0]

    return unamended_name


def get_progressive_name(doc):
    name = get_unamended_name(doc)
    return name.split("/")[-1]


# def set_state_code(doc, method):
#     if doc.get("country_code"):
#         doc.country_code = doc.country_code.upper()

#     if not doc.get("state"):
#         return

#     if not (
#         hasattr(doc, "state_code")
#         and doc.country
#         in ["Italy", "Italia", "Italian Republic", "Repubblica Italiana"]
#     ):
#         return

#     state_codes_lower = {key.lower(): value for key, value in state_codes.items()}

#     state = doc.get("state", "").lower()
#     if state_codes_lower.get(state):
#         doc.state_code = state_codes_lower.get(state)


# def get_progressive_name_and_number(doc, replace=False):
#     company_data = get_company_data(doc)
#     if replace:
#         for attachment in get_e_invoice_attachments(doc):
#             remove_file(
#                 attachment.name,
#                 attached_to_doctype=doc.doctype,
#                 attached_to_name=doc.name,
#             )
#             filename = attachment.file_name.split(".xml")[0]
#             return filename, filename.split("_")[1]

#     company_tax_id = (
#         company_data["tax_id"]
#         if company_data["tax_id"].startswith("IT")
#         else "IT" + company_data["tax_id"]
#     )
#     progressive_name = frappe.model.naming.make_autoname(company_tax_id + "_.#####")
#     progressive_number = progressive_name.split("_")[1]

#     return progressive_name, progressive_number


def get_e_invoice_file_name(doc):
    company_data = get_company_data(doc)
    company_tax_id = get_prefixed_company_tax_id(company_data["tax_id"])
    invoice_number = get_progressive_name(doc)
    return company_tax_id + "_" + invoice_number + ".xml"


def remove_e_invoice_attachments(doc):
    for attachment in get_e_invoice_attachments(doc):
        remove_file(
            attachment.name, attached_to_doctype=doc.doctype, attached_to_name=doc.name
        )


def prepare_and_attach_invoice(doc):
    remove_e_invoice_attachments(doc)
    invoice = get_invoice_data(doc)
    xml_filename = get_e_invoice_file_name(doc)

    invoice_xml = frappe.render_template(
        "italian_invoice/templates/fatture/new-e-invoice.xml",
        context={"doc": invoice},
        is_path=True,
    )

    invoice_xml = invoice_xml.replace("&", "&amp;")

    _file = frappe.get_doc(
        {
            "doctype": "File",
            "file_name": xml_filename,
            "attached_to_doctype": doc.doctype,
            "attached_to_name": doc.name,
            "is_private": True,
            "content": invoice_xml,
        }
    )
    _file.save()
    return _file


@frappe.whitelist()
def validate_invoice(docname, doctype):
    doc = frappe.get_doc(doctype, docname)
    frappe.has_permission(doctype, doc=doc, throw=True)

    e_invoice_fileDoc = prepare_and_attach_invoice(doc)
    xml_file = frappe.get_site_path("private", "files", e_invoice_fileDoc.file_name)
    xsd_file = frappe.get_app_path("italian_invoice", "utilities/schema_vfpr12.xsd")

    try:
        validate(xml_file, xsd_file)
        print("Il file XML è valido")
    except Exception as e:
        # Stampa dettagli dell'errore
        frappe.throw(
            _("Errore di validazione: {0}").format(e), title=_("Errore di validazione")
        )

    return e_invoice_fileDoc.file_url
