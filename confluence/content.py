import copy
import re
import sys
from dataclasses import dataclass
from enum import Enum
from xml.etree import ElementTree as ET
from xml.etree.ElementTree import ParseError


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


def analize_parse_error(re_list, msg, data) -> str:
    for (re_str, processor) in re_list:
        rex = re.compile(re_str)
        matched = re.fullmatch(rex, msg)
        if matched:
            return processor(matched, data)
    return msg


def unbound_prefix_report(matched, data: str):
    line = int(matched.group(1))
    start = int(matched.group(2))
    lines = data.split("\n")
    assert start > 0, "The author expect start to be start from 0."
    return lines[line - 1][start - 1:]


def create_fake_root(value, dic) -> ET.Element:
    xmlns = ""
    for ns in dic.keys():
        ET.register_namespace(ns, dic[ns])
        xmlns += f'''
        xmlns:{ns}="{dic[ns]}"
        '''
    fake_value = f"""
    <!DOCTYPE html [<!ENTITY nbsp "&#160;">]>
    <root {xmlns}>
    {value}
    </root>"""
    try:
        root = ET.fromstring(fake_value)
    except ParseError as ex:
        hint = analize_parse_error(
            [("unbound prefix: line ([0-9]+), column ([0-9]+)", unbound_prefix_report)],
            ex.msg, fake_value)
        print(f"XML parse error near {hint}\n{ex.msg}", file=sys.stderr)
        sys.exit(1)
    except Exception as ex:
        sys.exit(1)
    return root


def create_body(body, root, dic) -> dict:
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


def grouping(lst) -> list[dict]:
    if len(lst) == 0:
        return []
    ls = copy.deepcopy(lst)
    curr = ls[0]
    rest = ls[1:]
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
def daily_job(lss) -> list[dict]:
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


def update_tree(etree) -> ET.Element:
    root = ET.Element("root")
    lst = []
    for e in etree:
        lst.append(e)
    grouped = grouping(lst)
    updated = daily_job(grouped)
    for e in [item for agroup in updated for item in agroup]:
        root.append(e)
    return root
