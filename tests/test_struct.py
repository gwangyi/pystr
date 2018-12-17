"""
pystr struct test
"""
from pytest import raises


def test_struct_size():
    "Test size of struct"
    from pystr import Struct

    class SimpleStruct(Struct):
        "Simple struct"
        _layout_ = dict(
            a=dict(
                offset=1,
                width=32
            )
        )

        a: int

    SimpleStruct()
    assert SimpleStruct.size() == 5 and len(SimpleStruct().buffer) == SimpleStruct.size()


def test_alignment():
    "Test memory alignment"
    from pystr import Struct
    from pystr._ext import ffi

    class SimpleStruct(Struct, alignment=4096):
        "Simple Struct"
        _layout_ = dict(
            a=dict(
                offset=0
            )
        )

        a: int

    assert int(ffi.cast('uint64_t', SimpleStruct().buffer)) & 4095 == 0


def test_not_annotated():
    "Test layout and annotation mismatch"
    from pystr import Struct

    with raises(ValueError):
        class ErrorStruct(Struct):
            "Having not annotated field"
            _layout_ = dict(
                a=dict(
                    offset=0
                )
            )

        ErrorStruct()

def test_not_registered():
    "Test not registered annotation"
    from pystr import Struct

    with raises(ValueError):
        class Nothing: #pylint: disable=too-few-public-methods
            "A unregistered class"

        class ErrorStruct(Struct):
            "Having not registered annotation"
            _layout_ = dict(
                a=dict(
                    offset=0
                )
            )

            a: Nothing

        ErrorStruct()

def test_field_without_size():
    "Test field without size"
    from pystr import Struct

    class Nothing: #pylint: disable=too-few-public-methods
        "A unregistered class"

    @Struct.register_field(Nothing)  #pylint: disable=unused-variable
    class NothingProperty(property):
        "Property belongs to Nothing"
        def __init__(self, desc, field_type):  # pylint: disable=unused-argument
            super().__init__(lambda x: desc)

    class SimpleStruct(Struct):
        "Test struct"
        _layout_ = dict(
            a=dict(
                offset=0
            )
        )

        a: Nothing

    assert SimpleStruct.size() == 0

def test_custom_size_struct():
    "Test size-specified structs"
    from pystr import Struct

    with raises(ValueError):
        class TooSmallStruct(Struct, size=1):
            "Specified size is too small"
            _layout_ = dict(
                a=dict(
                    offset=0,
                    width=32
                )
            )
            a: int

        TooSmallStruct()

    class ExcessStruct(Struct, size=10):
        "Specified size is larger than fields"
        _layout_ = dict(
            a=dict(
                offset=0,
                width=32
            )
        )
        a: int

    assert ExcessStruct.size() == 10

    with raises(ValueError):
        ExcessStruct(size=8)

    assert len(ExcessStruct(size=15).buffer) == 15

def test_initial_value():
    "Test struct with initial value"
    from pystr import Struct

    class SubStruct(Struct):
        "Sub struct"
        _layout_ = dict(
            first=dict(
                offset=0
            )
        )
        first: int

    class BaseStruct(Struct):
        "Base struct"
        _layout_ = dict(
            first=dict(
                offset=0
            ),
            second=dict(
                offset=1
            ),
        )
        first: int
        second: SubStruct

    class ChildStruct(BaseStruct):
        "Initial value specified struct"
        first = 1

    class AnotherChildStruct(BaseStruct, initial=dict(first=2)):
        "Another initial value specified struct"

    class YetAnotherChildStruct(BaseStruct, initial={
            'first': 3,
            'second.first': 1
    }):
        "Yet another initial value specified struct"

    assert bytes(ChildStruct().buffer) == b'\x01\0'
    repr_str = repr(ChildStruct())
    assert repr_str.startswith('ChildStruct(') and repr_str.endswith(')')
    assert 'first=1' in repr_str and 'second=SubStruct(first=0)' in repr_str
    assert bytes(AnotherChildStruct().buffer) == b'\x02\0'
    assert bytes(YetAnotherChildStruct().buffer) == b'\x03\x01'

def test_sharing_memory():
    "Test struct sharing memory"
    from pystr import Struct

    class StructA(Struct):
        "Struct A"
        _layout_ = dict(
            first=dict(
                offset=0,
                width=32,
                endian="le"
            )
        )

        first: int

    class StructB(Struct):
        "Struct B"
        _layout_ = dict(
            first=dict(
                offset=0,
                size=4
            )
        )

        first: str

    str_a = StructA()
    str_a.first = 0x30313233
    str_b = StructB(ref=str_a)
    assert str_b.first == "3210"

def test_struct_field():
    "Test StructField"
    from pystr import Struct
    from pystr.struct import StructField, StructFieldDesc

    with raises(TypeError):
        StructField(dict(offset=0))

    class SubStruct(Struct, size=4):
        "Sub struct"

    with raises(ValueError):
        class ErrorStruct(Struct):
            "specified struct size is too small"
            _layout_ = dict(
                first=StructFieldDesc(0, size=1)
            )

            first: SubStruct

        ErrorStruct()

    class TestStruct(Struct):
        "Test target struct"
        _layout_ = dict(
            first=StructFieldDesc(0),
            second=StructFieldDesc(4, size=12)
        )

        first: SubStruct
        second: SubStruct

    target = TestStruct(bytes((0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15)))
    assert bytes(target.first.buffer) == bytes((0, 1, 2, 3))
    assert bytes(target.first.buffer) == bytes((0, 1, 2, 3))  # test caching
    assert bytes(target.second.buffer) == bytes((4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15))
