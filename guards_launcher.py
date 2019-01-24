import asyncio
from multiprocessing import Pool

from client.client_factory import GameClientFactory
from common.utils import GUARD
from utils.configure_logging import setup_logging

NAMES = ['1', '2', '3', '4']


def main(name):
    loop = asyncio.get_event_loop()
    setup_logging('INFO')

    factory = GameClientFactory(url=f'ws://127.0.0.1:9000', client_type=GUARD, name=name)
    loop.run_until_complete(loop.create_connection(factory, '127.0.0.1', 9000))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()


if __name__ == '__main__':
    pool = Pool(len(NAMES))
    pool.map(main, NAMES)
