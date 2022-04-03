import asyncio
import json
import logging
import os
from starlette.routing import Route, WebSocketRoute
import uvicorn
from websockets.exceptions import ConnectionClosedError
#-
from obs_layout_core.application import Application
from obs_layout_core.youtube_livechat import YoutubeLiveChat

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)


class Example(Application, YoutubeLiveChat):

    is_testing = True

    osb_dock_route = '/controller'
    google_auth_redirect = osb_dock_route

    def initialize(self):
        super().initialize()
        self.app.router.routes.append(Route('/', endpoint=self.homepage))
        self.app.router.routes.append(Route(self.osb_dock_route,
                endpoint=self.osb_dock))
        self.app.router.routes.append(WebSocketRoute('/ws',
                endpoint=self.websocket_index))


    async def homepage(self, request):
        return self.templates.TemplateResponse('index.html',
                {'request': request})


    async def osb_dock(self, request):
        self.check_google_auth()
        return self.templates.TemplateResponse('controller.html',
                {'request': request})


    async def websocket_index(self, websocket):
        await websocket.accept()
        try:
            while True:
                for item in self.youtube_livechat_messages():
                    if item['snippet']['type'] != 'textMessageEvent':
                        continue
                    js_item = {
                        'id': item['etag'],
                        'author': item['authorDetails']['displayName'],
                        'text': item['snippet']['displayMessage'],
                    }
                    await websocket.send_text(json.dumps(js_item))
                await asyncio.sleep(0.2)
        except ConnectionClosedError:
            pass
        finally:
            await websocket.close()


if __name__ == '__main__':
    example = Example()
    uvicorn.run(example.app, host=os.environ['LISTEN_ADDR'],
            port=int(os.environ['LISTEN_PORT']))
