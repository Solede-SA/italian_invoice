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

        frm.add_custom_button(__("Importa Fattura"), () => {
            const json_data = JSON.parse(frm.doc.dati_fattura);
            const supplier_vat = json_data.data.invoice.payload.fattura_elettronica_header.cedente_prestatore.dati_anagrafici.id_fiscale_iva.id_codice;

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

                    // Ora possiamo procedere con il dialog per i prodotti...
                    show_items_dialog(frm, json_data, supplier_data);
                }
            });
        });
    }
});


function show_items_dialog(frm, json_data, supplier_data) {
   // Filter out lines with quantity 0 or null
   const allLines = json_data.data.invoice.payload.fattura_elettronica_body[0].dati_beni_servizi.dettaglio_linee;
   const invoice_lines = allLines.filter(line => {
       // Check if line should be included based on quantity or total price
       try {
           // Include if it has a valid quantity greater than 0
           if (line.quantita) {
               const qty = parseFloat(line.quantita);
               if (!isNaN(qty) && qty > 0) return true;
           }
           
           // Include if quantita is null/missing but has a valid price_totale greater than 0
           if (line.prezzo_totale) {
               const total = parseFloat(line.prezzo_totale);
               if (!isNaN(total) && total > 0) return true;
           }
           
           // Exclude in all other cases
           return false;
       } catch (e) {
           return false; // If error in parsing, filter out the line
       }
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
       dialog_fields.push({
           fieldtype: 'Section Break'
       });

       dialog_fields.push({
           label: 'Prodotto in Fattura',
           fieldtype: 'Data',
           fieldname: `desc_${idx}`,
           read_only: 1,
           default: line.descrizione,
           description: `Importo: ${line.prezzo_unitario} EUR`
       });

       dialog_fields.push({
           label: 'Seleziona Item',
           fieldtype: 'Link',
           options: 'Item',
           fieldname: `item_${idx}`,
           get_query: () => {
               return {
                   filters: {
                       'default_supplier': supplier_data.name
                   }
               };
           },
           reqd: 1,
           only_select: true,
           description: 'Seleziona un prodotto esistente o creane uno nuovo'
       });

       dialog_fields.push({
           label: 'Conto di Costo',
           fieldtype: 'Link',
           options: 'Account',
           fieldname: `account_${idx}`,
           reqd: 1,
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

   d.show();
}