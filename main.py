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
import logging

from confluence.content import get_tag_category, Independent, DependOn, Subordinate, grouping, update_tree, \
    create_fake_root, create_body
from confluence.net import post, put, multi_get, get


def parse_args():
    top_parser = argparse.ArgumentParser()
    top_parser.add_argument('--yaml', help='email and token', type=str, required=True)
    top_parser.add_argument('--log-level', default="ERROR", choices=["NOTEST", "INFO", "DEBUG", "ERROR", "CRITICAL"], help="TRACE, INFO, DEBUG, ERROR, CRITICAL are available")

    cmd_parser = top_parser.add_subparsers(dest='command')
    daily_update_parser = cmd_parser.add_parser('daily-update', help='copy page on confluence')
    daily_update_parser.add_argument('--space', help='space name', required=True)
    daily_update_parser.add_argument('--from', dest='frm', help='page to be copied from', required=True)
    daily_update_parser.add_argument('--into', help='page to be copied int0', required=True)
    daily_update_parser.add_argument('--title-format', help='page title', required=True)

    update_page_parser = cmd_parser.add_parser('update-page', help='update page ')
    update_page_parser.add_argument('--page-id', help='page-id')

    new_month_parser = cmd_parser.add_parser('new-month', help='prepare for new month')
    new_month_parser.add_argument('--space', help='space name', required=True)
    new_month_parser.add_argument('--from', dest='frm', help='page to be copied from', required=True)
    new_month_parser.add_argument('--title-format', help='page title', required=True)

    args = top_parser.parse_args()

    with open(args.yaml, "r") as f:
        dic = yaml.safe_load(f)
        for k in ["url", "email", "token"]:
            if k in dic['confluence']:
                setattr(args, k, dic['confluence'][k])

    log_dict = {
        "CRITICAL":logging.CRITICAL,
        "ERROR":logging.ERROR,
        "WARN":logging.WARN,
        "DEBUG":logging.DEBUG,
        "INFO":logging.INFO,
        "NOTEST":logging.NOTSET
    }
    if args.log_level in log_dict:
        logging.getLogger().setLevel(log_dict[args.log_level])
    else:
        logging.getLogger().setLevel(logging.INFO)

    return args



def copy_page(url, src_page, to_page, new_title) -> (int, dict):
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
            "prefix": prefix,
            "replace": f"{new_title}",
            "search": ""
        }
    })

    res = post(copy_page_url, auth, payload)
    return (res.status_code, json.loads(res.text), prefix+src_page['title'])

# As newer date should get higher priority, the function
# rturns matched datetime. If title and fmt is same,
# it will get maximum priority.
def interpret_as_datetime(title, fmt):

    if title == fmt:
        # Exact same title gets maximum priority.
        return (title, datetime.datetime.max)
    else:
        try:
            dt = datetime.datetime.strptime(title, fmt)
            return (title, dt)
        except ValueError as ex:
            # error case is the least priority
            return (fmt, datetime.datetime.min)

def get_children(url, auth, page_id):
    # https: // howtoapi.atlassian.net / wiki / rest / api / content / 98400 / child / page
    page_children_url = f"{url}/wiki/rest/api/content/{page_id}/child/page?"
    (sc, res) = multi_get(page_children_url, auth, 2)
    if sc == 200:
        return res['results']
    else:
        logging.error("get_children failed")
        return []

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
        if title == interpreted_comp and curr_dt < dt:
            # Newesst date gets higher priority
            curr_dt = dt
            curr_page = page

    # There is no matched page against curr_comp, you don't have to
    # recursively call this function again.
    if curr_page is None:
        return None
    # We are end of the component
    if  rest == []:
        return curr_page

    children = get_children(url, auth, curr_page['id'])
    return find_page_by_path(url, auth, children, rest)

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
    auth = HTTPBasicAuth(email, token)
    now = datetime.datetime.now()

    if args.command == "daily-update":
        try:
            space_name = args.space
            logging.info("get space name")
            space_url = f"{url}/wiki/rest/api/space?"
            (sc, res) = multi_get(space_url, auth, 2)
            if sc != 200:
                logging.error(f"{space_url} error")
                sys.exit(1)
            res2 = list(filter(lambda dic: dic['name'] == space_name, res['results']))
            if len(res2) != 1:
                logging.error(f"multiple {space_name} found")
                sys.exit(1)

            space_key = res2[0]['key']
            space_root_pages_url = f"{url}/wiki/rest/api/space/{space_key}/content/page?depth=root&expand=children.page.page"
            logging.info(f"get top pages of {space_key}")
            (sc3, res3) = multi_get(space_root_pages_url, auth, 2)
            if sc != 200:
                sys.exit('getting top page error')
            top_pages = res3['results']

            logging.info(f"get page down through {args.frm}")
            src_page = find_page_by_path(url, auth, top_pages, args.frm.split('/'))
            if src_page is None:
                logging.error(f"src page not found:{args.frm}")
                sys.exit(1)

            logging.info(f"get page to be copied in")
            to_page = find_page_by_path(url, auth, top_pages, args.into.split('/'))
            if to_page is None:
                logging.error(f"destination parent not found:{args.into}")
                sys.exit(1)

            new_title = now.strftime(args.title_format)
            logging.info(f"copy page to {new_title}")
            (status_code, res5, dummy_title) = copy_page(url, src_page, to_page, new_title)
            if status_code == 202:
                task_id = res5['id']
                # This might be necessary in some situation.
                #(sc, r6) = get_long_running_task_by_id(url, auth, task_id)
            else:
                logging.error("copy page failed")
                sys.exit(1)
            # TODO: after copy_page() is succeeded, any error can cause to\
            #  leave a temporary file named with dummy_title. It has to be deleted.
            logging.info(f"get id of  {dummy_title}")
            (sc7, r7) = get_page_by_title(url, auth, space_key, dummy_title)
            if sc7 != 200:
                print(sc7, r7)
                logging.error('copied page not found')
                sys.exit(1)
            for p in r7['results']:
                if p['title']== dummy_title:
                    copied_page_id = p['id']
                    logging.info(f"update page as {new_title}")
                    resp = update_page(url, auth, copied_page_id, update_tree, new_title)
        except Exception as ex:
            logging.error(ex)
            sys.exit(1)
    elif args.command == 'update-page':
        try:
            resp = update_page(url, auth, 98793, update_tree, "2023-02-24-xyz")
        except Exception as ex:
            logging.error(f"{ex}")
            sys.exit(1)
    elif args.command == 'new-month':
        sys.exit('not implemented yet')
    else:
        print(f"{args.command} unhandled")
        logging.error(f"{args.command} not handled")
        sys.exit(1)
