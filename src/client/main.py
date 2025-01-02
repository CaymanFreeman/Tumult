"""Entry point for launching the client application"""

import logging
import sys

from PyQt6.QtWidgets import QApplication

from src.client.window import ClientWindow
from src.shared.logging import LOG_FORMAT, DATETIME_FORMAT


def _setup_logging() -> None:
    """Configures the logging with the formats from the Tumult logging module."""
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        datefmt=DATETIME_FORMAT,
    )


def main() -> None:
    """Initializes logging and launches the PyQt window."""
    _setup_logging()

    app: QApplication = QApplication(sys.argv)
    _window: ClientWindow = ClientWindow()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
