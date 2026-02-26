# Domain Model Documentation

## Purpose

This folder defines the conceptual domain entities and relationships for the Intelligent Personal Finance Management System.

## Canonical Model

- Primary model for current analysis: `Updated DomainModel/DomainModel_FINAL.puml`
- Earlier baseline (kept for reference): `DomainModel.puml`

Use `DomainModel_FINAL.puml` as the source of truth for downstream design work.

## Entity Groups

- **Identity and Ownership:** `User`
- **Accounts:** `FinancialAccount` (abstract), `BankAccount`, `CreditCardAccount`, `InvestmentAccount`, `Institution`
- **Transactions:** `Transaction`, `Merchant`, `Category`
- **Budgeting:** `Budget`, `BudgetItem`
- **Alerting:** `BudgetAlert`

## Key Structural Rules

- Inheritance:
  - `FinancialAccount` is specialized by `BankAccount`, `CreditCardAccount`, and `InvestmentAccount`.
- Ownership:
  - A `User` owns many `FinancialAccount`, `Budget`, and `BudgetAlert` records.
- Transaction placement:
  - A `FinancialAccount` contains many `Transaction` records.
  - A `Transaction` may reference one `Category` and one `Merchant`.
- Budget composition:
  - A `Budget` contains one or more `BudgetItem` records.
  - Each `BudgetItem` tracks spending for one `Category`.
- Alert linkage:
  - A `BudgetAlert` optionally monitors a `Budget`.

## Cardinality Summary (Final Model)

- `User "1" -- "0..*" FinancialAccount`
- `User "1" -- "0..*" Budget`
- `User "1" -- "0..*" BudgetAlert`
- `Institution "1" -- "0..*" FinancialAccount`
- `FinancialAccount "1" -- "0..*" Transaction`
- `Transaction "*" -- "0..1" Category`
- `Transaction "*" -- "0..1" Merchant`
- `Budget "1" -- "1..*" BudgetItem`
- `BudgetItem "*" -- "1" Category`
- `BudgetAlert "*" -- "0..1" Budget`

## Relationship to Use Cases

- UC02 relies on account ownership and account polymorphism.
- UC03 and UC04 rely on transaction-category-merchant linkage.
- UC05 and UC06 rely on budget-budget item-alert relationships.
- UC07 relies on aggregated reads across transactions, categories, budgets, and accounts.

## Update Guidance

When evolving the model:

1. Add entity attributes only if needed by at least one use case behavior.
2. Preserve cardinalities unless use case constraints explicitly change.
3. Keep association names semantically meaningful for future class and sequence diagrams.
