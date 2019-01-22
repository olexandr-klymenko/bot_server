from logging import getLogger
from os import getcwd
from os.path import join

import aiohttp_jinja2
import jinja2
from aiohttp.web import Application

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

        admin_resource = self.router.add_resource('/admin')
        admin_resource.add_route('GET', self.admin_page)

        aiohttp_jinja2.setup(self, loader=jinja2.FileSystemLoader(join(getcwd(), TEMPLATES_DIR)))

        logger.info('Web server has been initialized')

    @staticmethod
    async def play(request):
        context = {}
        response = aiohttp_jinja2.render_template('index.html', request, context)
        response.headers['Content-Language'] = 'en'
        return response

    @staticmethod
    async def reg(request):
        context = {}
        response = aiohttp_jinja2.render_template('reg.html', request, context)
        response.headers['Content-Language'] = 'en'
        return response

    @staticmethod
    async def admin_page(request):
        context = {}
        response = aiohttp_jinja2.render_template('admin.html', request, context)
        return response
