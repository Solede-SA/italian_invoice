"""Test fixtures for Italian Invoice app."""

import json
import os

import frappe


def before_tests():
	"""Setup test fixtures before running tests."""
	frappe.flags.in_test = True

	# Override Company test records with our custom ones that include custom fields
	_override_company_test_records()


def _override_company_test_records():
	"""Override Company test records to include custom_codice_sistema_interscambio field."""
	# Load our custom test records
	custom_records_path = os.path.join(
		os.path.dirname(__file__), "..", "overrides", "company_test_records.json"
	)

	if os.path.exists(custom_records_path):
		with open(custom_records_path) as f:
			custom_records = json.load(f)

		# Monkey patch frappe.get_test_records for Company to return our custom records
		original_get_test_records = frappe.get_test_records

		def patched_get_test_records(doctype, *args, **kwargs):
			if doctype == "Company":
				return custom_records
			return original_get_test_records(doctype, *args, **kwargs)

		frappe.get_test_records = patched_get_test_records
