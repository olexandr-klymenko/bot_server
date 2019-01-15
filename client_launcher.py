import asyncio
import sys

from client.client_factory import GameClientFactory
from game.cell_types import PLAYER
from utils.configure_logging import setup_logging


def main():
    loop = asyncio.get_event_loop()

    setup_logging('INFO')

    run_loop(loop)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()


def run_loop(loop):
    factory = GameClientFactory(url=f'ws://127.0.0.1:9000', client_type=PLAYER, name=sys.argv[1])
    loop.run_until_complete(loop.create_connection(factory, '127.0.0.1', 9000))


if __name__ == '__main__':
    main()
