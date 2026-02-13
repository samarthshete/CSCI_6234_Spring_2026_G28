# Analysis Phase – Robustness Diagrams

## Intelligent Personal Finance Management System

CSCI 6234 – Object-Oriented Design

---

## 📌 Purpose of This Folder

This folder contains the robustness diagrams created during the **Analysis discipline** of the OOAD process.

Robustness analysis bridges the gap between:

- **Use Case Analysis (What the system does)**
- **Design (How the system will be implemented)**

The diagrams follow the robustness modeling approach described by:

- I. Jacobson et al., _The Unified Software Development Process_, 1999
- J. Arlow & I. Neustadt, _UML and the Unified Process_, 2002

---

## 📊 Robustness Diagrams Included (7 Use Cases)

1. Authenticate User
2. Manage Accounts
3. Import Transactions
4. Categorize Expenses
5. Set Budget Thresholds
6. Receive Budget Alerts
7. View Analytics Dashboard

Each use case has its own folder.

---

## 📁 Folder Structure

Each use case folder contains:

- `<Use_Case_Name>.puml`  
  → PlantUML source file

- `<Use_Case_Name>.png`  
  → PNG image generated from PlantUML

- `<Use_Case_Name>_HandDrawn.pdf`  
  → Hand-drawn robustness diagram (white background, no lines)

Example:

Authenticate_User/
├── Authenticate_User.puml
├── Authenticate_User.png
└── Authenticate_User_HandDrawn.pdf

---

## 🔧 Robustness Modeling Conventions Used

The diagrams follow the **Entity–Control–Boundary (ECB)** pattern.

### Stereotypes

- `<<boundary>>`  
  Represents system interfaces (UI screens or external system interfaces)

- `<<control>>`  
  Represents coordination logic for a use case

- `<<entity>>`  
  Represents domain model objects and persistent data

---

## 🔗 Communication Rules Applied

The following robustness rules were enforced:

Allowed:

- Actor ↔ Boundary
- Boundary ↔ Control
- Control ↔ Entity
- Control ↔ Control

Not Allowed:

- Actor ↔ Entity
- Boundary ↔ Entity

This ensures proper separation of concerns and maintains the noun – verb – noun interaction pattern.

---

## 🎯 Objective of Robustness Analysis

The goal of these diagrams is to:

- Identify participating objects for each use case
- Separate interface logic from business logic
- Validate use case structure
- Prepare for future sequence and class diagram design

These diagrams do not represent execution order.  
They represent responsibility and object interaction structure.
