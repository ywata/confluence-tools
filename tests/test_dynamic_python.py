from dataclasses import make_dataclass, field, dataclass
def test_make_dataclass_():
    D = make_dataclass('D',['a',('b', str),('c', list, field(default_factory=lambda:['abc']))])

    return

def test_make_dataclass_2():
    E = make_dataclass('D', ['a','b',('c', list, field(default_factory=lambda:[]))])

    return


def test_make_dataclass_3():
    try:
        E = make_dataclass('D', [('a', dict, field(default_factory=lambda:{'x':'z'}))])
    except Exception as ex:
        assert False, "using default_factory should be OK"
    return

def test_make_dataclass_with_inheritance():
    @dataclass()
    class base:
        base_data: int = 1
    @dataclass()
    class ext(base):
        ext_data: str = "str"

    e = ext()
    try:
        f = make_dataclass("ext2", [('ext2_data',str, field(default=None))],bases=(base,))
        f1 = f()
        f2 = f(2)
        f3 = f(3, "str")
        f4 = f("str", 4)
        pass
    except Exception as ex:
        pass

    return

def test_make_dataclass_order():
    @dataclass()
    class c:
        a : int
        b : str
    try:
        c1 = c(1,2)
        pass
    except Exception as e:
        pass

    return