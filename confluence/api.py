import datetime
import json
import logging
import time
import urllib
from typing import Optional

import requests

from confluence.content import create_fake_root, create_body
from confluence.net import get, multi_get, put, post, multi_get_v2, format_query_parameter


def get_space(url, auth):
    space_url = f"{url}/wiki/api/v2/spaces?"
    (sc, res) = multi_get_v2(space_url, auth, 20)
    return (sc, res)


def get_page_by_title(url, auth, space, title, extra={}):
    extra['spaceKey'] = space
    extra['title'] = title
    get_url = f"{url}/wiki/rest/api/content?"
    response = get(get_url, auth, extra)
    return (response.status_code, json.loads(response.text))

def get_page_by_id(url, auth, page_id):
    request_url = f"{url}/wiki/api/v2/pages/{page_id}?"
    response = get(request_url, auth, {"body-format":"storage"})
    return (response.status_code, json.loads(response.text))

def get_page_version_by_id(url, auth, page_id) -> (int, dict):
    request_url = f"{url}/wiki/api/v2/pages/{page_id}/versions"
    response = get(request_url, auth)
    return (response.status_code, json.loads(response.text))

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
    copy_page_url = f"{url}/wiki/rest/api/content/{src_page['id']}/copy"
    prefix = "copy-"
    payload = json.dumps({
        "copyAttachments": True,
        "copyPermissions": True,
        "copyProperties": True,
        "copyLabels": True,
        "copyCustomContents": True,
        "copyDescendants": True,
        "destination": {
            "type": "parent_page",
            "value": f"{to_page['id']}"
        },
        "pageTitle":f"{new_title}"
    })

    res = post(copy_page_url, auth, payload)
    return (res.status_code, json.loads(res.text))


def update_page(url, auth, page_id, transform, space_id, new_title) -> (int, dict):
    #expand=body.storage,version.number
    (status_code, resp) = get_page_by_id(url, auth, page_id)
    if status_code != 200:
        return (status_code, resp)
    curr_body = resp['body']
    curr_ver = resp['version']['number']

    update_page_url = f"{url}/wiki/api/v2/pages/{page_id}"
    # As ElementTree doesn't allow us to use undefined xmlns,
    # create a fake xml tree using dummy name space seems required.
    dic = {"ac": "https://example.com/ac", "ri": "http://example.com/ri"}
    root = create_fake_root(curr_body['storage']['value'], dic)
    transformed_root = transform(root)
    transformed_body = create_body(curr_body, transformed_root, dic)
    payload2 = json.dumps({
        "id": f"{page_id}",
        "status": "current",
        "title": f"{new_title}",
        "spaceId": f"{space_id}",
        "body": {
            "representation": "storage",
            "value": transformed_body,
        },
        "version": {
            "number": curr_ver + 1
        },
    })
    response2 = put(update_page_url, auth, payload2)
    return (response2.status_code, json.loads(response2.text))


def get_long_running_task_by_id(url, auth, task_id) -> (int, dict):
    get_url = f"{url}/wiki/rest/api/longtask/{task_id}"
    res = get(get_url, auth)
    return (res.status_code, json.loads(res.text))


def find_page_by_path(url, auth, top_pages, components) -> Optional[dict]:
    if components == []:
        return None
    curr_comp = components[0]
    rest = components[1:]
    curr_page = None
    curr_dt = datetime.datetime.min  # initial value is the minimum
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
    if rest == []:
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
