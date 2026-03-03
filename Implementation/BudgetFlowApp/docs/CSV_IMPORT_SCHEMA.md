# CSV Import Schema — UC03

This document defines the **required columns**, accepted formats, and rejection messages for transaction CSV imports.

## Required Columns

| Column name (case-insensitive) | Type   | Description                    | Example        |
|--------------------------------|--------|--------------------------------|----------------|
| `date`                         | Date   | Transaction posted date        | 2025-01-15     |
| `amount`                      | Decimal| Signed amount (negative = debit)| -42.50 or 100.00 |
| `description`                 | String | Free-text description          | AMZN Mktp US   |

Optional but recommended:

| Column name (case-insensitive) | Type   | Description           | Example    |
|--------------------------------|--------|------------------------|------------|
| `merchant`                     | String | Merchant name          | Amazon     |
| `reference`                    | String | External transaction ID| TX-12345   |

## Accepted Date Formats

- `YYYY-MM-DD` (ISO)
- `MM/DD/YYYY`
- `DD/MM/YYYY`

Invalid dates or non-parseable values will cause row rejection with a message like: `Row N: Invalid date format for column 'date'. Use YYYY-MM-DD, MM/DD/YYYY, or DD/MM/YYYY.`

## Accepted Amount Format

- Decimal with optional minus sign and up to 2 decimal places.
- Rejection: `Row N: Invalid amount in column 'amount'. Must be a number with up to 2 decimal places.`

## Encoding and Delimiter

- **Encoding:** UTF-8. Other encodings may be rejected with: `File must be UTF-8 encoded.`
- **Delimiter:** Comma (`,`). First row must be header. Rejection: `Missing required header. Expected at least: date, amount, description.`

## Duplicate Detection

A row is considered duplicate if for the **same account and user** there is already a transaction with the same:

- `posted_date` (normalized to date)
- `amount`
- `description` (normalized: trimmed, case-insensitive)

Duplicate rows are **skipped** (not inserted) and counted in the import result (e.g. `duplicates_skipped`).

## Rejection Messages (User-Facing)

- Missing required column: `Missing required column: '<name>'. Required columns: date, amount, description.`
- Empty file: `File is empty or has no data rows.`
- Row-level error: `Row <N>: <reason>.`
- File too large: `File exceeds maximum size (e.g. 5MB).`
- Invalid account: `Account not found or access denied.` (404/403 at API level)

## Example Valid CSV

```csv
date,amount,description,merchant
2025-01-15,-42.50,AMZN Mktp US,Amazon
2025-01-16,1500.00,Salary deposit,
```

Implementation will live in `backend/app/utils/csv_schema.py` and be used by `ImportService` in UC03.
