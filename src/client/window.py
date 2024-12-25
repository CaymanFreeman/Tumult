import os
import re
import sys
from pathlib import Path

from PyQt6 import uic
from PyQt6.QtCore import pyqtSlot
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QMainWindow,
    QLineEdit,
    QPushButton,
    QTextBrowser,
    QStackedWidget,
    QWidget,
    QLabel,
)

from src.client.client import TumultClient
from src.shared.protocol import DEFAULT_PORT, DEFAULT_IPV4_ADDRESS

# IPv4 Regex from Danail Gabenski
# https://stackoverflow.com/questions/5284147/validating-ipv4-addresses-with-regexp
IPV4_PATTERN: str = r"^((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.?\b){4}$"
PORT_PATTERN: str = (
    r"^([1-9][0-9]{0,3}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])$"
)

JOIN_MESSAGE: str = "has joined the server"
LEAVE_MESSAGE: str = "has left the server"


class ClientWindow(QMainWindow):
    @classmethod
    def validate_socket_address(cls, ipv4_address: str, port: int) -> bool:
        if not bool(re.match(IPV4_PATTERN, ipv4_address)):
            return False
        if not bool(re.match(PORT_PATTERN, str(port))):
            return False

        return True

    def __init__(self):
        super(ClientWindow, self).__init__()
        self.client = TumultClient()

        self.set_icon()
        self.load_ui()

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

        self.connect_callbacks()

        self.adjustSize()
        self.show()
        print("[SYSTEM] Successfully loaded UI")

    def load_ui(self):
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

    def set_icon(self):
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

    def closeEvent(self, event):
        self.client.leave_server()

    def connect_callbacks(self):
        self.connect_button.clicked.connect(self.on_connect_button_clicked)
        self.send_button.clicked.connect(self.on_send_message)
        self.message_box_input.returnPressed.connect(self.on_send_message)
        self.leave_button.clicked.connect(self.on_leave_button_clicked)
        self.central_stack.currentChanged.connect(self.adjustSize)
        self.client.message_received.connect(self.on_message_received)
        self.client.join_message_received.connect(self.on_join_message_received)
        self.client.leave_message_received.connect(self.on_leave_message_received)
        self.client.disconnected.connect(self.on_disconnected)

    def on_connect_button_clicked(self):
        if self.client.server_ipv4_address and self.client.server_port:
            return

        entered_server_address = bool(self.server_address_input.text())
        entered_server_port = bool(self.server_address_input.text())
        entered_nickname = bool(self.nickname_input.text())

        server_ipv4_address = (
            self.server_address_input.text()
            if entered_server_address
            else DEFAULT_IPV4_ADDRESS
        )
        server_port = (
            int(self.server_address_input.text())
            if entered_server_port
            else DEFAULT_PORT
        )
        nickname = self.nickname_input.text() if entered_nickname else None

        if self.validate_socket_address(server_ipv4_address, server_port):
            connection_success = self.client.connect(
                server_ipv4_address, server_port, nickname
            )
            if connection_success:
                self.server_name_label.setText(f"{server_ipv4_address}:{server_port}")
                self.central_stack.setCurrentIndex(self.chat_page_index)

    def on_leave_button_clicked(self):
        self.central_stack.setCurrentIndex(self.connect_page_index)
        self.client.leave_server()

    def on_send_message(self):
        message = self.message_box_input.text()
        if message:
            self.client.send_message(message)
        self.message_box_input.clear()

    @pyqtSlot(str, str)
    def on_message_received(self, nickname: str, message: str):
        self.chat_box.append(f"<strong>{nickname}</strong> {message}")

    @pyqtSlot(str)
    def on_join_message_received(self, nickname: str):
        self.chat_box.append(f"<em>{nickname} {JOIN_MESSAGE}</em>")

    @pyqtSlot(str)
    def on_leave_message_received(self, nickname: str):
        self.chat_box.append(f"<em>{nickname} {LEAVE_MESSAGE}</em>")

    @pyqtSlot()
    def on_disconnected(self):
        self.central_stack.setCurrentIndex(self.connect_page_index)
