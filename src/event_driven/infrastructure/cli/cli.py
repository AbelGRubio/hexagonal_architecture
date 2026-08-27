"""CLI entry point for controlling event-driven worker processes."""

import signal
import sys
from typing import Type

import typer

from event_driven.infrastructure.config.enumerations import ThreadsEnum
from event_driven.infrastructure.config.init_resolved import get_threads_configurations
from event_driven.infrastructure.threads import ThreadManager, THREAD_REGISTRY, BaseWorkerThread
from event_driven.logger import get_logger

logger = get_logger("CLI")
console = logger.console

app = typer.Typer(
    name="event-driven-cli",
    help="CLI for managing and running worker consumer threads.",
    add_completion=False,
)

# ------------------------------------------------------------------
# CLI COMMANDS
# ------------------------------------------------------------------

@app.command("start")
def start_worker(
    worker: ThreadsEnum = typer.Argument(
        ...,
        help="The type of worker thread you want to launch.",
    ),
) -> None:
    """Start a single worker thread using the parameters defined in the YAML configuration."""
    console.print(f"[bold green]Starting single worker:[/] {worker.value}")

    # 1. Obtener la configuración general resolviendo según el YAML
    config = get_threads_configurations()
    thread_config = config.get_thread_config(thread_name=worker)

    # 2. Obtener la clase del thread según el registro
    worker_cls: Type[BaseWorkerThread] = THREAD_REGISTRY[worker]

    # 3. Inicializar el ThreadManager para gestionar el hilo individual
    manager = ThreadManager(max_retries=3, check_interval=5.0)
    manager.add_thread(worker_cls, config=thread_config)

    # 4. Manejador para un apagado controlado (Graceful Shutdown)
    def shutdown_handler(signum: int, frame: object) -> None:
        console.print(f"\n[bold yellow]Shutting down worker {worker.value} gracefully...[/]")
        manager.stop_all()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    # 5. Iniciar el worker y el monitoreo de salud
    manager.start_all()
    console.print("[dim]Worker running. Health monitoring active. Press Ctrl+C to exit.[/dim]")

    try:
        manager.start_monitoring()
    except KeyboardInterrupt:
        shutdown_handler(0, None)


@app.command("list")
def list_available() -> None:
    """Display the list of supported workers."""
    console.print("[bold]Available Workers:[/]")
    for worker in ThreadsEnum:
        console.print(f" - {worker.value}")


if __name__ == "__main__":
    app()