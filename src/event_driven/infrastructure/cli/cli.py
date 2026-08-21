import logging
import signal
import sys
import time
from typing import Type

import typer
from rich.console import Console

from event_driven.infrastructure.config.enumerations import BrokersType, ThreadsType
from event_driven.infrastructure.messaging.broker_factory import MessageBrokerFactory

from event_driven.infrastructure.threads.thread_base import BaseWorkerThread
from event_driven.infrastructure.threads.thread_inventory import InventoryThread
from event_driven.infrastructure.threads.thread_notification import NotificationThread
from event_driven.infrastructure.threads.thread_order import OrderThread
from event_driven.infrastructure.threads.thread_payment import PaymentThread
from event_driven.logger import get_logger


logger = get_logger("CLI")
console = logger.console

app = typer.Typer(
    name="worker-cli",
    help="CLI for managing and running worker consumer threads.",
    add_completion=False,
)

# ------------------------------------------------------------------
# REGISTRIES & ENUMS (Easily extensible to add more workers/brokers)
# ------------------------------------------------------------------

WORKER_REGISTRY: dict[ThreadsType, Type[BaseWorkerThread]] = {
    ThreadsType.INVENTORY: InventoryThread,
    ThreadsType.NOTIFICATION: NotificationThread,
    ThreadsType.ORDER: OrderThread,
    ThreadsType.PAYMENT: PaymentThread,
}


# ------------------------------------------------------------------
# CLI COMMANDS
# ------------------------------------------------------------------

@app.command("start")
def start_worker(
    worker: ThreadsType = typer.Argument(
        ...,
        help="The type of worker thread you want to launch."
    ),
    broker: BrokersType = typer.Option(
        BrokersType.LOCAL,
        "--broker", "-b",
        help="Type of messaging broker to connect."
    ),
    consume_topic: str | None = typer.Option(
        None,
        "--consume-topic", "-c",
        help="Override default consume topic/queue."
    ),
    publish_topic: str | None = typer.Option(
        None,
        "--publish-topic", "-pub",
        help="Override default publish topic/queue."
    ),
):
    """Starts a worker in a dedicated thread connected to the specified broker."""
    console.print(f"[bold green]Starting Worker:[/] {worker.value} using [bold cyan]{broker.value}[/]")

    # 1. Instantiate the Broker
    try:
        broker_instance = MessageBrokerFactory.create_broker(broker)
    except Exception as e:
        console.print(f"[bold red]Error instantiating broker:[/] {e}")
        raise typer.Exit(code=1)

    # 2. Retrieve the Worker class
    worker_cls = WORKER_REGISTRY[worker]

    # 3. Build initialization arguments
    kwargs = {"broker": broker_instance}
    if consume_topic:
        kwargs["consume_topic"] = consume_topic
    if publish_topic:
        kwargs["publish_topic"] = publish_topic

    # 4. Instantiate and start the Worker Thread
    worker_thread = worker_cls(**kwargs)
    worker_thread.start()

    # 5. Handle Graceful Shutdown
    def shutdown_handler(signum, frame):
        console.print("\n[bold yellow]Stopping worker gracefully...[/]")
        worker_thread.stop()
        worker_thread.join(timeout=5.0)
        console.print("[bold green]Worker stopped successfully. Exiting.[/]")
        sys.exit(0)

    # Catch Ctrl+C (SIGINT) and SIGTERM
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    console.print("[dim]Press Ctrl+C to stop the service.[/dim]")

    # Keep the main process alive while the thread is running
    while worker_thread.is_alive():
        time.sleep(0.5)


@app.command("list")
def list_available():
    """Display the list of available Workers and Brokers."""
    console.print("[bold]Available Workers:[/]")
    for w in ThreadsType:
        console.print(f" - {w.value}")

    console.print("\n[bold]Available Brokers:[/]")
    for b in BrokersType:
        console.print(f" - {b.value}")


if __name__ == "__main__":
    app()