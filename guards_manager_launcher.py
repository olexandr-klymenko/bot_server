import asyncio

from client.guard_manager import GuardManagerClientFactory
from utils.configure_logging import setup_logging

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    setup_logging('INFO')

    # factory = GameClientFactory(url=f'ws://127.0.0.1:9000', client_type=GUARD, name=name)
    factory = GuardManagerClientFactory(url=f'ws://127.0.0.1:9000')
    loop.run_until_complete(loop.create_connection(factory, '127.0.0.1', 9000))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()
