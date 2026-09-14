# Event-Driven Architecture (`event_driven_architecture`)


![GitHub release](https://img.shields.io/github/v/release/abelgrubio/event_driven_architecture)
![Python](https://img.shields.io/badge/python-3.12%20%7C%203.13-informational?style=flat-square&logo=python&logoColor=white)
[![Actions Status](https://github.com/abelgrubio/event_driven_architecture/actions/workflows/main.yml/badge.svg)](https://github.com/abelgrubio/event_driven_architecture/actions)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json&logo=uv&logoColor=white)](https://github.com/astral-sh/uv)
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

## 🛡️ Fault tolerance

This application is designed to continue operating even when the RabbitMQ broker becomes temporarily unavailable. The fault-tolerance flow is based on three mechanisms:

1. Automatic retry with exponential backoff using `tenacity`.
2. Circuit breaking with `pybreaker` to avoid repeatedly hammering a failing broker.
3. Message persistence in Redis so failed events can be retried later when the service recovers.

If a publish fails, the app does not simply crash. Instead, it retries several times, stops after a configured limit, opens the circuit breaker, and stores the failed message along with its metadata in Redis. A background recovery worker later inspects that queue and resends the events once RabbitMQ is available again.

Example summary:

```python
from tenacity import retry, stop_after_attempt, wait_exponential
from pybreaker import CircuitBreaker

breaker = CircuitBreaker(fail_max=5, reset_timeout=60)

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, max=30))
@breaker
def send_to_rabbit(payload):
    publish(payload)

try:
    send_to_rabbit(message)
except Exception:
    redis_client.lpush('failed_messages', serialize(message))
```

This prevents event loss and ensures the system can recover after a temporary outage without requiring a manual replay of all messages.

### How to test the fault-tolerance flow locally

To validate the behavior in a local environment, follow these steps:

1. Start the required services:

```bash
docker compose up -d
```

This brings up the infrastructure dependencies, including RabbitMQ and the auxiliary services needed by the project.

2. Configure the Toxiproxy route to RabbitMQ:

```bash
make proxy-setup
```

This redirects traffic from the application to the proxy, which allows you to simulate broker failures safely.

3. Run the application:

```bash
make run
```

4. Simulate a RabbitMQ outage:

```bash
make proxy-disable
```

When the proxy is disabled, the service will experience a temporary failure in the broker connection. Depending on the retry and circuit-breaker policies, the application may pause or slow down while waiting for recovery, but it should not lose events permanently because they are queued for retry in Redis.

5. Restore the connection:

```bash
make proxy-enable
```

You can check the proxy state at any time with:

```bash
make proxy-status
```

Once the proxy is re-enabled, the app can resume normal traffic and the recovery worker can re-send any pending messages. This is the practical demonstration that the system has fault tolerance: it tolerates a broker outage, pauses according to policy, and automatically recovers when connectivity is restored.

---

## ⚡ Automated Code Generation (PyModeller)

A significant portion of the data schemas and exception classes within this project are **automatically generated** using PyModeller.

*   **Definitions:** Models and exceptions are centrally defined using declarative configuration files (`exceptions.yaml` and `pymodeller.yaml`).
*   **Generation:** Through settings configured in these YAML files and the project's configuration, Python code files (`.py`) under domain schemas and exception directories are automatically synchronized and created, reducing boilerplate code and ensuring consistency across components.

---

## 🚀 Getting Started

### Prerequisites

*   Python 3.14+
