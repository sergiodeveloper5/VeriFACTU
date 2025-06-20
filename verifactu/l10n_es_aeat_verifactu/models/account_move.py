# Copyright 2024 Aures TIC - Almudena de La Puente <almudena@aurestic.es>
# Copyright 2024 Aures Tic - Jose Zambudio <jose@aurestic.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import pytz

import base64
import io
import qrcode
from PIL import Image

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .verifactu_mixin import VerifactuMixin

VERIFACTU_VALID_INVOICE_STATES = ["posted"]


class AccountMove(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "verifactu.mixin"]

    verifactu_document_type = fields.Selection(
        selection=lambda self: self._get_verifactu_docuyment_types(),
        default="F1",
    )
    verifactu_hash = fields.Char(
        string="Veri*FACTU Hash",
        copy=False,
        help="Hash SHA256 calculado para Veri*FACTU",
    )
    verifactu_qr_code = fields.Binary(
        string="Código QR EPC",
        copy=False,
        help="Código QR EPC generado para Veri*FACTU",
    )
    verifactu_qr_string = fields.Text(
        string="Datos QR",
        copy=False,
        help="Datos utilizados para generar el código QR EPC",
    )
    verifactu_reference = fields.Char(
        string="Referencia Veri*FACTU",
        copy=False,
        help="Referencia única de Veri*FACTU para esta factura",
    )

    def _get_verifactu_docuyment_types(self):
        return [
            ("F1", _("FACTURA (ART. 6, 7.2 Y 7.3 DEL RD 1619/2012)")),
            (
                "F2",
                _(
                    """FACTURA SIMPLIFICADA Y FACTURAS SIN IDENTIFICACIÓN DEL DESTINATARIO
                    (ART. 6.1.D RD 1619/2012)"""
                ),
            ),
            (
                "R1",
                _("FACTURA RECTIFICATIVA (Art 80.1 y 80.2 y error fundado en derecho)"),
            ),
            ("R2", _("FACTURA RECTIFICATIVA (Art. 80.3)")),
            ("R3", _("FACTURA RECTIFICATIVA (Art. 80.4)")),
            ("R4", _("FACTURA RECTIFICATIVA (Resto)")),
            ("R5", _("FACTURA RECTIFICATIVA EN FACTURAS SIMPLIFICADAS")),
            (
                "F3",
                _(
                    """FACTURA EMITIDA EN SUSTITUCIÓN DE FACTURAS SIMPLIFICADAS FACTURADAS
                    Y DECLARADAS"""
                ),
            ),
        ]

    @api.depends(
        "company_id",
        "company_id.verifactu_enabled",
        "move_type",
        "fiscal_position_id",
        "fiscal_position_id.aeat_active",
    )
    def _compute_verifactu_enabled(self):
        """Compute if the invoice is enabled for the veri*FACTU"""
        for invoice in self:
            if invoice.company_id.verifactu_enabled and invoice.is_invoice():
                invoice.verifactu_enabled = (
                    invoice.fiscal_position_id
                    and invoice.fiscal_position_id.aeat_active
                ) or not invoice.fiscal_position_id
            else:
                invoice.verifactu_enabled = False

    def _get_document_date(self):
        """
        TODO: this method is the same in l10n_es_aeat_sii_oca, so I think that
        it should be directly in l10n_es_aeat
        """
        return self._change_date_format(self.invoice_date)

    def _aeat_get_partner(self):
        """
        TODO: this method is the same in l10n_es_aeat_sii_oca, so I think that
        it should be directly in l10n_es_aeat
        """
        return self.commercial_partner_id

    def _get_document_fiscal_date(self):
        """
        TODO: this method is the same in l10n_es_aeat_sii_oca, so I think that
        it should be directly in l10n_es_aeat
        """
        return self.date

    def _get_mapping_key(self):
        """
        TODO: this method is the same in l10n_es_aeat_sii_oca, so I think that
        it should be directly in l10n_es_aeat
        """
        return self.move_type

    def _get_valid_document_states(self):
        return VERIFACTU_VALID_INVOICE_STATES

    def _get_document_serial_number(self):
        """
        TODO: this method is the same in l10n_es_aeat_sii_oca, so I think that
        it should be directly in l10n_es_aeat
        """
        serial_number = (self.name or "")[0:60]
        if self.thirdparty_invoice:
            serial_number = self.thirdparty_number[0:60]
        return serial_number

    def _get_verifactu_issuer(self):
        return self.company_id.partner_id._parse_aeat_vat_info()[2]

    def _get_verifactu_document_type(self):
        return self.verifactu_document_type or "F1"

    def _get_verifactu_amount_tax(self):
        return self.amount_tax

    def _get_verifactu_amount_total(self):
        return self.amount_total

    def _get_verifactu_previous_hash(self):
        # TODO store it? search it by some kind of sequence?
        return ""

    def _get_verifactu_registration_date(self):
        # Date format must be ISO 8601
        return pytz.utc.localize(self.create_date).isoformat()

    @api.model
    def _get_verifactu_hash_string(self):
        """Gets the verifactu hash string"""
        if (
            not self.verifactu_enabled
            or self.state == "draft"
            or self.move_type not in ("out_invoice", "out_refund")
        ):
            return ""
        issuerID = self._get_verifactu_issuer()
        serialNumber = self._get_document_serial_number()
        expeditionDate = self._get_document_date()
        documentType = self._get_verifactu_document_type()
        amountTax = self._get_verifactu_amount_tax()
        amountTotal = self._get_verifactu_amount_total()
        previousHash = self._get_verifactu_previous_hash()
        registrationDate = self._get_verifactu_registration_date()
        verifactu_hash_string = (
            f"IDEmisorFactura={issuerID}&"
            f"NumSerieFactura={serialNumber}&"
            f"FechaExpedicionFactura={expeditionDate}&"
            f"TipoFactura={documentType}&"
            f"CuotaTotal={amountTax}&"
            f"ImporteTotal={amountTotal}&"
            f"Huella={previousHash}&"
            f"FechaHoraHusoGenRegistro={registrationDate}"
        )
        return verifactu_hash_string

    def _compute_verifactu_hash(self):
        for record in self:
            if record.verifactu_enabled:
                hash_string = record._get_verifactu_hash_string()
                record.verifactu_hash_string = hash_string
                record.verifactu_hash = record._compute_verifactu_hash_value(hash_string)
                # Generar código QR EPC
                record._generate_verifactu_qr_code()
                # Generar referencia Veri*FACTU
                record._generate_verifactu_reference()
            else:
                record.verifactu_hash_string = False
                record.verifactu_hash = False
                record.verifactu_qr_code = False
                record.verifactu_qr_string = False
                record.verifactu_reference = False

    def _generate_verifactu_qr_code(self):
        """Genera el código QR EPC para Veri*FACTU"""
        if not self.verifactu_enabled or not self.verifactu_hash:
            return
        
        # Crear datos EPC QR según especificaciones
        qr_data = self._get_epc_qr_data()
        self.verifactu_qr_string = qr_data
        
        # Generar código QR
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Crear imagen
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convertir a base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        self.verifactu_qr_code = qr_code_base64

    def _get_epc_qr_data(self):
        """Genera los datos para el código QR EPC según especificaciones"""
        # Formato EPC QR Code según ISO 20022
        company = self.company_id
        
        # Datos básicos del EPC
        epc_data = [
            "BCD",  # Service Tag
            "002",  # Version
            "1",    # Character set (UTF-8)
            "SCT",  # Identification
            company.partner_id.name or "",  # Beneficiary Name
            company.partner_id.bank_ids[0].acc_number if company.partner_id.bank_ids else "",  # Beneficiary Account
            f"EUR{self.amount_total:.2f}",  # Amount
            "",     # Purpose
            "",     # Structured Reference
            f"Veri*FACTU {self.name} - Hash: {self.verifactu_hash[:10]}...",  # Unstructured Reference
            ""      # Beneficiary to Originator Information
        ]
        
        return "\n".join(epc_data)

    def _generate_verifactu_reference(self):
        """Genera una referencia única para Veri*FACTU"""
        if not self.verifactu_enabled:
            return
        
        # Formato: VF-YYYYMMDD-NNNNNN-HASH
        date_str = self.invoice_date.strftime("%Y%m%d") if self.invoice_date else ""
        invoice_number = self.name.replace("/", "-") if self.name else ""
        hash_short = self.verifactu_hash[:8] if self.verifactu_hash else ""
        
        self.verifactu_reference = f"VF-{date_str}-{invoice_number}-{hash_short}"

    def _compute_verifactu_hash_value(self, hash_string):
        """Calcula el hash SHA256 de la cadena de Veri*FACTU"""
        import hashlib
        if not hash_string:
            return False
        return hashlib.sha256(hash_string.encode('utf-8')).hexdigest()

    def action_send_verifactu(self):
        """Envía la factura a Veri*FACTU usando la cola"""
        if not self.verifactu_enabled:
            raise UserError(_("Esta factura no tiene Veri*FACTU habilitado."))
        
        if not self.verifactu_hash:
            self._compute_verifactu_hash()
        
        # Crear elemento en cola
        queue_obj = self.env['verifactu.queue']
        queue_item = queue_obj.create_queue_item(self.id, priority=5)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Veri*FACTU"),
                'message': _("Factura añadida a la cola de envío. Se procesará automáticamente."),
                'type': 'success',
            }
        }
    
    def action_post(self):
        """Override para envío automático a Veri*FACTU"""
        result = super().action_post()
        
        # Envío automático si está habilitado
        for move in self:
            if (move.verifactu_enabled and 
                move.company_id.verifactu_enabled and 
                move.move_type in ['out_invoice', 'out_refund']):
                
                # Añadir a cola automáticamente
                queue_obj = self.env['verifactu.queue']
                queue_obj.create_queue_item(move.id, priority=10)
        
        return result
