import queue
from typing import Any, Optional

from pydantic import BaseModel, ValidationError

from .thread_base import BaseWorkerThread


class PaymentServiceThread(BaseWorkerThread[BaseModel, BaseModel]):
    """
    Hilo consumidor para el servicio de pagos (Payment Service).
    Procesa las transacciones económicas del pedido.
    """

    def __init__(self, input_queue: queue.Queue, output_queue: queue.Queue, schema_model: type[BaseModel]):
        super().__init__(schema_model=schema_model, name="PaymentService-Thread")
        self.input_queue = input_queue
        self.output_queue = output_queue

    def read_raw_message(self) -> Optional[Any]:
        try:
            return self.input_queue.get(timeout=1.0)
        except queue.Empty:
            return None

    def process_payload(self, payload: BaseModel) -> Optional[BaseModel]:
        logger.info(f"[{self.name}] Procesando pago...")

        # Lógica de negocio de pagos
        # PaymentBusinessLogic.charge(payload)

        self.input_queue.task_done()
        return None

    def send_output_message(self, result: BaseModel) -> None:
        if self.output_queue:
            self.output_queue.put(result.model_dump_json())

    def handle_validation_error(self, raw_message: Any, error: ValidationError) -> None:
        logger.error(f"[{self.name}] Error de validación en datos de pago: {error}")
        self.input_queue.task_done()

    def handle_processing_error(self, payload: BaseModel, error: Exception) -> None:
        logger.error(f"[{self.name}] Fallo en la pasarela de pagos: {error}")
        self.input_queue.task_done()