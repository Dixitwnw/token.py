#!/usr/bin/env python3

"""Obtain a Facebook Access Token
From: https://github.com/dequis/purple-facebook/issues/445#issuecomment-967542766
Changes:
- Ported to Python3
- Auto generate the MACHINE_ID UUID
- Can set EMAIL from environment variable
USAGE:
    FBEMAIL=<YOUR_EMAIL> python3 fb_get_token.py
If you have 2FA, it will ask for the 2FA code after you type in password.
"""

from optparse import OptionParser
from urllib.parse import urlencode
from uuid import uuid1
import cgi
import getpass
import hashlib
import http.client
import json
import sys
import os
import urllib.request, urllib.parse, urllib.error
import argparse

DEBUG = False
MACHINE_ID = str(uuid1())
# put your email in here
EMAIL = os.environ.get('FBEMAIL', None)

# Don't change these two.
FB_API_KEY = '256002347743983'
FB_API_SECRET = '374e60f8b9bb6b8cbb30f78030438895'


def fb_sig(data):
    newdata = data.copy()
    params = ''.join(['%s=%s' % x for x in sorted(data.items())])
    newdata['sig'] = hashlib.md5((params + FB_API_SECRET).encode('utf-8')).hexdigest()
    return newdata

def debug(msg):
    global DEBUG
    if DEBUG:
        print(("DEBUG: %s", msg))

if not EMAIL:
    print("ERROR: set an email address, please")
    sys.exit()

if MACHINE_ID == '':
    print("ERROR: set a machine id (to any UUID), please")
    sys.exit()

parser = OptionParser()
parser.add_option('-d', '--debug', action='store_true', dest='debug', default=False)
(options, args) = parser.parse_args()

if options.debug:
    DEBUG = True

data = {
    "fb_api_req_friendly_name": "authenticate",
    "locale": "en",
    "format": "json",
    "api_key": FB_API_KEY,
    "method": "auth.login",
    "generate_session_cookies": "1",
    "generate_machine_id": "1",
    "email": EMAIL,
    "device_id": MACHINE_ID,
}
data['password'] = getpass.getpass()

headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "*/*"}
conn = http.client.HTTPSConnection('b-api.facebook.com:443')
params = urllib.parse.urlencode(fb_sig(data))
conn.request('POST', '/method/auth.login', params, headers)
response = conn.getresponse()
debug("status, reason: %s, %s" % (response.status, response.reason))
response_data = response.read()
debug("undecoded response: %s" % response_data)
response = json.loads(response_data)
debug(response)
error_data = json.loads(response['error_data'])
first_fac = error_data['login_first_factor']

data['credentials_type'] = 'two_factor'
data['error_detail_type'] = 'button_with_disabled'
data['first_factor'] = first_fac
data['twofactor_code'] = getpass.getpass('Code: ')
data['password'] = data['twofactor_code']
data['userid'] = error_data['uid']
data['machine_id'] = error_data['machine_id']

params = urllib.parse.urlencode(fb_sig(data))
conn.request('POST', '/method/auth.login', params, headers)
response = conn.getresponse()
debug("status, reason: %s, %s" % (response.status, response.reason))
response_data = response.read()
debug("undecoded response: %s" % response_data)
response = json.loads(response_data)
print(response)
