from client import Client


def main():
    client = Client()
    client.connect()
    client.send_message("Hello, World!")


if __name__ == "__main__":
    main()
