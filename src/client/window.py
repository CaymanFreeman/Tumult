"""Provides the PyQt window for the Tumult client."""

import logging
import os
import sys
from pathlib import Path
from typing import override, Optional

from PyQt6 import uic
from PyQt6.QtCore import pyqtSlot
from PyQt6.QtGui import QIcon, QCloseEvent
from PyQt6.QtWidgets import (
    QMainWindow,
    QLineEdit,
    QPushButton,
    QTextBrowser,
    QStackedWidget,
    QWidget,
    QLabel,
)

from src.client.tumult_client import TumultClient
from src.shared.protocol import DEFAULT_PORT, DEFAULT_IPV4_ADDRESS, TumultSocket

JOIN_MESSAGE: str = "has joined the server"
LEAVE_MESSAGE: str = "has left the server"


class ClientWindow(QMainWindow):
    """The PyQt window implementation for the Tumult client."""

    def __init__(self) -> None:
        super().__init__()
        self.client = TumultClient()

        self._set_icon()
        self._load_ui()

        self.form_container = self.findChild(QWidget, "form_container")
        self.connect_page = self.findChild(QWidget, "connect_page")
        self.chat_page = self.findChild(QWidget, "chat_page")
        self.central_stack = self.findChild(QStackedWidget, "central_stack")
        self.connect_page_index = self.central_stack.indexOf(self.connect_page)
        self.chat_page_index = self.central_stack.indexOf(self.chat_page)
        self.nickname_input = self.findChild(QLineEdit, "nickname_input")
        self.server_address_input = self.findChild(QLineEdit, "server_address_input")
        self.server_port_input = self.findChild(QLineEdit, "server_port_input")
        self.connect_button = self.findChild(QPushButton, "connect_button")
        self.message_box_input = self.findChild(QLineEdit, "message_box_input")
        self.send_button = self.findChild(QPushButton, "send_button")
        self.leave_button = self.findChild(QPushButton, "leave_button")
        self.chat_box = self.findChild(QTextBrowser, "chat_box")
        self.server_name_label = self.findChild(QLabel, "server_name_label")
        self.central_stack.setCurrentIndex(self.connect_page_index)

        self._connect_callbacks()

        self.adjustSize()
        self.show()
        logging.debug("Successfully loaded UI")

    @override
    def closeEvent(self, _: Optional[QCloseEvent]) -> None:
        """Forces the client to leave the current server when the window closes."""
        self.client.leave_server()

    def _load_ui(self) -> None:
        """Loads the UI layout from the .ui file in the assets directory."""
        source_ui_path = (
            Path(os.path.dirname(__file__))
            .parent.parent.joinpath("assets")
            .joinpath("client_window.ui")
        )

        if source_ui_path.exists():
            uic.loadUi(str(source_ui_path), self)
            return

        bundled_ui_path = (
            Path(os.path.dirname(__file__))
            .joinpath("assets")
            .joinpath("client_window.ui")
        )

        if bundled_ui_path.exists():
            uic.loadUi(str(bundled_ui_path), self)
            return

    def _set_icon(self) -> None:
        """Sets window icon with the icon PNG in the assets directory if the platform is Windows."""
        if not sys.platform.startswith("win"):
            return

        source_icon_path = (
            Path(os.path.dirname(__file__))
            .parent.parent.joinpath("assets")
            .joinpath("icon.png")
        )

        if source_icon_path.exists():
            self.setWindowIcon(QIcon(str(source_icon_path)))
            return

        bundled_icon_path = (
            Path(os.path.dirname(__file__)).joinpath("assets").joinpath("icon.png")
        )

        if bundled_icon_path.exists():
            self.setWindowIcon(QIcon(str(bundled_icon_path)))
            return

    def _connect_callbacks(self) -> None:
        """Connects each UI signal to its corresponding handler."""
        self.connect_button.clicked.connect(self._on_connect_button_clicked)
        self.send_button.clicked.connect(self._on_send_message)
        self.message_box_input.returnPressed.connect(self._on_send_message)
        self.leave_button.clicked.connect(self._on_leave_button_clicked)
        self.central_stack.currentChanged.connect(self.adjustSize)
        self.client.message_received.connect(self._on_message_received)
        self.client.join_message_received.connect(self._on_join_message_received)
        self.client.leave_message_received.connect(self._on_leave_message_received)
        self.client.disconnected.connect(self._on_disconnected)

    def _on_connect_button_clicked(self) -> None:
        """Validates the provided connection information and initiates the server connection."""
        if self.client.server.ipv4_address and self.client.server.port:
            return

        entered_server_address = bool(self.server_address_input.text())
        entered_server_port = bool(self.server_port_input.text())
        entered_nickname = bool(self.nickname_input.text())

        server_ipv4_address = (
            self.server_address_input.text()
            if entered_server_address
            else DEFAULT_IPV4_ADDRESS
        )
        if not entered_server_address:
            logging.info("Using default IPv4 address %s", DEFAULT_IPV4_ADDRESS)

        server_port = (
            int(self.server_port_input.text()) if entered_server_port else DEFAULT_PORT
        )
        if not entered_server_port:
            logging.info("Using default port %s", DEFAULT_PORT)

        self.client.server.socket_address = server_ipv4_address, server_port
        if not TumultSocket.valid_socket_address(self.client.server.socket_address):
            return

        if not entered_nickname:
            logging.info("Nickname not provided, will ask server for a nickname")
        self.client.nickname = self.nickname_input.text() if entered_nickname else None

        connection_success = self.client.connect()
        if connection_success:
            self.server_name_label.setText(f"{self.client.server}")
            self.central_stack.setCurrentIndex(self.chat_page_index)

    def _on_leave_button_clicked(self) -> None:
        """Disconnects from the server and returns to the connection page."""
        self.central_stack.setCurrentIndex(self.connect_page_index)
        self.client.leave_server()

    def _on_send_message(self) -> None:
        """Sends the text from the message field to the server then clears the field."""
        message = self.message_box_input.text()
        if message:
            self.client.send_message(message)
        self.message_box_input.clear()

    @pyqtSlot(str, str)
    def _on_message_received(self, nickname: str, message: str) -> None:
        """Displays the received chat message in chat box with sender's nickname."""
        self.chat_box.append(f"<strong>{nickname}</strong> {message}")

    @pyqtSlot(str)
    def _on_join_message_received(self, nickname: str) -> None:
        """Displays a join message for the user who joined."""
        self.chat_box.append(f"<em>{nickname} {JOIN_MESSAGE}</em>")

    @pyqtSlot(str)
    def _on_leave_message_received(self, nickname: str) -> None:
        """Displays a leave message for the user who left."""
        self.chat_box.append(f"<em>{nickname} {LEAVE_MESSAGE}</em>")

    @pyqtSlot()
    def _on_disconnected(self) -> None:
        """Returns to the connection page."""
        self.central_stack.setCurrentIndex(self.connect_page_index)
