import json
import urllib
import requests


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

def get(url, auth):
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
