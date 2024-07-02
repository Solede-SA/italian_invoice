frappe.ui.form.on("Sales Invoice", {
  refresh: (frm) => {
    frm.remove_custom_button("Generate E-Invoice");
    frm.set_df_property('vat_collectability', 'read_only', 0)
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
  onload_post_render: (frm) => {
    if (frm.doc.is_return) {
      frm.set_value("custom_tipo_di_documento", "TD04");
      frm.set_value("naming_series", "NCRED/.YY./");
    }
      
    
  },
  is_return: (frm) => {
    if (frm.doc.is_return) {
      frm.set_value("custom_tipo_di_documento", "TD04");
      frm.set_value("naming_series", "NCRED/.YY./");
    }
      
  },
  is_debit_note : (frm) => {
    if (frm.doc.is_debit_note){
      frm.set_value("custom_tipo_di_documento", "TD05");
    }
  },
  customer: (frm) => {
    if (frm.doc.customer) {
      frappe.db
        .get_value(
          "Customer",
          frm.doc.customer,
          ['custom_tipo_fattura_elettronica', 'custom_vat_collectability'],
        )
        .then((r) => {
          frm.set_value({
            custom_tipo_di_documento: r.message.custom_tipo_fattura_elettronica,
            vat_collectability: r.message.custom_vat_collectability
          })
        });
    }
  },
  validate : (frm) => {
    if (frm.doc.is_return && frm.doc.custom_tipo_di_documento !== "TD04") 
      frappe.throw(__("Tipo di documento must be TD04 for return invoice"));
    if (frm.doc.is_debit_note && frm.doc.custom_tipo_di_documento !== "TD05")
      frappe.throw(__("Tipo di documento must be TD05 for debit note"));
  }
});
