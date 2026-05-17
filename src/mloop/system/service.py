"""Service management for MLOOP."""

from __future__ import annotations

import logging
import signal
import time

logger = logging.getLogger("mloop.system.service")


class ServiceManager:
    """Manages the MLOOP service lifecycle."""

    def __init__(self) -> None:
        """Initialize the service manager."""
        self._running = False
        self._shutdown_requested = False

    def start(self) -> None:
        """Start the service."""
        self._running = True
        self._shutdown_requested = False
        logger.info("Service started")

    def stop(self) -> None:
        """Stop the service."""
        self._running = False
        logger.info("Service stopping")

    def request_shutdown(self, signum: int = 0, frame: object = None) -> None:
        """Request graceful shutdown.

        Args:
            signum: Signal number.
            frame: Current stack frame.
        """
        self._shutdown_requested = True
        logger.info("Shutdown requested (signal %s)", signum)

    def setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        signal.signal(signal.SIGINT, self.request_shutdown)
        signal.signal(signal.SIGTERM, self.request_shutdown)

    @property
    def is_running(self) -> bool:
        """Check if service is running."""
        return self._running and not self._shutdown_requested

    def wait_for_shutdown(self, check_interval: float = 1.0) -> None:
        """Wait for shutdown request.

        Args:
            check_interval: How often to check for shutdown.
        """
        while self.is_running:
            time.sleep(check_interval)
