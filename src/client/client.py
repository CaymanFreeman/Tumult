import socket
from dataclasses import dataclass
from enum import IntEnum


@dataclass
class TumultProtocol:
    transport_type: IntEnum = socket.SOCK_STREAM  # TCP Stream
    address_family: IntEnum = socket.AF_INET  # IPV4
    port: int = 65535
    header_length_bytes: int = 4
    encoding_format: str = "utf-8"


class Client:

    @staticmethod
    def client_host_address() -> str:
        return socket.gethostbyname(socket.gethostname())

    def __init__(
        self,
        server_address: str = client_host_address(),
        port: int = TumultProtocol.port,
    ):
        self.socket_address = server_address, port
        self.socket = socket.socket(
            type=TumultProtocol.transport_type,
            family=TumultProtocol.address_family,
        )

    def connect(self):
        self.socket.connect(self.socket_address)

    def send_message(self, message: str):
        message = message.encode(TumultProtocol.encoding_format)
        message_length = len(message)
        message_header_contents = str(message_length).encode(
            TumultProtocol.encoding_format
        )
        header_padding = b" " * (
            TumultProtocol.header_length_bytes - len(message_header_contents)
        )
        message_header = message_header_contents + header_padding
        self.socket.send(message_header)
        self.socket.send(message)
