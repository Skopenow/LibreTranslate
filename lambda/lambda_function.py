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
args.threads = -1
args.batch_limit = -1

app = create_app(args)
app.config["SESSION_FILE_DIR"] = "/tmp"
client = app.test_client()

def handler(event, context):
    route = ""
    data = {}

    if "rawPath" in event:
        route = event['rawPath']
        data = json.loads(event['body'])

    if "route" in event:
        route = event['route']

    if "data" in event:
        data = event['data']

    if route == "":
        return {
          "error": "Invalid request: missing route parameter",
          "request": event
        }

    if data == {}:
        return {
          "error": "Invalid request: missing data parameter",
          "request": event
        }

    response = client.post(route, data=json.dumps(data), content_type='application/json')

    return response.data

if __name__ == "__main__":
    print(handler({"route": "/translate", "data":{"q": "bonjour","source": "fr","target": "en","format": "text","api_key": "Q5OayeSDEmxdxE4WVTqmVaAI2va3FVNT69bZM-Vgk-8tD20"}}, {}))
