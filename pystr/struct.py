"""Struct facility"""
import typing
import functools
from . import _ext


class StructFieldDesc(typing.NamedTuple):
    """Struct field description"""
    offset: int
    """Byte offset of struct field"""
    size: typing.Optional[int] = None
    """Field size

    If not specified, the size of field is same as given Struct
    """
    doc: typing.Optional[str] = None
    """docstring"""


class StructField(property):
    """Struct field descriptor

    :param desc: Description of this field

        This parameter can be both of dictionary and :class:`StructFieldDesc`.
        If desc is a dictionary, it is treated as keyword arguments of constructor
        of :class:`StructFieldDesc`.
    :param field_type: Type of this field
    """

    def __init__(self,
                 desc: typing.Union[typing.Dict[str, typing.Any], StructFieldDesc],
                 field_type: typing.Optional[typing.Any] = None) -> None:
        if isinstance(desc, dict):
            desc = StructFieldDesc(**desc)
        offset, size, doc = desc
        self.offset = offset

        if field_type is None:
            raise TypeError("Field type is missing")
        self.type = field_type

        if size is None:
            self.size = field_type.size()
        else:
            self.size = size
        if self.size < self.type.size():
            raise ValueError("Struct field for {} must be at least {}".format(
                self.type.__name__, self.type.size()
            ))

        self.name = ""
        self._end_of_field = self.offset + self.size

        def getter(struct: 'Struct') -> typing.Any:
            if self.name in struct.__dict__:
                return struct.__dict__[self.name]
            obj = self.type(ref=struct.buffer[self.offset:self.offset + self.size])
            struct.__dict__[self.name] = obj
            return obj
        super().__init__(getter, doc=doc)

    def __set_name__(self, owner: typing.Type['Struct'], name: str) -> None:
        self.name = name


FieldPropType = typing.TypeVar('FieldPropType')


class Struct:
    """Struct class

    Base struct class that can

    * allocate C memory with/without memory alignment
    * automatically create field with layout specification and type annotation
    * give initial value of fields

    >>> class MyCommand(Struct):
    ...     _layout_ = dict(
    ...         opcode=dict(
    ...             offset=0
    ...         ),
    ...         force=dict(
    ...             offset=1,
    ...             bit=0
    ...         ),
    ...         lba=dict(
    ...             offset=2,
    ...             width=64,
    ...             endian='be'
    ...         )
    ...     )
    ...     opcode: int
    ...     force: bool
    ...     lba: int

    +-------+--------+-----------------------------------+---+---+---+---+---+---+---+---+
    |  Byte | 0      | 1                                 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
    +-------+--------+---+---+---+---+---+---+---+-------+---+---+---+---+---+---+---+---+
    |  bit  |        | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0     |                               |
    +-------+--------+---+---+---+---+---+---+---+-------+-------------------------------+
    | Field | opcode |                           | force | lba (with big endian)         |
    +-------+--------+---------------------------+-------+-------------------------------+
    """
    _size_: int = 0
    _alignment_: int = 0
    _fields_: typing.Set[str] = set()
    _layout_: typing.Dict[str, typing.Any] = {}

    _initial: typing.Dict[str, typing.Any] = {}
    _field_map: typing.Dict[type, typing.Any] = {}

    __annotations__: typing.Dict[str, type]

    buffer: typing.Any
    allocator: typing.Callable[[str, int], typing.Any]

    @classmethod
    def register_field(cls, field_type: type) -> typing.Callable[[FieldPropType], FieldPropType]:
        """Register field property descriptor to given type

        :param field_type: Type of field
            Struct will find field property descriptor class by given field type in _layout_
            attribute
        """
        def deco(prop_type: FieldPropType) -> FieldPropType:
            cls._field_map[field_type] = prop_type
            return prop_type

        return deco

    @classmethod
    def size(cls) -> int:
        """Return minimum size of this struct"""
        return cls._size_

    @classmethod
    def _setup_allocator(cls, alignment: typing.Optional[int]) -> None:
        if alignment is not None:
            cls._alignment_ = alignment
        if cls._alignment_ <= 1:
            allocator = _ext.ffi.new  #pylint: disable=c-extension-no-member
        else:
            allocator = _ext.ffi.new_allocator(  #pylint: disable=c-extension-no-member
                functools.partial(_ext.lib.aligned_malloc, cls._alignment_),  #pylint: disable=c-extension-no-member
                _ext.lib.aligned_free  #pylint: disable=c-extension-no-member
            )
        cls.allocator = allocator

    @classmethod
    def _create_fields(cls, size: typing.Optional[int]) -> None:
        # Create fields
        min_size = 0
        cls._fields_ = set()

        ## Collect field layout and annotation to create field property
        f2p_map = sorted(cls._field_map.items(), key=lambda elem: len(elem[0].mro()))
        for k, val in cls.__dict__.get('_layout_', {}).items():
            if k not in cls.__annotations__:
                raise ValueError("{} is not annotated".format(k))
            atype = cls.__annotations__[k]
            for field_type, prop_type in f2p_map:
                if issubclass(atype, field_type):
                    prop = prop_type(val, field_type=atype)
                    if hasattr(prop, '__set_name__'):
                        prop.__set_name__(cls, k)
                    setattr(cls, k, prop)
                    cls._fields_.add(k)
                    if hasattr(prop, '_end_of_field'):
                        min_size = max(min_size, prop._end_of_field)  #pylint: disable=protected-access
                    break
            else:
                raise ValueError("{} is not registered".format(atype.__name__))

        if size is not None:
            cls._size_ = size
        if cls._size_ == 0:
            cls._size_ = min_size
        if cls._size_ < min_size:
            raise ValueError("Size of {} must be larger then {} bytes".format(
                cls.__name__, min_size
            ))

    @classmethod
    def _collect_initial(cls, initial: typing.Optional[typing.Dict[str, typing.Any]]) -> None:
        old_fields = cls._fields_

        # Collect initial values
        initial_ = {}
        if initial is not None:
            initial_.update(initial)
        initial_.update({k: v for k, v in cls.__dict__.items() if k in old_fields})
        cls._initial = initial_
        # Delete initial value definition
        for k in initial_:
            if k in cls.__dict__:
                delattr(cls, k)

    def __init_subclass__(cls, *,
                          initial: typing.Optional[typing.Dict[str, typing.Any]] = None,
                          alignment: typing.Optional[int] = None,
                          size: typing.Optional[int] = None,
                          **_: typing.Any):
        cls._setup_allocator(alignment)
        cls._collect_initial(initial)
        cls._create_fields(size)

        # Collect all fields
        cls._fields_ = {
            k
            for cls in cls.mro() if issubclass(cls, Struct)
            for k in typing.cast(typing.Type[Struct], cls)._fields_  #pylint: disable=protected-access
        }

    def __init__(self,
                 init: typing.Optional[typing.Any] = None,
                 ref: typing.Optional[typing.Any] = None,
                 size: typing.Optional[int] = None):
        if ref:
            if isinstance(ref, Struct):
                self.buffer = ref.buffer
            else:
                self.buffer = ref
        elif size is not None and size < self._size_:
            raise ValueError("Size must be at least {}".format(self._size_))
        else:
            self.buffer = type(self).allocator('uint8_t[]', self._size_ if size is None else size)

        if init is not None:
            _ext.ffi.memmove(self.buffer, init, len(init))  #pylint: disable=c-extension-no-member

        for cls in reversed(type(self).mro()):
            if not issubclass(cls, Struct):
                continue
            for k, val in typing.cast(typing.Type[Struct], cls)._initial.items():  #pylint: disable=protected-access
                obj = self
                terms = k.split('.')
                for term in terms[:-1]:
                    obj = getattr(obj, term)
                setattr(obj, terms[-1], val)

    def __repr__(self) -> str:
        return "{}({})".format(
            type(self).__name__,
            ', '.join('{}={}'.format(k, repr(getattr(self, k))) for k in self._fields_)
        )

Struct.register_field(Struct)(StructField)
