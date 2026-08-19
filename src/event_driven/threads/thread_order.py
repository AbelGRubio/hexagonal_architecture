import queue
from typing import Any, Optional

from pydantic import BaseModel, ValidationError

from .thread_base import BaseWorkerThread


class OrderServiceThread(BaseWorkerThread[BaseModel, BaseModel]):
    """
    Hilo consumidor para el servicio de pedidos (Order Service).
    Escucha eventos de creación de pedidos o peticiones iniciales.
    """

    def __init__(self, input_queue: queue.Queue, output_queue: queue.Queue, schema_model: type[BaseModel]):
        super().__init__(schema_model=schema_model, name="OrderService-Thread")
        self.input_queue = input_queue
        self.output_queue = output_queue

    def read_raw_message(self) -> Optional[Any]:
        try:
            # Obtiene un mensaje de la cola de Python con un timeout para permitir parar el hilo limpiamente
            return self.input_queue.get(timeout=1.0)
        except queue.Empty:
            return None

    def process_payload(self, payload: BaseModel) -> Optional[BaseModel]:
        logger.info(f"[{self.name}] Procesando pedido: {payload}")

        # 1. Llamar a la lógica de negocio pura
        # result = OrderBusinessLogic.process(payload)

        # 2. Opcional: Si el pedido se creó bien, generamos un evento de salida para inventario o pagos
        # self.output_queue.put(result.model_dump_json())

        # Marcamos la tarea como completada en la cola de Python
        self.input_queue.task_done()
        return None

    def send_output_message(self, result: BaseModel) -> None:
        if self.output_queue:
            self.output_queue.put(result.model_dump_json())

    def handle_validation_error(self, raw_message: Any, error: ValidationError) -> None:
        logger.error(f"[{self.name}] Error de validación en el pedido: {error}. Mensaje crudo: {raw_message}")
        self.input_queue.task_done()

    def handle_processing_error(self, payload: BaseModel, error: Exception) -> None:
        logger.error(f"[{self.name}] Error de procesamiento crítico en el pedido: {error}")
        self.input_queue.task_done()


class InventoryServiceThread(BaseWorkerThread[BaseModel, BaseModel]):
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


class NotificationServiceThread(BaseWorkerThread[BaseModel, BaseModel]):
    """
    Hilo consumidor para el servicio de notificaciones (Notification Service).
    Envía correos o alertas finales al cliente.
    """

    def __init__(self, input_queue: queue.Queue, schema_model: type[BaseModel]):
        super().__init__(schema_model=schema_model, name="NotificationService-Thread")
        self.input_queue = input_queue

    def read_raw_message(self) -> Optional[Any]:
        try:
            return self.input_queue.get(timeout=1.0)
        except queue.Empty:
            return None

    def process_payload(self, payload: BaseModel) -> Optional[BaseModel]:
        logger.info(f"[{self.name}] Enviando notificación al usuario...")

        # Lógica de negocio de notificaciones
        # NotificationBusinessLogic.send_email(payload)

        self.input_queue.task_done()
        return None

    def send_output_message(self, result: BaseModel) -> None:
        # Al ser el último paso, normalmente no retransmite nada
        pass

    def handle_validation_error(self, raw_message: Any, error: ValidationError) -> None:
        logger.error(f"[{self.name}] Error validando notificación: {error}")
        self.input_queue.task_done()

    def handle_processing_error(self, payload: BaseModel, error: Exception) -> None:
        logger.error(f"[{self.name}] Error enviando notificación: {error}")
        self.input_queue.task_done()