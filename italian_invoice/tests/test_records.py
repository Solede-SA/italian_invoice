"""Test records for Italian Invoice app."""

test_records = {
	"Company": [
		{
			"doctype": "Company",
			"company_name": "_Test Company",
			"abbr": "_TC",
			"default_currency": "EUR",
			"country": "Italy",
			"custom_codice_sistema_interscambio": "0000000",
		}
	]
}


def get_test_records():
	"""Return test records."""
	return test_records
