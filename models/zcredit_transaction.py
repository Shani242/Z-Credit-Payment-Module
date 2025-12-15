# -*- coding: utf-8 -*-
import json
import logging
import re
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import requests
from requests.exceptions import Timeout, ConnectionError, RequestException
from datetime import date

_logger = logging.getLogger(__name__)


class ZCreditTransaction(models.Model):
    _name = 'zcredit.transaction'
    _description = 'Z-Credit Payment Test'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # API Configuration
    API_URL = 'https://pci.zcredit.co.il/ZCreditWS/api/Transaction/CommitFullTransaction'

    # Fields
    name = fields.Char('Reference', default=lambda self: _('New'), readonly=True, copy=False)

    # Terminal Configuration
    terminal_number = fields.Char('Terminal Number', required=True, tracking=True)
    terminal_password = fields.Char('Terminal Password', required=True, tracking=True)

    # Card Details
    card_number = fields.Char('Credit Card Number', required=True)
    expiry_date = fields.Char('Expiry (MM/YY)', required=True, help="Format: MM/YY")
    cvv = fields.Char('CVV', required=True)
    cardholder_name = fields.Char('Cardholder Name', required=True)

    # Transaction Details
    amount = fields.Float('Amount', required=True, tracking=True)
    transaction_type = fields.Selection([
        ('sale', 'Sale'),
        ('authorize', 'Authorize (J5)'),
        ('refund', 'Refund'),
    ], string='Transaction Type', default='sale', required=True, tracking=True)

    # Results
    result = fields.Text('API Response', readonly=True, copy=False)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('processing', 'Processing'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ], string='Status', default='draft', required=True, tracking=True, copy=False)

    # Odoo Overrides and Sequence
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('zcredit.transaction') or _('New')
        return super().create(vals_list)

    # Validation (@api.constrains)
    @api.constrains('amount')
    def _check_amount(self):
        """Validate amount is positive"""
        for record in self:
            if record.amount <= 0:
                raise ValidationError(_("Transaction amount must be a positive number."))

    @api.constrains('card_number')
    def _check_card_number(self):
        """Validate card number format """
        for record in self:
            if not re.fullmatch(r'\d{13,19}', record.card_number.replace(' ', '')):
                raise ValidationError(_("Invalid Card Number format. Must be 13-19 digits."))

    @api.constrains('expiry_date')
    def _check_expiry_date(self):
        """Validate expiry date format and if not expired"""
        for record in self:
            if not re.fullmatch(r'\d{2}/\d{2}', record.expiry_date):
                raise ValidationError(_("Invalid Expiry Date format. Must be MM/YY."))

            try:
                month_str, year_str = record.expiry_date.split('/')
                current_century = date.today().year // 100 * 100
                expiry_year = current_century + int(year_str)
                expiry_month = int(month_str)

                if not (1 <= expiry_month <= 12):
                    raise ValidationError(_("Invalid Expiry Month (must be 01-12)."))

                today = date.today()

                if expiry_year < today.year or (expiry_year == today.year and expiry_month < today.month):
                    raise ValidationError(_("Card is expired."))

            except ValueError:
                raise ValidationError(_("Invalid Expiry Date format."))

    @api.constrains('cvv')
    def _check_cvv(self):
        """Validate CVV format"""
        for record in self:
            if not re.fullmatch(r'\d{3,4}', record.cvv):
                raise ValidationError(_("Invalid CVV. Must be 3 or 4 digits."))

    # Helper Methods for API Response Handling

    def _return_notification(self, message, type='success'):
        """Helper to create an Odoo notification dictionary."""
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': message,
                'type': type,
                'sticky': type in ('danger', 'warning'),
            }
        }

    def _handle_api_response(self, response_text, http_status_code):
        """
        Processes the API response text and updates the record.
        """
        self.ensure_one()
        self.result = response_text

        try:
            response_json = json.loads(response_text)
            self.result = json.dumps(response_json, indent=2, ensure_ascii=False)

            # ---  Z-Credit ---
            has_error = response_json.get('HasError', True)
            return_code = response_json.get('ReturnCode')
            return_message = response_json.get('ReturnMessage')

            is_successful = (http_status_code == 200) and (has_error is False) and (return_code == 0)

            if is_successful:
                self.status = 'success'
                approval_num = response_json.get('ApprovalNumber', '')
                message = _("Transaction completed successfully! Approval: %s") % approval_num
                return self._return_notification(message, 'success')
            else:
                self.status = 'failed'

                prefix = f"Z-Credit Error ({return_code}): " if return_code is not None else "API Error: "
                error_message = return_message or _(
                    "Transaction failed. Check the 'API Response' field for full details.")

                _logger.warning("Z-Credit Transaction Failed: %s | Response: %s", self.name, response_text)
                return self._return_notification(prefix + error_message, 'danger')

        except json.JSONDecodeError:
            self.status = 'failed'
            _logger.error("API returned non-JSON data or invalid JSON: %s", response_text)
            self.result = _("API returned invalid data: %s") % response_text
            return self._return_notification(_("API returned invalid data. Check result field."), 'danger')
        except Exception as e:
            self.status = 'failed'
            _logger.error("Error handling Z-Credit response: %s", str(e))
            self.result += f"\nInternal Parsing Error: {str(e)}"
            return self._return_notification(_("An unexpected error occurred during response processing."), 'danger')

    # Main Transaction Method

    def action_test_transaction(self):
        self.ensure_one()

        self.status = 'processing'
        self.result = _("Sending request to Z-Credit API...")

        j_parameter = 0
        if self.transaction_type == 'authorize':
            j_parameter = 5  # J=5 for Authorization (J5)

        expiry_formatted = self.expiry_date.replace('/', '')  # MM/YY -> MMYY

        payload = {
            # Credentials
            'TerminalNumber': self.terminal_number,
            'password': self.terminal_password,
            # Card Data
            'CardNumber': self.card_number.replace(' ', ''),
            'ExpDate_MMYY': expiry_formatted,
            'CVV': self.cvv,
            'CardHolderName': self.cardholder_name,
            # Transaction Data
            'TransactionSum': self.amount,
            'J': j_parameter,
        }

        headers = {'Content-Type': 'application/json'}

        try:
            _logger.info("Z-Credit API Request for %s: %s", self.name, payload)

            response = requests.post(self.API_URL, headers=headers, json=payload, timeout=45)

            return self._handle_api_response(response.text, response.status_code)

        except Timeout:
            self.status = 'failed'
            self.result = _("Request timed out after 45 seconds.")
            return self._return_notification(_("The API request timed out."), 'danger')
        except ConnectionError:
            self.status = 'failed'
            self.result = _("Connection Error: Could not reach Z-Credit gateway.")
            return self._return_notification(_("Could not connect to the Z-Credit API endpoint."), 'danger')
        except RequestException as e:
            self.status = 'failed'
            self.result = _("A network error occurred: %s") % str(e)
            return self._return_notification(_("A general network error occurred."), 'danger')
        except Exception as e:
            #  ValidationError
            if isinstance(e, ValidationError):
                self.status = 'draft'
                raise e

            self.status = 'failed'
            self.result = _("An unexpected internal error occurred: %s") % str(e)
            _logger.exception("Unexpected error during Z-Credit transaction attempt.")
            return self._return_notification(_("An unexpected internal system error occurred."), 'danger')