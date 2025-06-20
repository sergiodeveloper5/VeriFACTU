# Copyright 2024 Aures TIC
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import datetime, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class VerifactuQueue(models.Model):
    """Cola de envío para Veri*FACTU"""
    
    _name = "verifactu.queue"
    _description = "Cola de envío Veri*FACTU"
    _order = "create_date desc"
    
    name = fields.Char(string="Nombre", required=True)
    invoice_id = fields.Many2one(
        "account.move", 
        string="Factura", 
        required=True,
        ondelete="cascade"
    )
    state = fields.Selection([
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('sent', 'Enviado'),
        ('error', 'Error'),
        ('cancelled', 'Cancelado'),
    ], string="Estado", default='pending', required=True)
    
    priority = fields.Integer(string="Prioridad", default=10)
    retry_count = fields.Integer(string="Intentos", default=0)
    max_retries = fields.Integer(string="Máximo intentos", default=3)
    
    scheduled_date = fields.Datetime(
        string="Fecha programada", 
        default=fields.Datetime.now
    )
    processed_date = fields.Datetime(string="Fecha procesado")
    
    error_message = fields.Text(string="Mensaje de error")
    response_data = fields.Text(string="Respuesta AEAT")
    
    company_id = fields.Many2one(
        "res.company", 
        string="Compañía", 
        required=True,
        default=lambda self: self.env.company
    )
    
    @api.model
    def create_queue_item(self, invoice_id, priority=10):
        """Crea un elemento en la cola para envío"""
        invoice = self.env['account.move'].browse(invoice_id)
        if not invoice.exists():
            raise UserError(_("La factura no existe"))
        
        # Verificar si ya existe en cola
        existing = self.search([
            ('invoice_id', '=', invoice_id),
            ('state', 'in', ['pending', 'processing'])
        ])
        if existing:
            return existing[0]
        
        return self.create({
            'name': f"Envío Veri*FACTU - {invoice.name}",
            'invoice_id': invoice_id,
            'priority': priority,
            'company_id': invoice.company_id.id,
        })
    
    def process_queue_item(self):
        """Procesa un elemento de la cola"""
        self.ensure_one()
        
        if self.state != 'pending':
            return False
        
        self.state = 'processing'
        
        try:
            # Procesar envío
            result = self._send_to_verifactu()
            
            if result.get('success'):
                self.write({
                    'state': 'sent',
                    'processed_date': fields.Datetime.now(),
                    'response_data': result.get('response', ''),
                })
                
                # Actualizar factura
                self.invoice_id.write({
                    'aeat_state': 'sent',
                    'aeat_send_failed': False,
                    'aeat_send_error': False,
                })
                
            else:
                self._handle_error(result.get('error', 'Error desconocido'))
                
        except Exception as e:
            _logger.error(f"Error procesando cola Veri*FACTU {self.id}: {str(e)}")
            self._handle_error(str(e))
        
        return True
    
    def _send_to_verifactu(self):
        """Envía la factura a Veri*FACTU"""
        # Aquí se implementaría la conexión real con AEAT
        # Por ahora simulamos el envío
        
        invoice = self.invoice_id
        
        # Verificar que la factura tenga todos los datos necesarios
        if not invoice.verifactu_hash:
            invoice._compute_verifactu_hash()
        
        # Simular envío exitoso
        return {
            'success': True,
            'response': f"Factura {invoice.name} enviada correctamente",
            'reference': invoice.verifactu_reference,
        }
    
    def _handle_error(self, error_message):
        """Maneja errores en el procesamiento"""
        self.retry_count += 1
        
        if self.retry_count >= self.max_retries:
            self.write({
                'state': 'error',
                'error_message': error_message,
                'processed_date': fields.Datetime.now(),
            })
            
            # Actualizar factura
            self.invoice_id.write({
                'aeat_state': 'error',
                'aeat_send_failed': True,
                'aeat_send_error': error_message,
            })
        else:
            # Reprogramar para reintento
            retry_delay = timedelta(minutes=5 * self.retry_count)
            self.write({
                'state': 'pending',
                'scheduled_date': fields.Datetime.now() + retry_delay,
                'error_message': error_message,
            })
    
    @api.model
    def process_pending_queue(self):
        """Procesa elementos pendientes en la cola"""
        pending_items = self.search([
            ('state', '=', 'pending'),
            ('scheduled_date', '<=', fields.Datetime.now()),
        ], order='priority desc, scheduled_date asc', limit=10)
        
        for item in pending_items:
            item.process_queue_item()
        
        return len(pending_items)
    
    def action_retry(self):
        """Reintenta el envío"""
        self.ensure_one()
        if self.state in ['error', 'cancelled']:
            self.write({
                'state': 'pending',
                'retry_count': 0,
                'scheduled_date': fields.Datetime.now(),
                'error_message': False,
            })
    
    def action_cancel(self):
        """Cancela el envío"""
        self.ensure_one()
        if self.state in ['pending', 'processing']:
            self.state = 'cancelled'