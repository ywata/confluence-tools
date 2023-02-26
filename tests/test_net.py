import unittest

from confluence.net import merge_results

def test_merge_result_one():
    res = [{'results':1, 'size': 2, 'limit':3}]
    ret = merge_results(res)

    assert  {'results':1, 'size': 2, 'limit':3} == ret

def test_merge_result_two():
    res = [{'results':1, 'size': 3, 'limit':3}, {'results':2, 'size': 2, 'limit':3}]
    ret = merge_results(res)

    assert  {'results':3, 'size': 5, 'limit':5} == ret

