import argparse
import logging
from argparse import Namespace
from src.server.server import TumultServer
from src.shared.logging import DATETIME_FORMAT, LOG_FORMAT
from src.shared.protocol import DEFAULT_IPV4_ADDRESS, DEFAULT_PORT


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        datefmt=DATETIME_FORMAT,
    )


def setup_arguments() -> Namespace:
    parser = argparse.ArgumentParser(description="Tumult Chat Server")
    parser.add_argument(
        "--host",
        type=str,
        default=DEFAULT_IPV4_ADDRESS,
        help="Server host IPv4 address",
    )
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Server port")
    return parser.parse_args()


def main():
    setup_logging()

    arguments = setup_arguments()
    server = TumultServer(arguments.host, arguments.port)
    server.start()


if __name__ == "__main__":
    main()
