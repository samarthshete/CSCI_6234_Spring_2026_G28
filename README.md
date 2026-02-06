# Intelligent Personal Finance Management System

## CSCI 6234 - Object-Oriented Design

### George Washington University | Spring 2026

---

## 📋 Project Overview

A comprehensive personal finance management system demonstrating Object-Oriented Design principles, UML modeling, and design patterns implementation.

### Key Features

- Transaction import from bank APIs and CSV files
- Automatic expense categorization (rule-based + AI)
- Budget management with threshold alerts
- Analytics dashboard and reporting
- Multi-account support

---

## 📁 Repository Structure

```
├── UML/                    # UML Diagrams (PlantUML)
│   ├── use_case_diagram.puml
│   ├── activity_diagram.puml
│   ├── communication_diagram.puml
│   ├── class_diagram.puml
│   ├── state_diagram.puml
│   ├── component_diagram.puml
│   └── sequence_diagram.puml
│
├── Requirements/           # Requirements Documentation
│   ├── SRS.md             # Software Requirements Specification
│   └── use_cases.md       # Detailed Use Case Descriptions
│
├── Analysis/              # Analysis Phase Artifacts
│   └── domain_model.md    # Domain Model & Entity Analysis
│
├── Design/                # Design Phase Artifacts
│   ├── design_patterns.md # Design Patterns Implementation
│   └── architecture.md    # System Architecture
│
└── Implementation/        # Source Code
    ├── src/               # Application source code
    │   ├── domain/        # Domain layer (entities, patterns)
    │   ├── application/   # Application services
    │   └── infrastructure/# Data access, adapters
    ├── tests/             # Unit tests
    └── requirements.txt   # Python dependencies
```

---

## 🎯 Design Patterns Implemented

| Pattern                     | Category      | Purpose                        |
| --------------------------- | ------------- | ------------------------------ |
| **Strategy**                | Behavioral    | Pluggable categorization rules |
| **Observer**                | Behavioral    | Budget threshold monitoring    |
| **Chain of Responsibility** | Behavioral    | Categorization fallback chain  |
| **State**                   | Behavioral    | Account lifecycle management   |
| **Factory Method**          | Creational    | Alert and report creation      |
| **Adapter**                 | Structural    | External API integration       |
| **Repository**              | Architectural | Data access abstraction        |

---

## 📐 SOLID Principles

| Principle                 | Implementation                     |
| ------------------------- | ---------------------------------- |
| **S**ingle Responsibility | Each class has one clear purpose   |
| **O**pen/Closed           | Strategy pattern enables extension |
| **L**iskov Substitution   | Interface-based polymorphism       |
| **I**nterface Segregation | Focused, specific interfaces       |
| **D**ependency Inversion  | Depend on abstractions             |

---

## 🔧 UML Diagrams

All diagrams are created using PlantUML. To view:

1. **Online**: Go to https://www.plantuml.com/plantuml/uml/

### Diagram Types (per Martin Fowler's UML Distilled)

- ✅ Use Case Diagram
- ✅ Activity Diagram
- ✅ Communication Diagram (Collaboration)
- ✅ Class Diagram
- ✅ State Diagram
- ✅ Component Diagram
- ✅ Sequence Diagram (Bonus)

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- PostgreSQL 14+

### Installation

```bash
cd Implementation
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Running Tests

```bash
pytest tests/ -v
```

---

## 👥 Team Members

- Samarth Shete
- Karan Patel

---

---

## 📝 Course Information

- **Course**: CSCI 6234 - Object-Oriented Design
- **Instructor**: Professor Walt
- **Semester**: Spring 2026
- **Reviewer**: waltatgit
