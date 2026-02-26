# Activity Diagram Documentation

## Purpose

This folder contains activity diagrams for the seven core use cases.  
Each diagram models workflow behavior, branching, and loop conditions across actors and system components.

## Diagram Inventory

| Use Case                        | Folder                      | Primary Actors/Lanes                  | Key Decision Points                                                                     |
| ------------------------------- | --------------------------- | ------------------------------------- | --------------------------------------------------------------------------------------- |
| UC01 - Authenticate User        | `Authenticate User/`        | User, System                          | Credential format validity, credential match, retry/exit                                |
| UC02 - Manage Accounts          | `Manage Accounts/`          | User, System                          | Authentication, action type (add/edit/delete), input validity, delete confirmation      |
| UC03 - Import Transactions      | `Import Transactions/`      | User, System, External Banking System | Authentication, import method (bank/csv), connection/file validity, import confirmation |
| UC04 - Categorize Expenses      | `Categorize Expenses/`      | System, User                          | Merchant-rule match, keyword match, manual categorization path                          |
| UC05 - Set Budget Thresholds    | `Set Budget Thresholds/`    | User, System                          | Authentication, action type (create/edit/delete), input validity, delete confirmation   |
| UC06 - Receive Budget Alerts    | `Receive Budget Alerts/`    | System, Notification Service, User    | Budget existence, threshold crossing, duplicate alert check, user follow-up action      |
| UC07 - View Analytics Dashboard | `View Analytics Dashboard/` | User, System                          | Authentication, interaction type (date/account/category), iterative dashboard refresh   |

## File Structure

Each use-case folder includes:

- `<Use_Case_Name>.puml` - PlantUML source (authoritative)
- `<Use_Case_Name>.png` - rendered image

## Modeling Conventions Used

- **Swimlanes** separate responsibility by actor/system role.
- **Decision nodes** capture alternatives and guard conditions.
- **Loops** represent retries and repeated processing.
- **Included use cases** are annotated as `<<include>>` in activity notes:
  - UC02 includes UC01
  - UC03 includes UC01 and UC04
  - UC05 includes UC01

## Coverage Notes

- Authentication gating is explicit in UC02, UC03, UC05, and UC07.
- Import and categorization are linked so transaction ingestion and semantic classification remain traceable.
- Budget configuration (UC05) and budget alerting (UC06) are behaviorally connected.
- Dashboard flow (UC07) models both initial load and iterative user-driven filtering.
