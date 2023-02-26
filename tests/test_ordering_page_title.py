import unittest

import confluence.api
import confluence.net
from confluence.api import get_children, find_page_by_path
from unittest.mock import Mock

def test_find_page_by_path_empty_top_page():
    top_pages = []
    components = [""]

    res = find_page_by_path("", "", top_pages, components)
    assert res is None

def test_find_page_by_path_empty_path():
    page = {}
    top_pages = [page]
    components = []
    res = find_page_by_path("", "", top_pages, components)
    assert res is None


def test_find_page_by_path_non_equal():
    page = {'title':"matched"}
    top_pages = [page]
    components = ["matched "]

    res = find_page_by_path("", "", top_pages, components)
    assert res is None

def test_find_page_by_path_non_equal():
    page = {'title':"matched"}
    top_pages = [page]
    components = ["%Y"]

    res = find_page_by_path("", "", top_pages, components)
    assert res is None

def test_find_page_by_path_date_match():
    page = {'title':"2000-01"}
    top_pages = [page]
    components = ["%Y-%m"]

    res = find_page_by_path("", "", top_pages, components)
    assert res == page

def test_find_page_by_path_date_match_multi():
    page1 = {'title': "2000-01"}
    page2 = {'title': "2000-02"}
    top_pages = [page1, page2]
    components = ["%Y-%m"]

    res = find_page_by_path("", "", top_pages, components)
    assert res == page2
def test_find_page_by_path_date_match_exact():
    page1 = {'title': "2000-01"}
    page2 = {'title': "exact"}
    page3 = {'title': "2000-02"}
    top_pages = [page1, page2, page3]
    components = ["exact"]

    res = find_page_by_path("", "", top_pages, components)
    assert res == page2

def test_find_page_by_path_recursive():
    components = ["%Y-%m", "exact"]

    # first call
    page1 = {'title': "2000-01", "id": 1}
    top_pages = [page1]
    # second call
    page2 = {'title':"exact"}
    confluence.api.get_children = Mock(return_value = [page2])
    res = find_page_by_path("", "", top_pages, components)
    assert res == page2
def test_get_children_400():
    confluence.api.multi_get = Mock(return_value = (400, {}))
    res = get_children("url", "auth", 123)
    assert res == []

def test_get_children_200():
    confluence.api.multi_get = Mock(return_value = (200, {'results':["a"]}))
    res = get_children("url", "auth", 123)
    assert res == ["a"]
