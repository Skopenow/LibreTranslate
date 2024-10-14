import argparse
import operator
import sys
import json
import os
import re
import requests

if os.environ.get("TEST_MODE","0") == "0":
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

if os.environ.get("TEST_MODE","0") == "1":
    from flask import Flask
    app = Flask(__name__)
else:
    app = create_app(args)

app.config["SESSION_FILE_DIR"] = "/tmp"
test_client = app.test_client()

os_clients = {}

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

    if os.environ.get("TEST_MODE","0") == "1":
        translation_result = str.encode(json.dumps({
            "translatedText": [
                "<name_en>Translated Title 1</name_en><description_en>HELLO Translated Description 1 <tht0 id=\"@channel\"></tht0></description_en><refid id=\"1\"></refid>"
            ]
        }))
    else:
        response = test_client.post(route, data=json.dumps(data), content_type='application/json')
        translation_result = response.data

    if os.environ.get("DEBUG_MODE","0") == "1":
        print("Translation result:", translation_result)

    translation_result = str(translation_result,"utf-8")
    translation_result = json.loads(translation_result)

    if ("translatedText" in translation_result and "meta" in data):
        sources_types = {
            1: "grid_event",
            2: "grid_object",
            3: "grid_article",
            4: "grid_post",
        }

        global os_clients
        if os.environ.get(data["meta"]["stage_version"] + "_OPENSEARCH_HOST","") != "":
            try:
                os_client = os_clients[data["meta"]["stage_version"]]
            except:
                from opensearchpy import OpenSearch, helpers
                os_client = os_clients[data["meta"]["stage_version"]] = OpenSearch(
                    hosts=[os.environ[data["meta"]["stage_version"] + '_OPENSEARCH_HOST']],
                    http_auth=(os.environ[data["meta"]["stage_version"] + '_OPENSEARCH_USER'], os.environ[data["meta"]["stage_version"] + '_OPENSEARCH_PASS']),
                    use_ssl=True,
                    verify_certs=True,
                    timeout=300,
                    http_compress=True
                )
        translations = translation_result["translatedText"]
        if (type(translations) == str):
            translations = [translations]

        bulk_query = []
        update_by_query = []
        socket_entries = []

        for entry_index, entry in enumerate(data["meta"]["entries"]):
            translation = translations[entry_index]
            translation = re.sub(r'<refid .+</refid>', '', translation)
            translation = re.sub(r'<tht0 id="', '', translation)
            translation = re.sub(r'"></tht0>', '', translation)

            attributes = {
                "main": {},
                "bookmarks": {},
                "alert_hits": {},
            }
            translated_attributes = {
                "main": {},
                "bookmarks": {},
                "alert_hits": {},
            }
            for attributes_group in entry["attributes"]:
                for attribute in entry["attributes"][attributes_group]:
                    try:
                        attribute_value = re.compile(f'<{attribute}>(.*?)</{attribute}>').search(translation).group(1)
                        attributes[attributes_group][attribute] = attribute_value
                        translated_attributes[attributes_group][attribute.replace("_en","")] = attribute_value
                    except:
                        True

            if (data["meta"]["update_opensearch"]):
                query = {
                    'size': 1,
                    'query': {
                        'terms': {
                            'key': [entry['key']]
                        }
                  }
                }

                translated_searchable_keywords = " ".join(str(x) for x in attributes["main"].values())

                item_response = os_client.search(
                    body = query,
                    index = sources_types[entry['source_type']]
                )

                item_hits_response = os_client.search(
                    body = query,
                    index = "grid_alerts_hits"
                )
                try:
                    item_data = item_response["hits"]["hits"][0]["_source"]
                    record = json.loads(item_data["record"])
                    extra = json.loads(item_data["extra"])

                    record['translated'] = True

                    bookmarks_record = record | attributes["bookmarks"]
                    bookmarks_extra = extra | attributes["bookmarks"]
                    bookmarks_record["extra"] = bookmarks_extra

                    record = record | attributes["main"]
                    extra = extra | attributes["main"]
                    record["extra"] = extra

                    item_hits_data = None
                    try:
                        item_hits_data = item_hits_response["hits"]["hits"][0]["_source"]
                        hits_record = json.loads(item_hits_data["record"])
                        hits_extra = json.loads(item_hits_data["extra"])

                        hits_record['translated'] = True

                        hits_record = hits_record | attributes["alert_hits"]
                        hits_extra = hits_extra | attributes["alert_hits"]
                        hits_record["extra"] = hits_extra
                    except:
                        True

                    bulk_query.append(
                        {
                          "update": {
                            "_index": sources_types[entry['source_type']],
                            "_id": entry['key'],
                          }
                        }
                    )
                    bulk_query.append(
                        {
                          "doc": {
                            "record": json.dumps(record),
                            "extra": json.dumps(extra),
                            "translated": True,
                            "translated_data": translated_attributes["main"],
                            "translated_searchable_keywords": translated_searchable_keywords
                          },
                          "doc_as_upsert": False
                        }
                    )


                    update_by_query.append(
                        {
                        "index": "grid_bookmarks",
                        "body": {
                            "query": {
                              "term": {
                                "key": entry['key']
                              }
                            },
                            "script": {
                              "source": "ctx._source.record = params.record;ctx._source.extra = params.extra;ctx._source.translated = params.translated;ctx._source.translated_data = params.translated_data;ctx._source.translated_searchable_keywords = params.translated_searchable_keywords;",
                              "params": {
                                "record": json.dumps(bookmarks_record),
                                "extra": json.dumps(bookmarks_extra),
                                "translated": True,
                                "translated_data": translated_attributes["bookmarks"],
                                "translated_searchable_keywords": translated_searchable_keywords
                              }
                            }
                          }
                        }
                    )

                    if item_hits_data:
                        update_by_query.append(
                            {
                            "index": "grid_alerts_hits",
                            "body": {
                                "query": {
                                  "term": {
                                    "key": entry['key']
                                  }
                                },
                                "script": {
                                  "source": "ctx._source.record = params.record;ctx._source.extra = params.extra;ctx._source.translated = params.translated;ctx._source.translated_data = params.translated_data;ctx._source.translated_searchable_keywords = params.translated_searchable_keywords;",
                                  "params": {
                                    "record": json.dumps(hits_record),
                                    "extra": json.dumps(hits_extra),
                                    "translated": True,
                                    "translated_data": translated_attributes["alert_hits"],
                                    "translated_searchable_keywords": translated_searchable_keywords
                                  }
                                }
                              }
                            }
                        )
                except Exception as e:
                    raise e
                    print("Search query failed!", e)

            if (data["meta"]["publish_to_socket"]):
                socket_entry = {
                    "key": entry['key'],
                    "source_id": entry['source_id'],
                    "translated": True,
                    "source_type": entry['source_type'],
                }
                for attribute in attributes["main"]:
                    socket_entry[attribute] = attributes["main"][attribute]

                socket_entries.append(socket_entry)


        if bulk_query:
            if os.environ.get("DEBUG_MODE","0") == "1":
                print("Bulk Query:", json.dumps(bulk_query))
            os_response = os_client.bulk(body=bulk_query)
            if os.environ.get("DEBUG_MODE","0") == "1":
                print(os_response)
                print("")

            for os_query in update_by_query:
                if os.environ.get("DEBUG_MODE","0") == "1":
                    print("Update Query:", json.dumps(os_query))
                os_response = os_client.update_by_query(body=os_query["body"],index=os_query["index"])
                if os.environ.get("DEBUG_MODE","0") == "1":
                    print(os_response)
                    print("")

        if socket_entries:
            socket_message = {
                "need_to_push": True,
                "phrases": socket_entries
            }
            url = os.environ[data["meta"]["stage_version"] + '_GRID_SOCKET_SERVER_URL'] + "data-to-all-subs"
            headers = {"Content-Type": "application/json"}
            if os.environ.get("DEBUG_MODE","0") == "1":
                print(url, headers, json.dumps(socket_message, indent=2))
            response = requests.post(url, headers=headers, json=socket_message)

    return translation_result

if __name__ == "__main__":
    print(handler({"route": "/translate", "data":{"q": "bonjour","source": "fr","target": "en","format": "text","api_key": "Q5OayeSDEmxdxE4WVTqmVaAI2va3FVNT69bZM-Vgk-8tD20"}}, {}))
