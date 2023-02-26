import json
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

def get(url, auth) -> (int, dict):
    headers = {
        "Accept": "application/json"
    }
    response = requests.request(
        "GET",
        url,
        headers=headers,
        auth=auth
    )
    return response
def multi_get(url, auth, limit)->(int, dict):
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
            return (response.status_code, json.loads(response.text))
    return (200, merge_results(res))


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
    if response.status_code == 200 or response.status_code == 202:
        return response
    else:
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
