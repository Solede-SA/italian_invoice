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
  custom_tipo_di_documento: (frm) => {
    if (["TD19", "TD17"].find((x) => x == frm.doc.custom_tipo_di_documento)) {
      frm.set_value("taxes_and_charges", "Reverse Charge");
    } else if (frm.doc.custom_tipo_di_documento == "TD18") {
      frm.set_value("taxes_and_charges", "IVA acquisti CEE al 22%");
    } else {
      frm.set_value("taxes_and_charges", "");
    }
    frm.refresh_field("taxes_and_charges");
  },
  validate: (frm) => {
    if (frm.doc.custom_tipo_di_documento == "TD19" || frm.doc.custom_tipo_di_documento == "TD17") {
      frm.doc.items.forEach((item) => {
        item.tax_rate = 0;
        if (!item.custom_motivo_esenzione_iva) {
          frappe.throw(
            __("Motivo esenzione IVA mancante per l'articolo {0}", [item.item_code])
          );
        }
      })
    }
  },
});

frappe.ui.form.on("Purchase Invoice Item", {
  item_code: (frm, cdt, cdn) => {
    const row = locals[cdt][cdn];
    if (row.item_code) {
      frappe.db
        .get_value("Item", row.item_code, "custom_codice_articolo")
        .then((r) => {
          frappe.model.set_value(
            row.doctype,
            row.name,
            "custom_codice_articolo",
            r.message.custom_codice_articolo,
          );
        });
    }
  },
});