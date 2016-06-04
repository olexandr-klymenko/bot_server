from argparse import ArgumentParser
import sys

import asyncio
from autobahn.asyncio.websocket import WebSocketClientFactory, WebSocketClientProtocol

from game_config import *
from utils.configure_logging import setup_logging
from client.client_prototype import BroadcastClientProtocol


NAMES = ['Arny', 'Bob', 'Charlie', 'Dick', 'Eva', 'Fred', 'Greg', 'Harry', 'Irena', 'Jack', 'Kat']


def main():
    loop = asyncio.get_event_loop()

    cmd_args = get_cmd_args()
    setup_logging(cmd_args.log_level, CLIENT_LOG_FILE)

    if len(sys.argv) > 1:
        if cmd_args.spectator:
            user_option = ''
        else:
            user_option = "?user=%s" % cmd_args.name
        factory = WebSocketClientFactory('ws://127.0.0.1:9000%s' % user_option)
        factory.protocol = WebSocketClientProtocol

        coro = loop.create_connection(factory, '127.0.0.1', 9000)
        loop.run_until_complete(coro)

    else:
        run_loop(loop)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    except WebSocketClientDisconnect:
        loop.close()
        run_loop(loop)
    finally:
        loop.close()


def get_cmd_args():
    parser = ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-n', '--name', dest='name')
    group.add_argument('-s', '--spectator', action='store_true')
    parser.add_argument('-l', '--log_level', dest='log_level', choices=['INFO', 'DEBUG'],
                        default='DEBUG' if DEBUG else 'INFO')
    arguments = parser.parse_args()

    return arguments


def run_loop(loop):
    for name in NAMES:
        factory = WebSocketClientFactory('ws://127.0.0.1:9000?user=%s' % name)
        factory.protocol = BroadcastClientProtocol
        coro = loop.create_connection(factory, '127.0.0.1', 9000)
        loop.run_until_complete(coro)


if __name__ == '__main__':
    main()
