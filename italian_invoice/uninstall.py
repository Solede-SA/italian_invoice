# Copyright (c) 2024-2025, Solede SA and contributors
# For license information, please see license.txt
# License: GNU Affero General Public License v3 or later (AGPLv3+)
# See https://www.gnu.org/licenses/agpl-3.0.html

import json
import os

import frappe


def before_uninstall():
	"""
	Cleanup tasks before Italian Invoice app is uninstalled.

	This function runs BEFORE Frappe removes:
	- Module Def records
	- Custom DocTypes
	- Database tables

	Use this to:
	- Backup data that should be preserved
	- Remove references that would break uninstallation
	- Clean up app-specific customizations
	"""
	backup_customer_data()
	remove_migration_file()


def after_uninstall():
	"""
	Final cleanup after Italian Invoice app is uninstalled.

	This function runs AFTER Frappe has removed:
	- All Module Def records
	- All Custom DocTypes
	- All database tables

	Use this for:
	- Final cleanup tasks
	- User notifications
	- Logging completion
	"""
	print(f"\n{'='*60}")
	print("Italian Invoice uninstallation completed")
	print(f"{'='*60}\n")


def backup_customer_data():
	"""
	Backup custom_first_name and custom_last_name data from Customer doctype.

	Since uninstallation will remove the Custom Fields created by this app,
	we backup the data so it can be restored manually if needed.
	"""
	print(f"\n{'='*60}")
	print("BACKUP DATI CUSTOMER")
	print(f"{'='*60}")

	# Check if custom fields exist
	custom_first_name_exists = frappe.db.exists("Custom Field", "Customer-custom_first_name")
	custom_last_name_exists = frappe.db.exists("Custom Field", "Customer-custom_last_name")

	if not custom_first_name_exists and not custom_last_name_exists:
		print("Campi custom non presenti, nessun backup necessario")
		return

	# Get all customers with data in custom fields
	fields_to_select = ["name"]
	if custom_first_name_exists:
		fields_to_select.append("custom_first_name")
	if custom_last_name_exists:
		fields_to_select.append("custom_last_name")

	customers = frappe.get_all("Customer", fields=fields_to_select)

	# Filter customers with actual data
	customers_data = {}
	for customer in customers:
		data = {}
		if custom_first_name_exists and customer.get("custom_first_name"):
			data["custom_first_name"] = customer["custom_first_name"]
		if custom_last_name_exists and customer.get("custom_last_name"):
			data["custom_last_name"] = customer["custom_last_name"]

		if data:
			customers_data[customer["name"]] = data

	if not customers_data:
		print("Nessun dato da backuppare")
		return

	# Save to backup file
	backup_file = frappe.get_site_path("private", "files", "italian_invoice_customer_backup.json")
	with open(backup_file, "w") as f:
		json.dump(customers_data, f, indent=2)

	print(f"Backup completato: {len(customers_data)} Customer")
	print(f"File salvato in: {backup_file}")
	print(f"{'='*60}\n")


def remove_migration_file():
	"""
	Remove migration file if it still exists from installation.
	"""
	migration_file = frappe.get_site_path("private", "files", "italian_invoice_migration.json")

	if os.path.exists(migration_file):
		try:
			os.remove(migration_file)
			print(f"Rimosso file di migrazione: {migration_file}")
		except Exception as e:
			print(f"Errore rimozione file migrazione: {str(e)}")
