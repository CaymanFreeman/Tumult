import socket

from server import TumultServer
from src.protocol import DEFAULT_PORT


def main():
    server = TumultServer(socket.gethostbyname(socket.gethostname()), DEFAULT_PORT)
    server.start()


if __name__ == "__main__":
    main()
