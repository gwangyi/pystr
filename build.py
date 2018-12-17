"""
CFFI Module Building Script
"""

import sys
from cffi import FFI


ffi = FFI()  #pylint: disable=invalid-name
if sys.byteorder == 'big':
    SWAP = 'le'
    NOSWAP = 'be'
elif sys.byteorder == 'little':
    SWAP = 'be'
    NOSWAP = 'le'
else:
    raise NotImplementedError("Byte order {} is not supported".format(repr(sys.byteorder)))

ENDIAN = ''.join([
    '#define _{f}to{t}{b}(x) __builtin_bswap{b}(x)\n'.format(f=f, t=t, b=b)
    for b in (16, 32, 64) for f, t in (('h', SWAP), (SWAP, 'h'))
] + [
    '#define _{}to{}{}(x) (x)\n'.format(f, t, b)
    for b in (16, 32, 64) for f, t in (('h', NOSWAP), (NOSWAP, 'h'), ('h', 'h'))
])

FIELD = ''.join([
    '#define get_{ed}_field{b}(ptr, offset) '
    '_{ed}toh{b}(*(uint{b}_t *)(((uint8_t *)(ptr)) + (offset)))\n'
    '#define get_{ed}_field{b}_partial(ptr, offset, msb, lsb) '
    '((get_{ed}_field{b}(ptr, offset) & ((1 << ((msb) + 1)) - 1)) >> (lsb))\n'
    '#define set_{ed}_field{b}(ptr, value, offset) '
    '(*(uint{b}_t *)(((uint8_t *)(ptr)) + (offset)) = _hto{ed}{b}(value))\n'
    '#define set_{ed}_field{b}_partial(ptr, value, offset, msb, lsb) '
    'set_{ed}_field{b}(ptr, '
    '(get_{ed}_field{b}(ptr, offset) & ~mask(msb, lsb)) |'
    '(((value) << (lsb)) & ((1 << ((msb) + 1)) - 1)), '
    'offset)\n'.format(ed=ed, b=b)
    for ed in ('le', 'be', 'h')
    for b in (16, 32, 64)
] + [
    '#define get_field8_partial(ptr, offset, msb, lsb)'
    '((((uint8_t *)(ptr))[offset] & ((1 << ((msb) + 1)) - 1)) >> (lsb))\n'
    '#define set_field8_partial(ptr, value, offset, msb, lsb)'
    '(((uint8_t *)(ptr))[offset] ='
    '(((uint8_t *)(ptr))[offset] & ~mask(msb, lsb)) |'
    '(((value) << (lsb)) & ((1 << ((msb) + 1)) - 1)))\n'
])

ffi.set_source('pystr._ext', r'''
#include <stdint.h>
#include <malloc.h>
#define mask(msb, lsb) (((1 << ((msb) + 1)) - 1) & ~((1 << (lsb)) - 1))
''' + ENDIAN + FIELD + r'''
void * aligned_malloc(size_t alignment, size_t size) {
    uint8_t * ptr = (uint8_t *)malloc(size + alignment + sizeof(void *));
    if(!ptr) return NULL;
    size_t offset = alignment - (ptr + alignment + sizeof(void *) - ((uint8_t *)0)) % alignment;
    void ** ret = (void **)(ptr + offset);
    ret[0] = ptr;
    return (void *)(ret + 1);
}
void aligned_free(void * ptr) {
    free(((void **)ptr)[-1]);
}
''')

ffi.cdef('\n'.join((
    'uint{b}_t get_{ed}_field{b}(void *, size_t);\n'
    'uint{b}_t get_{ed}_field{b}_partial(void *, size_t, size_t, size_t);\n'
    'void set_{ed}_field{b}(void *, uint{b}_t, size_t);\n'
    'void set_{ed}_field{b}_partial(void *, uint{b}_t, size_t, size_t, size_t);'.format(ed=ed, b=b)
    for ed in ('le', 'be', 'h')
    for b in (16, 32, 64)
)))
ffi.cdef(r'''
uint8_t get_field8_partial(void *, size_t, size_t, size_t);
void set_field8_partial(void *, uint8_t, size_t, size_t, size_t);
void * aligned_malloc(size_t, size_t);
void aligned_free(void *);
''')

if __name__ == '__main__':
    ffi.compile(verbose=True)

