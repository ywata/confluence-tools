import unittest
from confluence.content import analize_parse_error
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

