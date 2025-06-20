# Copyright 2024 Aures TIC
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
from unittest.mock import patch

from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


class TestVerifactuEnhanced(TransactionCase):
    """Tests para las nuevas funcionalidades de Veri*FACTU"""
    
    def setUp(self):
        super().setUp()
        
        # Configurar compañía
        self.company = self.env.ref('base.main_company')
        self.company.write({
            'verifactu_enabled': True,
            'verifactu_test': True,
            'vat': 'ES12345678Z',
        })
        
        # Crear partner
        self.partner = self.env['res.partner'].create({
            'name': 'Test Customer',
            'vat': 'ES87654321Y',
            'is_company': True,
        })
        
        # Crear producto
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'service',
            'list_price': 100.0,
        })
        
        # Crear factura
        self.invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 100.0,
            })],
        })
    
    def test_verifactu_enabled_computation(self):
        """Test que verifactu_enabled se calcula correctamente"""
        # Debe estar habilitado por defecto
        self.assertTrue(self.invoice.verifactu_enabled)
        
        # Deshabilitar en compañía
        self.company.verifactu_enabled = False
        self.invoice._compute_verifactu_enabled()
        self.assertFalse(self.invoice.verifactu_enabled)
    
    def test_hash_generation(self):
        """Test generación de hash Veri*FACTU"""
        self.invoice.action_post()
        
        # Verificar que se genera hash
        self.assertTrue(self.invoice.verifactu_hash_string)
        self.assertTrue(self.invoice.verifactu_hash)
        
        # Verificar formato del hash (SHA256 = 64 caracteres hex)
        self.assertEqual(len(self.invoice.verifactu_hash), 64)
        
        # Verificar que el hash es consistente
        hash1 = self.invoice.verifactu_hash
        self.invoice._compute_verifactu_hash()
        hash2 = self.invoice.verifactu_hash
        self.assertEqual(hash1, hash2)
    
    def test_qr_code_generation(self):
        """Test generación de código QR EPC"""
        self.invoice.action_post()
        
        # Verificar que se genera QR
        self.assertTrue(self.invoice.verifactu_qr_code)
        self.assertTrue(self.invoice.verifactu_qr_string)
        
        # Verificar que es base64 válido
        try:
            base64.b64decode(self.invoice.verifactu_qr_code)
        except Exception:
            self.fail("QR code no es base64 válido")
        
        # Verificar formato EPC
        qr_data = self.invoice.verifactu_qr_string
        lines = qr_data.split('\n')
        self.assertEqual(lines[0], 'BCD')  # Service Tag
        self.assertEqual(lines[1], '002')  # Version
        self.assertEqual(lines[2], '1')    # Character set
        self.assertEqual(lines[3], 'SCT')  # Identification
    
    def test_verifactu_reference_generation(self):
        """Test generación de referencia Veri*FACTU"""
        self.invoice.action_post()
        
        # Verificar que se genera referencia
        self.assertTrue(self.invoice.verifactu_reference)
        
        # Verificar formato VF-YYYYMMDD-NNNNNN-HASH
        ref = self.invoice.verifactu_reference
        self.assertTrue(ref.startswith('VF-'))
        parts = ref.split('-')
        self.assertEqual(len(parts), 4)
        self.assertEqual(parts[0], 'VF')
    
    def test_queue_creation(self):
        """Test creación de elementos en cola"""
        self.invoice.action_post()
        
        # Verificar que se crea elemento en cola automáticamente
        queue_items = self.env['verifactu.queue'].search([
            ('invoice_id', '=', self.invoice.id)
        ])
        self.assertEqual(len(queue_items), 1)
        
        queue_item = queue_items[0]
        self.assertEqual(queue_item.state, 'pending')
        self.assertEqual(queue_item.company_id, self.company)
    
    def test_manual_send_to_queue(self):
        """Test envío manual a cola"""
        self.invoice.action_post()
        
        # Limpiar cola existente
        self.env['verifactu.queue'].search([
            ('invoice_id', '=', self.invoice.id)
        ]).unlink()
        
        # Envío manual
        result = self.invoice.action_send_verifactu()
        
        # Verificar respuesta
        self.assertEqual(result['type'], 'ir.actions.client')
        self.assertEqual(result['tag'], 'display_notification')
        
        # Verificar que se crea en cola
        queue_items = self.env['verifactu.queue'].search([
            ('invoice_id', '=', self.invoice.id)
        ])
        self.assertEqual(len(queue_items), 1)
    
    def test_queue_processing(self):
        """Test procesamiento de cola"""
        self.invoice.action_post()
        
        # Obtener elemento de cola
        queue_item = self.env['verifactu.queue'].search([
            ('invoice_id', '=', self.invoice.id)
        ], limit=1)
        
        # Procesar elemento
        result = queue_item.process_queue_item()
        self.assertTrue(result)
        
        # Verificar estado
        self.assertEqual(queue_item.state, 'sent')
        self.assertTrue(queue_item.processed_date)
        
        # Verificar estado de factura
        self.assertEqual(self.invoice.aeat_state, 'sent')
        self.assertFalse(self.invoice.aeat_send_failed)
    
    def test_queue_retry_mechanism(self):
        """Test mecanismo de reintentos"""
        queue_item = self.env['verifactu.queue'].create({
            'name': 'Test Queue Item',
            'invoice_id': self.invoice.id,
            'state': 'pending',
        })
        
        # Simular error
        with patch.object(queue_item, '_send_to_verifactu') as mock_send:
            mock_send.return_value = {'success': False, 'error': 'Test error'}
            
            queue_item.process_queue_item()
            
            # Verificar reintento
            self.assertEqual(queue_item.retry_count, 1)
            self.assertEqual(queue_item.state, 'pending')
            self.assertTrue(queue_item.error_message)
    
    def test_queue_max_retries(self):
        """Test límite máximo de reintentos"""
        queue_item = self.env['verifactu.queue'].create({
            'name': 'Test Queue Item',
            'invoice_id': self.invoice.id,
            'state': 'pending',
            'retry_count': 3,  # Ya en el límite
            'max_retries': 3,
        })
        
        # Simular error
        with patch.object(queue_item, '_send_to_verifactu') as mock_send:
            mock_send.return_value = {'success': False, 'error': 'Test error'}
            
            queue_item.process_queue_item()
            
            # Verificar que pasa a error
            self.assertEqual(queue_item.state, 'error')
            self.assertEqual(self.invoice.aeat_state, 'error')
            self.assertTrue(self.invoice.aeat_send_failed)
    
    def test_verifactu_disabled_invoice(self):
        """Test factura con Veri*FACTU deshabilitado"""
        self.company.verifactu_enabled = False
        self.invoice._compute_verifactu_enabled()
        
        # Intentar envío manual
        with self.assertRaises(UserError):
            self.invoice.action_send_verifactu()
        
        # Verificar que no se generan datos
        self.invoice.action_post()
        self.assertFalse(self.invoice.verifactu_hash)
        self.assertFalse(self.invoice.verifactu_qr_code)
        self.assertFalse(self.invoice.verifactu_reference)
    
    def test_queue_duplicate_prevention(self):
        """Test prevención de duplicados en cola"""
        queue_obj = self.env['verifactu.queue']
        
        # Crear primer elemento
        item1 = queue_obj.create_queue_item(self.invoice.id)
        
        # Intentar crear segundo elemento
        item2 = queue_obj.create_queue_item(self.invoice.id)
        
        # Debe devolver el mismo elemento
        self.assertEqual(item1.id, item2.id)
        
        # Verificar que solo hay uno
        items = queue_obj.search([('invoice_id', '=', self.invoice.id)])
        self.assertEqual(len(items), 1)
    
    def test_queue_batch_processing(self):
        """Test procesamiento por lotes"""
        # Crear múltiples facturas
        invoices = []
        for i in range(5):
            invoice = self.invoice.copy()
            invoice.action_post()
            invoices.append(invoice)
        
        # Procesar cola
        processed = self.env['verifactu.queue'].process_pending_queue()
        
        # Verificar que se procesaron elementos
        self.assertGreater(processed, 0)
        
        # Verificar estados
        for invoice in invoices:
            queue_items = self.env['verifactu.queue'].search([
                ('invoice_id', '=', invoice.id)
            ])
            if queue_items:
                self.assertEqual(queue_items[0].state, 'sent')