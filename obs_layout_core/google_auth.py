from aiogoogle import Aiogoogle
from aiogoogle.auth.utils import create_secret
import asyncio
import logging
import os
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse
from starlette.responses import RedirectResponse
from starlette.routing import Route

_logger = logging.getLogger(__name__)


class GoogleAuth:

    google_auth_redirect = '/controller'

    def __init__(self):
        self.google_client_creds = {
            'client_id': os.environ['GOOGLE_CLIENT_ID'],
            'client_secret': os.environ['GOOGLE_CLIENT_SECRET'],
            'scopes': [
                'https://www.googleapis.com/auth/youtube.readonly',
            ],
            'redirect_uri': 'http://localhost:8282/google/oauth_callback',
        }

        self.google_auth = None
# Example:
#{
#  'access_token': 'ya29.A0ARrdaM9lYRmPYCx4ApkuV65zgDbH0ZctCxdQP84mvBDK7aSMkALzHWDWOOM-Dn-geh7L7Fiosx7bcAFEHRNDKBL4FjZ03fRU5UFh34sENX2BN2j1zZyDTWI-LKfz39e8Ek0XdMraRl-5Thv7ox9-M6s15pse',
#  'refresh_token': '1//0gemk3lA-jUOgCgYIARAAGBASNwF-L9IrFdnkhLrtKni7Yxcma1-KBQ55ZkyAGS63zF_YApzA3wgACx-nz_WFsjHeSq493-5AJz8',
#  'expires_in': 3599,
#  'expires_at': '2022-03-29T16:21:16.623700',
#  'scopes': [
#    'https://www.googleapis.com/auth/userinfo.profile',
#    'https://www.googleapis.com/auth/youtube.readonly',
#    'https://www.googleapis.com/auth/userinfo.email',
#    'openid'],
#  'id_token': 'eyJhbGciOiJSUzI1NiIsImtpZCI6IjU4YjQyOTY2MmRiMDc4NmYyZWZlZmUxM2MxZWIxMmEyOGRjNDQyZDAiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20iLCJhenAiOiI5OTQ3NTkyNzc4MjUtMG1jcmJndjI2bDAzbTI2ZXQ1YmhicjVkbTBuN2RiYWUuYXBwcy5nb29nbGV1c2VyY29udGVudC5jb20iLCJhdWQiOiI5OTQ3NTkyNzc4MjUtMG1jcmJndjI2bDAzbTI2ZXQ1YmhicjVkbTBuN2RiYWUuYXBwcy5nb29nbGV1c2VyY29udGVudC5jb20iLCJzdWIiOiIxMDc0NDQxMjI5NzA5MDQwNDk5NzgiLCJlbWFpbCI6ImRvenltb2VAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImF0X2hhc2giOiJBeDl2djB4dHhYNXRZRzc4U1pmc1R3IiwibmFtZSI6IkZhaHJpIFJlemEiLCJwaWN0dXJlIjoiaHR0cHM6Ly9saDMuZ29vZ2xldXNlcmNvbnRlbnQuY29tL2EtL0FPaDE0R2ozWVVxTGhmajgzOFV1NkllVExTVkhqU3FGbmFIZjdvVDJPaWFIPXM5Ni1jIiwiZ2l2ZW5fbmFtZSI6IkZhaHJpIiwiZmFtaWx5X25hbWUiOiJSZXphIiwibG9jYWxlIjoiZW4tR0IiLCJpYXQiOjE2NDg1Njc0MDcsImV4cCI6MTY0ODU3MTAwN30.M_Rd6_WV2PyD2o4q1sUgzYcBuASSgvHozm0DaIuhQC1hecQZL0wccwyYPtrdSclZORauNYSDkWlgruC783R_ITfwymaoLttPzsC--J6Vw6mUPoCM-ike3zmNXBvINvVcTdC1DF-eDDZ_h4PynZFbvjGk1DnaOleJRIHNTTmliW8HE958B4fQXa3EOH6d7yJviadhnhKvN-DY9DGWl49IJZB-RUSBQbo8LcwwRCBQoXLGyt8uDAfwsywbDa1h5b8gfQDSd6NLafXyIjLx5DtTsJQ7pMo60Kr4uRRihUvIUmQ6hkRqXwv9zRHUr-E_vYV2EoIMOuMjgmBcAAAsasTklA',
#  'id_token_jwt': None,
#  'token_type': 'Bearer',
#  'token_uri': 'https://oauth2.googleapis.com/token',
#  'token_info_uri': 'https://www.googleapis.com/oauth2/v4/tokeninfo',
#  'revoke_uri': 'https://oauth2.googleapis.com/revoke'
#}


    def check_google_auth(self):
        if not self.google_auth:
            raise HTTPException(302, "Redirect to google authorization",
                    headers={'Location': '/google/authorize'})


    def initialize(self):
        self.app.router.routes.append(Route('/google/authorize',
                endpoint=self.google_authorize))
        self.app.router.routes.append(Route('/google/oauth_callback',
                endpoint=self.google_oauth_callback))


    def destroy(self):
        # So subclass won't throw error on super().destroy()
        pass


    def google_authorize(self, request):
        gapi = Aiogoogle(client_creds=self.google_client_creds)
        if gapi.oauth2.is_ready(self.google_client_creds):
            url = gapi.oauth2.authorization_url(
                    client_creds=self.google_client_creds,
                    state=create_secret(),
                    access_type='offline',
                    include_granted_scopes=True,
                    prompt="select_account")
            return RedirectResponse(url=url)
        else:
            raise HTTPException(500, "Client doesn't have enough info for Oauth2")


    async def google_oauth_callback(self, request):
        if request.query_params.get('error'):
            error = {
                'error': request.query_params['error'],
                'error_description': request.query_params['error_description'],
            }
            return JSONResponse(error)
        elif request.query_params.get('code'):
            gapi = Aiogoogle(client_creds=self.google_client_creds)
            self.google_auth = await gapi.oauth2.build_user_creds(
                    grant=request.query_params['code'],
                    client_creds=self.google_client_creds)
            _logger.debug(self.google_auth)
            await self.google_oauth_callback_success(request)
            return RedirectResponse(url=self.google_auth_redirect)

        raise HTTPException(500,
                "Something is probably wrong with your callback")


    async def google_oauth_callback_success(self, request):
        pass
