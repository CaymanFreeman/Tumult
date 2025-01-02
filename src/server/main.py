"""Entry point for launching the server"""

import argparse
import logging
from argparse import Namespace, ArgumentParser

from src.server.tumult_server import TumultServer
from src.shared.logging import DATETIME_FORMAT, LOG_FORMAT
from src.shared.protocol import DEFAULT_IPV4_ADDRESS, DEFAULT_PORT


def _setup_logging() -> None:
    """Configures the logging with the formats from the Tumult logging module."""
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        datefmt=DATETIME_FORMAT,
    )


def _parse_arguments() -> Namespace:
    """Parses the command line arguments for the server host and port."""
    parser: ArgumentParser = argparse.ArgumentParser(description="Tumult Chat Server")
    parser.add_argument(
        "--host",
        type=str,
        default=DEFAULT_IPV4_ADDRESS,
        help="Server host IPv4 address",
    )
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Server port")
    return parser.parse_args()


def main() -> None:
    """Initializes logging and launches the server with the configured arguments."""
    _setup_logging()

    arguments: Namespace = _parse_arguments()
    server: TumultServer = TumultServer(arguments.host, arguments.port)
    server.start()


if __name__ == "__main__":
    main()
