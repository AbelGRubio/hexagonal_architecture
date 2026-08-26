"""CLI entry point for controlling event-driven worker processes.

This module exposes commands to start worker threads against a chosen broker and
list the supported worker/broker combinations available in the application.
"""

import signal
import sys
import time
from typing import Type

import typer

from event_driven.infrastructure.config.enumerations import BrokersEnum, ThreadsEnum
from event_driven.infrastructure.messaging.broker_factory import MessageBrokerFactory

from event_driven.infrastructure.threads import THREAD_REGISTRY
from event_driven.logger import get_logger


logger = get_logger("CLI")
console = logger.console

app = typer.Typer(
    name="worker-cli",
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
    broker: BrokersEnum = typer.Option(
        BrokersEnum.LOCAL,
        "--broker",
        "-b",
        help="Type of messaging broker to connect.",
    ),
    consume_topic: str | None = typer.Option(
        None,
        "--consume-topic",
        "-c",
        help="Override default consume topic/queue.",
    ),
    publish_topic: str | None = typer.Option(
        None,
        "--publish-topic",
        "-pub",
        help="Override default publish topic/queue.",
    ),
) -> None:
    """Start a worker in a dedicated thread connected to the selected broker."""
    console.print(f"[bold green]Starting Worker:[/] {worker.value} using [bold cyan]{broker.value}[/]")

    try:
        broker_instance = MessageBrokerFactory.create_broker(broker)
    except Exception as exc:
        console.print(f"[bold red]Error instantiating broker:[/] {exc}")
        raise typer.Exit(code=1)

    worker_cls = THREAD_REGISTRY[worker]

    kwargs: dict[str, object] = {"broker": broker_instance}
    if consume_topic:
        kwargs["consume_topic"] = consume_topic
    if publish_topic:
        kwargs["publish_topic"] = publish_topic

    worker_thread = worker_cls(**kwargs)
    worker_thread.start()

    def shutdown_handler(signum: int, frame: object) -> None:
        """Stop the worker gracefully when the process receives a termination signal."""
        console.print("\n[bold yellow]Stopping worker gracefully...[/]")
        worker_thread.stop()
        worker_thread.join(timeout=5.0)
        console.print("[bold green]Worker stopped successfully. Exiting.[/]")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    console.print("[dim]Press Ctrl+C to stop the service.[/dim]")

    while worker_thread.is_alive():
        time.sleep(0.5)


@app.command("list")
def list_available() -> None:
    """Display the list of supported workers and brokers."""
    console.print("[bold]Available Workers:[/]")
    for worker in ThreadsEnum:
        console.print(f" - {worker.value}")

    console.print("\n[bold]Available Brokers:[/]")
    for broker in BrokersEnum:
        console.print(f" - {broker.value}")


if __name__ == "__main__":
    app()