import json
from logging import getLogger
from os import getcwd
from os.path import join
from traceback import format_exc
from typing import Callable

import aiohttp_jinja2
import jinja2
from aiohttp.web import Application, Response, Request

TEMPLATES_DIR = "templates"

logger = getLogger()


class WebApp(Application):
    def __init__(self, loop, admin_command_func: Callable):
        super().__init__(loop=loop)
        self._admin_command_func = admin_command_func

        html_resource = self.router.add_resource("/")
        html_resource.add_route("GET", self.reg)
        self.router.add_static("/static", "static", name="static")

        play_resource = self.router.add_resource("/play")
        play_resource.add_route("GET", self.play)

        admin_resource = self.router.add_resource("/admin")
        admin_resource.add_route("POST", self.admin_command)
        admin_resource.add_route("GET", self.admin_page)

        aiohttp_jinja2.setup(
            self, loader=jinja2.FileSystemLoader(join(getcwd(), TEMPLATES_DIR))
        )

        logger.info("Web server has been initialized")

    async def play(self, request):
        context = {}
        response = aiohttp_jinja2.render_template("index.html", request, context)
        response.headers["Content-Language"] = "en"
        return response

    @staticmethod
    async def reg(request):
        context = {}
        response = aiohttp_jinja2.render_template("reg.html", request, context)
        response.headers["Content-Language"] = "en"
        return response

    async def admin_command(self, request: Request):
        try:
            raw_body = json.loads(await request.text())
            func_name = raw_body["command"]
            func_args = raw_body.get("args", [])
            if func_args:
                func_args = [func_args]

            result = self._admin_command_func(func_name, func_args)
            return Response(text=str(result))
        except Exception as err:
            logger.error(str(format_exc()))
            return Response(text=str(err), status=500)

    @staticmethod
    async def admin_page(request):
        context = {}
        response = aiohttp_jinja2.render_template("admin.html", request, context)
        return response
