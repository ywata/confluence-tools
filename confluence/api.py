import datetime
import json
import logging
import time
import urllib
from typing import Optional

import requests

from confluence.content import create_fake_root, create_body
from confluence.net import get, multi_get, put, post, multi_get_v2

def get_space(url, auth):
    space_url = f"{url}/wiki/rest/api/space?"
    (sc, res) = multi_get_v2(space_url, auth, 20)
    return (sc, res)
def get_page_by_title(url, auth, space, title):
    space_ = urllib.parse.quote(space)
    title_ = urllib.parse.quote(title)
    # TODO: expand parameter should be supplied by an argument.
    get_url = f"{url}/wiki/rest/api/content?spaceKey={space_}&title={title_}&expand=version.number"
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
    page_children_url = f"{url}/wiki/api/v2/pages/{page_id}/children?"
    (sc, res) = multi_get_v2(page_children_url, auth, 20)
    if sc == 200:
        return res['results']
    else:
        logging.error("get_children failed")
        return []


def get_top_pages(url, auth, space_key):
    space_root_pages_url = f"{url}/wiki/rest/api/space/{space_key}/content/page?depth=root&expand=children.page.page"
    res = multi_get(space_root_pages_url, auth, 20)
    return res


def rename_page(url, auth, src_page, new_title):
    rename_page_url = f"{url}/wiki/rest/api/content/{src_page['id']}"
    payload = json.dumps({
        "version": {
            "number": src_page['version']['number'] + 1
        },

        "title": new_title,
        "type": "page",
        "status": "current"
    })
    res = put(rename_page_url, auth, payload)
    return (res.status_code, json.loads(res.text))


def copy_page(url, auth, src_page, to_page, new_title) -> (int, dict):
    copy_page_url = f"{url}/wiki/rest/api/content/{src_page['id']}/pagehierarchy/copy"
    prefix = "copy-"
    payload = json.dumps({
        "copyAttachments": True,
        "copyPermissions": True,
        "copyProperties": True,
        "copyLabels": True,
        "copyCustomContents": True,
        "copyDescendants": True,
        "destinationPageId": f"{to_page['id']}",
        "titleOptions": {
            "prefix": f"{prefix}",
            "replace": f"",
            "search": ""
        }
    })

    res = post(copy_page_url, auth, payload)
    return (res.status_code, json.loads(res.text), prefix+src_page['title'])


def update_page(url, auth, page_id, transform, new_title)->(int, dict):
    (status_code, resp) = get_page_by_id(url, auth, page_id)
    if status_code != 200:
        return (status_code, resp)

    update_page_url = f"{url}/wiki/rest/api/content/{page_id}"
    curr_body = resp['body']
    # As ElementTree doesn't allow us to use undefined xmlns,
    # create a fake xml tree using dummy name space seems required.
    dic = {"ac": "https://example.com/ac", "ri":"http://example.com/ri"}
    root = create_fake_root(curr_body['storage']['value'], dic)
    transformed_root = transform(root)
    transformed_body = create_body(curr_body, transformed_root, dic)
    payload2 = json.dumps({
        "version": {
            "number": resp['version']['number'] + 1,
        },
        "body": transformed_body,
        "title": new_title,
        "type": "page",
        "status": "current"
    })
    response2 = put(update_page_url, auth, payload2)
    return (response2.status_code, json.loads(response2.text))


def get_long_running_task_by_id(url, auth, task_id) -> (int, dict):
    get_url = f"{url}/wiki/rest/api/longtask/{task_id}"
    res = get(get_url, auth)
    return (res.status_code, json.loads(res.text))


def find_page_by_path(url, auth, top_pages, components)->Optional[dict]:
    if components == []:
        return None
    curr_comp = components[0]
    rest = components[1:]
    curr_page = None
    curr_dt = datetime.datetime.min #initial value is the minimum
    # find a top level page with the newest datetime.
    for page in top_pages:
        title = page['title']
        (interpreted_comp, dt) = interpret_as_datetime(title, curr_comp)
        logging.debug(f"{title} {curr_comp} {interpreted_comp}")
        if title == interpreted_comp and curr_dt < dt:
            # Newesst date gets higher priority
            curr_dt = dt
            curr_page = page
            if curr_dt == datetime.datetime.max:
                break

    # There is no matched page against curr_comp, you don't have to
    # recursively call this function again.
    if curr_page is None:
        return None
    # We are end of the component
    if  rest == []:
        return curr_page

    children = get_children(url, auth, curr_page['id'])
    return find_page_by_path(url, auth, children, rest)


def interpret_as_datetime(title, fmt):

    if title == fmt:
        # Exact same title gets maximum priority.
        return (title, datetime.datetime.max)
    else:
        try:
            dt = datetime.datetime.strptime(title, fmt)
            return (title, dt)
        except ValueError as ex:
            # error case means title does not match agaisnt fmt
            # it means, title get least priority
            return (None, datetime.datetime.min)
