import json
import socket
import time
from collections import namedtuple
from dataclasses import dataclass
from enum import IntEnum
from typing import Optional, Self, Tuple

VERSION: str = "0.1.1"
DEFAULT_IPV4_ADDRESS: str = "127.0.0.1"
DEFAULT_PORT: int = 65535
ENCODING_FORMAT: str = "utf-8"


class RequestType(IntEnum):
    MESSAGE = 1
    JOIN_MESSAGE = 2
    LEAVE_MESSAGE = 3
    NICKNAME = 4


@dataclass
class TumultHeader:
    request_type: RequestType
    version: str = VERSION
    timestamp: Optional[float] = time.time()
    nickname: Optional[str] = None
    content_length: int = 0

    def to_bytes(self) -> bytes:
        header = json.dumps(
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
    def from_bytes(cls, header_bytes: bytes) -> Self:
        header = json.loads(header_bytes.decode(ENCODING_FORMAT).strip())
        return cls(
            version=header["version"],
            timestamp=header["timestamp"],
            request_type=RequestType(header["request_type"]),
            nickname=header["nickname"],
            content_length=header["content_length"],
        )


class TumultSocket:

    Request = namedtuple("Request", ["header", "contents"])

    def __init__(self, raw_socket: Optional[socket.socket] = None):
        self.__raw_socket = raw_socket if raw_socket is not None else socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    @property
    def unwrap(self):
        return self.__raw_socket

    def bind(self, socket_address: Tuple[str, int]):
        self.__raw_socket.bind(socket_address)

    def accept(self) -> Tuple[socket.socket, Tuple[str, int]]:
        return self.__raw_socket.accept()

    def connect(self, socket_address: Tuple[str, int]):
        self.__raw_socket.connect(socket_address)

    def listen(self):
        self.__raw_socket.listen()

    def close(self):
        self.__raw_socket.close()

    def write_message(
        self,
        nickname: str,
        message: str,
        request_type: RequestType = RequestType.MESSAGE,
    ):
        message_bytes = message.encode(ENCODING_FORMAT)
        header_bytes = TumultHeader(
            request_type=request_type,
            nickname=nickname,
            content_length=len(message_bytes),
        ).to_bytes()
        self.__raw_socket.send(header_bytes + message_bytes)

    def write_join_message(self, nickname: str):
        header_bytes = TumultHeader(
            request_type=RequestType.JOIN_MESSAGE, nickname=nickname
        ).to_bytes()
        self.__raw_socket.send(header_bytes)

    def write_leave_message(self, nickname: str):
        header_bytes = TumultHeader(
            request_type=RequestType.LEAVE_MESSAGE, nickname=nickname
        ).to_bytes()
        self.__raw_socket.send(header_bytes)

    def write_nickname(self, nickname: str):
        header_bytes = TumultHeader(
            request_type=RequestType.NICKNAME,
            nickname=nickname,
        ).to_bytes()
        self.__raw_socket.send(header_bytes)

    def read_request(self) -> Request:
        header_bytes = b""
        reading_bytes = True
        while reading_bytes:
            byte = self.__raw_socket.recv(1)
            if not byte:
                raise ConnectionError
            header_bytes += byte
            if header_bytes.endswith(b"\r\n"):
                reading_bytes = False

        header = TumultHeader.from_bytes(header_bytes)
        contents = (
            self.__raw_socket.recv(header.content_length) if header.content_length > 0 else b""
        )
        return TumultSocket.Request(header, contents)

    def wait_for_request(self, request_type: RequestType) -> Request:
        waiting_for_request = True
        while waiting_for_request:
            request = self.read_request()
            if request and request.header:
                if request.header.request_type == request_type:
                    return request
