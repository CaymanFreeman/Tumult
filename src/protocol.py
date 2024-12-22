import socket
from dataclasses import dataclass
from enum import Enum
from typing import Optional


@dataclass
class TumultProtocol:
    transport_type = socket.SOCK_STREAM  # TCP Stream
    address_family = socket.AF_INET  # IPV4
    default_port: int = 65535
    header_length_bytes: int = 3
    max_encoded_chars: int = ((10**header_length_bytes) - 1) // 4
    encoding_format: str = "utf-8"

    class Request(Enum):
        NICKNAME: int = 0
        MESSAGE: int = 1

        @classmethod
        def from_int(cls, value: int):
            for item in cls:
                if item.value == value:
                    return item
            raise ValueError(f"No matching request for value: {value}")

    @staticmethod
    def socket() -> socket.socket:
        return socket.socket(
            type=TumultProtocol.transport_type,
            family=TumultProtocol.address_family,
        )

    @staticmethod
    def header_pad(header_contents: bytes):
        return header_contents + (
            b" " * (TumultProtocol.header_length_bytes - len(header_contents))
        )

    @staticmethod
    def send_request_header(connection: socket, request_type: Request):
        header_contents = str(request_type.value).encode(TumultProtocol.encoding_format)
        connection.send(TumultProtocol.header_pad(header_contents))

    @staticmethod
    def send_string_length_header(connection: socket, string_length: int):
        header_contents = str(string_length).encode(TumultProtocol.encoding_format)
        connection.send(TumultProtocol.header_pad(header_contents))

    @staticmethod
    def send_string(connection: socket, request_type: Request, string: str):
        TumultProtocol.send_request_header(connection, request_type)
        string = string.encode(TumultProtocol.encoding_format)
        TumultProtocol.send_string_length_header(connection, len(string))
        connection.send(string)

    @staticmethod
    def handle_incoming_string(connection: socket) -> Optional[str]:
        header_contents = connection.recv(TumultProtocol.header_length_bytes).decode(
            TumultProtocol.encoding_format
        )
        if not header_contents:
            return None

        string_length = int(header_contents)
        string = connection.recv(string_length).decode(TumultProtocol.encoding_format)
        return string

    @staticmethod
    def handle_incoming_request(connection: socket) -> Request:
        return TumultProtocol.Request.from_int(
            int(
                connection.recv(TumultProtocol.header_length_bytes).decode(
                    TumultProtocol.encoding_format
                )
            )
        )
