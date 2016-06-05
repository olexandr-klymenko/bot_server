from argparse import ArgumentParser

import asyncio

from utils.configure_logging import setup_logging
from server.server_protocol import BroadcastServerProtocol
from server.web_server import WebServer
from server.server_factory import BroadcastServerFactory
from game_config import *
from game.guards_factory import run_guards


def main():
    cmd_args = get_cmd_args()
    setup_logging(cmd_args.log_level, SERVER_LOG_FILE)

    game_factory = BroadcastServerFactory(url=GAME_SERVER_WEB_SOCKET_URL % cmd_args.port)

    game_factory.protocol = BroadcastServerProtocol

    loop = asyncio.get_event_loop()
    game_ws_server = loop.run_until_complete(loop.create_server(game_factory, '0.0.0.0', cmd_args.port))

    guard_client = run_guards(loop, cmd_args.port, game_factory.game_session)

    web_app = WebServer(loop, game_factory.game_session)
    web_server = loop.run_until_complete(loop.create_server(web_app.make_handler(), '0.0.0.0', FRONTEND_PORT))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        guard_client.close()
        game_ws_server.close()
        web_server.close()
        loop.close()


def get_cmd_args():
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', dest='port', default=GAME_SERVER_WEB_SOCKET_PORT)
    parser.add_argument('-l', '--log_level', dest='log_level', choices=['INFO', 'DEBUG'],
                        default='DEBUG' if DEBUG else 'INFO')
    return parser.parse_args()


if __name__ == '__main__':
    main()
