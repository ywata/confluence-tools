from dataclasses import make_dataclass, field
def test_make_dataclass_():
    D = make_dataclass('D',['a',('b', str),('c', list, field(default_factory=lambda:['abc']))])

    return

def test_make_dataclass_2():
    E = make_dataclass('D', ['a','b',('c', list, field(default_factory=lambda:[]))])

    return