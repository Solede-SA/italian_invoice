import frappe


def execute():
	if not frappe.db.has_column("Sales Order", "custom_codice_commessa"):
		return

	# Create new column
	frappe.db.sql(
		"""ALTER TABLE `tabSales Order`
		ADD COLUMN IF NOT EXISTS `custom_codice_endpoint` varchar(140)"""
	)

	# Copy data from old to new
	frappe.db.sql(
		"""UPDATE `tabSales Order`
		SET `custom_codice_endpoint` = `custom_codice_commessa`
		WHERE `custom_codice_commessa` IS NOT NULL AND `custom_codice_commessa` != ''"""
	)

	# Hide old field (keep data as backup)
	frappe.db.sql(
		"""UPDATE `tabCustom Field`
		SET hidden = 1, read_only = 1, label = 'Codice Commessa (deprecato)'
		WHERE name = 'Sales Order-custom_codice_commessa'"""
	)

	# Update Property Setters referencing the old fieldname
	frappe.db.sql(
		"""UPDATE `tabProperty Setter`
		SET value = REPLACE(value, 'custom_codice_commessa', 'custom_codice_endpoint')
		WHERE doc_type = 'Sales Order'
		AND value LIKE '%custom_codice_commessa%'"""
	)

	frappe.db.commit()
