# Copyright (c) 2024, Solede SA and contributors
# For license information, please see license.txt

import frappe
import json
from frappe.model.document import Document
from italian_invoice.utilities.fatture import (
    get_supplier_vat_from_json,
    get_invoice_number_from_json,
    get_invoice_lines_from_json,
    get_invoice_total_from_json,
    get_fattura_body
)


class FatturaFornitoriSDI(Document):
    @frappe.whitelist()
    def get_supplier_vat(self):
        """Estrae la P.IVA del fornitore dai dati fattura"""
        if not self.dati_fattura:
            frappe.throw("Dati fattura non disponibili")

        return get_supplier_vat_from_json(json.loads(self.dati_fattura) if isinstance(self.dati_fattura, str) else self.dati_fattura)

    @frappe.whitelist()
    def get_invoice_number(self):
        """Estrae il numero fattura dai dati fattura"""
        if not self.dati_fattura:
            frappe.throw("Dati fattura non disponibili")

        return get_invoice_number_from_json(json.loads(self.dati_fattura) if isinstance(self.dati_fattura, str) else self.dati_fattura)

    @frappe.whitelist()
    def get_invoice_lines(self):
        """Estrae le linee fattura dai dati fattura"""
        if not self.dati_fattura:
            frappe.throw("Dati fattura non disponibili")

        return get_invoice_lines_from_json(json.loads(self.dati_fattura) if isinstance(self.dati_fattura, str) else self.dati_fattura)

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
        dati = json.loads(self.dati_fattura) if isinstance(self.dati_fattura, str) else self.dati_fattura
        body = get_fattura_body(dati)
        if not body:
            return None

        return body.get("dati_generali", {}).get("dati_generali_documento", {}).get("tipo_documento")

    def _get_numero_fattura(self):
        """Estrae il numero fattura dai dati fattura"""
        try:
            dati = json.loads(self.dati_fattura) if isinstance(self.dati_fattura, str) else self.dati_fattura
            return get_invoice_number_from_json(dati)
        except:
            return None

    def _get_importo_totale(self):
        """Estrae l'importo totale imponibile dai dati fattura"""
        try:
            dati = json.loads(self.dati_fattura) if isinstance(self.dati_fattura, str) else self.dati_fattura
            return get_invoice_total_from_json(dati)
        except:
            return None
