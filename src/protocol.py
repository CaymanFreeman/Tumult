import json
import socket
import time
from collections import namedtuple
from dataclasses import dataclass
from enum import IntEnum
from typing import Optional, Self

VERSION: str = "0.1.0"
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


class TumultSocket(socket.socket):

    Request = namedtuple("Request", ["header", "contents"])

    def __init__(self):
        super().__init__(type=socket.SOCK_STREAM, family=socket.AF_INET)

    @classmethod
    def from_socket(cls, python_socket: socket.socket) -> Self:
        tumult_socket = cls.__new__(cls)
        super(cls, tumult_socket).__init__(
            family=python_socket.family,
            type=python_socket.type,
            proto=python_socket.proto,
            fileno=python_socket.fileno(),
        )
        return tumult_socket

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
        self.send(header_bytes + message_bytes)

    def write_join_message(self, nickname: str):
        header_bytes = TumultHeader(
            request_type=RequestType.JOIN_MESSAGE, nickname=nickname
        ).to_bytes()
        self.send(header_bytes)

    def write_leave_message(self, nickname: str):
        header_bytes = TumultHeader(
            request_type=RequestType.LEAVE_MESSAGE, nickname=nickname
        ).to_bytes()
        self.send(header_bytes)

    def write_nickname(self, nickname: str):
        header_bytes = TumultHeader(
            request_type=RequestType.NICKNAME,
            nickname=nickname,
        ).to_bytes()
        self.send(header_bytes)

    def read_request(self) -> Request:
        header_bytes = b""
        reading_bytes = True
        while reading_bytes:
            byte = self.recv(1)
            if not byte:
                raise ConnectionError
            header_bytes += byte
            if header_bytes.endswith(b"\r\n"):
                reading_bytes = False

        header = TumultHeader.from_bytes(header_bytes)
        contents = (
            self.recv(header.content_length) if header.content_length > 0 else b""
        )
        return TumultSocket.Request(header, contents)

    def wait_for_request(self, request_type: RequestType) -> Request:
        waiting_for_request = True
        while waiting_for_request:
            request = self.read_request()
            if request and request.header:
                if request.header.request_type == request_type:
                    return request
