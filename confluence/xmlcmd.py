import copy
from collections import deque
from dataclasses import dataclass
from xml.etree import ElementPath as EP
from xml.etree import ElementTree as ET


@dataclass
class GetXPath:
    xpath: str


@dataclass
class Copy:
    pass


@dataclass
class Dup:
    pass


@dataclass
class Pop:
    pass


@dataclass
class Push:
    elem: ET.Element


@dataclass
class CallFunction:
    fun: object
    args: object
    conv: object


@dataclass
# Inject data on data_stack into the second node.
class Insert:
    nth: int


@dataclass
class Remove:
    pass


Cmd = GetXPath | Copy | Dup | Insert | Remove | Push | CallFunction


@dataclass
class Node:
    elem: ET.Element


@dataclass
class Null:
    pass


Data = Node | Null


def interp(cmd_stack: deque, data_stack) -> Data:
    if len(cmd_stack) == 0:
        return data_stack
    curr_cmd = cmd_stack.popleft()

    match curr_cmd:
        case GetXPath(xp):
            assert len(data_stack) > 0
            node = data_stack[0]
            match node:
                case Node(elm):
                    r = EP.find(elm, xp)
                    if r is None:
                        data_stack.appendleft(Null())
                    else:
                        data_stack.appendleft(Node(r))
                case _:
                    raise Exception("Invalid node")

        case Copy():
            assert len(data_stack) > 0
            org_node = data_stack.popleft()
            new_node = copy.deepcopy(org_node)
            data_stack.appendleft(new_node)
        case Dup():
            assert len(data_stack) > 0
            org_node = data_stack[0]
            data_stack.appendleft(org_node)
        case Pop():
            assert len(data_stack) > 0
            data_stack.popleft()
        case Remove():
            assert len(data_stack) >= 2
            node = data_stack.popleft()
            top = data_stack[0]
            match node, top:
                case Node(elm), Node(root):
                    root.remove(elm)
                case _, _:
                    raise Exception("Invalid Node")
        case Push(elm):
            data_stack.appendleft(Node(elm))
        case Insert(nth):
            assert nth >= 0
            assert len(data_stack) >= 2
            node = data_stack.popleft()
            top = data_stack[0]
            match node, top:
                case Node(elm), Node(root):
                    root.insert(nth, elm)
                case _, _:
                    raise Exception("Invalid Node")
        case CallFunction(func, args, conv):
            assert func is not None
            res = func(*args)
            if res is not None:
                data_stack.appendleft(Node(conv(res)))
            else:
                data_stack.appendleft(Null)

    res = interp(cmd_stack, data_stack)
    return res


def interpreter(ls: list, root: ET.Element):
    cq = deque(ls)
    dq = deque([Node(root)])
    return interp(cq, dq)
