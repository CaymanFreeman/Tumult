import logging
import sys

from PyQt6.QtWidgets import QApplication

from src.client.window import ClientWindow
from src.shared.logging import LOG_FORMAT, DATETIME_FORMAT


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        datefmt=DATETIME_FORMAT,
    )


def main():
    setup_logging()

    app = QApplication(sys.argv)
    window = ClientWindow()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
