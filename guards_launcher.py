import asyncio

from client.client_factory import GameClientFactory
from game.cell_types import GUARD
from utils.configure_logging import setup_logging

NAMES = ['1', '2', '3', '4']


def main():
    loop = asyncio.get_event_loop()
    setup_logging('INFO', '')

    run_loop(loop)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()


def run_loop(loop):
    coros = []
    for name in NAMES:
        factory = GameClientFactory(url=f'ws://127.0.0.1:9000', client_type=GUARD, name=name)
        coros.append(loop.create_connection(factory, '127.0.0.1', 9000))
    loop.run_until_complete(asyncio.gather(*coros))


if __name__ == '__main__':
    main()
