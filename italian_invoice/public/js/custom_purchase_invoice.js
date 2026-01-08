const updateTaxRate = (frm) => {
  if (frm.doc.taxes && frm.doc.taxes.length > 0) {
    frm.doc.taxes.forEach((tax) => {
      let itemWiseTaxDetail = tax.item_wise_tax_detail;
      if (itemWiseTaxDetail) {
        if (typeof itemWiseTaxDetail === "string") {
          itemWiseTaxDetail = JSON.parse(itemWiseTaxDetail);
        }
        Object.keys(itemWiseTaxDetail).forEach((itemCode) => {
          let taxDetails = itemWiseTaxDetail[itemCode];
          let taxRate = taxDetails[0];
          let item = frm.doc.items.find(i => i.item_code === itemCode);
          if (item) {
            item.tax_rate = taxRate;
          }
        });
      }
    });
  }
};

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
    if (["TD17", "TD18", "TD19"].includes(frm.doc.custom_tipo_di_documento)) {
      frm.set_value("taxes_and_charges", "IVA acquisti CEE al 22%");
    } else {
      frm.set_value("taxes_and_charges", "");
    }
    frm.refresh_field("taxes_and_charges");
  },
  validate: (frm) => {
    updateTaxRate(frm);
  },
});

// frappe.ui.form.on("Purchase Invoice Item", {
//   item_code: (frm, cdt, cdn) => {
//     const row = locals[cdt][cdn];
//     if (row.item_code) {
//       frappe.db
//         .get_value("Item", row.item_code, "custom_codice_articolo")
//         .then((r) => {
//           frappe.model.set_value(
//             row.doctype,
//             row.name,
//             "custom_codice_articolo",
//             r.message.custom_codice_articolo,
//           );
//         });
//     }
//   },
// });