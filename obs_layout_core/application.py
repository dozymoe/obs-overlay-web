import inspect
import json
import logging
import os
from pathlib import Path
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
import sys

_logger = logging.getLogger(__name__)


class Application:

    is_testing = False
    base_dir = None
    templates = None
    api_dump_file = None

    def __init__(self):
        super().__init__()
        self.app = Starlette(on_startup=[self.initialize],
                on_shutdown=[self.destroy])
        self.base_dir = Path(os.path.dirname(sys.modules['__main__'].__file__))
        self.templates = Jinja2Templates(directory=self.base_dir/'templates')


    def initialize(self):
        super().initialize()
        self.app.router.routes.append(Mount('/static',
                app=StaticFiles(directory=self.base_dir/'static')))


    def destroy(self):
        super().destroy()


    def dump_data(self, data):
        if self.api_dump_file:
            with open(self.api_dump_file, 'a', encoding='utf-8') as f:
                json.dump(data, f)
                f.write("\n")
