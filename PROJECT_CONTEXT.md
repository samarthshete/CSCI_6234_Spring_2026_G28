Intelligent Personal Finance Management System is a personal finance platform that helps users manage accounts, automatically import and categorize transactions, set budget thresholds, receive alerts when spending exceeds limits, and analyze financial behavior through dashboards and trends.

Unlike basic finance trackers, our system integrates:

automated transaction import,

intelligent categorization,

budget threshold monitoring,

and analytics-driven insights

all structured using a clean object-oriented domain model and UML-based design.

The system focuses on usability, automation, and financial awareness while staying within realistic project scope.

🔷 2. Project Vision

To build a structured, modular, and intelligent personal finance system that:

Centralizes account management

Automates transaction categorization

Prevents overspending via budget alerts

Provides meaningful financial analytics

Demonstrates correct OOAD methodology using UML artifacts

🔷 3. Core User Persona
🎯 Primary Persona: Individual Budget-Conscious User

Profile

Age: 22–40

Has multiple bank/credit accounts

Wants better control over spending

Often overspends in certain categories

Goals

See all transactions in one place

Automatically categorize expenses

Set monthly budgets

Get alerted before overspending

Visualize spending patterns

Pain Points

Manual expense tracking

No early warning before budget breach

Lack of spending insights

Disconnected banking systems

🔷 4. System Scope (What It Does)

The system allows users to:

Authenticate and securely access their data

Manage multiple financial accounts

Import transactions from banking sources

Automatically categorize expenses

Set budget thresholds

Receive alerts when thresholds are exceeded

View analytics dashboards with trends and breakdowns

🔷 5. Features We Decided (Finalized Scope)
🔐 1. Authentication

Login with credentials

Validate user

Create session

🏦 2. Account Management

Add bank/credit/investment accounts

Edit account details

Delete accounts

📥 3. Import Transactions

Import from external banking system

Parse & normalize data

Detect duplicates

Save transactions

🏷 4. Categorize Expenses

Rule-based matching

AI-based classification fallback

Manual override

Persist category

📊 5. View Analytics Dashboard

Spending breakdown by category

Trend over time

Filter by date range

Budget vs actual

💰 6. Set Budget Thresholds

Set category-level budgets

Define period (monthly, etc.)

Define alert threshold percentages

🚨 7. Receive Budget Alerts

Monitor spending vs threshold

Create BudgetAlert

Send via Notification Service

Display in app

🔷 6. Use Case List (Final)
UC# Use Case Name
UC01 Authenticate User
UC02 Manage Accounts
UC03 Import Transactions
UC04 Categorize Expenses
UC05 Set Budget Thresholds
UC06 Receive Budget Alerts
UC07 View Analytics Dashboard
🔷 7. Domain Model Summary

Core Entities:

User

FinancialAccount (BankAccount, CreditCardAccount, InvestmentAccount)

Transaction

Category

Budget

BudgetItem

BudgetAlert

Merchant

Institution

ImportSession

Key Relationships

User owns FinancialAccounts

FinancialAccount records Transactions

Transaction belongs to Category

Budget contains BudgetItems

BudgetItem applies to Category

BudgetAlert relates to Budget

ImportSession imports Transactions

This ensures:

No control/UI classes in domain model

Pure entity-level abstraction

Clean separation from robustness/control layer

🔷 8. Diagram Summary (Artifacts)
Use Case Diagram

Shows:

User as primary actor

External Banking System

Notification Service

7 core use cases

Include relationships:

Import → Categorize

Budget → Alerts

All → Authenticate

Robustness Diagrams

Each use case includes:

Boundary (screens)

Control (controllers)

Entity (domain classes only)
No ad-hoc classes used.

Activity Diagrams

7 separate .puml
Each includes:

Start and End nodes

Proper decision diamonds

Merge nodes

Step text mapping to actions

Domain Model

UML Class Diagram

Inheritance for FinancialAccount

Multiplicities

Association names (owns, contains, categorizedAs, etc.)

🔷 9. Technical Constraints
🔹 Must Use Existing Repo

Project started from WeFinance GitHub repository

Extended functionality without breaking original structure

Cleaned unnecessary comments and code

Kept modular structure

🔹 Scope Control

We explicitly avoided:

Real banking API integration

Real ML training

Payment processing

Multi-user admin panel

Investment prediction

Complex financial forecasting

Reason:
Keep within semester scope and UML analysis focus.

🔹 Architectural Constraints

Must follow OOAD discipline

Must align robustness → domain model

Must not introduce domain entities not reflected in use cases

Must not introduce UI/control classes into domain model

🔷 10. System Architecture (High-Level)

Layered approach:

Presentation Layer
→ Controllers
→ Domain Model
→ Persistence Layer

External systems:

Banking API (simulated)

Notification Service (simulated)

🔷 11. What Makes This Project Strong

Full OOAD discipline

Clean mapping:

Use Case → Robustness → Domain → Activity

Clear responsibility separation

Budget monitoring automation

Transaction intelligence

Practical real-world problem

🔷 12. What We Deliberately Did NOT Include

To defend scope during presentation:

Cryptocurrency trading

Loan management

Tax optimization

Multi-user family budgeting

Real-time banking integration

Complex AI financial prediction

This is a personal finance management core system, not a fintech enterprise platform.

🔷 13. Risk Areas Professor Might Question

Be ready to answer:

Why Merchant is in domain model?

Why ImportSession exists?

Why BudgetItem separate from Budget?

Why alerts modeled as entity?

Why authentication not deeply modeled?

You should answer:

Merchant helps categorization and analytics.

ImportSession tracks import metadata.

BudgetItem allows category-level limits.

BudgetAlert stores history.

Authentication kept simple to avoid scope explosion.

🔷 14. One-Line System Definition

“A modular, object-oriented personal finance management system that integrates account management, intelligent expense categorization, budgeting, alerting, and financial analytics.”
