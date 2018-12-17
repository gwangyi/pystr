# pystr

Python Struct tool

## Installation

```bash
git clone https://github.com/gwangyi/pystr
python setup.py install
```

## Usage

```python
from pystr import Struct

class BaseCommand(Struct):
    _layout_ = dict(
        opcode=dict(
            offset=0,
        ),
        fua=dict(
            offset=1,
            bit=0,
        ),
        lba=dict(
            offset=2,
            width=64,
            endian='be'
        ),
    )
    opcode: Opcode
    fua: bool
    lba: int
```
