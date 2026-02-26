# Analysis Artifacts

This folder contains the analysis deliverables for the **Intelligent Personal Finance Management System**.

## Scope

The analysis package is organized into three diagram families:

- **Activity Diagrams** (`Analysis/ActivityDiagram`): Workflow behavior per use case.
- **Domain Model** (`Analysis/DomainModel`): Core business entities and associations.
- **Robustness Diagrams** (`Analysis/Robustness`): Boundary-control-entity responsibility mapping.

## Use Cases Covered

All three diagram sets are aligned to these use cases:

1. UC01 - Authenticate User
2. UC02 - Manage Accounts
3. UC03 - Import Transactions
4. UC04 - Categorize Expenses
5. UC05 - Set Budget Thresholds
6. UC06 - Receive Budget Alerts
7. UC07 - View Analytics Dashboard

## Folder Guide

- `ActivityDiagram/README.md`: Detailed guide for workflow diagrams and UC-level flow intent.
- `DomainModel/README.md`: Canonical domain model, entity groups, and cardinalities.
- `Robustness/README.md`: ECB object responsibilities and interaction rules by use case.

## Source of Truth

- PlantUML files (`.puml`) are the editable source artifacts.
- Image/PDF files are rendered or presentation exports.
- If content differs, treat `.puml` files as authoritative.

## Rendering

If PlantUML is installed locally, render all analysis diagrams from repository root:

```bash
find Analysis -name "*.puml" -print0 | xargs -0 plantuml
```
