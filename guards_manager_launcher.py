import asyncio

from client.guard_manager import GuardManagerClientFactory
from utils.configure_logging import setup_logging

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    setup_logging('INFO')

    factory = GuardManagerClientFactory(url=f'ws://127.0.0.1:9000')

    while True:
        try:
            loop.run_until_complete(loop.create_connection(factory, '127.0.0.1', 9000))
            loop.run_forever()
        except ConnectionRefusedError:
            pass
            loop.run_until_complete(asyncio.sleep(1))
        except KeyboardInterrupt:
            loop.close()
