from dataclasses import dataclass
from enum import Enum


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


def grouping(lst):
    if len(lst) == 0:
        return []
    # Ugly.
    lst.reverse()
    curr = lst.pop()  # Current group leader
    lst.reverse()
    rest = lst
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
