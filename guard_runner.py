import asyncio

from uuid import uuid4

from client.game_client import GameClientFactory
from common.utils import GUARD
from utils.configure_logging import setup_logging

GAME_SERVER_WEB_SOCKET_URL = "ws://0.0.0.0"
GAME_SERVER_WEB_SOCKET_PORT = 9000


def main():
    loop = asyncio.get_event_loop()
    setup_logging('INFO')

    guard_factory = GameClientFactory(
        url=f'{GAME_SERVER_WEB_SOCKET_URL}:{GAME_SERVER_WEB_SOCKET_PORT}',
        client_type=GUARD,
        name=uuid4()
    )

    while True:
        try:
            loop.run_until_complete(loop.create_connection(guard_factory, '127.0.0.1', 9000))
            loop.run_forever()
        except ConnectionRefusedError:
            pass
            loop.run_until_complete(asyncio.sleep(1))
        # except Exception:
        #     loop.stop()
        #     loop.close()
        #     raise


if __name__ == '__main__':
    main()
