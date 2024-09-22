import argparse
import operator
import sys
import json

from libretranslate.main import *
from libretranslate.app import create_app
from libretranslate.default_values import DEFAULT_ARGUMENTS as DEFARGS

args = lambda:None
args.load_only = None
args.update_models = None
args.force_update_models = None
args.url_prefix = ''
args.shared_storage = 'memory://'
args.disable_files_translation = True
args.frontend_language_source = "auto"
args.frontend_language_target = "locale"
args.req_limit = -1
args.api_keys = False
args.daily_req_limit = -1
args.metrics = False
args.req_flood_threshold = -1
args.require_api_key_secret = False
args.debug = True
args.char_limit = -1

app = create_app(args)

client = app.test_client()

def handler(event, context):
    response = client.post("/translate", data=event)

    response_json = json.loads(response.data)

    return response.data