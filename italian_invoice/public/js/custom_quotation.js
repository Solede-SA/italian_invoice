frappe.ui.form.on("Quotation", {
    refresh: function (frm) {
        if (frm.doc.custom_bank_account === undefined) {
            frappe.call({
                method: "italian_invoice.api.company.bank.get_default_bank_account",
                args: {
                "company": frm.doc.company,
                },
                callback: function (r) {
                if (r.message) {
                    frm.set_value("custom_bank_account", r.message.name);
                }
                }
            })
        }
    }
});