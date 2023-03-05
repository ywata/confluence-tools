import unittest
from confluence.content import analize_parse_error
from confluence.xmlcmd import *
def test_analize_parse_error_empty():
    patterns = []
    res = analize_parse_error([], "msg", "parsed data")
    assert res == "msg"

def test_analize_parse_error_no_match():
    msg = "bound prefix: line 4, column 17"
    rex = "unbound prefix: line ([0-9]+), column ([0-9]+)"
    res = analize_parse_error([(rex, lambda matched, data :  "")], msg, "not used")
    assert res == msg

def test_analize_parse_error_match():
    msg = "unbound prefix: line 4, column 17"
    rex = "unbound prefix: line ([0-9]+), column ([0-9]+)"
    def processor(matched, data):
        return f"{matched.group(1)} {matched.group(2)}"
    res = analize_parse_error([(rex, processor)], msg, "not used")
    assert res == "4 17"

def test_analize_parse_error_use_data():
    msg = "unbound prefix: line 4, column 17"
    rex = "unbound prefix: line ([0-9]+), column ([0-9]+)"
    def processor(matched, data):
        return f"{matched.group(1)} {matched.group(2)}"
    res = analize_parse_error([(rex, lambda _, data: data)], msg, "use data")
    assert res == "use data"

def test_interp_empty_stack():
    xml = """
    <root>
    <h1>text</h1>
    </root>
    """
    root = ET.fromstring(xml)
    res = interpreter([], root)
    assert [*res] == [Node(root)]

def test_interp_get_valid():
    xml = """
    <root>
    <h1>text</h1>
    </root>
    """
    root = ET.fromstring(xml)
    res = interpreter([GetXPath("./h1")], root)
    assert res[0].elem.tag == "h1"

def test_interp_get_invalid():
    xml = """
    <root>
    <h1>text</h1>
    </root>
    """
    root = ET.fromstring(xml)
    res = interpreter([GetXPath("./hx")], root)
    assert [*res] == [Null(), Node(root)]

def test_interp_copy():
    xml = """
    <root>
    <h1>text</h1>
    </root>
    """
    root = ET.fromstring(xml)
    res = interpreter([CopyNode()], root)
    assert res[0].elem.tag == "root"
    assert res[0].elem != root

def test_interp_dup():
    xml = """
    <root>
    <h1>text</h1>
    </root>
    """
    root = ET.fromstring(xml)
    res = interpreter([DupNode()], root)

    assert len(res) == 2
    assert res[1].elem == root
    assert res[0].elem == root


def test_interp_pop():
    xml = """
    <root>
    <h1>text</h1>
    </root>
    """
    root = ET.fromstring(xml)
    res = interpreter([PopNode()], root)
    assert len(res) == 0

def test_interp_remove():
    xml = """
    <root>
    <h1>text1</h1>
    <h1>text2</h1>    
    <hex></hex>
    </root>
    """
    root = ET.fromstring(xml)
    res = interpreter([GetXPath("h1"), Remove()], root)
    h1 = EP.find(root, "h1")
    assert h1.text == "text2"

def test_interp_push():
    xml = """
    <root>
    </root>
    """
    root = ET.fromstring(xml)
    res = interpreter([Push(ET.Element("tag"))], root)
    assert len(res) == 2
    assert res[0].elem.tag == "tag"
def test_interp_insert():
    xml = """
    <root>
    <elem1></elem1>
    <elem2></elem2>
    <elem3></elem3>
    <elem4></elem4>
    </root>
    """
    root = ET.fromstring(xml)
    res = interpreter([Push(ET.Element("tag")), Insert(1)], root)
    assert res[0].elem[1].tag == "tag"

def test_interp_call_function_valid_tuple():
    xml = """
    <root>
    </root>
    """
    root = ET.fromstring(xml)
    def fun(tag1, tag2):
        return tag1 + tag2
    def conv(tag):
        return ET.Element(tag)

    res = interpreter([CallFunction(fun, ("tag1", "tag2"), conv)], root)
    assert res[0].elem.tag == "tag1tag2"

def test_interp_call_function_valid_single():
    xml = """
    <root>
    </root>
    """
    root = ET.fromstring(xml)
    def fun(tag1):
        return tag1
    def conv(tag):
        return ET.Element(tag)
    # This is tricky pattern to pass generic argument for general function to work.
    res = interpreter([CallFunction(fun, ("tag1",), conv), Insert(1)], root)
    assert res[0].elem[0].tag == "tag1"

