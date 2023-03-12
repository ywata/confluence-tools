import copy
import json
import re
import urllib
import requests


def merge_results(res) -> dict:
    assert res != []
    ret = res[0]
    for r in res[1:]:
        ret['results'] += r['results']
        ret['size'] += r['size']
        ret['limit'] += r['size']
    return ret


def merge_results_v2(res) -> dict:
    assert res != []
    ret = {}
    ret['results'] = res[0]['results']
    for r in res[1:]:
        ret['results'] += r['results']

    ret['size'] = len(ret['results'])
    ret['limit'] = len(ret['results']) + 1
    return ret


def get(url, auth, extra = {}) -> (int, dict):
    headers = {
        "Accept": "application/json"
    }
    query_param = format_query_parameter(extra)
    request_url = f"{url}{query_param}"
    response = requests.request(
        "GET",
        request_url,
        headers=headers,
        auth=auth
    )
    return response


def multi_get(url, auth, limit, extra = {}) -> (int, dict):
    headers = {
        "Accept": "application/json"
    }
    start = 0
    res = []
    while True:
        extra['limit'] = limit
        extra['start'] = start
        query_param = format_query_parameter(extra)
        request_url = f"{url}{query_param}"
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
            return (response.status_code, json.loads(response.text))
    return (200, merge_results(res))


def parse_link_header(header):
    if header is None:
        return None
    # I only support limited scenario, since I'm not figure out the below page.
    # https://developer.atlassian.com/cloud/confluence/rest/v2/intro/#using
    assert header.count(';') == 1
    assert header.count(',') == 0
    pat = re.compile('<(.+)>; rel="next"')
    matched = pat.fullmatch(header)
    if matched:
        return matched.group(1)
    else:
        # I don't expect this happens
        return None


def multi_get_v2(url, auth, limit, extra = {}) -> (int, dict):
    headers = {
        "Accept": "application/json"
    }
    res = []
    next_link = None
    while True:
        extra2 = copy.copy(extra)
        extra2['limit'] = limit
        if next_link:
            extra2['next'] = next_link
        query_param = format_query_parameter(extra2) # instead of extra
        request_url = f"{url}{query_param}"

        response = requests.request(
            "GET",
            request_url,
            headers=headers,
            auth=auth
        )
        if response.status_code == 200:
            resp = json.loads(response.text)
            res.append(resp)
            next_link = parse_link_header(response.headers.get("link"))
            if next_link is None:
                break
        else:
            return (response.status_code, json.loads(response.text))
    return (200, merge_results_v2(res))


def post(url, auth, payload) -> (int, dict):
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
    return response


def put(url, auth, payload) -> (int, dict):
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

def format_query_parameter(dic):
    res = ""
    tmp = []
    for key in dic:
        tmp.append(f"{key}={dic[key]}")

    return "&".join(tmp)