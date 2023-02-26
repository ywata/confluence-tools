import json
import logging
import time
import urllib
from typing import Optional

import requests

from confluence.net import get, multi_get

def get_space(url, auth):
    space_url = f"{url}/wiki/rest/api/space?"
    (sc, res) = multi_get(space_url, auth, 2)
    return (sc, res)
def get_page_by_title(url, auth, space, title):
    space_ = urllib.parse.quote(space)
    title_ = urllib.parse.quote(title)
    get_url = f"{url}/wiki/rest/api/content?spaceKey={space_}&title={title_}"
    response = get(get_url, auth)
    return (response.status_code, json.loads(response.text))


def get_page_by_id(url, auth, page_id, repeat = 1)-> Optional[tuple]:
    get_page_url = f"{url}/wiki/rest/api/content/{page_id}?expand=body.storage,version.number"
    get_headers = {
        "Accept": "application/json"
    }
    count = repeat
    while count > 0:
        response = requests.request(
            "GET",
            get_page_url,
            headers=get_headers,
            auth=auth
        )
        if response.status_code == 200:
            resp = json.loads(response.text)
            return (response.status_code, json.loads(response.text))
        else:
            count = count - 1
            if count == 0:
                return (response.status_code, json.loads(response.text))
            time.sleep(1000)
    return None


def get_children(url, auth, page_id):
    # https: // howtoapi.atlassian.net / wiki / rest / api / content / 98400 / child / page
    page_children_url = f"{url}/wiki/rest/api/content/{page_id}/child/page?"
    (sc, res) = multi_get(page_children_url, auth, 2)
    if sc == 200:
        return res['results']
    else:
        logging.error("get_children failed")
        return []
