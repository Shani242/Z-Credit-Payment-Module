
-----

# Z-Credit Payment Test Module

## Project Overview

This is a comprehensive Odoo 18 module developed for the Z-Credit Payment Gateway Integration assignment. The module provides a user interface to interact directly with the **official Z-Credit Sandbox API endpoint** (`CommitFullTransaction`), featuring robust input validation, secure data handling, and precise error parsing.

**Module Name:** `zcredit_payment_test`  
**Odoo Version:** 18.0  
**Focus:** API Integration, Advanced Validation, and Error Handling.

-----

## Table of Contents

1.  [Installation and Access](https://www.google.com/search?q=%23installation-and-access)
2.  [Current API Status & Logic](https://www.google.com/search?q=%23current-api-status--logic)
3.  [Features Summary](https://www.google.com/search?q=%23features-summary)
4.  [Test Credentials](https://www.google.com/search?q=%23test-credentials)
5.  [Test Scenarios](https://www.google.com/search?q=%23test-scenarios)
6.  [Implementation Details](https://www.google.com/search?q=%23implementation-details)
7.  [Module Structure](https://www.google.com/search?q=%23module-structure)

-----

## 1\. Installation and Access

### Installation Steps

1.  **Clone/Copy Module:** Place the `zcredit_payment_test` folder into your Odoo `addons` path.
2.  **Install Dependencies:** Ensure Odoo's Python environment includes `requests`.
3.  **Install in Odoo:** Install the module via the Apps menu or by starting Odoo with the `-i zcredit_payment_test` flag.

### Access

  - Navigate to the **Accounting** app in Odoo.
  - Select **Z-Credit** → **Transactions**.

-----

## 2\. Current API Status & Logic

The module is configured to communicate with the following live Z-Credit Sandbox endpoint:

| Endpoint Name | URL |
| :--- | :--- |
| **CommitFullTransaction** | `https://pci.zcredit.co.il/ZCreditWS/api/Transaction/CommitFullTransaction` |

### Critical Logic 

The module uses a highly reliable method for determining success, based on the specific JSON structure returned by the Z-Credit API:

Success is confirmed only if **ALL** three conditions are met:

1.  **HTTP Status:** `HTTP 200` (Connection successful).
2.  **API Error Flag:** `HasError` is `False`.
3.  **Return Code:** `ReturnCode` is `0` (indicating transaction approval).

Any deviation from this combined logic results in the transaction being marked as **Failed**, ensuring data integrity.

-----

## 3\. Features Summary

| Category | Key Features |
| :--- | :--- |
| **Form & UX** | Masked password/CVV fields, clear status bar (`draft`, `processing`, `success`, `failed`), detailed transaction history, Chatter for auditing.  |
| **Validation** | Strict field validation (`@api.constrains`) to prevent bad data from reaching the API (e.g., Expired Card check, positive Amount check, format checking). |
| **API Integration** | Direct call to live Z-Credit endpoint, correct JSON payload construction (`password` as key, `ExpDate_MMYY` format), timeout protection (45s). |
| **Error Handling** | Comprehensive `try/except` for network errors (`Timeout`, `ConnectionError`) and application errors (`JSONDecodeError`), displaying Z-Credit's specific `ReturnCode` on failure. |
| **Transaction Types** | Supports **Sale** (`J=0`) and **Authorize** (`J=5`) via the `J` parameter mapping. |

-----

## 4\. Test Credentials

Use these credentials (for the Z-Credit testing environment) to execute transactions:

| Field | Value |
|-------|-------|
| **Terminal Number** | `0882016016` |
| **Terminal Password** | `Z0882016016` |
| **Test Card Number** | `375510390507767` |
| **Expiry Date** | `12/25` |
| **CVV** | `488` |
| **Cardholder Name** | *Any valid name (e.g., Test User)* |

-----

## 5\. Test Scenarios

These scenarios test both the Odoo validation layer and the live API communication.

| Scenario | Input / Action | Expected Result |
| :--- | :--- | :--- |
| **1. Successful Sale** | Valid credentials, Amount \> 0, Type: Sale | **Status: Success**. Green notification with Approval Number. |
| **2. Successful Authorize** | Valid credentials, Type: Authorize (J5) | **Status: Success**. Transaction authorized (not captured). |
| **3. Invalid Amount** | Amount: 0.0 or -10.0 | **Validation Error** (before API call): "Transaction amount must be a positive number." |
| **4. Expired Card** | Expiry Date: `01/24` (assuming current date is after Jan 2024) | **Validation Error** (before API call): "Card is expired." |
| **5. Network Timeout** | Simulate network issue or high latency | **Status: Failed**. Red notification: "The API request timed out." |
| **6. Authentication Failure** | Wrong Terminal Password | **Status: Failed**. Red notification with Z-Credit Error Code (e.g., Code -1 to -20). |
| **7. Invalid Card Format** | Card Number with non-numeric characters | **Validation Error** (before API call): "Invalid Card Number format." |

-----

## 6\. Module Structure

The module adheres to standard Odoo directory conventions:

```
zcredit_payment_test/
├── __manifest__.py
├── __init__.py
├── models/
│   ├── __init__.py
│   └── zcredit_transaction.py
├── views/
│   └── zcredit_transaction_views.xml
├── security/
│   └── ir.model.access.csv  
``