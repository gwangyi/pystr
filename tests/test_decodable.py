"""
pystr decodable test
"""

def test_decodable():
    "Test decodable"
    from pystr import Decodable

    class BaseStruct(Decodable):
        "Base decodable struct"
        _layout_ = dict(
            first=dict(
                offset=0
            ),
            second=dict(
                offset=1
            ),
        )

        first: int
        second: int

    class FirstStruct(BaseStruct):
        "First decodable struct"
        first = 1

    class SecondStruct(BaseStruct):
        "Second decodable struct"
        first = 2

    class ThirdStruct(SecondStruct):
        "Third decodable struct"
        second = 1

    base = BaseStruct()
    assert type(base.decode()) is BaseStruct  #pylint: disable=unidiomatic-typecheck
    base.first = 1
    assert type(base.decode()) is FirstStruct  #pylint: disable=unidiomatic-typecheck
    base.first = 2
    assert type(base.decode()) is SecondStruct  #pylint: disable=unidiomatic-typecheck
    base.second = 1
    assert type(base.decode()) is ThirdStruct  #pylint: disable=unidiomatic-typecheck
