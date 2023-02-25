import argparse
import requests
from requests.auth import HTTPBasicAuth
import json
import datetime
from xml.etree import ElementTree as ET
import sys
from typing import Optional
import yaml
import time
import urllib

from confluence.content import get_tag_category, Independent, DependOn, Subordinate, grouping, update_tree, \
    create_fake_root, create_body
from confluence.net import post, put, multi_get, get


def parse_args():
    top_parser = argparse.ArgumentParser()
    top_parser.add_argument('--yaml', help='email and token', type=str, required=True)
    cmd_parser = top_parser.add_subparsers(dest='command')
    daily_update_parser = cmd_parser.add_parser('daily-update', help='copy page on confluence')
    daily_update_parser.add_argument('--space', help='space name', required=True)
    daily_update_parser.add_argument('--from', dest='frm', help='page to be copied from', required=True)
    daily_update_parser.add_argument('--into', help='page to be copied int0', required=True)
    daily_update_parser.add_argument('--title-format', help='page title', required=True)

    update_page_parser = cmd_parser.add_parser('update-page', help='update page ')
    update_page_parser.add_argument('--page-id', help='page-id')

    test_ns_parser = cmd_parser.add_parser('test-ns', help='update page ')
    test_ns_parser.add_argument('--page-id', help='page-id')
    args = top_parser.parse_args()

    with open(args.yaml, "r") as f:
        dic = yaml.safe_load(f)
        for k in ["url", "email", "token"]:
            if k in dic['confluence']:
                setattr(args, k, dic['confluence'][k])
    return args



def copy_page(url, src_page, to_page, new_title) -> (int, dict):
    copy_page_url = f"{url}/wiki/rest/api/content/{src_page['id']}/pagehierarchy/copy"
    payload = json.dumps({
        "copyAttachments": True,
        "copyPermissions": True,
        "copyProperties": True,
        "copyLabels": True,
        "copyCustomContents": True,
        "copyDescendants": True,
        "destinationPageId": f"{to_page['id']}",
        "titleOptions": {
            "prefix": "copy ",
            "replace": f"{new_title}",
            "search": ""
        }
    })

    res = post(copy_page_url, auth, payload)
    return (res.status_code, json.loads(res.text))


def find_page_by_path(url, top_pages, page_path)->Optional[dict]:
    assert top_pages != []
    components = page_path.split('/')
    assert components != []
    curr_comp = components[0] # this should be OK because of it's not empty list.
    rest = components[1:]

    for page in top_pages:
        if page['title'] == curr_comp:
            if rest == []:
                return page
            # if we have more components, decent one level more.
            page_id = page['id']
            # https: // howtoapi.atlassian.net / wiki / rest / api / content / 98400 / child / page
            page_children_url = f"{url}/wiki/rest/api/content/{page_id}/child/page?"
            (sc, res) = multi_get(page_children_url, auth, 2)
            if sc == 200:
                return find_page_by_path(url, res['results'], "/".join(rest))
            else:
                return None
    return None

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

def get_page_by_title(url, auth, space, title):
    space_ = urllib.parse.quote(space)
    title_ = urllib.parse.quote(title)
    get_url = f"{url}/wiki/rest/api/content?spaceKey={space_}&title={title_}"
    response = get(get_url, auth)
    return (response.status_code, json.loads(response.text))

def update_page(url, auth, page_id, transform, new_title)->(int, dict):
    (status_code, resp) = get_page_by_id(url, auth, page_id)
    if status_code != 200:
        return (status_code, resp)

    update_page_url = f"{url}/wiki/rest/api/content/{page_id}"
    curr_body = resp['body']
    # As ElementTree doesn't allow us to use undefined xmlns,
    # create a fake xml tree using dummy name space seems required.
    dic = {"ac": "https://example.com/ac"}
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
    get_url = f"{url}wiki/rest/api/longtask/{task_id}"
    res = get(get_url, auth)
    return (res.status_code, json.loads(res.text))


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    args = parse_args()
    url = args.url
    email = args.email
    token = args.token
    contet_url = f"{url}/wiki/rest/api/content?"
    space_url = f"{url}/wiki/rest/api/space?"
    auth = HTTPBasicAuth(email, token)
    now = datetime.datetime.now()

    if args.command == "daily-update":
        try:
            space_name = args.space
            (sc, res) = multi_get(space_url, auth, 2)
            if sc != 200:
                sys.exit(f'{space_url} error')
            res2 = list(filter(lambda dic: dic['name'] == space_name, res['results']))
            if len(res2) != 1:
                sys.exit(f"multiple {space_name} found")
            space_key = res2[0]['key']
            space_root_pages_url = f"{url}/wiki/rest/api/space/{space_key}/content/page?depth=root&expand=children.page.page"
            (sc3, res3) = multi_get(space_root_pages_url, auth, 2)
            if sc != 200:
                sys.exit('getting top page error')
            top_pages = res3['results']
            src_page = find_page_by_path(url, top_pages, args.frm)
            if src_page is None:
                sys.exit(f'src page not found')
            to_page = find_page_by_path(url, top_pages, args.into)
            if to_page is None:
                sys.exit(f'pagent page not found')

            new_title = now.strftime(args.title_format)
            (status_code, res5) = copy_page(url, src_page, to_page, new_title)
            print(res5)
            if status_code == 202:
                task_id = res5['id']
                #(sc, r6) = get_long_running_task_by_id(url, auth, task_id)
                #print(sc, r6)
            else:
                sys.exit('copy failed')
            new_title = "copy 2023-02-23-xyz"
            (sc7, r7) = get_page_by_title(url, auth, space_key, new_title)
            if sc7 != 200:
                print(sc7, r7)
                sys.exit('copied page not found')
            for p in r7['results']:
                if p['title']== new_title:
                    copied_page_id = p['id']
                    resp = update_page(url, auth, copied_page_id, update_tree, "2023-02-04-abc")



        except Exception as ex:
            print(ex)
    elif args.command == 'update-page':
        try:
            resp = update_page(url, auth, 98793, update_tree, "2023-02-24-xyz")
        except Exception as ex:
            print(ex)
            sys.exit('probably parse error')
    elif args.command == 'test-ns':
        page_id = args.page_id
        try:
            get_page_url = f"{url}/wiki/rest/api/content/{page_id}?expand=body.storage,version.number"
            get_headers = {
                "Accept": "application/json"
            }
            response = requests.request(
                "GET",
                get_page_url,
                headers=get_headers,
                auth=auth
            )
            if response.status_code != 200:
                sys.exit('error response')
            resp = json.loads(response.text)
            xml = f"""
            <xml
            xmlns:ac="http://example.com/ac"
            >
            {resp['body']['storage']['value']}
            </xml>
            """
            ET.register_namespace("ac", "http://example.com/ac")
            et = ET.fromstring(xml)

            # ET.indent(et, space=" ", level=1)
            ()
        except Exception as ex:
            print(ex)
            sys.exit('got exception')
