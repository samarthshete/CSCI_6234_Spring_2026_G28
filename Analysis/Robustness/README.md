# Robustness Diagram Documentation

## Purpose

This folder contains robustness diagrams for all seven use cases using the **Entity-Control-Boundary (ECB)** approach.  
These diagrams bridge use case text and detailed design by assigning responsibilities to UI boundaries, control logic, and domain entities.

## Diagram Inventory

| Use Case | Boundary Focus | Control Focus | Entity Focus |
|---|---|---|---|
| UC01 - Authenticate User | Login screen, dashboard, error display | Authentication controller, session manager | User account, session |
| UC02 - Manage Accounts | Account list/forms, confirmation, message display | Account controller, validation handler | Account, user |
| UC03 - Import Transactions | Import UI, account selector, file/bank interfaces, result/progress UI | Import controller, parser, duplicate detector, categorization trigger | Transaction, account |
| UC04 - Categorize Expenses | Transaction list, manual prompt, category selector, result display | Categorization controller with rule/AI/manual handlers | Transaction, category, categorization rule |
| UC05 - Set Budget Thresholds | Budget settings UI, selectors/forms, confirmation message | Budget controller, validation handler, alert config manager | Budget, category, user |
| UC06 - Receive Budget Alerts | Alert panel/details, notification interface, dashboard badge | Budget monitor, alert controller, alert factory, dispatcher | Budget, budget alert, transaction, user preferences |
| UC07 - View Analytics Dashboard | Dashboard screen, charts, filters, progress indicators | Analytics controller, data aggregator, chart/trend processors | Transaction, category, budget, account |

## File Structure

Each use-case folder generally includes:

- `<Use_Case_Name>.puml` - PlantUML source (authoritative)
- `<Use_Case_Name>.png` - rendered diagram
- `<Use_Case_Name>_HandDrawn.pdf` - hand-drawn version used during analysis

## ECB Interaction Rules Applied

- Allowed:
  - Actor <-> Boundary
  - Boundary <-> Control
  - Control <-> Entity
  - Control <-> Control
- Avoided by design:
  - Actor <-> Entity
  - Boundary <-> Entity

These rules preserve separation of concerns and keep business logic out of UI objects.

## Pattern-Oriented Notes Captured

- UC04 models categorization control as a chain-style flow (rule -> AI -> manual path).
- UC06 explicitly models monitoring/notification behavior with observer and factory-style responsibilities.
- UC03 and UC05 include cross-use-case coupling (`UC03 -> UC04`, `UC05 -> UC06`) via control-level triggers.

## What Robustness Diagrams Do and Do Not Show

- They **do show** object responsibility and permitted communication paths.
- They **do not show** detailed runtime sequence timing (that belongs in sequence diagrams).

## Update Guidance

When updating robustness diagrams:

1. Keep all UI elements as `boundary` objects.
2. Keep orchestration/validation/processing in `control` objects.
3. Keep persistent business data in `entity` objects.
4. Re-check ECB interaction rules after any new connection is introduced.
