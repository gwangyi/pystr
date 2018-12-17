"""This module provides integer field functionality of struct"""
import enum
import typing
from . import _ext
from .struct import Struct


class Endian(str, enum.Enum):
    """Define available endians for :class:`IntField`"""
    Big = 'be'
    Little = 'le'
    Native = 'h'


class IntFieldDesc(typing.NamedTuple):
    """Descriptor of integer field property"""
    offset: int
    """Byte offset of field"""
    width: int = 8
    """Base bit width of field

    Must be one of 8, 16, 32, 64
    """
    endian: Endian = Endian.Native
    """Endian of field"""
    bit: typing.Union[None, int, typing.Tuple[int, int]] = None
    """Bit offset of field

    If bit is None or missing, the field uses all bits.
    If bit is an integer, the field uses specified bit only.
    If bit is (msb, lsb), the field uses msb to lsb (inclusive)
    """
    doc: typing.Optional[str] = None
    """Docstring for this field"""


_GetterSetter = typing.Tuple[
    typing.Callable[[Struct], typing.Any],
    typing.Callable[[Struct, typing.Any], None]
]

@Struct.register_field(int)
class IntField(property):
    """Integer field property descriptor class

    :param desc: IntField description
    :type desc: IntFieldDesc
    """
    @staticmethod
    def _init_sb(desc: IntFieldDesc,
                 field_type: typing.Callable[[int], typing.Any]) -> _GetterSetter:
        offset, _, _, bit, _ = desc
        if bit is None:
            def getter(struct: Struct) -> typing.Any:
                return field_type(struct.buffer[offset])

            def setter(struct: Struct, val: typing.Any) -> None:
                struct.buffer[offset] = int(val)
        else:
            if not isinstance(bit, tuple):
                bit_ = (bit, bit)
            else:
                bit_ = bit

            get_field = _ext.lib.get_field8_partial  #pylint: disable=c-extension-no-member
            set_field = _ext.lib.set_field8_partial  #pylint: disable=c-extension-no-member

            def getter(struct: Struct) -> typing.Any:
                return field_type(get_field(struct.buffer, offset, *bit_))

            def setter(struct: Struct, val: typing.Any) -> None:
                set_field(struct.buffer, int(val), offset, *bit_)

        return getter, setter

    @staticmethod
    def _init_mb(desc: IntFieldDesc,
                 field_type: typing.Callable[[int], typing.Any]) -> _GetterSetter:
        offset, width, endian, bit, _ = desc
        try:
            get_field = getattr(_ext.lib, 'get_{}_field{}{}'.format(
                endian, width, '' if bit is None else '_partial'))
            set_field = getattr(_ext.lib, 'set_{}_field{}{}'.format(
                endian, width, '' if bit is None else '_partial'))
        except AttributeError:
            raise NotImplementedError(
                "Field width {} and endian {} is not supported".format(width, endian))

        if bit is None:
            def getter(struct: Struct) -> typing.Any:
                return field_type(get_field(struct.buffer, offset))

            def setter(struct: Struct, val: typing.Any) -> None:
                set_field(struct.buffer, int(val), offset)
        else:
            if not isinstance(bit, tuple):
                bit_ = (bit, bit)
            else:
                bit_ = bit

            def getter(struct: Struct) -> typing.Any:
                return field_type(get_field(struct.buffer, offset, *bit_))

            def setter(struct: Struct, val: typing.Any) -> None:
                set_field(struct.buffer, int(val), offset, *bit_)

        return getter, setter

    def __init__(self,
                 desc: typing.Union[typing.Dict[str, typing.Any], IntFieldDesc],
                 field_type: typing.Callable[[int], typing.Any] = int):
        if isinstance(desc, dict):
            desc = IntFieldDesc(**desc)
        offset, width, _, _, doc = desc
        if width == 8:
            getter, setter = self._init_sb(desc, field_type)
        elif width in (16, 32, 64):
            getter, setter = self._init_mb(desc, field_type)
        else:
            raise NotImplementedError("Field width {} is not supported".format(width))

        super().__init__(getter, setter, doc=doc)
        self._end_of_field = offset + width // 8
