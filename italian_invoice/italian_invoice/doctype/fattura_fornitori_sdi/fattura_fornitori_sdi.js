function format_currency(value) {
    return new Intl.NumberFormat('it-IT', {
        style: 'currency',
        currency: 'EUR'
    }).format(value);
}

frappe.ui.form.on("Fattura Fornitori SDI", {
    refresh(frm) {
        // Check if we're in development mode
        if (!frappe.boot.developer_mode) {
            frm.disable_save();
        } else {
            // In development mode, enable save button
            frm.enable_save();
        }

        frm.add_custom_button(__("Scarica PDF"), () => {
            window.location.href = `/api/method/openapi.api.sdi.fatture.download?doctype=Fattura Fornitori SDI&docname=${frm.doc.name}&type=pdf`;
        });

        // Pulisci campo documenti aperti
        frm.get_field('documenti_aperti').$wrapper.html('');

        // Mostra pulsante Importa solo se non è già importata
        if (frm.doc.stato === "Da importare") {
            frm.add_custom_button(__("Importa Fattura"), () => {
                // Ottieni supplier_vat dalla utility function
                frappe.call({
                    method: 'italian_invoice.utilities.fatture.get_supplier_vat_from_json',
                    args: {
                        invoice_data: frm.doc.dati_fattura
                    },
                    callback: (r) => {
                        const supplier_vat = r.message;

                    // Prima verifichiamo/creiamo il fornitore
                    frappe.call({
                        method: "openapi.api.eInvoice.purchase_invoice.get_or_create_supplier",
                        args: {
                            supplier_vat_id: supplier_vat,
                            fattura_fornitori_sdi: frm.doc.name
                        },
                        callback: (r) => {
                            if (!r.message.success) {
                                frappe.throw(r.message.error);
                                return;
                            }

                            const supplier_data = r.message.supplier_data;
                            if (r.message.is_new) {
                                frappe.show_alert({
                                    message: __(`Nuovo fornitore ${supplier_data.supplier_name} creato`),
                                    indicator: 'green'
                                });
                            }

                            // Ora possiamo procedere con il dialog per i prodotti
                            show_items_dialog(frm, supplier_data);
                        }
                    });
                    }
                });
            });

            // Verifica PO/PR aperti (non bloccante)
            if (frm.doc.partita_iva_fornitore) {
                check_open_purchase_documents(frm);
            }
        }
    }
});


function show_items_dialog(frm, supplier_data) {
   // Get all invoice lines from utility function
   frappe.call({
       method: 'italian_invoice.utilities.fatture.get_invoice_lines_from_json',
       args: {
           invoice_data: frm.doc.dati_fattura
       },
       callback: (r) => {
           const allLines = r.message;
   const invoice_lines = allLines.filter(line => {
       // Include all lines with valid prezzo_totale or quantita (including negative values)
       return line.prezzo_totale != null || line.quantita != null;
   });

   // Display info about filtered lines
   if (allLines.length !== invoice_lines.length) {
       const skippedCount = allLines.length - invoice_lines.length;
       frappe.show_alert({
           message: __(`${skippedCount} righe con quantità zero ignorate automaticamente`),
           indicator: 'blue'
       }, 5);
   }

   const dialog_fields = [
       {
           fieldtype: 'HTML',
           fieldname: 'supplier_info',
           options: `
               <div class="row">
                   <div class="col-sm-12">
                       <p><strong>Fornitore:</strong> ${supplier_data.supplier_name}</p>
                       <p><strong>P.IVA:</strong> ${supplier_data.tax_id}</p>
                   </div>
               </div>
           `
       },
       {
           fieldtype: 'Section Break',
           label: 'Prodotti in Fattura'
       }
   ];

   invoice_lines.forEach((line, idx) => {
       // Verifica se la riga ha valore zero
       const isZeroValue = parseFloat(line.prezzo_totale || 0) === 0;

       dialog_fields.push({
           fieldtype: 'Section Break'
       });

       const importo_formatted = format_currency(line.prezzo_totale);
       const html_desc = `
           <div style="margin-bottom: 5px;">
               <strong>Prodotto presente in Fattura</strong>
           </div>
           <div style="padding: 10px; background-color: #f8f9fa; border-radius: 4px; margin-bottom: 10px;">
               <div style="font-size: 14px; font-weight: bold; margin-bottom: 5px;">${line.descrizione}</div>
               <div style="font-size: 13px; color: #6c757d;">
                   Importo: <span style="font-weight: bold; color: ${isZeroValue ? '#ffc107' : '#28a745'};">${importo_formatted}</span>
                   ${isZeroValue ? '<span style="color: #ffc107; margin-left: 10px;">(Opzionale - valore zero)</span>' : ''}
               </div>
           </div>
       `;

       dialog_fields.push({
           label: 'Prodotto presente in Fattura',
           fieldtype: 'HTML',
           fieldname: `desc_${idx}`,
           options: html_desc
       });

       dialog_fields.push({
           label: 'Seleziona Item',
           fieldtype: 'Link',
           options: 'Item',
           fieldname: `item_${idx}`,
           get_query: () => {
               return {
                   query: 'italian_invoice.utilities.fatture_passive.get_items_by_supplier',
                   filters: {
                       'default_supplier': supplier_data.name
                   }
               };
           },
           reqd: isZeroValue ? 0 : 1,
           only_select: true,
           description: isZeroValue ? 'Opzionale - lascia vuoto per non importare' : 'Seleziona un prodotto esistente o creane uno nuovo'
       });

       dialog_fields.push({
           label: 'Conto di Costo',
           fieldtype: 'Link',
           options: 'Account',
           fieldname: `account_${idx}`,
           reqd: isZeroValue ? 0 : 1,
           get_query: () => {
               return {
                   filters: {
                       'is_group': 0,
                       'company': frm.doc.company
                   }
               };
           }
       });

        // Pulsante per creare nuovo Item
        dialog_fields.push({
            fieldtype: 'Button',
            label: 'Crea Nuovo Item',
            fieldname: `create_item_${idx}`,
            click: () => {
                let item_dialog = new frappe.ui.Dialog({
                    title: 'Crea Nuovo Item',
                    fields: [
                        {
                            label: 'Nome Item',
                            fieldtype: 'Data',
                            fieldname: 'item_name',
                            default: line.descrizione,
                            reqd: 1
                        },
                        {
                            label: 'Item Group',
                            fieldtype: 'Link',
                            fieldname: 'item_group',
                            options: 'Item Group',
                            reqd: 1
                        },
                        {
                            label: 'Unità di Misura',
                            fieldtype: 'Link',
                            fieldname: 'uom',
                            options: 'UOM',
                            reqd: 1
                        },
                        {
                            label: 'Conto di Costo',
                            fieldtype: 'Link',
                            options: 'Account',
                            fieldname: 'expense_account',
                            reqd: 1,
                            get_query: () => ({
                                filters: {
                                    'is_group': 0,
                                    'company': frm.doc.company
                                }
                            })
                        }
                    ],
                    primary_action_label: 'Crea',
                    primary_action(values) {
                        frappe.call({
                            method: 'frappe.client.insert',
                            args: {
                                doc: {
                                    doctype: 'Item',
                                    item_code: values.item_name,
                                    item_name: values.item_name,
                                    item_group: values.item_group,
                                    description: values.description,
                                    stock_uom: values.uom,
                                    is_stock_item: 0,
                                    is_sales_item: 0,
                                    is_purchase_item: 1,
                                    item_defaults: [{
                                        company: frm.doc.company,
                                        expense_account: values.expense_account,
                                        default_supplier: supplier_data.name
                                    }]
                                }
                            },
                            callback: (r) => {
                                if (r.message) {
                                    item_dialog.hide();
                                    d.set_value(`item_${idx}`, r.message.name);
                                    d.set_value(`account_${idx}`, values.expense_account);
                                    frappe.show_alert({
                                        message: __('Item creato con successo'),
                                        indicator: 'green'
                                    });
                                }
                            }
                        });
                    }
                });
                item_dialog.show();
            }
        });
   });

    let d = new frappe.ui.Dialog({
        title: 'Associa Prodotti',
        fields: dialog_fields,
        primary_action_label: 'Importa',
        primary_action(values) {
            let item_mappings = {};
            invoice_lines.forEach((line, idx) => {
                // Salta righe senza item_code (opzionali non compilate)
                if (!values[`item_${idx}`]) {
                    return;
                }

                // Make sure we use the original line number
                item_mappings[line.numero_linea] = {
                    item_code: values[`item_${idx}`],
                    account: values[`account_${idx}`],
                    description: line.descrizione,
                    qty: parseFloat(line.quantita) || 1, // Convert to number and ensure no zeros
                    rate: line.prezzo_unitario,
                    tax_rate: line.aliquota_iva,
                    tax_nature: line.natura
                };
            });

            frappe.call({
                method: "openapi.api.eInvoice.purchase_invoice.process_supplier_invoice",
                args: {
                    json_data_string: frm.doc.dati_fattura,
                    fattura_fornitori_sdi: frm.doc.name,
                    item_mappings: item_mappings
                },
                callback: (r) => {
                    if (r.message) {
                        d.hide();
                        frappe.set_route("Form", "Purchase Invoice", r.message);
                    }
                }
            });
        }
    });

   // Aggiungiamo handlers per l'autocompilazione del conto quando si seleziona un Item
   invoice_lines.forEach((line, idx) => {
        d.fields_dict[`item_${idx}`].df.onchange = () => {
            let item_code = d.get_value(`item_${idx}`);
            if (item_code) {
                frappe.db.get_doc('Item', item_code).then(item => {
                    if (item.item_defaults && item.item_defaults.length > 0) {
                        const default_account = item.item_defaults.find(
                            def => def.company === frm.doc.company
                        );
                        if (default_account && default_account.expense_account) {
                            d.set_value(`account_${idx}`, default_account.expense_account);
                        }
                    }
                });
            }
        };
    });

   // Auto-match item basato sulla descrizione
   frappe.call({
       method: 'italian_invoice.utilities.fatture_passive.find_matching_items',
       args: {
           supplier_name: supplier_data.name,
           invoice_lines: invoice_lines
       },
       callback: (r) => {
           if (r.message) {
               // Pre-popola i campi trovati
               invoice_lines.forEach((line, idx) => {
                   const match = r.message[line.numero_linea];
                   if (match) {
                       d.set_value(`item_${idx}`, match.item_code);
                       if (match.expense_account) {
                           d.set_value(`account_${idx}`, match.expense_account);
                       }
                   }
               });
           }
       }
   });

   d.show();
       }
   });
}


function check_open_purchase_documents(frm) {
    // Ottieni numero fattura dalla utility function
    frappe.call({
        method: 'italian_invoice.utilities.fatture.get_invoice_number_from_json',
        args: {
            invoice_data: frm.doc.dati_fattura
        },
        callback: (r) => {
            const bill_no = r.message;

        frappe.call({
            method: 'italian_invoice.utilities.fatture_passive.get_open_purchase_documents_summary',
            args: {
                supplier_vat: frm.doc.partita_iva_fornitore
            },
            callback: (r) => {
                if (r.message) {
                    const pos = r.message.purchase_orders || [];
                    const prs = r.message.purchase_receipts || [];
                    const total = pos.length + prs.length;

                    if (total > 0) {
                        show_po_pr_in_form(frm, pos, prs, bill_no);
                    } else {
                        frm.get_field('documenti_aperti').$wrapper.html('');
                    }
                }
            }
        });
        }
    });
}


function show_po_pr_in_form(frm, purchase_orders, purchase_receipts, bill_no) {
    const total = purchase_orders.length + purchase_receipts.length;
    let html = `
        <div style="background-color: #fff3cd; border: 1px solid #ffc107; border-radius: 4px; padding: 15px; margin-bottom: 15px;">
            <h5 style="margin-top: 0; color: #856404;">
                <i class="fa fa-exclamation-triangle"></i>
                Attenzione! Ci sono <b>${total} documenti aperti</b> per questo fornitore
            </h5>
    `;

    if (purchase_orders.length > 0) {
        html += `
            <div style="margin-bottom: 20px;">
                <b>Purchase Orders (${purchase_orders.length}):</b>
                <table class="table table-bordered" style="margin-top: 10px; background-color: white;">
                    <thead>
                        <tr>
                            <th style="width: 50%;">Documento</th>
                            <th style="width: 30%; text-align: right;">Importo</th>
                            <th style="width: 20%; text-align: center;">Azione</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        purchase_orders.forEach(po => {
            html += `
                <tr>
                    <td>${po.name}</td>
                    <td style="text-align: right;">${format_currency(po.grand_total)}</td>
                    <td style="text-align: center;">
                        <button class="btn btn-primary btn-sm" onclick="window.create_from_doc_${frm.doc.name.replace(/[^a-zA-Z0-9]/g, '_')}('${po.name}', 'Purchase Order', '${bill_no}')">Crea Fattura</button>
                    </td>
                </tr>
            `;
        });
        html += `
                    </tbody>
                </table>
            </div>
        `;
    }

    if (purchase_receipts.length > 0) {
        html += `
            <div>
                <b>Purchase Receipts (${purchase_receipts.length}):</b>
                <table class="table table-bordered" style="margin-top: 10px; background-color: white;">
                    <thead>
                        <tr>
                            <th style="width: 50%;">Documento</th>
                            <th style="width: 30%; text-align: right;">Importo</th>
                            <th style="width: 20%; text-align: center;">Azione</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        purchase_receipts.forEach(pr => {
            html += `
                <tr>
                    <td>${pr.name}</td>
                    <td style="text-align: right;">${format_currency(pr.grand_total)}</td>
                    <td style="text-align: center;">
                        <button class="btn btn-primary btn-sm" onclick="window.create_from_doc_${frm.doc.name.replace(/[^a-zA-Z0-9]/g, '_')}('${pr.name}', 'Purchase Receipt', '${bill_no}')">Crea Fattura</button>
                    </td>
                </tr>
            `;
        });
        html += `
                    </tbody>
                </table>
            </div>
        `;
    }

    html += `</div>`;

    // Funzione globale per gestire il click sui bottoni
    const funcName = `create_from_doc_${frm.doc.name.replace(/[^a-zA-Z0-9]/g, '_')}`;
    window[funcName] = (doc_name, doctype, bill_no) => {
        frappe.call({
            method: 'italian_invoice.utilities.fatture_passive.create_purchase_invoice_from_document',
            args: {
                doc_name: doc_name,
                doctype: doctype,
                bill_no: bill_no,
                fattura_sdi_name: frm.doc.name
            },
            callback: (r) => {
                if (r.message) {
                    frappe.show_alert({
                        message: __('Purchase Invoice creata con successo'),
                        indicator: 'green'
                    });
                    frappe.set_route('Form', 'Purchase Invoice', r.message);
                }
            }
        });
    };

    // Popola il campo HTML
    frm.get_field('documenti_aperti').$wrapper.html(html);
}