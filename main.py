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

from confluence.content import get_tag_category, Independent, DependOn, Subordinate, grouping, update_tree, \
    create_fake_root, create_body
from confluence.net import post, put, multi_get


def parse_args():
    top_parser = argparse.ArgumentParser()
    top_parser.add_argument('--yaml', help='email and token', type=str, required=True)
    cmd_parser = top_parser.add_subparsers(dest='command')
    copy_page_parser = cmd_parser.add_parser('copy-page', help='copy page on confluence')
    copy_page_parser.add_argument('--space', help='space name', required=True)
    copy_page_parser.add_argument('--from', dest='frm', help='page to be copied from', required=True)
    copy_page_parser.add_argument('--into', help='page to be copied int0', required=True)
    copy_page_parser.add_argument('--title-format', help='page title', required=True)

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



def copy_page(url, src_page, to_page, new_title):
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
    return res


def find_page_by_path(url, top_pages, page_path):
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
            res = multi_get(page_children_url, auth, 2)
            if res:
                return find_page_by_path(url, res['results'], "/".join(rest))
            else:
                return None
    return None

def get_page_by_id(url, auth, page_id, repeat = 1)-> Optional[dict]:
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
            return resp
        else:
            count = count - 1
            time.sleep(1000)
    return None


def update_page(url, auth, page_id, transform, new_title):
    resp = get_page_by_id(url, auth, page_id)

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
    return response2




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

    if args.command == "copy-page":
        try:
            space_name = args.space
            res = multi_get(space_url, auth, 2)
            res2 = list(filter(lambda dic: dic['name'] == space_name, res['results']))
            if len(res2) != 1:
                sys.exit(f"multiple {space_name} found")
            space_key = res2[0]['key']
            space_root_pages_url = f"{url}/wiki/rest/api/space/{space_key}/content/page?depth=root&expand=children.page.page"
            res3 = multi_get(space_root_pages_url, auth, 2)
            src_page = find_page_by_path(url, res3['results'], args.frm)
            to_page = find_page_by_path(url, res3['results'], args.into)

            new_title = now.strftime(args.title_format)
            res5 = copy_page(url, src_page, to_page, new_title)
            print(res5)
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
