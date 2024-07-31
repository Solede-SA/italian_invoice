const getCustomerTipoFatturaElettronica = (frm) => {
  if (frm.doc.is_return) {
    frm.set_value("custom_tipo_di_documento", "TD04");
    frm.set_value("naming_series", "NCINV/.YY./");
    return true;
  }
  // if (frm.doc.custom_tipo_di_documento) {
  //   return true;
  // }
  if (frm.doc.customer) {
      frappe.db
        .get_value(
          "Customer",
          frm.doc.customer,
          ['custom_tipo_fattura_elettronica', 'custom_vat_collectability', 'custom_codice_univoco', 'is_public_administration', 'tax_id', 'fiscal_code'],
        )
        .then((r) => {
          if (r.message.custom_tipo_fattura_elettronica) {
            frm.set_value("custom_tipo_di_documento", r.message.custom_tipo_fattura_elettronica);
          } else {
            frm.set_value("custom_tipo_di_documento", "TD24");
          }
          if (r.message.custom_vat_collectability) {
            frm.set_value("vat_collectability", r.message.custom_vat_collectability);
          }

          if (r.message.is_public_administration) {
            frm.set_value("vat_collectability", 'S-Scissione dei Pagamenti');
            if (frm.doc.is_return == 0) {
              frm.set_value("naming_series", "PAINV/.YY./")
            }
            ;
          }
          
          if (r.message.tax_id) {
            frm.set_value("tax_id", r.message.tax_id);
          } else {
            frm.set_value("tax_id", r.message.fiscal_code);
          }
          
        });
  }
}


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
  },
  is_return: (frm) => {
    if (frm.doc.is_return) {
      frm.set_value("custom_tipo_di_documento", "TD04");
      frm.set_value("naming_series", "NCINV/.YY./");
    }
      
  },
  is_debit_note : (frm) => {
    if (frm.doc.is_debit_note){
      frm.set_value("custom_tipo_di_documento", "TD05");
    }
  },
  customer: (frm) => {
    getCustomerTipoFatturaElettronica(frm);
  },
  onload: (frm) => {
    getCustomerTipoFatturaElettronica(frm);
  },
  validate: (frm) => {
    if (frm.doc.is_return && frm.doc.custom_tipo_di_documento !== "TD04") 
      frappe.throw(__("Tipo di documento must be TD04 for return invoice"));
    if (frm.doc.is_debit_note && frm.doc.custom_tipo_di_documento !== "TD05")
      frappe.throw(__("Tipo di documento must be TD05 for debit note"));
  },
  before_save: async (frm) => {
    let responce = await frappe.db.get_value("Customer", frm.doc.customer, ['is_public_administration', 'name']);
    let customer = responce.message;
    if (customer.is_public_administration)
          frm.doc.items.forEach((item, idx) => {
            if (item.custom_riferimento_amministrativo === undefined) {
              frappe.throw(__("<b>Riferimento amministrativo</b> mancante nella riga {0}", [idx + 1]));
            }
          });
  },
});