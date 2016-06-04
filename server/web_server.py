import asyncio
from os.path import join
from os import getcwd
import jinja2

from aiohttp.web import Application, Response
import aiohttp_jinja2

from game_config import TEMPLATES_DIR, REST_ROOT


class WebServer(Application):

    def __init__(self, loop, game_session):
        super().__init__(loop=loop)
        self.game_session = game_session

        html_resource = self.router.add_resource('/')
        html_resource.add_route('GET', self.reg)
        self.router.add_static('/static', 'static', name='static')

        play_resource = self.router.add_resource('/play')
        play_resource.add_route('GET', self.play)

        rest_resource = self.router.add_resource('/%s/{command}' % REST_ROOT)
        rest_resource.add_route('GET', self.query)

        aiohttp_jinja2.setup(self, loader=jinja2.FileSystemLoader(join(getcwd(), TEMPLATES_DIR)))

    @asyncio.coroutine
    def play(self, request):
        context = {}
        response = aiohttp_jinja2.render_template('index.html', request, context)
        response.headers['Content-Language'] = 'en'
        return response

    @asyncio.coroutine
    def reg(self, request):
        context = {}
        response = aiohttp_jinja2.render_template('reg.html', request, context)
        response.headers['Content-Language'] = 'en'
        return response

    @asyncio.coroutine
    def query(self, request):
        func_name = request._splitted_path.path.replace('/%s/' % REST_ROOT, '')
        func_args = request._splitted_path.query
        if func_args:
            func_args = [func_args]
        else:
            func_args = []

        result = self.game_session.run_rest_action(func_name, func_args)
        return Response(text=str(result))

        # func = getattr(self.game_session, func_name)
        # return Response(text=str(func(*func_args)))
