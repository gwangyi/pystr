"""
pystr str_field tests
"""

def test_str_field():
    "Test string field creation"
    from pystr import Struct
    from pystr.str_field import StrFieldDesc

    class SimpleStruct(Struct):
        "A struct with several str field"
        _layout_ = dict(
            first=dict(
                offset=0,
                size=4,
            ),
            second=dict(
                offset=4,
                size=4,
                encoding='latin1',
            ),
            third=StrFieldDesc(
                offset=8,
                size=4,
                terminator=""
            )
        )
        first: str
        second: str
        third: str

    target = SimpleStruct(b'wow\0\x80xxxa\0b\0')
    assert target.first == 'wow'
    assert target.second == '\x80xxx'
    assert target.third == 'a\0b\0'

    target.third = 'asdf'
    target.second = '\x90yyyy'
    target.first = 'zzz'
    assert bytes(target.buffer) == b'zzz\0\x90yyyasdf'
