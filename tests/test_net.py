import unittest

from confluence.net import merge_results, format_query_parameter

def test_merge_result_one():
    res = [{'results':1, 'size': 2, 'limit':3}]
    ret = merge_results(res)

    assert  {'results':1, 'size': 2, 'limit':3} == ret

def test_merge_result_two():
    res = [{'results':1, 'size': 3, 'limit':3}, {'results':2, 'size': 2, 'limit':3}]
    ret = merge_results(res)

    assert  {'results':3, 'size': 5, 'limit':5} == ret

def test_query_param_empty():
    qp = {}
    res = format_query_parameter(qp)
    assert res == ""

def test_query_param_one_item():
    qp = {'one':1}
    res = format_query_parameter(qp)
    assert res == "one=1"

def test_query_param_two_items():
    qp = {'one':1, 'two':2}
    res = format_query_parameter(qp)
    assert res == "one=1&two=2"