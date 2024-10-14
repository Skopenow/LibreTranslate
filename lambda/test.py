import os
os.environ["TEST_MODE"] = "1"
os.environ["DEBUG_MODE"] = "1"
os.environ["D_OPENSEARCH_HOST"] = "https://search-grid-vns6gxthsisbmvi6eajqf47cfa.us-west-2.es.amazonaws.com:443"
os.environ["D_OPENSEARCH_PASS"] = "5qv%_k!pE6"
os.environ["D_OPENSEARCH_USER"] = "root"
os.environ["D_GRID_SOCKET_SERVER_URL"] = "https://grid-socket.dev.skopenow.com/"

from lambda_function import *

#print(handler({"route": "/translate", "data":{"q": "bonjour","source": "fr","target": "en","format": "text","api_key": "Q5OayeSDEmxdxE4WVTqmVaAI2va3FVNT69bZM-Vgk-8tD20"}}, {}))
print(handler({
    "route": "/translate",
    "data":
        {
            "q": [
                "<name_en>title1</name_en><description_en>description1<tht0 id=\"@channel\"></tht0></description_en><refid id=\"1\"></refid>"
            ],
            "source": "fr",
            "target": "en",
            "format": "text",
            "api_key": "Q5OayeSDEmxdxE4WVTqmVaAI2va3FVNT69bZM-Vgk-8tD20",

            "meta": {
                "stage_version": "D",
                "publish_to_socket": 1,
                "update_opensearch": 1,

                "entries": [
                    {
                        "source_id": 75,
                        "source_type": 4,
                        "key": "a29cb4c0f85ad962c58342ffbe9774db",
                        "attributes": {
                            "main":[
                                "ai_severity",
                                "ai_risk_type",
                                "ai_severity_id",
                                "ai_risk_type_id",
                                "extra",
                                "translated",
                                "description_en",
                                "title_en",
                                "name_en",
                                "translated_data",
                                "translated_searchable_keywords"
                            ],
                            "bookmarks":[
                                "ai_severity",
                                "ai_risk_type",
                                "ai_severity_id",
                                "ai_risk_type_id",
                                "extra",
                                "translated",
                                "description_en",
                                "title_en",
                                "name_en",
                                "translated_data",
                                "translated_searchable_keywords"],
                            "alert_hits":[
                                "translated",
                                "description_en",
                                "title_en",
                                "name_en"
                            ]
                        }
                    }
                ]
            }
        }
    },{}))