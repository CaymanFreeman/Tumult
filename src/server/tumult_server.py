"""Provides the server implementation for Tumult."""

import logging
import socket
import threading
from dataclasses import dataclass
from typing import Optional

from src.shared.protocol import (
    TumultSocket,
    RequestType,
    ENCODING_FORMAT,
)


@dataclass
class ClientInfo:
    """Container for client connection information."""

    ipv4_address: str
    port: int
    socket: TumultSocket
    nickname: Optional[str] = None

    def __str__(self) -> str:
        """Returns a string representation of the socket address in address:port format."""
        return f"{self.ipv4_address}:{self.port}"

    @property
    def socket_address(self) -> tuple[str, int]:
        """Returns the socket address as a tuple."""
        return self.ipv4_address, self.port


@dataclass
class Message:
    """Container for chat messages with the message type and sender nickname."""

    nickname: Optional[str]
    contents: str
    message_type: RequestType = RequestType.MESSAGE


class TumultServer:
    """Server implementation for Tumult."""

    def __init__(self, ipv4_address: str, port: int) -> None:
        self.ipv4_address: str = ipv4_address
        self.port: int = port
        self.socket: TumultSocket = TumultSocket()
        self.clients: list[ClientInfo] = []
        self.message_history: list[Message] = []

        try:
            self.socket.bind((ipv4_address, port))
        except socket.error as error:
            logging.error(
                "An error occurred while binding socket (%s, %i): %s",
                ipv4_address,
                port,
                error,
            )

    def __str__(self) -> str:
        """Returns a string representation of the socket address in address:port format."""
        return f"{self.ipv4_address}:{self.port}"

    @property
    def socket_address(self) -> tuple[str, int]:
        """Returns the current socket address as a tuple."""
        return self.ipv4_address, self.port

    @property
    def client_sockets(self) -> list[TumultSocket]:
        """Returns the current list of client socket connections."""
        return [client.socket for client in self.clients]

    @property
    def client_nicknames(self) -> list[Optional[str]]:
        """Returns the current list of client nicknames."""
        return [client.nickname for client in self.clients]

    @property
    def client_ipv4_addresses(self) -> list[str]:
        """Returns the current list of client addresses."""
        return [client.ipv4_address for client in self.clients]

    def start(self) -> None:
        """Starts listening for and accepting client connections."""
        logging.info("Listening at %s", self)
        self.socket.listen()
        self._handle_client_connections()

    def broadcast_message(self, nickname: Optional[str], contents: str) -> None:
        """Sends a message to all connected clients."""
        message = Message(nickname, contents, RequestType.MESSAGE)
        self.message_history.append(message)
        logging.info("%s says %s", message.nickname, message.contents)
        for client_socket in self.client_sockets:
            client_socket.write_message(message.nickname, message.contents)

    def broadcast_join_message(self, nickname: Optional[str]) -> None:
        """Sends a join to all connected clients."""
        message = Message(nickname, "joined", RequestType.JOIN_MESSAGE)
        self.message_history.append(message)
        logging.info("%s joined", nickname)
        for client_socket in self.client_sockets:
            client_socket.write_join_message(nickname)

    def broadcast_leave_message(self, nickname: Optional[str]) -> None:
        """Sends a leave to all connected clients."""
        message = Message(nickname, "left", RequestType.LEAVE_MESSAGE)
        self.message_history.append(message)
        logging.info("%s left", nickname)
        for client_socket in self.client_sockets:
            client_socket.write_leave_message(nickname)

    def send_message_history(self, client: ClientInfo) -> None:
        """Sends all previous messages to a client."""
        client_socket = client.socket
        for message in self.message_history:
            match message.message_type:
                case RequestType.MESSAGE:
                    client_socket.write_message(message.nickname, message.contents)
                case RequestType.JOIN_MESSAGE:
                    client_socket.write_join_message(message.nickname)
                case RequestType.LEAVE_MESSAGE:
                    client_socket.write_leave_message(message.nickname)

    @classmethod
    def _request_nickname(cls, client: ClientInfo) -> None:
        """Requests the nickname from a client."""
        client.socket.write_nickname(client.nickname)

    def _wait_for_nickname(self, client: ClientInfo) -> None:
        """Waits for a client nickname response then accepts it or generates a default."""
        nickname_request = client.socket.wait_for_request(RequestType.NICKNAME)

        if nickname_request.header.nickname is None:
            self._generate_nickname(client)
        else:
            client.nickname = nickname_request.header.nickname
        self.broadcast_join_message(client.nickname)

    def _disconnect_client(self, client: ClientInfo) -> None:
        """Removes a client from the server and broadcast a leave message the other clients."""
        self.clients.remove(client)
        if client.socket:
            client.socket.close()
        self.broadcast_leave_message(client.nickname)

        logging.info("Client list updated to %s", str(self.client_ipv4_addresses))

    def _generate_nickname(self, client: ClientInfo) -> None:
        """
        Creates default nickname for the client based on connection order.
        E.g. User1, User2, User3...
        """
        client.nickname = f"User{self.clients.index(client) + 1}"
        logging.info("Generated nickname %s for client %s", client.nickname, client)

    def _handle_client_requests(self, client: ClientInfo) -> None:
        """Processes incoming requests from a specific client."""
        logging.info("Client connected from %s", client)
        self.clients.append(client)
        logging.info("Client list updated to %s", str(self.client_ipv4_addresses))
        logging.info("Sending message history to client %s", client)
        self.send_message_history(client)

        self._request_nickname(client)
        self._wait_for_nickname(client)

        handling_requests: bool = True
        while handling_requests:
            try:
                request: TumultSocket.Request = client.socket.read_request()
                if not request or not request.header:
                    continue

                match request.header.request_type:

                    case RequestType.NICKNAME:
                        client.nickname = request.header.nickname

                    case RequestType.MESSAGE:
                        message = request.contents.decode(ENCODING_FORMAT)
                        self.broadcast_message(client.nickname, message)

            except TimeoutError:
                logging.info("Connection with client %s timed out", client)
                handling_requests = False
            except ConnectionResetError:
                logging.info(
                    "Connection with client %s was forcibly closed by them", client
                )
                handling_requests = False
            except ConnectionAbortedError:
                logging.info("Connection with client %s was aborted", client)
                handling_requests = False
            except ConnectionError as error:
                logging.error(
                    "Connection with client %s experienced an error: %s",
                    client,
                    error,
                )
                handling_requests = False
            except socket.error as error:
                logging.error(
                    "An unknown error occurred with client %s: %s",
                    client,
                    error,
                )
                handling_requests = False
        self._disconnect_client(client)

    def _handle_client_connections(self) -> None:
        """Accepts new client connections and creates a corresponding handler thread."""
        handling_connections: bool = True
        while handling_connections:

            client_socket_info: tuple[socket.socket, tuple[str, int]] = (
                self.socket.accept()
            )
            client_socket: socket.socket = client_socket_info[0]
            client_socket_address: tuple[str, int] = client_socket_info[1]
            client_ipv4_address: str = client_socket_address[0]
            client_port: int = client_socket_address[1]
            client_thread: threading.Thread = threading.Thread(
                target=self._handle_client_requests,
                args=[
                    ClientInfo(
                        ipv4_address=client_ipv4_address,
                        port=client_port,
                        socket=TumultSocket(client_socket),
                    )
                ],
            )
            client_thread.start()
