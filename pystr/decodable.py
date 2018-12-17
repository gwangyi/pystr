r"""This module provides decoding functionality of struct

+-------+--------+-------------------------------+---+---+---+---+---+---+---+---+
|  Byte | 0      | 1                             | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
+-------+--------+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
|  bit  |        | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |                               |
+-------+--------+---+---+---+---+---+---+---+---+-------------------------------+
| Field | opcode |                           |fua| lba (big endian)              |
+-------+--------+---------------------------+---+-------------------------------+

If command block has layout shown as above and there is 5 command as following:

+--------+-----+-------------+
| opcode | fua | Command     |
+--------+-----+-------------+
| 0x00   |  X  | NOP         |
+--------+-----+-------------+
| 0x01   |  0  | Cache Write |
+--------+-----+-------------+
| 0x01   |  1  | Force Write |
+--------+-----+-------------+
| 0x02   |  0  | Cache Read  |
+--------+-----+-------------+
| 0x02   |  1  | Force Read  |
+--------+-----+-------------+

Command classes can be defined as following:

>>> from pystr import Decodable
>>> from enum import IntEnum

>>> class Opcode(IntEnum):
...     Nop = 0
...     Write = 1
...     Read = 2

>>> class BaseCommand(Decodable):
...     _layout_ = dict(
...         opcode=dict(
...             offset=0,
...         ),
...         fua=dict(
...             offset=1,
...             bit=0,
...         ),
...         lba=dict(
...             offset=2,
...             width=64,
...             endian='be'
...         ),
...     )
...     opcode: Opcode
...     fua: bool
...     lba: int

>>> class NopCommand(BaseCommand):
...     opcode = Opcode.Nop

>>> class WriteCommand(BaseCommand):
...     opcode = Opcode.Write

>>> class ReadCommand(BaseCommand):
...     opcode = Opcode.Read

>>> class CacheWriteCommand(WriteCommand):
...     fua = False

>>> class ForceWriteCommand(WriteCommand):
...     fua = True

>>> class CacheReadCommand(ReadCommand):
...     fua = False

>>> class ForceReadCommand(ReadCommand):
...     fua = True

The results of each case are same as following:

>>> print(BaseCommand(b'\0\0\0\0\0\0\0\0').decode())
NopCommand(lba=0, fua=False, opcode=<Opcode.Nop: 0>)
>>> print(BaseCommand(b'\x01\0\0\0\0\0\0\0').decode())
CacheWriteCommand(lba=0, fua=False, opcode=<Opcode.Write: 1>)
>>> print(BaseCommand(b'\x01\x01\0\0\0\0\0\0').decode())
ForceWriteCommand(lba=0, fua=True, opcode=<Opcode.Write: 1>)
>>> print(BaseCommand(b'\x02\0\0\0\0\0\0\0').decode())
CacheReadCommand(lba=0, fua=False, opcode=<Opcode.Read: 2>)
>>> print(BaseCommand(b'\x02\x01\0\0\0\0\0\0').decode())
ForceReadCommand(lba=0, fua=True, opcode=<Opcode.Read: 2>)

If you want to add initial value to sub struct, `initial` parameter can be used.

>>> class SomeDecodable(Decodable):
...     _layout_ = ...
...     child: ChildDecodable
... class DerivedDecodable(SomeDecodable, initial={"child.value": 1}):
...     pass
"""
import typing
from .struct import Struct


DerivedDecodable = typing.TypeVar('DerivedDecodable', bound='Decodable')


class Decodable(Struct):
    """Decoding facility added Struct"""
    _decode_map: typing.List[
        typing.Tuple[
            typing.Dict[str, typing.Any],
            typing.Type['Decodable']
        ]
    ] = []

    def __init_subclass__(cls, **kwargs: typing.Any):  #pylint: disable=arguments-differ
        super().__init_subclass__(**kwargs)
        if cls._initial:
            cls._decode_map.append((cls._initial, cls))
            cls._decode_map = []

    def decode(self: DerivedDecodable) -> DerivedDecodable:
        """Decode struct by derived Decodables"""
        dmap = self._decode_map
        ret_tp = type(self)
        while True:
            for cond, child_tp in reversed(dmap):
                if all(getattr(self, k) == v for k, v in cond.items()):
                    dmap = child_tp._decode_map  #pylint: disable=protected-access
                    ret_tp = typing.cast(typing.Type[DerivedDecodable], child_tp)
                    break
            else:
                return self if ret_tp is type(self) else ret_tp(ref=self.buffer)
