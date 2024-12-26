import argparse

from src.server.server import TumultServer
from src.shared.protocol import DEFAULT_IPV4_ADDRESS, DEFAULT_PORT


def main():
    parser = argparse.ArgumentParser(description="Tumult Chat Server")
    parser.add_argument(
        "--host",
        type=str,
        default=DEFAULT_IPV4_ADDRESS,
        help="Server host IPv4 address",
    )
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Server port")
    args = parser.parse_args()

    server = TumultServer(args.host, args.port)
    server.start()


if __name__ == "__main__":
    main()
