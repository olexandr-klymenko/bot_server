from autobahn.asyncio.websocket import WebSocketClientFactory

from client.client_protocol import LodeRunnerClientProtocol


class GameClientFactory(WebSocketClientFactory):
    def __init__(self, url, client_type, name):
        self.name = name
        self.client_type = client_type
        super().__init__(f'{url}?client_type={client_type}&name={name}')
        self.protocol = LodeRunnerClientProtocol
        self.client = None
