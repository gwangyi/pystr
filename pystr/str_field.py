"""This module provides string field functionality of struct"""
import typing
from .struct import Struct


class StrFieldDesc(typing.NamedTuple):
    """Descriptor of integer field property"""
    offset: int
    """Byte offset of field"""
    size: int
    """Byte length of field"""
    encoding: str = "utf-8"
    """String encoding"""
    terminator: str = "\0"
    """String terminator

    The field returns string cut at character which is specified by any character in terminator.
    If string shorter than size is given, empty space will be filled by first character of
    terminator"""
    doc: typing.Optional[str] = None
    """Docstring of field"""


@Struct.register_field(str)
class StrField(property):
    """String field property descriptor class

    :param desc: StrField description
    :type desc: StrFieldDesc
    """
    def __init__(self,
                 desc: typing.Union[typing.Dict[str, typing.Any], StrFieldDesc],
                 field_type: typing.Callable[[str], typing.Any] = str):
        if isinstance(desc, dict):
            desc = StrFieldDesc(**desc)
        offset, size, encoding, terminator, doc = desc
        def getter(struct: Struct) -> typing.Any:
            ret = bytes(struct.buffer[offset:offset + size]).decode(encoding, errors="replace")
            if terminator:
                ret, *_ = ret.split(terminator, 1)
            return field_type(ret)

        def setter(struct: Struct, val: typing.Any) -> None:
            val_ = str(val).encode(encoding)[:size]
            val_ += bytes(ord(terminator) % 256 for _ in range(size - len(val_)))
            struct.buffer[offset:offset + size] = val_

        super().__init__(getter, setter, doc=doc)
        self._end_of_field = offset + size
