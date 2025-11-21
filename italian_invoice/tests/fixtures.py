"""Test fixtures for Italian Invoice app."""

import json
import os

import frappe


def before_tests():
	"""Setup test fixtures before running tests."""
	frappe.flags.in_test = True

	# Create master data that ERPNext needs but doesn't have test_records.json for
	_create_missing_master_data()

	# Override Company test records with our custom ones that include custom fields
	_override_company_test_records()


def _create_missing_master_data():
	"""Create master data that ERPNext requires but doesn't have test_records.json for.

	ERPNext creates these in install_fixtures.py during setup wizard,
	but not in test_records.json. Following the same pattern as ERPNext's own tests.
	"""
	# Warehouse Types required by Company.create_default_warehouses()
	# See: erpnext/stock/doctype/material_request/test_material_request.py
	warehouse_types = ["Transit", "Regular", "Fixed Asset"]

	for wh_type in warehouse_types:
		if not frappe.db.exists("Warehouse Type", wh_type):
			frappe.get_doc({"doctype": "Warehouse Type", "name": wh_type}).insert(
				ignore_permissions=True, ignore_if_duplicate=True
			)

	frappe.db.commit()


def _override_company_test_records():
	"""Override Company test records to include custom_codice_sistema_interscambio field."""
	# Monkey patch frappe.get_test_records to add custom field to Company records
	original_get_test_records = frappe.get_test_records

	def patched_get_test_records(doctype, *args, **kwargs):
		records = original_get_test_records(doctype, *args, **kwargs)

		# Add custom_codice_sistema_interscambio to all Company records
		if doctype == "Company" and records:
			for record in records:
				if not record.get("custom_codice_sistema_interscambio"):
					record["custom_codice_sistema_interscambio"] = "0000000"

		return records

	frappe.get_test_records = patched_get_test_records
