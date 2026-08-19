import queue
from typing import Any, Optional

from pydantic import BaseModel, ValidationError

from .thread_base import BaseWorkerThread


class InventoryThread(BaseWorkerThread[BaseModel, BaseModel]):
    """
    Hilo consumidor para el servicio de inventario (Inventory Service).
    Valida y descuenta el stock de los productos.
    """

    def __init__(self, input_queue: queue.Queue, output_queue: queue.Queue, schema_model: type[BaseModel]):
        super().__init__(schema_model=schema_model, name="InventoryService-Thread")
        self.input_queue = input_queue
        self.output_queue = output_queue

    def read_raw_message(self) -> Optional[Any]:
        try:
            return self.input_queue.get(timeout=1.0)
        except queue.Empty:
            return None

    def process_payload(self, payload: BaseModel) -> Optional[BaseModel]:
        logger.info(f"[{self.name}] Verificando stock para los ítems...")

        # Lógica de negocio de inventario
        # InventoryBusinessLogic.check_and_reserve(payload)

        self.input_queue.task_done()
        return None

    def send_output_message(self, result: BaseModel) -> None:
        if self.output_queue:
            self.output_queue.put(result.model_dump_json())

    def handle_validation_error(self, raw_message: Any, error: ValidationError) -> None:
        logger.error(f"[{self.name}] Error validando esquema de inventario: {error}")
        self.input_queue.task_done()

    def handle_processing_error(self, payload: BaseModel, error: Exception) -> None:
        logger.error(f"[{self.name}] Error procesando stock (posible stock insuficiente): {error}")
        self.input_queue.task_done()