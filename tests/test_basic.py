"""
pystr basic tests
"""
def test_basic():
    "Subclassing Struct test"
    from pystr import Struct

    class EmptyStruct(Struct):
        "Empty struct"

    EmptyStruct()
