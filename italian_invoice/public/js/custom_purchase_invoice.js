frappe.ui.form.on("Purchase Invoice", {
  refresh: (frm) => {
    if (frm.doc.docstatus == 0 || frm.doc.docstatus == 1) {
      frm.add_custom_button(
        __("Scarica XML"),
        () => {
          frm.call({
            method: "italian_invoice.utilities.fatture.validate_invoice",
            args: {
              docname: frm.doc.name,
              doctype: frm.doc.doctype,
            },
            callback: function (r) {
              frm.reload_doc();
              if (r.message) {
                open_url_post(frappe.request.url, {
                  cmd: "frappe.core.doctype.file.file.download_file",
                  file_url: r.message,
                });
              }
            },
          });
        },
        __("Fatt. Elettronica"),
      );
    }
  },
  supplier: (frm) => {
    if (frm.doc.supplier) {
      frappe.db
        .get_value(
          "Supplier",
          frm.doc.supplier,
          "custom_tipo_fattura_elettronica",
        )
        .then((r) => {
          frm.set_value(
            "custom_tipo_di_documento",
            r.message.custom_tipo_fattura_elettronica,
          );
        });
    }
  },
});
