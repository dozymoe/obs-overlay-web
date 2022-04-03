from aiogoogle import Aiogoogle
from aiogoogle.excs import HTTPError
import asyncio
from datetime import datetime, timedelta
from dateutil.parser import parse as date_parse
import logging
from uuid import uuid4
#-
from .google_auth import GoogleAuth

_logger = logging.getLogger(__name__)


class YoutubeLiveChat(GoogleAuth):

    page_size = 20

    def __init__(self):
        super().__init__()
        self.youtube_chat_worker = None
        self.youtube_chat_messages = []
        self.youtube_chat_last_position = 0
        self.youtube_chat_fetch_interval = timedelta(seconds=10)
        self.youtube_chat_fetch_timestamp = datetime.now()
        self.youtube_livechat_id = None
        self.youtube_livechat_pagetoken = None
        self.youtube_livechat_pageindex = 0


    def youtube_livechat_messages(self):
        self.fetch_youtube_livechat_messages()

        while len(self.youtube_chat_messages) > self.youtube_chat_last_position:
            yield self.youtube_chat_messages[self.youtube_chat_last_position]
            self.youtube_chat_last_position += 1


    async def google_oauth_callback_success(self, request):
        self.youtube_chat_worker = asyncio.create_task(
                self.really_fetch_youtube_livechat_messages())


    def reset(self):
        self.youtube_chat_messages = []
        self.youtube_chat_last_position = 0
        self.youtube_livechat_id = None
        self.youtube_livechat_pagetoken = None
        self.youtube_livechat_pageindex = 0


    def fetch_youtube_livechat_messages(self):
        if self.youtube_chat_worker is None and\
                datetime.now() - self.youtube_chat_fetch_timestamp\
                > self.youtube_chat_fetch_interval:

            self.youtube_chat_worker = asyncio.create_task(
                    self.really_fetch_youtube_livechat_messages())


    async def testing_fetch_youtube_livechat_messages(self):
        from faker import Faker
        fake = Faker()

        for _ in range(5):
            self.youtube_chat_messages.append({
                'etag': uuid4().hex,
                'snippet': {
                    'type': 'textMessageEvent',
                    'hasDisplayContent': True,
                    'displayMessage': fake.sentence(),
                    'publishedAt': datetime.now(),
                },
                'authorDetails': {
                    'channelId': fake.barcode(),
                    'channelUrl': fake.url(),
                    'displayName': fake.name(),
                    'profileImageUrl': fake.image_url(),
                    'isVerified': fake.pybool(),
                    'isChatOwner': fake.pybool(),
                    'isChatSponsor': fake.pybool(),
                    'isChatModerator': fake.pybool(),
                },
            })
            await asyncio.sleep(0.1)
        self.youtube_chat_worker = None
        self.youtube_chat_fetch_timestamp = datetime.now()


    async def get_livechat_id(self, youtube, gapi):
        request = youtube.liveBroadcasts.list(
                mine=True,
                part=['status', 'snippet'])
        pager = await gapi.as_user(request, full_res=True)
        async for response in pager:
            broadcasts = response['items']
            if not broadcasts:
                break
            _logger.debug(response)
            self.dump_data(response)
# Example:
#{
#  'kind': 'youtube#liveBroadcastListResponse',
#  'etag': 'HQ26jKee2XSw_o2EuGpBIVwOD2I',
#  'pageInfo': {'totalResults': 5, 'resultsPerPage': 5},
#  'items': [
#    {
#      'kind': 'youtube#liveBroadcast',
#      'etag': 'y0bO6XC2o7SZeALdGHV8Da1MkCE',
#      'id': 'SUPnT7-1Lqs',
#      'snippet': {
#        'publishedAt': '2022-03-29T01:37:25Z',
#        'channelId': 'UCYbDZUX3iSB_5E7u0JLPBqw',
#        'title': 'Fahri Reza Live Stream',
#        'description': '',
#        'thumbnails': {'default': {'url': 'https://i.ytimg.com/vi/SUPnT7-1Lqs/default_live.jpg', 'width': 120, 'height': 90}, 'medium': {'url': 'https://i.ytimg.com/vi/SUPnT7-1Lqs/mqdefault_live.jpg', 'width': 320, 'height': 180}, 'high': {'url': 'https://i.ytimg.com/vi/SUPnT7-1Lqs/hqdefault_live.jpg', 'width': 480, 'height': 360}, 'standard': {'url': 'https://i.ytimg.com/vi/SUPnT7-1Lqs/sddefault_live.jpg', 'width': 640, 'height': 480}},
#        'actualStartTime': '2022-03-29T01:38:56Z',
#        'isDefaultBroadcast': False,
#        'liveChatId': 'KicKGFVDWWJEWlVYM2lTQl81RTd1MEpMUEJxdxILU1VQblQ3LTFMcXM'
#      },
#      'status': {
#        'lifeCycleStatus': 'live',
#        'privacyStatus': 'public',
#        'recordingStatus': 'recording',
#        'madeForKids': False,
#        'selfDeclaredMadeForKids': False
#      }
#    }
#  ]
#}
            for item in broadcasts:
                if item['status']['lifeCycleStatus'] == 'live':
                    _id = item['snippet']['liveChatId']
                    self.youtube_livechat_id = _id
                    return _id
        return None


    async def really_fetch_youtube_livechat_messages(self):
        if self.is_testing:
            await self.testing_fetch_youtube_livechat_messages()
            return

        if not self.google_auth:
            return

        async with Aiogoogle(client_creds=self.google_client_creds,
                user_creds=self.google_auth) as gapi:
            youtube = await gapi.discover('youtube', 'v3')

            liveChatId = self.youtube_livechat_id or\
                    await self.get_livechat_id(youtube, gapi)
            if liveChatId:
                await self.fetch_next_youtube_livechat_messages(liveChatId,
                        youtube, gapi)

        self.youtube_chat_worker = None
        self.youtube_chat_fetch_timestamp = datetime.now()


    async def fetch_next_youtube_livechat_messages(self, liveChatId, youtube,
            gapi):
        request = youtube.liveChatMessages.list(
                liveChatId=liveChatId,
                part=['snippet', 'authorDetails'],
                maxResults=self.page_size,
                pageToken=self.youtube_livechat_pagetoken)
        try:
            response = await gapi.as_user(request)
        except HTTPError:
            self.reset()
            return

        chat_items = response['items']
        # some are already added to self.youtube_chat_messages
        next_items = chat_items[self.youtube_livechat_pageindex:]
        if not next_items:
            return
        _logger.debug(response)
        self.dump_data(response)
# Example:
#{
#  'kind': 'youtube#liveChatMessageListResponse',
#  'etag': 'genxwM2yB2k-krEymvr1-MtB2bc',
#  'pollingIntervalMillis': 1048,
#  'pageInfo': {'totalResults': 2, 'resultsPerPage': 2},
#  'nextPageToken': 'GKjZyZyw9vYCIIausaCw9vYC',
#  'items': [
#    {
#      'kind': 'youtube#liveChatMessage',
#      'etag': 'NQlu6DKmARbOeJJcD5FqNk-hsFI',
#      'id': 'LCC.CikqJwoYVUNZYkRaVVgzaVNCXzVFN3UwSkxQQnF3EgtjbnBTQmVKdjA1WRI5ChpDSnVVcEp1dzl2WUNGYUFBclFZZHEyWU55dxIbQ1BEdThwMnY5dllDRmNoQ25Ra2RFZ1FGcWcw',
#      'snippet': {
#        'type': 'textMessageEvent',
#        'liveChatId': 'KicKGFVDWWJEWlVYM2lTQl81RTd1MEpMUEJxdxILY25wU0JlSnYwNVk',
#        'authorChannelId': 'UCYbDZUX3iSB_5E7u0JLPBqw',
#        'publishedAt': '2022-04-02T21:59:46.397785+00:00',
#        'hasDisplayContent': True,
#        'displayMessage': 'testing',
#        'textMessageDetails': {'messageText': 'testing'}
#      },
#      'authorDetails': {
#        'channelId': 'UCYbDZUX3iSB_5E7u0JLPBqw',
#        'channelUrl': 'http://www.youtube.com/channel/UCYbDZUX3iSB_5E7u0JLPBqw',
#        'displayName': 'Fireh',
#        'profileImageUrl': 'https://yt3.ggpht.com/6ltej2RcUdNFDoE0fKJrg1rtluKHOdVXJzTf2D76Gqs4zg7JCVm-vMKUimY64fF1T53yz6Qr=s88-c-k-c0x00ffffff-no-rj',
#        'isVerified': False,
#        'isChatOwner': True,
#        'isChatSponsor': False,
#        'isChatModerator': False
#      }
#    },
#    {
#      'kind': 'youtube#liveChatMessage',
#      'etag': 'JvQgIu5yIP9ZJ528byi6yr4q6HI',
#      'id': 'LCC.CikqJwoYVUNZYkRaVVgzaVNCXzVFN3UwSkxQQnF3EgtjbnBTQmVKdjA1WRI5ChpDTWJZeVp5dzl2WUNGU1VxclFZZC1NNEdmQRIbQ1BEdThwMnY5dllDRmNoQ25Ra2RFZ1FGcWcx',
#      'snippet': {
#        'type': 'textMessageEvent',
#        'liveChatId': 'KicKGFVDWWJEWlVYM2lTQl81RTd1MEpMUEJxdxILY25wU0JlSnYwNVk',
#        'authorChannelId': 'UCYbDZUX3iSB_5E7u0JLPBqw',
#        'publishedAt': '2022-04-02T21:59:49.109928+00:00',
#        'hasDisplayContent': True,
#        'displayMessage': 'nyahalo',
#        'textMessageDetails': {'messageText': 'nyahalo'}
#      },
#      'authorDetails': {
#        'channelId': 'UCYbDZUX3iSB_5E7u0JLPBqw',
#        'channelUrl': 'http://www.youtube.com/channel/UCYbDZUX3iSB_5E7u0JLPBqw',
#        'displayName': 'Fireh',
#        'profileImageUrl': 'https://yt3.ggpht.com/6ltej2RcUdNFDoE0fKJrg1rtluKHOdVXJzTf2D76Gqs4zg7JCVm-vMKUimY64fF1T53yz6Qr=s88-c-k-c0x00ffffff-no-rj',
#        'isVerified': False,
#        'isChatOwner': True,
#        'isChatSponsor': False,
#        'isChatModerator': False
#      }
#    }
#  ]
#}
        for item in next_items:
            item['snippet']['publishedAt'] = date_parse(
                    item['snippet']['publishedAt'])
            self.youtube_chat_messages.append(item)
            self.youtube_livechat_pageindex += 1

        if len(chat_items) == self.page_size:
            self.youtube_livechat_pagetoken = response['nextPageToken']
            self.youtube_livechat_pageindex = 0
