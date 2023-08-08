# -*- coding: utf-8 -*-

from odoo import fields, models

class Task(models.Model):
    _inherit = "project.task"


    picking_type_id = fields.Many2one(
        'stock.picking.type', 'Operation Type', copy=True, readonly=False,
        # compute='_compute_picking_type_id', store=True, precompute=True,
        # domain="[('code', '=', 'mrp_operation'), ('company_id', '=', company_id)]",
        required=True, check_company=True, index=True)


    move_ids_to_remove = fields.One2many('stock.move','remove_from_task_id',string='Productos a quitar')

    move_ids = fields.One2many('stock.move', 'task_id', string="Stock Moves", copy=True)


    move_ids_to_add = fields.One2many(
        'stock.move',
        'add_to_task_id',
        string='Productos a agregar'
    )

    def validate_moves(self):
        # Añade aquí tu lógica para validar los movimientos.
        pass

    def action_assign(self):
        for production in self:
            production.move_raw_ids._action_assign()
        return True

    def _action_done(self):
        """Call `_action_done` on the `stock.move` of the `stock.picking` in `self`.
        This method makes sure every `stock.move.line` is linked to a `stock.move` by either
        linking them to an existing one or a newly created one.

        If the context key `cancel_backorder` is present, backorders won't be created.

        :return: True
        :rtype: bool
        """
        self._check_company()
        all_moves = self.move_ids_to_remove | self.move_ids_to_add
        todo_moves = all_moves.filtered(lambda self: self.state in ['draft', 'waiting', 'partially_available', 'assigned', 'confirmed'])
        # for task in self:
        #     if task.owner_id:
        #         task.move_ids.write({'restrict_partner_id': task.owner_id.id})
        #         task.move_line_ids.write({'owner_id': task.owner_id.id})
        todo_moves._action_done(cancel_backorder=self.env.context.get('cancel_backorder'))
        self.write({'date_done': fields.Datetime.now(), 'priority': '0'})

        # if incoming/internal moves make other confirmed/partially_available moves available, assign them
        done_incoming_moves = self.filtered(lambda p: p.picking_type_id.code in ('incoming', 'internal')).move_ids.filtered(lambda m: m.state == 'done')
        done_incoming_moves._trigger_assign()

        self._send_confirmation_email()
        return True



class Project(models.Model):
    _inherit = "project.project"

    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Bodega'
    )

class Warehouse(models.Model):
    _inherit = "stock.warehouse"

    installed_stock_id = fields.Many2one(
        'stock.location',
        string='Ubicación de instalados en faena'
    )

    failure_stock_id = fields.Many2one(
        'stock.location',
        string='Ubicación de falla en faena'
    )

class StockMove(models.Model):
    _inherit = 'stock.move'

    task_id = fields.Many2one('project.task',string='Tarea')
    remove_from_task_id = fields.Many2one('project.task',string='Tarea de remoción')
    add_to_task_id = fields.Many2one('project.task',string='Tarea de adición')

# class StockMove(models.Model):
#     _inherit = 'stock.move'

#     task_id = fields.Many2one(
#         'project.task',
#         string='Tarea'
#     )