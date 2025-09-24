# Copyright (c) 2024, Solede SA and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class FatturaFornitoriSDI(Document):
    def validate(self):
        # Check if we are in development mode
        if not frappe.conf.get('developer_mode'):
            # In production, ensure all fields are read-only for direct editing
            if not self.flags.ignore_validate:
                if self.is_new() and not self.get('via_webhook'):
                    frappe.throw('In production mode, new records can only be created via webhook')
                
                if self.has_value_changed('dati_fattura') or self.has_value_changed('uuid'):
                    frappe.throw('In production mode, invoice data cannot be modified directly')
