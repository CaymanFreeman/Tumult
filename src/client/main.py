from client import Client
from src.protocol.protocol import TumultProtocol


def main():
    client = Client()
    handle_inputs(client)


def handle_inputs(client: Client):
    while True:
        user_input = input("> ")
        if user_input == "/dc" or user_input == "/disconnect":
            if client.is_connected:
                client.disconnect()
            else:
                print("Not connected to a server")
        elif user_input.startswith("/con") or user_input.startswith("/connect"):
            try:
                server_address = user_input.split(" ")[1]
                if ":" in server_address and server_address.count(":") == 1:
                    server_address = server_address.split(":")
                    server_ip_address = server_address[0]
                    server_port = server_address[1]
                    if client.is_connected:
                        client.disconnect()
                    client.server_socket_address = server_ip_address, server_port
                    client.connect()
                elif ":" not in server_address:
                    if client.is_connected:
                        client.disconnect()
                    client.server_socket_address = (
                        server_address,
                        TumultProtocol.default_port,
                    )
                    client.connect()
                else:
                    print("Invalid input")
            except IndexError:
                print("Invalid input")
        elif client.is_connected:
            client.send_message(user_input)


if __name__ == "__main__":
    main()
