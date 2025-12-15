# Z-Credit Payment Test Module

## Project Overview

This is a comprehensive Odoo 18 module developed for the Z-Credit Payment Gateway Integration assignment. The module demonstrates professional payment gateway integration with advanced validation, error handling, and edge case management.

**Module Name:** `zcredit_payment_test`  
**Odoo Version:** 18.0  
**Python Version:** 3.11+  

---

## Table of Contents

1. [Installation](#installation)
2. [Features](#features)
3. [Test Credentials](#test-credentials)
4. [Test Scenarios](#test-scenarios)
5. [Module Structure](#module-structure)
6. [Implementation Details](#implementation-details)
7. [Security Features](#security-features)
8. [Real API Integration](#real-api-integration)
9. [Troubleshooting](#troubleshooting)

---

## Installation

### Prerequisites

- Odoo 18.0 installed and running
- Python 3.11 or higher
- PostgreSQL 18+
- Virtual environment with Odoo dependencies installed

### Step-by-Step Installation

1. **Navigate to Odoo addons directory:**
   ```bash
   cd /path/to/odoo/addons
   ```

2. **Copy the module:**
   ```bash
   cp -r zcredit_payment_test /path/to/odoo/addons/
   ```

3. **Install the module in Odoo:**
   ```bash
   python odoo-bin -d your_database -i zcredit_payment_test --dev=reload
   ```

4. **Access the module:**
   - Navigate to **Accounting** menu
   - Click **Z-Credit** → **Transactions**

---

## Features

### 1. Form Creation (40 Points)

The module includes a professional, user-friendly form with complete field organization:

**Terminal Configuration Section:**
- Terminal Number (required)
- Terminal Password (masked input for security)

**Transaction Details Section:**
- Amount (required, with validation)
- Transaction Type (Sale, Authorize, Refund)

**Card Details Section:**
- Card Number (required, with format validation)
- Expiry Date (MM/YY format, expiration checking)
- CVV (required, 3-4 digit validation)
- Cardholder Name (required, with character validation)

**API Response Section:**
- Displays complete JSON response from API
- Read-only field for data integrity

**Status Bar:**
- Visual status indicator (Draft/Success/Failed)
- Quick status overview

###  2. API Integration

The module implements a robust API integration layer:

**API Request Handling:**
- Proper JSON payload construction
- Secure credential transmission
- Configurable timeout (30 seconds)
- Multiple HTTP status code handling

**Transaction Type Support:**
- **Sale:** Complete payment transaction
- **Authorize:** Authorization only (no actual charge)
- **Refund:** Return of previously charged amount

**Response Parsing:**
- Automatic JSON parsing
- Error code mapping
- Human-readable error messages
- Detailed logging for debugging

**Error Handling:**
- Network timeout handling
- Connection error recovery
- Invalid JSON response handling
- General exception catching
- Detailed error logging

### 3. User Experience 

The module provides an intuitive user experience:

**Visual Feedback:**
- Green success notifications 
- Red error notifications
- Clear, descriptive messages
- Real-time status updates

**Form State Management:**
- Draft state for initial entry
- Success state after approved transaction
- Failed state for declined transactions
- Pending state for timeout scenarios

**Data Persistence:**
- All transaction data automatically saved
- API responses stored in database
- Full audit trail via logs
- Transaction history available

---

## Test Credentials

Use the following credentials for testing transactions:

| Field | Value |
|-------|-------|
| **Terminal Number** | `0882016016` |
| **Terminal Password** | `Z0882016016` |
| **Test Card Number** | `375510390507767` |
| **Expiry Date** | `12/25` |
| **CVV** | `488` |

**Note:** These are mock credentials for testing purposes. They will work with the mock API implementation.

---

## Test Scenarios

### Category A: Basic Required Scenarios

#### Test 1: Successful Transaction
- **Expected Outcome:** Transaction approved
- **Status:** Success
- **Credentials:** Valid test credentials
- **Result:** API Response with transaction ID

#### Test 2: Failed Transaction (Invalid Credentials)
- **Input:** Wrong terminal password
- **Expected Outcome:** Authentication error
- **Status:** Failed
- **Error Code:** 101
- **Message:** "Authentication Failed"

#### Test 3: Network Error Handling
- **Scenario:** API timeout (30+ seconds)
- **Expected Outcome:** Timeout error
- **Status:** Pending
- **User Message:** "Request Timeout"

#### Test 4: Invalid Amount Handling
- **Input:** Negative amount (-50) or zero (0)
- **Expected Outcome:** Validation error before API call
- **Error:** "Amount must be a positive number"

#### Test 5: Invalid Card Number Format
- **Input:** Short card number (< 15 digits)
- **Expected Outcome:** API error response
- **Error Code:** 106
- **Message:** "Invalid Card Format"

### Category B: Advanced Edge Cases - Validation

#### Test 6: Expired Card
- **Input:** Expiry date in the past (e.g., 01/24)
- **Expected Outcome:** Validation error on save
- **Error:** "Card has expired"

#### Test 7: Invalid CVV Format
- **Input:** CVV with only 2 digits (e.g., 12)
- **Expected Outcome:** Validation error
- **Error:** "CVV must be 3 or 4 digits"

#### Test 8: Invalid Cardholder Name (Special Characters)
- **Input:** Name with special characters (e.g., "John@Doe")
- **Expected Outcome:** Validation error
- **Error:** "Only letters, spaces, hyphens, and dots are allowed"

#### Test 9: invalid Cardholder Name (Numbers Only)
- **Input:** Name with only numbers (e.g., "123")
- **Expected Outcome:** Validation error
- **Error:** "Only letters, spaces, hyphens, and dots are allowed"

### Category C: Advanced Edge Cases - Transaction Denials

#### Test 10: Stolen/Lost Card
- **Input:** Card number `4532015112830366`
- **Expected Outcome:** Card decline
- **Error Code:** 205
- **Message:** "Card Declined - Do Not Honor (Card reported stolen/lost)"

#### Test 11: Credit Limit Exceeded
- **Input:** Amount > $5,000 (e.g., 10000)
- **Expected Outcome:** Insufficient funds error
- **Error Code:** 206
- **Message:** "Insufficient Funds - Amount exceeds credit limit"

#### Test 12: Refund Limit Exceeded
- **Input:** Refund type with amount > $1,000
- **Expected Outcome:** Transaction not allowed
- **Error Code:** 207
- **Message:** "Transaction Not Allowed - Refund limit exceeded"

#### Test 13: Unique Reference ID Generation
- **Expected Outcome:** Each transaction gets unique ID
- **Format:** ZCTR0001, ZCTR0002, ZCTR0003, etc.
- **Verification:** No two transactions share same reference ID

---

## Module Structure

```
zcredit_payment_test/
│
├── __init__.py
│   └── Package initialization, imports models
│
├── __manifest__.py
│   └── Module metadata, dependencies, data files
│
├── models/
│   ├── __init__.py
│   │   └── Model imports
│   │
│   └── zcredit_transaction.py
│       └── Main model with:
│           • Field definitions
│           • Validation constraints
│           • API integration logic
│           • Error handling
│           • Edge case management
│
├── views/
│   └── zcredit_transaction_views.xml
│       └── Form view (for data entry)
│       └── List view (for transaction history)
│       └── Action definition (menu integration)
│       └── Menu items
│
└── security/
    └── ir.model.access.csv
        └── Access control rules (user permissions)
```

---

## Implementation Details

### Model Definition

**Model Name:** `zcredit.transaction`

**Field Definitions:**

| Field | Type | Required | Validation | Notes |
|-------|------|----------|-----------|-------|
| name | Char | Yes | Unique | Auto-generated Reference ID |
| terminal_number | Char | Yes | - | Terminal identifier |
| terminal_password | Char | Yes | - | Password (masked in UI) |
| card_number | Char | Yes | 13-19 digits | Credit/debit card |
| expiry_date | Char | Yes | MM/YY format | Date validation |
| cvv | Char | Yes | 3-4 digits | Security code |
| cardholder_name | Char | Yes | Letters, spaces, hyphens, dots | Account holder |
| amount | Float | Yes | > 0, <= 999999.99 | Transaction amount |
| transaction_type | Selection | Yes | sale/authorize/refund | Type of transaction |
| result | Text | No | Read-only | JSON API response |
| status | Selection | No | draft/success/failed/pending | Transaction state |

### Validation Constraints

1. **Amount Validation:**
   ```python
   - Must be positive (> 0)
   - Must not exceed 999,999.99
   ```

2. **Card Number Validation:**
   ```python
   - Length: 13-19 digits
   - Type: Numeric only
   - Format: Can include spaces (removed for validation)
   ```

3. **Expiry Date Validation:**
   ```python
   - Format: MM/YY (e.g., 12/25)
   - Month: 01-12
   - Must not be expired (checks against current date)
   ```

4. **CVV Validation:**
   ```python
   - Format: Numeric only
   - Length: 3-4 digits
   ```

5. **Cardholder Name Validation:**
   ```python
   - Length: 3-100 characters
   - Allowed: Letters, spaces, hyphens, periods
   - Not allowed: Numbers, special characters (@, #, $, etc.)
   ```

### API Integration Flow

```
User Action (Save/Test)
    ↓
Input Validation (Constraint Checks)
    ├─ If FAILED → Show ValidationError
    ├─ If PASSED → Continue
    ↓
Duplicate Check
    ├─ If DUPLICATE → Show Error
    ├─ If UNIQUE → Continue
    ↓
Business Logic Validation
    ├─ Card validation (stolen, etc.)
    ├─ Amount limits (credit limit, etc.)
    ├─ Transaction restrictions
    ↓
Mock/Real API Call
    ├─ Prepare JSON payload
    ├─ Send HTTP POST request
    ├─ Handle timeout (30 seconds)
    ↓
Response Parsing
    ├─ Parse JSON response
    ├─ Check success flag
    ├─ Extract error messages
    ↓
Update Record
    ├─ Save API response
    ├─ Update status (success/failed)
    ├─ Create log entry
    ↓
User Notification
    ├─ Show success (green) or error (red) message
    ├─ Display detailed response
```

---

## Security Features

###  Data Security

1. **Password Masking:**
   - Terminal password displayed as dots (••••••••)
   - CVV displayed as masked dots

2. **Input Validation:**
   - Prevents malicious input via constraints
   - Sanitizes cardholder name (no special chars)
   - Type validation on all fields

3. **API Security:**
   - Supports HTTPS for real API calls
   - Authorization header support
   - Timeout protection against hanging requests

### Access Control

- User-level permissions via `ir.model.access.csv`
- Group-based access (base.group_user)
- Read/write restrictions based on roles

### Audit Trail

- All transactions logged with timestamps
- API responses stored for audit
- Transaction history preserved in database
- Detailed error logging for debugging

---

## Real API Integration

### Upgrading to Production API

To upgrade from mock to real Z-Credit API:

1. **Update API Endpoint:**
   ```python
   url = "https://api.zcredit.com/v1/transactions"  # Real endpoint
   ```

2. **Add Authentication:**
   ```python
   headers = {
       'Content-Type': 'application/json',
       'Authorization': f'Bearer {API_KEY}',
       'X-API-Version': '1.0'
   }
   ```

3. **Replace Mock Logic:**
   ```python
   # Remove mock condition checks
   # Use actual API response instead
   response = requests.post(url, headers=headers, json=payload, timeout=30)
   api_result = response.json()
   ```

4. **Handle Additional Error Codes:**
   - Map Z-Credit error codes to messages
   - Implement retry logic for transient failures
   - Add webhook support for async notifications

5. **Add PCI Compliance:**
   - Implement tokenization
   - Remove card number storage
   - Use secure API keys

---

## Files Included

- `__init__.py` - Package initialization
- `__manifest__.py` - Module metadata
- `models/zcredit_transaction.py` - Core model implementation
- `models/__init__.py` - Models package init
- `views/zcredit_transaction_views.xml` - UI definitions
- `security/ir.model.access.csv` - Access control


## Known Limitations

1. Mock API only - real Z-Credit API not integrated
2. No webhook support for async notifications
3. No transaction reconciliation features
4. No multi-currency support (base currency only)

