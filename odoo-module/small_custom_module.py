# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, Warning
from odoo.osv import expression
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.addons import decimal_precision as dp
from operator import itemgetter

class Inventory(models.Model):
    _inherit = "stock.inventory"

    def action_validate(self):
        # do your necessary actions here
        for record in self.line_ids:
            record.discrepancy_qty = record.product_qty - record.x_theoretical_qty
            #raise Warning(_('test = %s %s %s') % (record, self.line_ids, record.x_discrepancy_qty))
            if record.theoretical_qty != record.x_theoretical_qty:
                record.theoretical_qty = record.x_theoretical_qty
            if record.x_theoretical_qty:
                record.discrepancy_percent = 100 * abs((record.product_qty - record.x_theoretical_qty) / record.x_theoretical_qty)
        
        res = super(Inventory, self).action_validate()
        return res


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    active = fields.Boolean("Active", default=True)

    picking_ids = fields.Many2many(
        comodel_name='stock.picking',
        string='Related Pickings',
        readonly=False,
        copy=False,
        help="Related pickings "
             "(only when the invoice has been generated from a sale order).",
    )


class SaleOrderHistory(models.Model):
    _inherit = "sale.order.history"

    cpc_soh =  fields.Char('C_ProductCode', related='name.cpc_sol', store=False, readonly=True)


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if args is None:
            args = []

        if name:
            r_partner_id = self.env.context.get('search_default_customer_id')
            recs = self.env['product.customer.code'].search([('partner_id', '=', r_partner_id), ('product_code', operator, name)], limit=10)
            searchpid = self.env['product.product'].search([('product_tmpl_id', '=', recs.mapped('product_id').ids)], limit=10)
            if recs:
                #args = expression.AND([args, [('id', 'in', recs.mapped('product_id').ids)]])
                args = expression.AND([args, [('id', 'in', searchpid.mapped('id'))]])
                result = self.search(args, limit=limit).name_get()
                #raise UserError("answer 1=%s 2=%s 3=%s" % (recs, args, result))
                #raise UserError("answer 1=%s 2=%s 3=%s 4=%s 5=%s 6=%s" % (recs, searchpid, id, args[2], result, recs.mapped('product_id').ids) )
                #raise UserError("answer 1=%s 2=%s 3=%s" % (recs, result, searchpid.id ))
                #raise UserError("answer 1=%s 2=%s 3=%s" % (recs, args, result))
                #return result
                if result:
                    return result

        if self.env.context.get('search_default_customer_id'):
            customer_args = args + [('product_customer_code_ids.partner_id', '=', self.env.context['search_default_customer_id'])]
            products = super(ProductProduct, self).name_search(name, args=customer_args, operator=operator, limit=limit)
            if products:
                return products

        return super(ProductProduct, self).name_search(name, args=args, operator=operator, limit=limit)


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'
    _order = "id DESC"

    reserved_qty = fields.Float('Reserved Qty', compute='_reserved_qty')
    
    @api.one
    def _reserved_qty(self):
        # We only care for the quants in internal or transit locations.
        quants = self.quant_ids.filtered(lambda q: q.location_id.name in ['Pre-Production'])
        self.reserved_qty = sum(quants.mapped('reserved_quantity'))
#    available_qty = self.env['stock.quant']._get_available_quantity(self.product_id, self.location_id, self.lot_id, strict=True)

    @api.multi
    def remove(self):
        context = dict(self.env.context)
        move_line = self.env['stock.move.line']
        active_ids = context.get('active_ids')
        lineLengths = []

        for active_id in active_ids:
            lines = move_line.search([
                ('lot_id', '=', active_id),
                ('state', '=', 'done'),
            ])
            lineLengths.append(len(lines))

        for i in range(len(lineLengths)):
            if lineLengths[i] == 0:
                super(ProductionLot, self[i]).unlink()
        
        return True

    @api.multi
    def button_remove(self):
        self.remove()
        return True

class stock_scrap(models.Model):
    _inherit = 'stock.scrap'

    state = fields.Selection(selection_add=[('approved', 'Approved')])
    # TODO: inherit state but adding approved state in a position after 'to
    # approve' state.

    @api.multi
    def button_release(self):
        #approve_scrap = self.filtered(
        #lambda p: p.company_id.scrap_approve_active)
        self.write({'state': 'approved'})
        return {}

class archive_man(models.Model):
    _inherit = "mrp.production"
    active = fields.Boolean("Active", default=True)

class mrp_production(models.Model):
    _inherit = 'mrp.production'

    lot_name_mrp = fields.Char('Lot No', related='finished_move_line_ids.lot_id.name', store=True, readonly=True)

    finished_move_line_ids = fields.One2many(
        'stock.move.line', 'production_id', compute='_compute_lines', inverse='_inverse_lines', string='Finished Produc', store=True)

class ProductCategory(models.Model):
    _inherit = 'product.category'

    category_desc = fields.Char('Description', store=True)

class ReportBomStructure(models.AbstractModel):
    _inherit = 'report.mrp.report_bom_structure'
    _description = 'BOM Structure Report'

    def _get_pdf_line(self, bom_id, product_id=False, qty=1, child_bom_ids=[], unfolded=False):

        data = self._get_bom(bom_id=bom_id, product_id=product_id.id, line_qty=qty)

        def get_sub_lines(bom, product_id, line_qty, line_id, level):
            data = self._get_bom(bom_id=bom.id, product_id=product_id.id, line_qty=line_qty, line_id=line_id, level=level)
            bom_lines = data['components']
            lines = []
            for bom_line in bom_lines:
                lines.append({
                    'name': bom_line['prod_name'],
                    'suppliername': bom_line['suppliers_name'],
                    'prod_price': bom_line['prod_price'],
                    'vendor_price': bom_line['vendor_price'],
                    'vendor_currency': bom_line['vendor_currency'],
                    'type': 'bom',
                    'quantity': bom_line['prod_qty'],
                    'uom': bom_line['prod_uom'],
                    'prod_cost': bom_line['prod_cost'],
                    'bom_cost': bom_line['total'],
                    'level': bom_line['level'],
                    'code': bom_line['code']
                })
                if bom_line['child_bom'] and (unfolded or bom_line['child_bom'] in child_bom_ids):
                    line = self.env['mrp.bom.line'].browse(bom_line['line_id'])
                    lines += (get_sub_lines(line.child_bom_id, line.product_id, bom_line['prod_qty'], line, level + 1))
            if data['operations']:
                lines.append({
                    #'name': _('Operations'),
                    'name': 'Operations',
                    'type': 'operation',
                    'quantity': data['operations_time'],
                    #'uom': _('minutes'),
                    'uom': 'minutes',
                    'bom_cost': data['operations_cost'],
                    'level': level,
                })
                for operation in data['operations']:
                    if unfolded or 'operation-' + str(bom.id) in child_bom_ids:
                        lines.append({
                            'name': operation['name'],
                            'type': 'operation',
                            'quantity': operation['duration_expected'],
                            #'uom': _('minutes'),
                            'uom': 'minutes',
                            'bom_cost': operation['total'],
                            'level': level + 1,
                        })
            return lines

        bom = self.env['mrp.bom'].browse(bom_id)
        product = product_id or bom.product_id or bom.product_tmpl_id.product_variant_id
        pdf_lines = get_sub_lines(bom, product, qty, False, 1)
        data['components'] = []
        data['lines'] = pdf_lines
        return data

    def _get_bom_lines(self, bom, bom_quantity, product, line_id, level):
        components = []
        total = 0
        for line in bom.bom_line_ids:
            line_quantity = (bom_quantity / (bom.product_qty or 1.0)) * line.product_qty
            if line._skip_bom_line(product):
                continue
            price = line.product_id.uom_id._compute_price(line.product_id.standard_price, line.product_uom_id) * line_quantity
            if line.child_bom_id:
                factor = line.product_uom_id._compute_quantity(line_quantity, line.child_bom_id.product_uom_id) / line.child_bom_id.product_qty
                sub_total = self._get_price(line.child_bom_id, factor, line.product_id)
            else:
                sub_total = price
            sub_total = self.env.user.company_id.currency_id.round(sub_total)
            components.append({
                'prod_id': line.product_id.id,
                'prod_name': line.product_id.display_name,
                'prod_price': line.product_tmpl_id.standard_price,
                'vendor_price': line.x_vendor_price,
                'vendor_currency': line.x_vendor_currency,
                'suppliers_name': line.suppliers,
                'code': line.child_bom_id and self._get_bom_reference(line.child_bom_id) or '',
                'prod_qty': line_quantity,
                'prod_uom': line.product_uom_id.name,
                'prod_cost': self.env.user.company_id.currency_id.round(price),
                'parent_id': bom.id,
                'line_id': line.id,
                'level': level or 0,
                'total': sub_total,
                'child_bom': line.child_bom_id.id,
                'phantom_bom': line.child_bom_id and line.child_bom_id.type == 'phantom' or False,
                'attachments': self.env['mrp.document'].search(['|', '&',
                    ('res_model', '=', 'product.product'), ('res_id', '=', line.product_id.id), '&', ('res_model', '=', 'product.template'), ('res_id', '=', line.product_id.product_tmpl_id.id)]),

            })
            total += sub_total
        return components, total

#class ResConfigSettings(models.TransientModel):
#    _inherit='res.config.settings'

#    scrap_ratio = fields.Float(string='Scrap Rate', digits=dp.get_precision('Product Unit of Measure'), store=True)

#    @api.model
#    def get_values(self):
#        res = super(ResConfigSettings, self).get_values()
#        res['scrap_ratio'] = float(self.env['ir.config_parameter'].sudo().get_param('small_custom_module.scrap_ratio', default=0.0))
#        return res

#    @api.model
#    def set_values(self):
#        self.env['ir.config_parameter'].sudo().set_param('small_custom_module.scrap_ratio', self.scrap_ratio)
#        super(ResConfigSettings, self).set_values()


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    scrap_rate = fields.Float(string='Scrap Rate', digits=dp.get_precision('Product Unit of Measure'), store=True)
    before_scrap_qty = fields.Float(default=0, string='Before Scrap Qty',
            digits=dp.get_precision('Product Unit of Measure'), store=True)
    custom_product_type = fields.Selection(
            related='product_tmpl_id.custom_product_type', readonly=True,
            help="Declare product type - Finished Products 成品, Semi-Finished Product 半成品, Raw Material 物料, Miscellaneous 雜項")
    suppliers = fields.Char(string='Supplier', related='product_id.seller_ids.name.name', readonly=True, store=False)

    @api.onchange('custom_product_type')
    def _compute_scrap_rate(self):
        #result = self.env['res.config.settings'].sudo().search([],order="id desc", limit=1)
        #defaults = super(MrpBomLine, self).default_get(fields_list)
        for record in self:
            if record.custom_product_type == 'FG':
                record.scrap_rate = 0


    @api.onchange('product_qty')
    def _compute_scrap_qty(self):
        resultValue = self.before_scrap_qty * self.scrap_rate
        if self.custom_product_type == 'RM' and self.product_uom_id.name != 'pcs':
            if resultValue != self.product_qty:
                self.before_scrap_qty = self.product_qty
                self.product_qty = self.before_scrap_qty * self.scrap_rate
        else:
            self.before_scrap_qty = self.product_qty

class StockMove(models.Model):
    _inherit = "stock.move"

    customer_product_code_sm = fields.Char('Customer Product Code', related='sale_line_id.cpc_sol', store=True, readonly=True)
    lotid_line = fields.Many2one('stock.production.lot', string='Lot Stock Move Line', related='move_line_ids.lot_id', readonly=True)
    product_carton = fields.Integer('Carton')
    product_weight = fields.Float('Product Weight', digits=dp.get_precision('Product Unit of Measure'))
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure', default=3, required=True, help="Default unit of measure used for all stock operations.")

    #qty_compute = field.Float('Qty difference', compute='_compute_qty_total', readonly=True, store=True)

    #@api.multi
    #@api.depends('quantity_done', 'product_uom_qty')
    #def _compute_qty_total(self):
    #    for record in self:
    #        record.qty_compute = record.quantity_done - record.product_uom_qty

    product_qty = fields.Float(
        'Real Reserved Quantity', digits=dp.get_precision('Product Unit of Measure'),
        compute='_compute_product_qty', inverse='_set_product_qty', store=True)
        
    #product_uom_qty = fields.Float('Reserved', default=0.0, digits=dp.get_precision('Product Unit of Measure'), required=True)
    
    @api.one
    @api.depends('product_id', 'product_uom', 'product_uom_qty')
    def _compute_product_qty(self):
        rounding_method = self._context.get('rounding_method', 'UP')
        self.product_qty = self.product_uom._compute_quantity(self.product_uom_qty, self.product_id.uom_id, rounding_method=rounding_method)

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    vendor_price_pol = fields.Float('Vendor Price', related='product_id.seller_ids.price', store=True, readonly=True)
    vendor_price_currency_pol = fields.Char('Vendor Price Currency', related='product_id.seller_ids.currency_id.name',
            store=True, readonly=True)
    product_miniqty_pol = fields.Float('Vendor MOQ', related='product_id.seller_ids.min_qty', readonly=True, store=True)

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    reserved_qty_sml = fields.Float(
            related='lot_id.reserved_qty',
            string='Reserved Qty', store=False, readonly=True)
    product_qty_lot1 = fields.Float(
            related='lot_id.product_qty',
            string='On Hand Quantity', store=True, readonly=True)

    customer_product_code_sml = fields.Char('Customer Product Code',
            related='move_id.sale_line_id.cpc_sol', store=True, readonly=True)

    product_qty = fields.Float(
        'Real Reserved Quantity', digits=dp.get_precision('Product Unit of Measure'),
        compute='_compute_product_qty', inverse='_set_product_qty', store=True)
 
    @api.one
    @api.depends('picking_id.picking_type_id', 'product_id.tracking')
    def _compute_lots_visible(self):
        picking = self.picking_id
        if picking.picking_type_id and self.product_id.tracking != 'none':  # TDE FIXME: not sure correctly migrated
            self.lots_visible = picking.picking_type_id.use_existing_lots or picking.picking_type_id.use_create_lots
        else:
            self.lots_visible = self.product_id.tracking != 'none'
    
    #product_uom_qty = fields.Float('Reserved', default=0.0, digits=dp.get_precision('Product Unit of Measure'), required=True)

class SaleOrder(models.Model):
    _inherit = 'stock.picking'

    vendor_dn_no = fields.Char('Vendor DN')
    client_order_ref_so = fields.Char('Customer Po no', related='sale_id.client_order_ref', store=True, readonly=True)
    st_moid = fields.Many2one('mrp.production','ST-MO', compute='_compute_st_moid', store=True)
    st_soid = fields.Many2one('sale.order','ST-SO', compute='_compute_st_soid', store=True)
    # so_id = fields.Many2one('sale.order','SO', compute='_compute_so_id')
    # mo_id = fields.Many2one('mrp.production','MO', compute='_compute_mo_id')
    active = fields.Boolean("Active", default=True)
    st_soconfirmdate = fields.Datetime('SO Confirm Date', compute='_compute_st_soconfirmdate', store=True)
    
    @api.depends('create_date') 
    def _compute_st_soconfirmdate(self):
        for record in self:
            # tempno = tempno + 1
            if record.picking_type_id.name == 'Pick Components' and not record.st_soconfirmdate:
                #raise Warning(_('test = %s') % record.origin)
                #moidlist = self.env['mrp.production'].search([('name','=',record.origin)],limit=1)
                st_soconfirmdates = self.env['mrp.production'].search([('name','=',record.origin)],limit=1).sale_order_id
                #raise Warning(_('test = %s %s %s') % (moidlist[0].id, moidlist[0].sale_order_id[0].id, moidlist[0]))
                if st_soconfirmdates:
                    record.st_soconfirmdate  = st_soconfirmdates.confirmation_date                   
        # raise Warning(_('test-p = %s ') % (tempno))
        return

    @api.depends('create_date') 
    def _compute_st_soid(self):
        # raise Warning(_('test-st_soid = %s ') % (self))
        # tempno = 0
        # DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
        for record in self:
            # tempno = tempno + 1
            if record.picking_type_id.name == 'Pick Components' and not record.st_soid:
                soids = self.env['mrp.production'].search([('name','=',record.origin)],limit=1).sale_order_id
                #raise Warning(_('test = %s %s %s') % (moidlist[0].id, moidlist[0].sale_order_id[0].id, moidlist[0]))
                if soids:
                    record.st_soid = soids[0].id
                    # record.st_soconfirmdate = fields.Datetime.to_string(soids[0].confirmation_date)
                   # record.st_soconfirmdate = fields.datetime.now()
                    # self.sudo().write({'record.st_soconfirmdate': fields.Datetime.from_string(soids.confirmation_date)})
                    #raise Warning(_('test-st_soid = %s ') % (record.st_soconfirmdate))
                    # raise Warning(_('test-abc = %s %s %s %s') % (soids[0].confirmation_date, soids, soids.confirmation_date, record.st_soconfirmdate ))
                    # record.sale_id = soids[0].id    
        #raise Warning(_('test-abc = %s ') % (tempno))
        return

    @api.depends('create_date') 
    def _compute_st_moid(self):
        # tempno = 0
        for record in self:
            # tempno = tempno + 1
            if record.picking_type_id.name == 'Pick Components' and not record.st_moid:
                #raise Warning(_('test = %s') % record.origin)
                #moidlist = self.env['mrp.production'].search([('name','=',record.origin)],limit=1)
                moids = self.env['mrp.production'].search([('name','=',record.origin)],limit=1)
                #raise Warning(_('test = %s %s %s') % (moidlist[0].id, moidlist[0].sale_order_id[0].id, moidlist[0]))
                if moids:
                    record.st_moid = moids[0].id                   
        # raise Warning(_('test-p = %s ') % (tempno))
        return

    # @api.multi
    # def _compute_mo_id(self):
    #     # raise Warning(_('test-moid = %s ') % (self))
    #     return
    #     # tempno = 0
    #     # result = self.filtered(lambda r: r.picking_type_id.name == 'Pick Components')
    #     # #  and not r.mo_id):
    #     # raise Warning(_('test-lambda = %s') % result)
    #     #raise Warning(_('test-lambda123 = %s') % self)
    #     for record in self:
    #         # tempno = tempno + 1
    #         #record.mo_id = 234
    #         #if record.picking_type_id.name == 'Pick Components' and not record.mo_id:
    #         if record.picking_type_id.name == 'Pick Components' and not record.mo_id:
    #             #raise Warning(_('test = %s') % record.origin)
    #             #moidlist = self.env['mrp.production'].search([('name','=',record.origin)],limit=1)
    #             moids = self.env['mrp.production'].search([('name','=',record.origin)],limit=1)
    #             #raise Warning(_('test = %s %s %s') % (moidlist[0].id, moidlist[0].sale_order_id[0].id, moidlist[0]))
    #             if moids:
    #                 record.mo_id = moids[0].id                   
    #                 return
    #     #raise Warning(_('test-p = %s ') % (tempno))
    #     return

    # @api.multi
    # def _compute_so_id(self):
    #     #raise Warning(_('test-soid = %s ') % (self))
    #     return
    #     # tempno = 0
    #     for record in self:
    #         # tempno = tempno + 1
    #         if record.picking_type_id.name == 'Pick Components' and not record.so_id:
    #             soids = self.env['mrp.production'].search([('name','=',record.origin)],limit=1).sale_order_id
    #             #raise Warning(_('test = %s %s %s') % (moidlist[0].id, moidlist[0].sale_order_id[0].id, moidlist[0]))
    #             if soids:
    #                 record.so_id = soids[0].id
    #                 record.sale_id = soids[0].id      
    #     #raise Warning(_('test-abc = %s ') % (tempno))
    #     return

    @api.multi
    def button_validate(self):
        self.ensure_one()
        if not self.move_lines and not self.move_line_ids:
            raise UserError(_('Please add some items to move.'))

        # If no lots when needed, raise error
        picking_type = self.picking_type_id
        precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        no_quantities_done = all(float_is_zero(move_line.qty_done, precision_digits=precision_digits) for move_line in self.move_line_ids.filtered(lambda m: m.state not in ('done', 'cancel')))
        no_reserved_quantities = all(float_is_zero(move_line.product_qty, precision_rounding=move_line.product_uom_id.rounding) for move_line in self.move_line_ids)
        if no_reserved_quantities and no_quantities_done:
            raise UserError(_('You cannot validate a transfer if no quantites are reserved nor done. To force the transfer, switch in edit more and encode the done quantities.'))

        if picking_type.use_create_lots or picking_type.use_existing_lots:
            lines_to_check = self.move_line_ids
            if not no_quantities_done:
                lines_to_check = lines_to_check.filtered(
                    lambda line: float_compare(line.qty_done, 0,
                                               precision_rounding=line.product_uom_id.rounding)
                )

            for line in lines_to_check:
                product = line.product_id
                if product and product.tracking != 'none':
                    if not line.lot_name and not line.lot_id:
                        raise UserError(_('You need to supply a Lot/Serial number for product %s.') % product.display_name)

        if no_quantities_done:
            view = self.env.ref('stock.view_immediate_transfer')
            wiz = self.env['stock.immediate.transfer'].create({'pick_ids': [(4, self.id)]})
            return {
                'name': _('Immediate Transfer?'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'stock.immediate.transfer',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': wiz.id,
                'context': self.env.context,
            }

        if self._get_overprocessed_stock_moves() and not self._context.get('skip_overprocessed_check'):
            view = self.env.ref('stock.view_overprocessed_transfer')
            wiz = self.env['stock.overprocessed.transfer'].create({'picking_id': self.id})
            return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'stock.overprocessed.transfer',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': wiz.id,
                'context': self.env.context,
            }

        # Check backorder should check for other barcodes
        if picking_type.id == 2 or picking_type.id == 10:
            #raise Warning(_('123test = %s , 123test1 = %s , 123test2 = %s') % (picking_type.name, picking_type, picking_type.id))
            self.name = self.env['ir.sequence'].next_by_code('stock.picking.small')
        #raise Warning(_('test = %s') % picking_type.name)
        #raise Warning(_('test = %s , test1 = %s , test2 = %s') % (picking_type.name, picking_type, picking_type.id))
        if self._check_backorder():
            return self.action_generate_backorder_wizard()
        self.action_done()
        return

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    po_stock_picking_state_template_field = fields.Selection(
            related='picking_ids.state', string='Delivery Status', store=True, readonly=True,
            help="Stock Picking List Status for Sale Order whether it is delivered or not.")

    def _add_supplier_to_product(self):
        super(PurchaseOrder, self)._add_supplier_to_product()
        for line in self.order_line:
            partner = self.partner_id if not self.partner_id.parent_id else self.partner_id.parent_id
            supplier = line.product_id.seller_ids.filtered(lambda x: x.name.id == partner.id)
            if supplier:
                currency = partner.property_purchase_currency_id or self.env.user.company_id.currency_id
                supplier.write({'price': self.currency_id.compute(line.price_unit, currency)})

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    #stock_picking_state_template_field = fields.Selection(
    #        related='picking_ids.state', string='Delivery Status', store=True, readonly=True,
    #        help="Stock Picking List Status for Sale Order whether it is delivered or not.")

    multi_terms_condition_id_SaleOrder = fields.Many2one('x_multi_terms_condition', string='Terms and Condition',
            store=True, help="This connected to model Multiple Terms and Condition")

    so_ref_field1 = fields.Char('sReference 1')

    so_ref_field2 = fields.Char('sReference 2')

class ProductCustomerCode(models.Model):
    _inherit = "product.customer.code"

    x_product_customer_price = fields.Float('Customer Product Price', store=True, digits=dp.get_precision('Product Price'))

class sale_order_line(models.Model):
    _inherit = 'sale.order.line'

    #cpp_sol_template_field = fields.Float(
    #        related='product_id.product_customer_code_ids.x_product_customer_price',
    #        string='C_Price', digits=dp.get_precision('Product Price'), store=True, readonly=False, copy=False)

    #cpc_sol_template_field = fields.Char(related='product_id.product_customer_code_ids.product_code',
    #        string='Customer Product Code', store=True, readonly=False, copy=False)

    defaultCode_sol = fields.Char('Internal Reference', store=False, related='product_id.default_code')

    cpp_sol = fields.Float('C_Price', digits=dp.get_precision('Product Price'), store=True)

    cpc_sol = fields.Char('C_ProductCode', store=True)

    client_order_ref_sol = fields.Char(related='order_id.client_order_ref', readonly=True, store=True)

    ref_field1 = fields.Char('Reference 1')

    ref_field2 = fields.Char('Reference 2')

    @api.onchange('price_unit', 'product_id', 'purchase_price')
    #@api.multi
    #@api.depends('product_id' 'price_unit', 'product_uom_qty')
    def get_cpc(self):
        r_partner_id = False
        r_product_id = False
        resultCPC = False
        cpc_sol = False
        cpp_sol = False

        r_partner_id = self.env.context.get('search_default_customer_id')

        #tempid = str(self.product_id)

        #pd_id = tempid.split('(')[1].split(',')[0]

        pd_id = self.product_id.product_tmpl_id

        if r_partner_id and pd_id:
            resultCPC = self.env['product.customer.code'].search([('partner_id', '=', r_partner_id), ('product_id', '=', int(pd_id))], limit=1)

        #raise UserError("answer 1=%s 2=%s 3=%s" % (pd_id, self.product_id.id, resultCPC))

        if resultCPC:
            self.cpc_sol = resultCPC.product_code
            self.cpp_sol = resultCPC.x_product_customer_price

        #    for cpcid in resultCPC:
        #        self.cpc_sol = cpcid.product_code
        #        self.cpp_sol = cpcid.x_product_customer_price

        return

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    customer_ref_id_template_field = fields.Char(related='product_customer_code_ids.x_product_company_ref',
        string='Customer Ref Id', store=True, readonly=True)

    customer_name_template_field = fields.Char(related='product_customer_code_ids.x_customer_name_product',
            string='Customer Name', store=True, readonly=True)

    customer_product_price_template_field = fields.Float(related='product_customer_code_ids.x_product_customer_price',
            string='Customer Product Price', digits=dp.get_precision('Product Price'), store=True, readonly=True)

    product_name_template_field = fields.Char(related='product_customer_code_ids.product_name',
            string='Customer Product Name', store=True, readonly=True)

    product_code_template_field = fields.Char(related='product_customer_code_ids.product_code',
            string='Customer Product Code', store=True, readonly=True)

    custom_product_long_name = fields.Char('Product Long Name')

    custom_product_type = fields.Selection([
            ('FG', 'Finished 成品'),('HG', 'Semi-Finished 半成品'),('RM', 'Raw Material 物料'),
            ('CG', 'Miscellaneous 雜項')], string='Type 類型', change_default=True,
            help='Declare product type - Finished Products 成品, Semi-Finished Product 半成品, Raw Material 物料, Miscellaneous 雜項')

    uom_id = fields.Many2one(
            'uom.uom', 'Unit of Measure', required=True, default=False,
            help="Default unit of measure used for all stock operations.")

    drawing_no = fields.Char('Drawing No')

    drawing_version_no = fields.Char('Drawing Version No')

    name = fields.Char('Name', index=True, required=True, translate=False)

        #cpc_pt = fields.Many2one('product.customer.code', string='CPC Code', default=_get_default_cpc)


    @api.model
    def default_get(self, fields_list):
        self.warehouse = self.env.ref('stock.warehouse0')
        route_manufacture = self.env.ref('stock.warehouse0').manufacture_pull_id.route_id.id
        route_mto = self.env.ref('stock.warehouse0').mto_pull_id.route_id.id
        buy_route = self.env.ref('stock.warehouse0').buy_pull_id.route_id.id
        defaults = super(ProductTemplate, self).default_get(fields_list)
        defaults.update({'route_ids': [(6, 0, [])]})
        return defaults

    @api.onchange('custom_product_type')
    def _onchange_custom_product_type(self):
        if self.custom_product_type:
            self.warehouse = self.env.ref('stock.warehouse0')
            route_manufacture = self.env.ref('stock.warehouse0').manufacture_pull_id.route_id.id
            route_mto = self.env.ref('stock.warehouse0').mto_pull_id.route_id.id
            buy_route = self.env.ref('stock.warehouse0').buy_pull_id.route_id.id
            #raise UserError(_("answer %s ") % buy_route)
            #raise UserError("answer %r " % (self.route_ids))
            self.type='product'
            if self.custom_product_type == 'RM' or self.custom_product_type == 'CG':
                self.sale_ok = False
                self.purchase_ok = True
                self.no_auto_reorder = False
                self.update({'route_ids': [(6, 0, [buy_route])]})
            elif self.custom_product_type == 'FG' or self.custom_product_type == 'HG' :
                self.sale_ok = True
                self.purchase_ok = False
                self.no_auto_reorder = True
                self.update({'route_ids': [(6, 0, [route_manufacture, route_mto])]})
                #self.route_ids = [(6, 0, [route_manufacture, route_mto])]
