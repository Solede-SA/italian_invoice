# Copyright (c) 2024, Solede SA and contributors
# For license information, please see license.txt

import frappe
import json
from frappe.model.document import Document
from italian_invoice.utilities.fatture import get_value_from_json_paths


def _get_fattura_body_from_json(dati_fattura):
    """
    Funzione DRY per estrarre il fattura_elettronica_body dal JSON

    Args:
        dati_fattura: JSON della fattura (str o dict)

    Returns:
        Il primo elemento del fattura_elettronica_body o None
    """
    paths = [
        ["data", "data", "invoice", "payload", "fattura_elettronica_body"],
        ["data", "invoice", "payload", "fattura_elettronica_body"],
        ["invoice", "payload", "fattura_elettronica_body"],
        ["invoice", "fattura_elettronica_body"],
        ["fattura_elettronica_body"]
    ]

    body = get_value_from_json_paths(dati_fattura, paths)
    return body[0] if body and len(body) > 0 else None


class FatturaFornitoriSDI(Document):
    @frappe.whitelist()
    def get_supplier_vat(self):
        """Estrae la P.IVA del fornitore dai dati fattura"""
        if not self.dati_fattura:
            frappe.throw("Dati fattura non disponibili")

        paths = [
            ["data", "data", "invoice", "payload", "fattura_elettronica_header", "cedente_prestatore", "dati_anagrafici", "id_fiscale_iva", "id_codice"],
            ["data", "invoice", "payload", "fattura_elettronica_header", "cedente_prestatore", "dati_anagrafici", "id_fiscale_iva", "id_codice"],
            ["invoice", "payload", "fattura_elettronica_header", "cedente_prestatore", "dati_anagrafici", "id_fiscale_iva", "id_codice"],
            ["payload", "fattura_elettronica_header", "cedente_prestatore", "dati_anagrafici", "id_fiscale_iva", "id_codice"]
        ]

        result = get_value_from_json_paths(self.dati_fattura, paths)
        if not result:
            frappe.throw("Impossibile estrarre la P.IVA del fornitore dal JSON")

        return result

    @frappe.whitelist()
    def get_invoice_number(self):
        """Estrae il numero fattura dai dati fattura"""
        numero = self._get_numero_fattura()
        if not numero:
            frappe.throw("Impossibile estrarre il numero fattura dal JSON")
        return numero

    @frappe.whitelist()
    def get_invoice_lines(self):
        """Estrae le linee fattura dai dati fattura"""
        body = _get_fattura_body_from_json(self.dati_fattura)
        if not body:
            frappe.throw("Impossibile estrarre le linee fattura dal JSON")

        lines = body.get("dati_beni_servizi", {}).get("dettaglio_linee", [])
        if not lines:
            frappe.throw("Nessuna linea fattura trovata nel JSON")

        return lines

    def validate(self):
        # Validazioni di sicurezza per produzione
        if not frappe.conf.get('developer_mode'):
            if self.is_new() and not self.get('via_webhook'):
                frappe.throw('In production mode, new records can only be created via webhook')

            if not self.is_new() and (self.has_value_changed('dati_fattura') or self.has_value_changed('uuid')):
                frappe.throw('In production mode, invoice data cannot be modified directly')

        # Estrai numero fattura e importo totale dal JSON
        if self.dati_fattura:
            if not self.numero_fattura:
                numero = self._get_numero_fattura()
                if numero:
                    self.numero_fattura = numero

            if not self.importo_totale:
                importo = self._get_importo_totale()
                if importo:
                    self.importo_totale = importo

        # Autofatture non devono essere segnate come "Da importare"
        if self.is_new() and self.dati_fattura:
            tipo_documento = self._get_tipo_documento()
            if tipo_documento in ["TD17", "TD18", "TD19", "TD20"]:
                self.stato = "Importata"

    def _get_tipo_documento(self):
        """Estrae il tipo documento dai dati fattura"""
        body = _get_fattura_body_from_json(self.dati_fattura)
        if not body:
            return None

        return body.get("dati_generali", {}).get("dati_generali_documento", {}).get("tipo_documento")

    def _get_numero_fattura(self):
        """Estrae il numero fattura dai dati fattura"""
        body = _get_fattura_body_from_json(self.dati_fattura)
        if not body:
            return None

        return body.get("dati_generali", {}).get("dati_generali_documento", {}).get("numero")

    def _get_importo_totale(self):
        """Estrae l'importo totale imponibile dai dati fattura"""
        body = _get_fattura_body_from_json(self.dati_fattura)
        if not body:
            return None

        riepilogo = body.get("dati_beni_servizi", {}).get("dati_riepilogo", [])
        if not riepilogo:
            return None

        # Somma tutti gli imponibili
        try:
            totale = sum(float(riga.get("imponibile_importo", 0)) for riga in riepilogo)
            return totale
        except:
            return None
