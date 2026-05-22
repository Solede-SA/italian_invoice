const getCustomerTipoFatturaElettronica = (frm) => {
  // Non modificare documenti già submitted
  if (frm.doc.docstatus !== 0) {
    return true;
  }
  if (frm.doc.is_return) {
    frm.set_value("custom_tipo_di_documento", "TD04");
    frm.set_value("naming_series", "NCINV/.YY./");
    return true;
  }
  if (frm.doc.custom_tipo_di_documento) {
    return true;
  }
  if (frm.doc.customer !== undefined) {
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
            if (frm.doc.is_return == 0 && frm.doc.__islocal) {
              frm.set_value("naming_series", "PAINV/.YY./")
            }
            ;
          } else {
            if (frm.doc.is_return == 0 && frm.doc.__islocal) {
              frm.set_value("naming_series", "SINV/.YY./")
            }
          }


          if (r.message.tax_id) {
            frm.set_value("tax_id", r.message.tax_id);
          } else {
            frm.set_value("tax_id", r.message.fiscal_code);
          }

        });
  }
}

const updateTaxRate = (frm) => {
  // ERPNext v16: use item_wise_tax_details child table instead of tax.item_wise_tax_detail
  const taxDetails = frm.doc.item_wise_tax_details || [];
  taxDetails.forEach((row) => {
    const itemRow = frm.doc.items.find(i => i.name === row.item_row);
    if (itemRow) {
      itemRow.tax_rate = row.rate;
    }
  });
}

const setTaxesAndCharges = (frm) => {
  if (frm.doc.customer) {
    frappe.db.get_value("Customer", frm.doc.customer, "custom_abilita_lettera_dintento").then((r) => {
      if (r.message.custom_abilita_lettera_dintento) {
        frm.set_value("taxes_and_charges", "N3.5 - CBM");
      }
    });
  }
}

frappe.ui.form.on("Sales Invoice", {
  refresh: (frm) => {
    frm.remove_custom_button("Generate E-Invoice");
    frm.set_df_property('vat_collectability', 'read_only', 0)

    // Aggiungi un indicatore se c'è discrepanza tra due_date e payment_schedule
    check_due_date_consistency(frm);

    // Aggiungi bottone per ricalcolo manuale se ci sono payment terms
    if (frm.doc.payment_terms_template && !frm.doc.__islocal) {
        frm.add_custom_button(__('Recalculate Payment Schedule'), function() {
            frappe.call({
                method: 'italian_invoice.api.sales_invoice.recalculate_payment_schedule',
                args: {
                    sales_invoice_name: frm.doc.name
                },
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.show_alert({
                            message: __('Payment schedule recalculated'),
                            indicator: 'green'
                        });
                        frm.reload_doc();
                    }
                }
            });
        }, __('Actions'));
    }

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
    // Setta il bank account di default SOLO per documenti nuovi/draft, non per quelli submitted
    if (frm.doc.docstatus === 0 && frm.doc.custom_bank_account === undefined) {
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
    } else {
      frm.set_value("custom_tipo_di_documento", "TD24");
      frm.set_value("naming_series", "SINV/.YY./");
    }

  },
  is_debit_note : (frm) => {
    if (frm.doc.is_debit_note){
      frm.set_value("custom_tipo_di_documento", "TD05");
    }
  },
  customer: (frm) => {
    getCustomerTipoFatturaElettronica(frm);
    setTaxesAndCharges(frm);
  },
  onload: (frm) => {
    getCustomerTipoFatturaElettronica(frm);

    // Se c'è un payment terms template ma nessun payment schedule, ricalcola
    if (frm.doc.payment_terms_template && (!frm.doc.payment_schedule || frm.doc.payment_schedule.length === 0)) {
        frm.trigger('payment_terms_template');
    }
  },
  grand_total: function(frm) {
    // Quando cambia il grand_total, aggiorna gli importi nel payment schedule
    if (frm.doc.payment_schedule && frm.doc.payment_schedule.length > 0 && frm.doc.grand_total > 0) {
        frm.doc.payment_schedule.forEach(row => {
            if (row.invoice_portion) {
                let amount = (frm.doc.grand_total * row.invoice_portion) / 100;
                frappe.model.set_value(row.doctype, row.name, 'payment_amount', amount);
                frappe.model.set_value(row.doctype, row.name, 'base_payment_amount', amount);
                frappe.model.set_value(row.doctype, row.name, 'outstanding', amount);
            }
        });
    }
  },
  payment_terms_template: function(frm) {
    // Quando viene selezionato un payment terms template
    if (frm.doc.payment_terms_template) {
        // Se la fattura è nuova e il grand_total è 0, calcola manualmente
        if (frm.doc.__islocal && (!frm.doc.grand_total || frm.doc.grand_total === 0)) {
            calculate_payment_schedule_manually(frm);
        } else {
            // Forza il ricalcolo del payment schedule
            frappe.call({
                method: 'erpnext.controllers.accounts_controller.get_payment_terms',
                args: {
                    terms_template: frm.doc.payment_terms_template,
                    posting_date: frm.doc.posting_date || frm.doc.transaction_date,
                    grand_total: frm.doc.grand_total || 0,
                    base_grand_total: frm.doc.base_grand_total || frm.doc.grand_total || 0,
                    bill_date: frm.doc.bill_date
                },
                callback: function(r) {
                    if (r.message && r.message.length > 0) {
                        // Pulisci il payment schedule esistente
                        frm.clear_table('payment_schedule');

                        // Aggiungi le nuove righe
                        r.message.forEach(function(term) {
                            let row = frm.add_child('payment_schedule');
                            row.payment_term = term.payment_term;
                            row.due_date = term.due_date;
                            row.invoice_portion = term.invoice_portion;
                            row.payment_amount = term.payment_amount;
                            row.base_payment_amount = term.base_payment_amount || term.payment_amount;
                            row.outstanding = term.outstanding || term.payment_amount;
                            row.paid_amount = 0;
                        });

                        frm.refresh_field('payment_schedule');

                        // Aggiorna la due_date principale con la scadenza più lontana
                        update_main_due_date(frm);
                    } else {
                        // Se non ci sono termini, prova a calcolarli manualmente
                        calculate_payment_schedule_manually(frm);
                    }
                },
                error: function(err) {
                    // In caso di errore, prova il calcolo manuale
                    calculate_payment_schedule_manually(frm);
                }
            });
        }
    }
  },
  posting_date: function(frm) {
    // Ricalcola payment schedule quando cambia la data
    if (frm.doc.payment_terms_template) {
        frm.trigger('payment_terms_template');
    }
  },
  validate: (frm) => {
    updateTaxRate(frm);
    if (frm.doc.is_return && frm.doc.custom_tipo_di_documento !== "TD04")
      frappe.throw(__("Tipo di documento must be TD04 for return invoice"));
    if (frm.doc.is_debit_note && frm.doc.custom_tipo_di_documento !== "TD05")
      frappe.throw(__("Tipo di documento must be TD05 for debit note"));

    // Prima della validazione, assicurati che la due_date sia corretta
    update_main_due_date(frm);
  },
  before_save: async (frm) => {
    // Prima di salvare, assicurati che la due_date sia corretta
    if (frm.doc.payment_schedule && frm.doc.payment_schedule.length > 0) {
        update_main_due_date(frm);
    }

    let responce = await frappe.db.get_value("Customer", frm.doc.customer, ['is_public_administration', 'name']);
    let customer = responce.message;
    if (customer.is_public_administration) {
       frm.doc.items.forEach((item, idx) => {
            if (item.custom_riferimento_amministrativo === undefined) {
              frappe.throw(__("<b>Riferimento amministrativo</b> mancante nella riga {0}", [idx + 1]));
            }
        });
    }

    if (frm.doc.taxes) {
      frm.doc.taxes.forEach((tax, idx) => {
        if (tax.base_tax_amount == 0 && tax.custom_motivo_esenzione_iva === undefined) {
          frappe.throw(__("<b>Motivo esenzione IVA</b> mancante nella tassa {0}", [idx + 1]));
        }
        if (tax.custom_motivo_esenzione_iva !== undefined) {
          tax.tax_exemption_reason = "N3-Non Imponibili"
        }


      });
    }

  },
  // after_save: (frm) => {
  //   frm.doc.items.forEach((item) => {
  //     if (item.tax_rate <= 0 && !item.custom_motivo_esenzione_iva) {
  //         frm.dirty ()
  //         frappe.throw(
  //           __("Motivo esenzione IVA mancante per l'articolo {0}", [item.item_code])
  //         );
  //       }
  //   })
  // }
});

// frappe.ui.form.on("Sales Taxes and Charges", {
//   taxes_add: (frm) => {
//     console.log(frm);
//     updateTaxRate(frm);
//   },
//   taxes_remove: (frm) => {
//     console.log(frm);
//     updateTaxRate(frm);
//   },
//   taxes_move: (frm) => {
//     console.log(frm);
//     updateTaxRate(frm);
//   },
//   rate: (frm, cdt, cdn) => {
//     console.log(frm.doc.taxes);
//     frm.reload_doc();
//     updateTaxRate(frm);
//   },
//   item_wise_tax_detail: (frm, cdt, cdn) => {
//     console.log(frm.doc.taxes);
//     updateTaxRate(frm);
//   }


// });

// Gestione della tabella payment_schedule
frappe.ui.form.on('Payment Schedule', {
    due_date: function(frm, cdt, cdn) {
        // Quando cambia una due_date nel payment schedule
        update_main_due_date(frm);
    },

    payment_schedule_remove: function(frm, cdt, cdn) {
        // Quando viene rimossa una riga
        update_main_due_date(frm);
    }
});

function update_main_due_date(frm) {
    // Aggiorna la due_date principale basandosi sul payment_schedule
    if (frm.doc.payment_schedule && frm.doc.payment_schedule.length > 0) {
        let due_dates = frm.doc.payment_schedule
            .filter(row => row.due_date)
            .map(row => row.due_date); // Le date sono già stringhe nel formato corretto

        if (due_dates.length > 0) {
            // Ordina le date e prendi l'ultima
            due_dates.sort();
            let max_due_date = due_dates[due_dates.length - 1];

            // Aggiorna solo se diversa
            if (frm.doc.due_date !== max_due_date) {
                frm.set_value('due_date', max_due_date);

                // Mostra notifica
                frappe.show_alert({
                    message: __('Due date updated based on payment schedule'),
                    indicator: 'blue'
                }, 3);
            }
        }
    }
}

function check_due_date_consistency(frm) {
    // Controlla se c'è inconsistenza tra due_date e payment_schedule
    if (frm.doc.payment_schedule && frm.doc.payment_schedule.length > 0) {
        let due_dates = frm.doc.payment_schedule
            .filter(row => row.due_date)
            .map(row => row.due_date);

        if (due_dates.length > 0) {
            let max_schedule_date = due_dates.sort().reverse()[0];

            if (frm.doc.due_date && frm.doc.due_date !== max_schedule_date) {
                // Mostra un indicatore di warning
                frm.dashboard.add_comment(
                    __('Due date ({0}) differs from payment schedule maximum date ({1})', [
                        frappe.format_date(frm.doc.due_date),
                        frappe.format_date(max_schedule_date)
                    ]),
                    'orange'
                );
            }
        }
    }
}

function calculate_payment_schedule_manually(frm) {
    // Calcolo manuale del payment schedule quando il metodo standard fallisce
    if (!frm.doc.payment_terms_template || !frm.doc.posting_date) {
        return;
    }

    // Ottieni i dettagli del payment terms template
    frappe.db.get_doc('Payment Terms Template', frm.doc.payment_terms_template)
        .then(template => {
            if (template.terms && template.terms.length > 0) {
                frm.clear_table('payment_schedule');

                template.terms.forEach(term_detail => {
                    // term_detail contiene già tutti i campi necessari dal Payment Terms Template Detail
                    // che ha fatto fetch_from del Payment Term
                    let due_date = calculate_due_date_from_term(frm.doc.posting_date, term_detail);

                    let row = frm.add_child('payment_schedule');
                    row.payment_term = term_detail.payment_term;
                    row.description = term_detail.description;
                    row.due_date = due_date;
                    row.invoice_portion = term_detail.invoice_portion || 100;
                    row.mode_of_payment = term_detail.mode_of_payment;

                    // Per nuove fatture, non calcolare l'importo se grand_total è 0
                    if (frm.doc.grand_total && frm.doc.grand_total > 0) {
                        let amount = (frm.doc.grand_total * (term_detail.invoice_portion || 100)) / 100;
                        row.payment_amount = amount;
                        row.base_payment_amount = amount;
                        row.outstanding = amount;
                    } else {
                        // Impostiamo solo la percentuale, gli importi verranno calcolati al salvataggio
                        row.payment_amount = 0;
                        row.base_payment_amount = 0;
                        row.outstanding = 0;
                    }
                    row.paid_amount = 0;
                });

                frm.refresh_field('payment_schedule');
                update_main_due_date(frm);
            }
        })
        .catch(err => {
            frappe.msgprint(__("Error loading payment terms template"));
        });
}

function calculate_due_date_from_term(posting_date, term) {
    // Calcola la due_date basandosi sul tipo di termine di pagamento
    let due_date;

    if (term.due_date_based_on === "Day(s) after invoice date") {
        due_date = frappe.datetime.add_days(posting_date, term.credit_days || 0);
    } else if (term.due_date_based_on === "Day(s) after the end of the invoice month") {
        // Fine del mese corrente + giorni di credito
        let end_of_month = frappe.datetime.month_end(posting_date);
        due_date = frappe.datetime.add_days(end_of_month, term.credit_days || 0);
    } else if (term.due_date_based_on === "Month(s) after the end of the invoice month") {
        // Fine del mese + mesi di credito
        let end_of_month = frappe.datetime.month_end(posting_date);
        due_date = frappe.datetime.add_months(end_of_month, term.credit_months || 0);
    } else {
        // Default: same as posting date
        due_date = posting_date;
    }

    return due_date;
}