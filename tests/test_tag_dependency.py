import unittest
from xml.etree import ElementTree as ET
from confluence.content import grouping, compare, Ord

def test_no_element():
    res = grouping([])
    assert res == []

def map_map(fun, lss):
    res = []
    for ls in lss:
        rs = list(map(fun, ls))
        res.append(rs)
    return res
def compare_tags(left, right):
    l = map_map(lambda e: e.tag, left)
    r = map_map(lambda e: e.tag, right)
    return l == r

def test_toplevel_p():
    p = ET.Element('p')
    res = grouping([p])
    assert compare(p, res)

def test_h1_h1():
    h1 = ET.Element('h1')
    res = grouping([h1, h1])
    assert compare_tags(res, [[h1],[h1]])

def test_p_h1_p_h1():
    h1 = ET.Element('h1')
    p = ET.Element('p')
    res = grouping([p, h1, p, h1])
    assert compare_tags(res, [[p], [h1,p], [h1]])

def test_h1_h2_h3():
    h1 = ET.Element('h1')
    h2 = ET.Element('h2')
    h3 = ET.Element('h3')
    res = grouping([h1, h2, h3])
    assert compare_tags(res, [[h1, h2, h3]])


def test_compare():
    p = ET.Element('p')
    h1 = ET.Element('h1')
    h2 = ET.Element('h2')
    h3 = ET.Element('h3')
    xy = ET.Element('xy')
    assert compare(p, p) == Ord.EQ
    assert compare("p", "h1") == Ord.LT
    assert compare("h1", "p") == Ord.GT
    assert compare("xy", "p") == Ord.EQ
    assert compare("p", "xy") == Ord.EQ
    assert compare("h1", "h1") == Ord.GT
    assert compare("h1", "h2") == Ord.GT
    assert compare("h2", "h1") == Ord.LT

