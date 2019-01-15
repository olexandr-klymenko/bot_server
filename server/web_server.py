from logging import getLogger
from os import getcwd
from os.path import join

import aiohttp_jinja2
import jinja2
from aiohttp.web import Application, Response

REST_ROOT = 'rest'
TEMPLATES_DIR = 'templates'

logger = getLogger()


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

    async def play(self, request):
        context = {}
        response = aiohttp_jinja2.render_template('index.html', request, context)
        response.headers['Content-Language'] = 'en'
        return response

    async def reg(self, request):
        context = {}
        response = aiohttp_jinja2.render_template('reg.html', request, context)
        response.headers['Content-Language'] = 'en'
        return response

    async def query(self, request):
        func_name = str(request.rel_url.path).replace('/%s/' % REST_ROOT, '')
        func_args = request.query_string
        logger.info(func_args)
        if func_args:
            func_args = [func_args]
        else:
            func_args = []

        result = self.game_session.run_rest_action(func_name, func_args)
        return Response(text=str(result))
