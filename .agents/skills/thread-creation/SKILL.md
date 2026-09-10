# Thread creation skill

## Objective

Create a new event-driven worker thread for the project by following the same conventions used by the existing infrastructure threads. The new thread must inherit from `BaseWorkerThread`, be registered so the runtime can resolve it, and be exposed through the generated enum configuration.

## Scope

This skill is used when a new asynchronous worker is needed in the event-driven system, such as a new domain process, broker consumer, or producer-only worker.

## Required workflow

### 1. Choose the thread name

Use a clear and domain-specific name that describes the business purpose of the worker.

- The file must live under `src/event_driven/infrastructure/threads/`.
- The filename pattern must be: `thread_<name_of_thread>.py`
- The class name must be the PascalCase version of that thread name, for example:
  - `thread_inventory.py` -> `InventoryThread`
  - `thread_notification.py` -> `NotificationThread`

The `name_of_thread` should be chosen according to the use case and must match the enum value later added to the application configuration.

### 2. Define the payload and output models

Before implementing the thread logic, define the domain models used by the worker.

The thread must have a `PayloadModel` and an `OutputModel` that represent the incoming message and the processed result.

These models must be declared in `pymodeller/pymodeller.yaml` under the `models` section, using the `type: model` entry format, so they are generated and kept consistent with the project config.

Example:

```yaml
models:
  - name: NewThreadPayload
    description: Payload for the new thread.
    type: model
    include_general: false
    variables:
      - name: id
        type: str
      - name: status
        type: str

  - name: NewThreadOutput
    description: Output emitted by the new thread.
    type: model
    include_general: false
    variables:
      - name: result
        type: str
```

Then, in the thread implementation, use those generated models as the generic arguments:

```python
from event_driven.domain.schemas import NewThreadPayload, NewThreadOutput
from event_driven.infrastructure.config.schemas import ThreadConfigModel
from .thread_base import BaseWorkerThread


class NewThreadNameThread(BaseWorkerThread[NewThreadPayload, NewThreadOutput]):
    def __init__(self, config: ThreadConfigModel) -> None:
        super().__init__(
            config=config,
            payload_model=NewThreadPayload,
        )

    def process_payload(self, payload: NewThreadPayload) -> NewThreadOutput:
        # business logic here
        return NewThreadOutput(result="ok")
```

Important rules:

- `PayloadModel` and `OutputModel` must be explicitly defined for the thread.
- These models must exist in `pymodeller/pymodeller.yaml` under the `models` section with `type: model`.
- The class must inherit from `BaseWorkerThread`.
- The constructor must call `super().__init__(...)` with the `config` and the `payload_model`.
- `process_payload` is mandatory and contains the thread logic.
- Keep the file aligned with the project structure and naming conventions used by the current thread implementations.

### 3. Export the class from the threads package

Update `src/event_driven/infrastructure/threads/__init__.py`.

Add the import for the new class and include it in `__all__`.

Example:

```python
from .thread_new_name import NewThreadNameThread

__all__ = [
    "BaseWorkerThread",
    "NewThreadNameThread",
    "THREAD_REGISTRY",
]
```

This ensures the new thread is available wherever the package is imported.

### 4. Register the thread in the registry

Update `src/event_driven/infrastructure/threads/threads_registry.py`.

Add the new class to `THREAD_REGISTRY` using the corresponding enum key.

Example:

```python
from event_driven.infrastructure.config.enumerations import ThreadsEnum
from event_driven.infrastructure.threads import BaseWorkerThread, NewThreadNameThread

THREAD_REGISTRY: dict[ThreadsEnum, Type[BaseWorkerThread]] = {
    ThreadsEnum.NEW_THREAD: NewThreadNameThread,
}
```

This registry is what the runtime uses to resolve a thread by enum value.

### 5. Add the new option to the generated enumeration

The `ThreadsEnum` is driven by the project configuration file, not by ad-hoc manual edits.

Update `pymodeller/pymodeller.yaml` under the `enumerations` section, inside the `Threads` definition.

Add the new option in `options:` using the lower-case thread name.

Example:

```yaml
enumerations:
  - name: Threads
    destination: infrastructure
    description: Types of threads.
    options:
      - inventory
      - notification
      - order
      - payment
      - producer
      - new_thread
```

After updating the YAML, regenerate the enum definitions if the project workflow requires it. Do not bypass the source-of-truth configuration.

### 6. Validate the integration

Before finishing the task, verify that all required links are consistent:

- The file exists in `src/event_driven/infrastructure/threads/`.
- The class inherits from `BaseWorkerThread`.
- `PayloadModel` and `OutputModel` are defined in `pymodeller/pymodeller.yaml` under `models` with `type: model`.
- The generated domain models are available to the thread implementation.
- The class is imported from `src/event_driven/infrastructure/threads/__init__.py`.
- The class is added to `THREAD_REGISTRY`.
- The enum value exists in `pymodeller/pymodeller.yaml`.
- The generated enum reflects the new thread name.

## Expected result

A new thread can be created and instantiated through the project registry using the corresponding `ThreadsEnum` value. It behaves like the other infrastructure threads, consumes/produces messages through the broker configuration, and follows the repository’s event-driven architecture.

## Checklist

- [ ] New worker file created with the correct naming pattern.
- [ ] `PayloadModel` and `OutputModel` defined in `pymodeller/pymodeller.yaml` under `models` with `type: model`.
- [ ] Class inherits `BaseWorkerThread`.
- [ ] `process_payload` implemented.
- [ ] Thread exported in `__init__.py`.
- [ ] Entry added to `THREAD_REGISTRY`.
- [ ] New enum option added under `Threads` in `pymodeller/pymodeller.yaml`.
- [ ] Generated enum/configuration synced with the change.

## Reference examples in the repository

The current project already follows this pattern:

- `src/event_driven/infrastructure/threads/thread_inventory.py`
- `src/event_driven/infrastructure/threads/thread_notification.py`
- `src/event_driven/infrastructure/threads/thread_order.py`
- `src/event_driven/infrastructure/threads/thread_payment.py`
- `src/event_driven/infrastructure/threads/threads_registry.py`
- `src/event_driven/infrastructure/config/enumerations/threads.py`

Use these files as the canonical examples when creating a new worker thread.
