from __future__ import print_function
import httplib2
import os

from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools
from oauth2client.client import SignedJwtAssertionCredentials

client_email = 'account-1@teachers-kiosk.iam.gserviceaccount.com'
with open("client.p12") as f:
  private_key = f.read()

credentials = SignedJwtAssertionCredentials(client_email, private_key,
    'https://www.googleapis.com/auth/drive')
from httplib2 import Http
http_auth = credentials.authorize(Http())

service = discovery.build('drive', 'v2', http=http_auth)
results = service.files().list(maxResults=10).execute()
items = results.get('items', [])
if not items:
    print('No files found.')
else:
    print('Files:')
    for item in items:
        print('{0} ({1})'.format(item['title'], item['id']))




__author__ = 'gaurav'
