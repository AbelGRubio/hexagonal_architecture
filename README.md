# Event-Driven Architecture (`event_driven_architecture`)


![GitHub release](https://img.shields.io/github/v/release/abelgrubio/event_driven_architecture)

![Python](https://img.shields.io/badge/python-3.12%20%7C%203.13-informational?style=flat-square&logo=python&logoColor=white)

[![Actions Status](https://github.com/abelgrubio/event_driven_architecture/actions/workflows/main.yml/badge.svg)](https://github.com/abelgrubio/event_driven_architecture/actions)

[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json&logo=uv&logoColor=white)](https://github.com/astral-sh/uv)

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat-square&logo=fastapi)

![MkDocs](https://img.shields.io/badge/docs-MkDocs%20Material-8c4fff?style=flat-square&logo=materialformkdocs&logoColor=white)

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

![License](https://img.shields.io/github/license/abelgrubio/event_driven_architecture?style=flat-square&color=gh-success)

![Coverage](https://img.shields.io/badge/coverage-83.2%25-green)





An enterprise-grade, event-driven Python application structured around **Hexagonal Architecture** (Ports and Adapters) principles. This project utilizes automated code generation via **PyModeller** to maintain clean models and centralized exceptions from YAML definitions.

---

## 🏗️ Hexagonal Architecture Overview

This project strictly separates the core business logic from external concerns (databases, message brokers, configuration, and frameworks). This decoupling ensures that the application remains maintainable, testable, and independent of external technologies.

```text
                  +----------------------------------+
                  |         INFRASTRUCTURE           |
                  |  (DB, Kafka, RabbitMQ, Config)   |
                  |          +--------------------+  |
                  |          |      DOMAIN        |  |
                  |          |  (Business Logic,  |  |
                  |          |    Schemas, Core)  |  |
                  |          +--------------------+  |
                  +----------------------------------+
```

### Key Layers:

*   **`domain/` (The Core):** 
    Contains the enterprise's pure business logic, domain models, schemas (`cart_item.py`, `order_created.py`), and core domain exceptions. **All critical business rules reside here**, completely isolated from infrastructure details. It does not know about databases, HTTP protocols, or message brokers.
*   **`infrastructure/` (The Adapters & Drivers):** 
    Houses all technology-specific implementations. This includes database connections and models (`persistence/`), message broker implementations for Kafka, RabbitMQ, and local execution (`messaging/`), background workers/threads (`threads/`), and dynamic configuration management (`config/`).

---

## 📂 Project Structure

```text
src
├── event_driven
│   ├── domain                # Core Business Logic & Domain Models
│   │   ├── exceptions        # Domain-specific exceptions
│   │   └── schemas           # Data structures & domain entities
│   ├── infrastructure        # External interfaces, DB, & Brokers
│   │   ├── config            # Settings, environment, and YAML configs
│   │   ├── exceptions        # Infrastructure & HTTP-mapped exceptions
│   │   ├── messaging         # Event brokers (Kafka, RabbitMQ, Local)
│   │   ├── persistence       # Database connections and ORM models
│   │   └── threads           # Background processes & workers
│   ├── info.py
│   ├── logger.py
│   └── __main__.py
└── __main__.py
```

---

## ⚡ Automated Code Generation (PyModeller)

A significant portion of the data schemas and exception classes within this project are **automatically generated** using PyModeller.

*   **Definitions:** Models and exceptions are centrally defined using declarative configuration files (`exceptions.yaml` and `pymodeller.yaml`).
*   **Generation:** Through settings configured in these YAML files and the project's configuration, Python code files (`.py`) under domain schemas and exception directories are automatically synchronized and created, reducing boilerplate code and ensuring consistency across components.

---

## 🚀 Getting Started

### Prerequisites

*   Python 3.14+

