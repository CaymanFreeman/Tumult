import socket
from dataclasses import dataclass
from enum import Enum


@dataclass
class TumultProtocol:
    transport_type = socket.SOCK_STREAM  # TCP Stream
    address_family = socket.AF_INET  # IPV4
    port: int = 65535
    header_length_bytes: int = 4
    encoding_format: str = "utf-8"


class Request(Enum):
    DISCONNECT: int = 0
    MESSAGE: int = 1
