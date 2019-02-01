import asyncio
import sys
from logging import getLogger

from client.game_client import GameClientFactory
from common.utils import PLAYER
from utils.configure_logging import setup_logging

logger = getLogger()


def main():
    loop = asyncio.get_event_loop()
    setup_logging('INFO')
    try:
        run_loop(loop)
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info('Exiting from client')


def run_loop(loop):
    factory = GameClientFactory(url=f'ws://127.0.0.1:9000', client_type=PLAYER, name=sys.argv[1])

    while True:
        try:
            loop.run_until_complete(loop.create_connection(factory, '127.0.0.1', 9000))
            loop.run_forever()
        except ConnectionRefusedError:
            loop.run_until_complete(asyncio.sleep(1))
        except KeyboardInterrupt:
            raise


if __name__ == '__main__':
    main()
