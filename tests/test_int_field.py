"""
pystr int_field tests
"""
from pytest import raises


def test_int_field():
    "Test integer field creation"
    from pystr import Struct
    from pystr.int_field import IntFieldDesc

    class SimpleStruct(Struct):
        "A struct with several integer field"
        _layout_ = dict(
            first=dict(
                offset=0,
            ),
            second=dict(
                offset=1,
                width=8,
            ),
            third=dict(
                offset=2,
                width=16,
                endian='le'
            ),
            fourth=IntFieldDesc(4, 32, endian='be'),
        )
        first: int
        second: int
        third: int
        fourth: int

    target = SimpleStruct(bytes((1, 2, 3, 4, 5, 6, 7, 8)))
    assert target.first == 1
    assert target.second == 2
    assert target.third == 0x0403
    assert target.fourth == 0x05060708

    target.first = 9
    target.second = 10
    target.third = 0x0c0b
    target.fourth = 0x0d0e0f10

    assert bytes(target.buffer) == bytes((9, 10, 11, 12, 13, 14, 15, 16))

def test_int_field_bitfield():
    "Test bit field"
    from pystr import Struct

    class BitFieldStruct(Struct):
        "A struct with bitfield"
        _layout_ = dict(
            first=dict(
                offset=0,
                bit=(6, 1)
            ),
            second=dict(
                offset=1,
                bit=5
            ),
            third=dict(
                offset=2,
                width=16,
                bit=(14, 1)
            ),
            fourth=dict(
                offset=4,
                width=16,
                bit=9
            )
        )
        first: int
        second: bool
        third: int
        fourth: bool

    target = BitFieldStruct(bytes((0xff, 0xff, 0xff, 0xff, 0xff, 0xff)))
    assert target.first == 0x3f and target.second is True
    assert target.third == 0x3fff and target.fourth is True

    target.first = 0
    target.second = False
    target.third = 0xaaaa
    target.fourth = False
    assert bytes(target.buffer) == b'\x81\xdf\x55\xd5\xff\xfd'

def test_int_field_invalid_endian():
    "Test when invalid parameters are given"
    from pystr import Struct

    with raises(NotImplementedError):
        class ErrorEndianStruct(Struct):
            "A struct with invalid endian"
            _layout_ = dict(
                second=dict(
                    offset=0,
                    width=16,
                    endian="pdp"
                ),
            )
            second: int

        ErrorEndianStruct()

    with raises(NotImplementedError):
        class ErrorWidthStruct(Struct):
            "A struct with invalid field width"
            _layout_ = dict(
                first=dict(
                    offset=0,
                    width=13,
                ),
            )
            first: int

        ErrorWidthStruct()
