frappe.ui.form.on("Customer", {
	refresh: function (frm) {
		// Nascondi i campi standard first_name/last_name per Customer Individual
		// Usiamo i campi custom_first_name/custom_last_name per e-invoicing
		if (frm.doc.customer_type === "Individual") {
			frm.set_df_property("first_name", "hidden", 1);
			frm.set_df_property("last_name", "hidden", 1);
		}
	},

	customer_type: function (frm) {
		// Nascondi/mostra i campi quando cambia customer_type
		if (frm.doc.customer_type === "Individual") {
			frm.set_df_property("first_name", "hidden", 1);
			frm.set_df_property("last_name", "hidden", 1);
		} else {
			frm.set_df_property("first_name", "hidden", 0);
			frm.set_df_property("last_name", "hidden", 0);
		}
	},
});
