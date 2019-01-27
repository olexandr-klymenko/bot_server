import asyncio

from argparse import ArgumentParser

from server.guard_manager import GuardManagerServerFactory, GuardManagerServerProtocol
from utils.configure_logging import setup_logging

GUARD_MANAGER_SERVER_WEB_SOCKET_URL = "ws://0.0.0.0"
GUARD_MANAGER_SERVER_WEB_SOCKET_PORT = 9090
DEBUG = False


def main():
    cmd_args = get_cmd_args()
    setup_logging(cmd_args.log_level)

    loop = asyncio.get_event_loop()

    factory = GuardManagerServerFactory(
        url=f'{GUARD_MANAGER_SERVER_WEB_SOCKET_URL}:{GUARD_MANAGER_SERVER_WEB_SOCKET_PORT}')

    factory.protocol = GuardManagerServerProtocol

    guard_manager_ws_server = loop.run_until_complete(
        loop.create_server(factory, '0.0.0.0', cmd_args.port)
    )

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        guard_manager_ws_server.close()
        loop.close()


def get_cmd_args():
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', dest='port', default=GUARD_MANAGER_SERVER_WEB_SOCKET_PORT)
    parser.add_argument('-l', '--log_level', dest='log_level', choices=['INFO', 'DEBUG'],
                        default='DEBUG' if DEBUG else 'INFO')
    return parser.parse_args()


if __name__ == '__main__':
    main()
