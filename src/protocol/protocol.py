import socket
from dataclasses import dataclass
from enum import Enum


@dataclass
class TumultProtocol:
    transport_type = socket.SOCK_STREAM  # TCP Stream
    address_family = socket.AF_INET  # IPV4
    default_port: int = 65535
    header_length_bytes: int = 4
    encoding_format: str = "utf-8"

    class Request(Enum):
        DISCONNECT: int = 0
        MESSAGE: int = 1

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
    def send_message_header(connection: socket, message_length: int):
        header_contents = str(message_length).encode(TumultProtocol.encoding_format)
        connection.send(TumultProtocol.header_pad(header_contents))

    @staticmethod
    def send_message(connection: socket, message: str):
        TumultProtocol.send_request_header(connection, TumultProtocol.Request.MESSAGE)
        message = message.encode(TumultProtocol.encoding_format)
        TumultProtocol.send_message_header(connection, len(message))
        connection.send(message)

    @staticmethod
    def handle_incoming_message(connection: socket):
        header_contents = connection.recv(TumultProtocol.header_length_bytes).decode(
            TumultProtocol.encoding_format
        )

        if not header_contents:
            return None, None

        message_length = int(header_contents)
        message = connection.recv(message_length).decode(TumultProtocol.encoding_format)

        return message_length, message

    @staticmethod
    def handle_incoming_request(connection: socket):
        return connection.recv(TumultProtocol.header_length_bytes).decode(
            TumultProtocol.encoding_format
        )
