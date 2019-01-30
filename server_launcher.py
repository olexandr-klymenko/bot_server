import asyncio

from argparse import ArgumentParser

from game.game_board import LodeRunnerGameBoard
from game.game_session import LodeRunnerGameSession
from server.game_server import BroadcastServerFactory, BroadcastServerProtocol
from server.web_server import WebServer
from utils.configure_logging import setup_logging

GAME_SERVER_WEB_SOCKET_URL = "ws://0.0.0.0"
GAME_SERVER_WEB_SOCKET_PORT = 9000
FRONTEND_PORT = 8080
DEBUG = False


def main():
    cmd_args = get_cmd_args()
    setup_logging(cmd_args.log_level)

    loop = asyncio.get_event_loop()

    game_board = LodeRunnerGameBoard.from_blocks_number()
    game_session = LodeRunnerGameSession(loop, game_board)

    game_factory = BroadcastServerFactory(url=f"{GAME_SERVER_WEB_SOCKET_URL}:{cmd_args.port}")
    game_session.clients_info = game_factory.clients_info
    game_session.send_admin_info_callback = game_factory.send_admin_info
    game_factory.game_session = game_session
    game_factory.protocol = BroadcastServerProtocol

    game_ws_server = loop.run_until_complete(
        loop.create_server(game_factory, '0.0.0.0', cmd_args.port)
    )

    web_app = WebServer(loop, game_session)
    web_server = loop.run_until_complete(
        loop.create_server(web_app.make_handler(), '0.0.0.0', FRONTEND_PORT)
    )

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
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


# TODO: Add docker support
# TODO: Get back guards manager
