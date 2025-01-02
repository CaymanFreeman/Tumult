"""Implementation of the Tumult protocol for client-server communication."""

import ipaddress
import json
import logging
import re
import socket
import time
from collections import namedtuple
from dataclasses import dataclass
from enum import IntEnum
from typing import Optional, Any

PROTOCOL_VERSION: str = "1.0"
DEFAULT_IPV4_ADDRESS: str = "127.0.0.1"
DEFAULT_PORT: int = 65535
ENCODING_FORMAT: str = "utf-8"


class RequestType(IntEnum):
    """Enum for the supported message types in the Tumult protocol."""

    MESSAGE = 1
    JOIN_MESSAGE = 2
    LEAVE_MESSAGE = 3
    NICKNAME = 4


@dataclass
class TumultHeader:
    """Header containing metadata for Tumult protocol messages."""

    request_type: RequestType
    version: str = PROTOCOL_VERSION
    timestamp: float = time.time()
    nickname: Optional[str] = None
    content_length: int = 0

    def to_bytes(self) -> bytes:
        """Encodes a header to JSON bytes with a 'carriage-return-new-line' termination."""
        header: str = json.dumps(
            {
                "version": self.version,
                "timestamp": self.timestamp,
                "request_type": int(self.request_type),
                "nickname": self.nickname,
                "content_length": self.content_length,
            }
        )
        return f"{header}\r\n".encode(ENCODING_FORMAT)

    @classmethod
    def from_bytes(cls, header_bytes: bytes) -> "TumultHeader":
        """Creates a header instance from JSON bytes."""
        header: dict[str, Any] = json.loads(
            header_bytes.decode(ENCODING_FORMAT).strip()
        )
        return cls(
            version=header["version"],
            timestamp=header["timestamp"],
            request_type=RequestType(header["request_type"]),
            nickname=header["nickname"],
            content_length=header["content_length"],
        )


class TumultSocket:
    """Socket wrapper implementing the Tumult protocol."""

    Request = namedtuple("Request", ["header", "contents"])

    @classmethod
    def valid_socket_address(cls, socket_address: tuple[str, int]) -> bool:
        """Validates the provided socket address as a proper IPv4 address and port number."""
        ipv4_address, port = socket_address
        logging.info("Validating socket address %s:%i", ipv4_address, port)
        try:
            ipaddress.IPv4Address(ipv4_address)
        except ipaddress.AddressValueError:
            logging.info("IPv4 address of the socket address is invalid")
            return False

        port_pattern: str = (
            r"^([1-9][0-9]{0,3}|"
            r"[1-5][0-9]{4}|"
            r"6[0-4][0-9]{3}|"
            r"65[0-4][0-9]{2}|"
            r"655[0-2][0-9]|"
            r"6553[0-5])$"
        )

        if not bool(
            re.match(
                port_pattern,
                str(port),
            )
        ):
            logging.info("Port number of the socket address is invalid")
            return False
        logging.info("Socket address is valid")
        return True

    def __init__(self, raw_socket: Optional[socket.socket] = None) -> None:
        self.__raw_socket = (
            raw_socket
            if raw_socket is not None
            else socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        )

    def bind(self, socket_address: tuple[str, int]) -> None:
        """Binds the socket to the socket address"""
        self.__raw_socket.bind(socket_address)

    def accept(self) -> tuple[socket.socket, tuple[str, int]]:
        """Accepts a connection and returns the accepted socket, socket address tuple."""
        return self.__raw_socket.accept()

    def connect(self, socket_address: tuple[Optional[str], Optional[int]]) -> None:
        """Attempts a connection with the provided socket address."""
        self.__raw_socket.connect(socket_address)

    def listen(self) -> None:
        """Starts listening on the socket"""
        self.__raw_socket.listen()

    def close(self) -> None:
        """Closes the current connection"""
        self.__raw_socket.close()

    def write_message(self, nickname: Optional[str], message: str) -> None:
        """Writes a message to the socket with the provided user's nickname and message."""
        message_bytes = message.encode(ENCODING_FORMAT)
        header_bytes = TumultHeader(
            request_type=RequestType.MESSAGE,
            nickname=nickname,
            content_length=len(message_bytes),
        ).to_bytes()
        self.__raw_socket.send(header_bytes + message_bytes)

    def write_join_message(self, nickname: Optional[str]) -> None:
        """Writes a join message to the socket with the provided user's nickname."""
        header_bytes = TumultHeader(
            request_type=RequestType.JOIN_MESSAGE, nickname=nickname
        ).to_bytes()
        self.__raw_socket.send(header_bytes)

    def write_leave_message(self, nickname: Optional[str]) -> None:
        """Writes a join message to the socket with the provided user's nickname."""
        header_bytes = TumultHeader(
            request_type=RequestType.LEAVE_MESSAGE, nickname=nickname
        ).to_bytes()
        self.__raw_socket.send(header_bytes)

    def write_nickname(self, nickname: Optional[str]) -> None:
        """Writes a nickname to the socket."""
        header_bytes = TumultHeader(
            request_type=RequestType.NICKNAME,
            nickname=nickname,
        ).to_bytes()
        self.__raw_socket.send(header_bytes)

    def read_request(self) -> Request:
        """Reads and parses the next request from the socket."""
        header_bytes: bytes = b""
        reading_bytes: bool = True
        while reading_bytes:
            byte: bytes = self.__raw_socket.recv(1)
            if not byte:
                raise ConnectionError
            header_bytes += byte
            if header_bytes.endswith(b"\r\n"):
                reading_bytes = False

        header: TumultHeader = TumultHeader.from_bytes(header_bytes)
        contents: bytes = (
            self.__raw_socket.recv(header.content_length)
            if header.content_length > 0
            else b""
        )
        return TumultSocket.Request(header, contents)

    def wait_for_request(self, request_type: RequestType) -> Request:
        """Blocks the socket until a request of the provided type is received."""
        request: TumultSocket.Request = TumultSocket.Request(None, None)
        waiting_for_request: bool = True
        while waiting_for_request:
            request = self.read_request()
            if request and request.header:
                if request.header.request_type == request_type:
                    waiting_for_request = False
        return request
