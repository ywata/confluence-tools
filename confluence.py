import argparse
import requests
from requests.auth import HTTPBasicAuth
import json
import datetime
from xml.etree import ElementTree as ET
import sys
from dataclasses import dataclass
from enum import Enum
import copy
import yaml


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


def merge_results(res):
    assert res != []
    res.reverse()
    ret = res.pop()
    res.reverse()
    for r in res:
        ret['results'] += r['results']
        ret['size'] += r['size']
        ret['limit'] += r['size']
    return ret


def multi_get(url, auth, limit):
    headers = {
        "Accept": "application/json"
    }
    start = 0
    res = []
    while True:
        request_url = f"{url}limit={limit}&start={start}"
        response = requests.request(
            "GET",
            request_url,
            headers=headers,
            auth=auth
        )
        if response.status_code == 200:
            resp = json.loads(response.text)
            size = resp['size']
            if size == 0:
                break
            start = start + size
            res.append(resp)
        else:
            print(response.content)
            break
    return merge_results(res)


def post(url, auth, payload):
    post_headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    response = requests.request(
        "POST",
        url,
        data=payload,
        headers=post_headers,
        auth=auth
    )
    if response.status_code == 200 or response.status_code == 202:
        return response
    else:
        return response


def put(url, auth, payload):
    post_headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    response = requests.request(
        "PUT",
        url,
        data=payload,
        headers=post_headers,
        auth=auth
    )
    if response.status_code == 200 or response.status_code == 202:
        return response
    else:
        return response


def copy_page(url, src_page, to_page, title_format):
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
            "replace": f"{now.strftime(title_format)}",
            "search": ""
        }
    })

    res = post(copy_page_url, auth, payload)
    return res


def find_page_by_path(url, top_pages, page_path):
    assert top_pages != []
    components = page_path.split('/')
    assert components != []
    components.reverse()
    curr_comp = components.pop()
    components.reverse()
    rest = components

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


def create_fake_root(value, dic):
    xmlns = ""
    for ns in dic.keys():
        ET.register_namespace(ns, dic[ns])
        xmlns += f'''
        xmlns:{ns}="{dic[ns]}"
        '''
    fake_value = f"""
    <root {xmlns}>
    {value}
    </root>"""

    root = ET.fromstring(fake_value)
    return root


def create_body(body, root, dic):
    val = ET.tostring(root).decode()

    for ns in dic.keys():
        xmlns = f'xmlns:{ns}={dic[ns]}"'
        val = val.replace(xmlns, "")
    updated_body = {
        "storage": {
            "value": val,
            "representation": body['storage']['representation']
        }
    }
    return updated_body


def update_page(url, auth, page_id, transform, new_title):
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
        return None
    resp = json.loads(response.text)

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


def flatten(etree):
    lst = []
    for e in etree:
        lst.append(e)
    return lst


# Independent tag is always the highest priority.
# The tag marked as Independent becomes the top level group if any.
@dataclass
class Independent:
    pass


# Subordiate tag can be toplevel group but
# if it follows Independent or DependOn tag, it is
# put in the preceding tag.
@dataclass
class Subordinate:
    pass


# DependOn tag can have some ordering restriction if higher order
# tag appears.
# As h2 or h3 can appear even if h1 does not appear,
# h2 or h3 can construct a group.
@dataclass
class DependOn:
    depend: list


TagCategory = Independent | Subordinate | DependOn


class Ord(Enum):
    LT = -1
    EQ = 0
    GT = 1


def get_tag_category(curr_tag) -> TagCategory:
    dependency = [("h1", Independent()), ("h2", DependOn(["h1"])), ("h3", DependOn(["h1", "h2"]))]
    for (t, tg) in dependency:
        if curr_tag == t:
            return tg
    return Subordinate()


# LT : left < right
# EQ : left ~ right
# GT : left > right
def compare(ltag, rtag) -> Ord:
    l = get_tag_category(ltag)
    r = get_tag_category(rtag)
    match (l, r):
        case (Independent(), Independent()):
            return Ord.GT
        case (Independent(), _):
            return Ord.GT
        case (_, Independent()):
            return Ord.LT
        case (Subordinate(), Subordinate()):
            return Ord.EQ
        case (Subordinate(), DependOn(_)):
            return Ord.LT
        case (DependOn(_), Subordinate()):
            return Ord.GT
        case (DependOn(ll), DependOn(rr)):
            if l == r:
                return Ord.EQ
            if l in rr:
                return Ord.GT
            if r in ll:
                return Ord.GT
            # uncomparable case returns EQ so far
            return Ord.EQ
        case _:
            return Ord.EQ


def grouping(lst):
    if len(lst) == 0:
        return []
    # Ugly.
    lst.reverse()
    curr = lst.pop()  # Current group leader
    lst.reverse()
    rest = lst
    res = []
    tmp = [curr]
    for elem in rest:
        match compare(elem.tag, curr.tag):
            case Ord.GT:
                # elem superseeds the current group tag
                res.append(tmp)
                tmp = [elem]
                curr = elem
            case _:
                tmp.append(elem)
    res.append(tmp)
    return res


# remove first h? tag group
# duplicate second h? group
# Keep non h? group as it is.
def daily_job(lss):
    res = list()
    count = 0
    previous_text = ""
    for ls in lss:
        # As the construction assures that at least one element exists in ls.
        assert ls != []
        fst = ls[0]
        tag_category = get_tag_category(fst.tag)
        match tag_category:
            case Independent() | DependOn(_):
                count = count + 1
                if count == 1:
                    previous_text = ls[0].text
                elif count == 2:
                    # duplicate this group
                    ls2 = copy.deepcopy(ls)
                    res.append(ls)
                    if previous_text != "":
                        ls[0].text = previous_text
                    res.append(ls2)
                else:
                    res.append(ls)
            case Subordinate():
                res.append(ls)
    return res


def update_tree(etree):
    root = ET.Element("root")
    lst = []
    for e in etree:
        lst.append(e)
    grouped = grouping(lst)
    updated = daily_job(grouped)
    for e in [item for agroup in updated for item in agroup]:
        root.append(e)
    return root


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
            space_name = "API TEST"
            res = multi_get(space_url, auth, 2)
            res2 = list(filter(lambda dic: dic['name'] == space_name, res['results']))
            if len(res2) != 1:
                sys.exit(f"multiple {space_name} found")
            space_key = res2[0]['key']
            space_root_pages_url = f"{url}/wiki/rest/api/space/{space_key}/content/page?depth=root&expand=children.page.page"
            res3 = multi_get(space_root_pages_url, auth, 2)
            src_page = find_page_by_path(url, res3['results'], args.frm)
            to_page = find_page_by_path(url, res3['results'], args.into)

            res5 = copy_page(url, src_page, to_page, args.title_format)
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
