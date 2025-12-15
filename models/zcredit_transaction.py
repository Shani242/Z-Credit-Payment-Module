# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime
import re
import requests
import json
import logging

_logger = logging.getLogger(__name__)


class ZCreditTransaction(models.Model):
    _name = 'zcredit.transaction'
    _description = 'Z-Credit Payment Test'

    # Required Fields
    name = fields.Char('Reference', default='New', readonly=True)

    terminal_number = fields.Char('Terminal Number', required=True)
    terminal_password = fields.Char('Terminal Password', required=True)

    card_number = fields.Char('Card Number', required=True)
    expiry_date = fields.Char('Expiry (MM/YY)', required=True, help="Format: MM/YY")
    cvv = fields.Char('CVV', required=True)
    cardholder_name = fields.Char('Cardholder Name', required=True)

    amount = fields.Float('Amount', required=True)
    transaction_type = fields.Selection([
        ('sale', 'Sale'),
        ('authorize', 'Authorize'),
        ('refund', 'Refund'),
    ], string='Transaction Type', default='sale', required=True)

    result = fields.Text('API Response', readonly=True)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('pending', 'Pending'),  # For timeout scenarios
    ], string='Status', default='draft', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        """Generate unique Reference ID on creation"""
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                # Generate unique ID
                seq = self.env['ir.sequence'].next_by_code('zcredit.transaction')
                vals['name'] = seq or f'TRX-{self.env.uid}-{fields.Datetime.now().timestamp()}'
        return super().create(vals_list)

    # ========== VALIDATION CONSTRAINTS ==========

    @api.constrains('amount')
    def _check_amount(self):
        """Validate amount is positive"""
        for record in self:
            if record.amount <= 0:
                raise ValidationError("Amount must be a positive number.")
            if record.amount > 999999.99:
                raise ValidationError("Amount exceeds maximum allowed limit.")

    @api.constrains('card_number')
    def _check_card_number(self):
        """Validate card number format (Luhn algorithm)"""
        for record in self:
            card = record.card_number.replace(' ', '')

            # Check length
            if not (13 <= len(card) <= 19):
                raise ValidationError("Card number must be between 13-19 digits.")

            # Check if only digits
            if not card.isdigit():
                raise ValidationError("Card number must contain only digits.")

    @api.constrains('expiry_date')
    def _check_expiry_date(self):
        """Validate expiry date format and if not expired"""
        for record in self:
            expiry = record.expiry_date.strip()

            # Check format MM/YY
            if not re.match(r'^\d{2}/\d{2}$', expiry):
                raise ValidationError("Expiry date must be in MM/YY format (e.g., 12/25).")

            # Parse month and year
            try:
                month, year = expiry.split('/')
                month = int(month)
                year = int(year)

                # Validate month
                if not (1 <= month <= 12):
                    raise ValidationError("Month must be between 01 and 12.")

                # Check if card is expired (assuming 20YY format)
                current_year = datetime.now().year
                current_month = datetime.now().month

                # Convert YY to YYYY (assuming 20YY)
                full_year = 2000 + year

                # Card expires at the end of the month
                if full_year < current_year or (full_year == current_year and month < current_month):
                    raise ValidationError(f"Card has expired. Expiry date: {expiry}")

            except (ValueError, IndexError):
                raise ValidationError("Invalid expiry date format.")

    @api.constrains('cvv')
    def _check_cvv(self):
        """Validate CVV format"""
        for record in self:
            cvv = record.cvv.strip()

            # CVV should be 3-4 digits
            if not re.match(r'^\d{3,4}$', cvv):
                raise ValidationError("CVV must be 3 or 4 digits.")

    @api.constrains('cardholder_name')
    def _check_cardholder_name(self):
        """Validate cardholder name"""
        for record in self:
            name = record.cardholder_name.strip()

            # Check if empty
            if not name:
                raise ValidationError("Cardholder name is required.")

            # Check length
            if len(name) < 3:
                raise ValidationError("Cardholder name must be at least 3 characters.")

            if len(name) > 100:
                raise ValidationError("Cardholder name must not exceed 100 characters.")

            # Check for valid characters (letters, spaces, hyphens, dots)
            if not re.match(r"^[a-zA-Z\s\-\.]*$", name):
                raise ValidationError(
                    "Cardholder name contains invalid characters. "
                    "Only letters, spaces, hyphens, and dots are allowed."
                )

    # ========== EDGE CASE HANDLERS ==========

    def _check_duplicate_transaction(self):
        """Check if this transaction was already processed (Duplicate Prevention)"""
        existing = self.search([
            ('name', '=', self.name),
            ('status', '!=', 'draft'),
            ('id', '!=', self.id),
        ])

        if existing:
            raise ValidationError(
                f"Transaction {self.name} was already processed. "
                "Duplicate transactions are not allowed."
            )

    def _simulate_card_validation(self):
        """Simulate card validation scenarios"""
        # Stolen/Lost card simulation
        stolen_cards = ['4532015112830366', '5425233010103442']
        if self.card_number in stolen_cards:
            return {
                'Success': False,
                'Code': '205',
                'Message': 'Card Declined - Do Not Honor (Card is reported stolen/lost)'
            }

        # Credit limit simulation
        if self.amount > 5000:
            return {
                'Success': False,
                'Code': '206',
                'Message': 'Insufficient Funds - Amount exceeds credit limit'
            }

        # Restricted transaction type
        if self.transaction_type == 'refund' and self.amount > 1000:
            return {
                'Success': False,
                'Code': '207',
                'Message': 'Transaction Not Allowed - Refund limit exceeded'
            }

        return None

    # ========== MAIN ACTION ==========

    def action_test_transaction(self):
        """Test transaction with Z-Credit API (Mock Implementation)"""
        self.ensure_one()

        try:
            # Check for duplicate transactions
            self._check_duplicate_transaction()

            # ========== VALIDATION PHASE ==========
            if not self.terminal_number or not self.terminal_password:
                return self._return_error(
                    'Missing Required Fields',
                    'Terminal number and password are required.'
                )

            if not self.cardholder_name:
                return self._return_error(
                    'Missing Required Fields',
                    'Cardholder name is required.'
                )

            # ========== BUSINESS LOGIC PHASE ==========

            # Check for known card issues
            card_error = self._simulate_card_validation()
            if card_error:
                return self._handle_api_response(card_error, 400)

            TERMINAL_OK = (self.terminal_number == '0882016016' and
                           self.terminal_password == 'Z0882016016')

            # Invalid card format
            if len(self.card_number) < 15:
                api_result = {
                    'Success': False,
                    'Code': '106',
                    'Message': 'Invalid Card Format'
                }
                return self._handle_api_response(api_result, 400)

            # Authentication failed
            elif not TERMINAL_OK:
                api_result = {
                    'Success': False,
                    'Code': '101',
                    'Message': 'Authentication Failed: Invalid Terminal ID or Password'
                }
                return self._handle_api_response(api_result, 401)

            # Amount validation
            elif self.amount <= 0:
                api_result = {
                    'Success': False,
                    'Code': '102',
                    'Message': 'Invalid Amount'
                }
                return self._handle_api_response(api_result, 400)

            # Successful transaction
            else:
                api_result = {
                    'Success': True,
                    'Code': '000',
                    'Message': 'Transaction Approved',
                    'ZCreditID': f'TRX-{self.name}',
                    'Amount': self.amount,
                    'Type': self.transaction_type.upper(),
                    'Timestamp': fields.Datetime.now()
                }
                return self._handle_api_response(api_result, 200)

        except ValidationError as e:
            # Validation error from constraints
            return self._return_error('Validation Error', str(e))

        except requests.exceptions.Timeout:
            # Network timeout - Transaction status unknown
            return self._return_error(
                'API Request Timeout',
                'Server did not respond in time. Transaction status is pending.',
                status='pending'
            )

        except requests.exceptions.ConnectionError:
            return self._return_error(
                'Connection Error',
                'Cannot reach API server. Please check your internet connection.'
            )

        except requests.exceptions.RequestException as e:
            return self._return_error(
                'Request Error',
                f'An error occurred during the request: {str(e)}'
            )

        except json.JSONDecodeError:
            return self._return_error(
                'Invalid API Response',
                'Server returned invalid JSON. Please contact support.'
            )

        except Exception as e:
            _logger.error(f"Unexpected error in transaction: {str(e)}", exc_info=True)
            return self._return_error(
                'Unexpected Error',
                f'An unexpected error occurred: {str(e)}'
            )

    # ========== HELPER METHODS ==========

    def _handle_api_response(self, api_result, status_code):
        """Handle API response and update transaction"""
        response_text = json.dumps(api_result, indent=2, default=str)
        self.result = response_text

        if api_result.get('Success') and status_code in [200, 201]:
            self.status = 'success'
            return self._return_success(api_result.get('Message', 'Transaction approved'))
        else:
            self.status = 'failed'
            return self._return_error(
                'Transaction Failed',
                api_result.get('Message', 'Unknown error occurred')
            )

    def _return_success(self, message):
        """Return success notification"""
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': f'{message}',
                'type': 'success',
                'sticky': False,
            }
        }

    def _return_error(self, title, message, status='failed'):
        """Return error notification and update status"""
        self.result = f"{title}: {message}"
        self.status = status
        _logger.error(f"{title} - {message}")

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': f' {title}: {message}',
                'type': 'danger',
                'sticky': True,
            }
        }