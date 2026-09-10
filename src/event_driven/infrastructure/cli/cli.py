"""CLI entry point for controlling event-driven worker processes."""

import signal
import sys

import typer

from event_driven.infrastructure.config.enumerations import ThreadsEnum
from event_driven.infrastructure.config.init_resolved import get_threads_configurations
from event_driven.infrastructure.threads import THREAD_REGISTRY, BaseWorkerThread, ThreadManager
from event_driven.logger import get_logger, propagate_loggers

logger = get_logger("CLI")
console = logger.console

propagate_loggers()

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
    workers: list[ThreadsEnum] = typer.Argument(
        ...,
        help="The worker thread(s) to launch. Accepts one or multiple values separated by space"
        " (e.g. 'start producer' or 'start producer inventory').",
    ),
) -> None:
    """Start a single worker thread using the parameters defined in the YAML configuration."""
    target_workers = list(dict.fromkeys(workers))

    worker_names = ", ".join([w.value for w in target_workers])
    console.print(f"[bold green]Starting worker(s):[/] {worker_names}")

    # 1. Retrieve global configuration resolved according to YAML/environment settings
    config = get_threads_configurations()
    manager = ThreadManager(max_retries=3, check_interval=5.0)

    # 2. Register each of the requested workers into the manager
    for worker in target_workers:
        thread_config = config.get_thread_config(thread_name=worker)
        worker_cls: type[BaseWorkerThread] = THREAD_REGISTRY[worker]
        manager.add_thread(worker_cls, config=thread_config)

    # 3. Register signals for graceful shutdown
    def shutdown_handler(signum: int, frame: object) -> None:
        console.print(f"\n[bold yellow]Shutting down workers ({worker_names}) gracefully...[/]")
        manager.stop_all()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    # 4. Launch workers and activate health monitoring
    manager.start_all()
    console.print("[dim]Worker(s) running. Health monitoring active. Press Ctrl+C to exit.[/dim]")

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
