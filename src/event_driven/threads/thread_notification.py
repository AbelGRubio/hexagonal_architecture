
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