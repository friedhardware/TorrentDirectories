"""Web interface for the torrent client."""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from flask import Flask, Response, jsonify, render_template, request

logger = logging.getLogger(__name__)


class WebInterface:
    """Web interface for monitoring and controlling the torrent client."""

    def __init__(self, host: str = "localhost", port: int = 8080) -> None:
        """Initialize the web interface.

        Args:
            host: Host to listen on
            port: Port to listen on
        """
        module_dir = Path(__file__).parent
        self.app = Flask(
            __name__,
            template_folder=str(module_dir / "templates"),
            static_folder=str(module_dir / "static"),
        )
        self.host = host
        self.port = port
        self.torrents: Dict[str, Dict[str, Any]] = {}
        self.batch_running = False
        self.errors: List[str] = []
        self.batch_status: Dict[str, Union[bool, int, Optional[str]]] = {
            "is_running": False,
            "last_run": 0,
            "next_check": 0,
            "message": None,
            "success": False,
            "failure": False,
        }
        self._on_start: Optional[Callable] = None
        self._on_stop: Optional[Callable] = None
        self.thread: Optional[threading.Thread] = None

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        self._setup_routes()

    def _setup_routes(self) -> None:
        """Set up the Flask routes."""

        @self.app.route("/")
        def index() -> Response:
            """Render the index page."""
            return render_template("index.html")

        @self.app.route("/status")
        def status() -> Response:
            """Get the current status."""
            return jsonify(
                {
                    "torrents": self.torrents,
                    "errors": self.errors,
                    "batch_status": self.batch_status,
                    "stats": self._get_stats(),
                }
            )

        @self.app.route("/batch/start", methods=["POST"])
        def start_batch() -> Response:
            """Start the batch process."""
            if self._on_start:
                self._on_start()
                return jsonify({"success": True})
            return jsonify({"success": False, "error": "No batch handler configured"})

        @self.app.route("/batch/stop", methods=["POST"])
        def stop_batch() -> Response:
            """Stop the batch process."""
            if self._on_stop:
                self._on_stop()
                return jsonify({"success": True})
            return jsonify({"success": False, "error": "No batch handler configured"})

        @self.app.route("/shutdown", methods=["POST"])
        def shutdown() -> Response:
            """Handle shutdown route."""
            func = request.environ.get("werkzeug.server.shutdown")
            if func is None:
                raise RuntimeError("Not running with Werkzeug server")
            func()
            return "Server shutting down..."

    def set_batch_handlers(self, on_start: Callable, on_stop: Callable) -> None:
        """Set handlers for batch operations.

        Args:
            on_start: Handler for starting batch process
            on_stop: Handler for stopping batch process
        """
        self._on_start = on_start
        self._on_stop = on_stop

    def update_torrent(
        self, name: str, progress: float, status: str, rate: float = 0.0
    ) -> None:
        """Update torrent status.

        Args:
            name: Torrent name
            progress: Download progress (0-100)
            status: Torrent status
            rate: Download rate in bytes/s
        """
        self.torrents[name] = {
            "name": name,
            "progress": progress * 100 if progress <= 1.0 else progress,
            "status": status,
            "rate": rate,
        }

    def _format_rate(self, rate: float) -> str:
        """Format a rate in bytes/s to a human-readable string.

        Args:
            rate: Rate in bytes/s

        Returns:
            Formatted rate string
        """
        return f"{rate / 1024:.1f} KB/s"

    def update_torrents(self, torrents: Dict[str, Any]) -> None:
        """Update multiple torrents at once.

        Args:
            torrents: Dictionary of torrent handles
        """
        self.torrents = torrents

    def update_batch_status(
        self,
        is_running: bool,
        last_run: int,
        next_check: int,
        message: Optional[str] = None,
        success: bool = False,
        failure: bool = False,
    ) -> None:
        """Update the batch process status.

        Args:
            is_running: Whether the batch process is running
            last_run: Timestamp of last run
            next_check: Timestamp of next check
            message: Optional status message
            success: Whether the last run was successful
            failure: Whether the last run failed
        """
        self.batch_status = {
            "is_running": is_running,
            "last_run": last_run,
            "next_check": next_check,
            "message": message,
            "success": success,
            "failure": failure,
        }

    def add_error(self, error: str) -> None:
        """Add an error message.

        Args:
            error: Error message to add
        """
        self.errors.append(error)
        if len(self.errors) > 10:
            self.errors = self.errors[-10:]  # Keep only the last 10 errors

    def _get_stats(self) -> Dict[str, int]:
        """Get torrent statistics."""
        stats = {
            "total": len(self.torrents),
            "seeding": 0,
            "downloading": 0,
            "errors": 0,
        }

        for torrent in self.torrents.values():
            if torrent["status"] == "seeding":
                stats["seeding"] += 1
            elif torrent["status"] == "downloading":
                stats["downloading"] += 1
            elif torrent["status"] == "error":
                stats["errors"] += 1

        return stats

    def start(self) -> None:
        """Start the web interface in a background thread."""
        logger.info(f"Starting web interface on port {self.port}")
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()

    def stop(self) -> None:
        """Stop the web interface."""
        logger.info("Stopping web interface")
        if self.thread and self.thread.is_alive():
            # Send shutdown request
            try:
                request.environ.get("werkzeug.server.shutdown")()
            except Exception as e:
                logger.error(f"Error shutting down web interface: {e}")
            self.thread.join(timeout=5)

    def _run(self) -> None:
        """Run the Flask application."""
        self.app.run(host="0.0.0.0", port=self.port)
