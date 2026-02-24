<div align="center">

![download](https://github.com/user-attachments/assets/2488f342-3351-4dbf-8c12-08077ba33a2f)

_A Python library for constraining language model outputs to follow CFG, REGEX and JSON (experimental)._

</div>

## Features

- Zero dependencies
- Parses all context-free grammars, including ambiguous grammars
- Returns tokens constrained to a specified vocabulary if needed
- Type annotations with `mypy`
- Includes a Rust [implementation](https://github.com/miftahmoha/lextrail-rs)

## Quick Start

### Installation

``` bash
pip install lextrail
```

## Usage Modes

The library supports two ways to generate constrained text, depending on your use case:

### Trail

Use a **Trail** object when you want to generate the complete next element without vocabulary constraints.


**CFG**

```python
from lextrail.guide import trail_cfg

example = r"""
    start: expression

    expression: term (("+" | "-") term)

    term: factor (("*" | "/") factor)

    factor: NUMBER

    NUMBER: /-?[0-9]+/
"""

trail = trail_cfg(example)
```

**Regex**

```python
from lextrail.guide import trail_rex

example = r"[a-z]+@[a-z]+\.(com|org|net)"

trail = trail_rex(example)
```

You can also combine both TERMINAL and REGEX expressions using `trail_exp`.

```python
from lextrail.guide import trail_exp

example = r"/[0-9]\.[0-9]/ "+" /[0-9]\.[0-9]/"

trail = trail_exp(example)
```

**JSON**

_This is an experimental version. Not intended for production use._

- Currently supported keywords: `type`, `enum`, `const`, `properties`, `required`, `items`, `prefixItems`, `oneOf`
- Constraint intersection (e.g., combining `prefixItems` with `items`, or `const` with `enum`) is not yet implemented

```python
from lextrail.json import trail_json

example = r"""
    {
        "type": "object",
        "properties": {
            "user": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "email": {"type": "string"}
                },
                "required": ["email"]
            }
        }
    }
"""

trail = trail_json(example)
```

Then, run a random simulation.

```python
import random

from lextrail.guide import get_next_values

response, value = [], ""

while values := get_next_values(trail, value):
    value = random.choice(values)
    response.append(value)

print("".join(response))
```

_You can pretty-print JSON output using `lextrail.json.format_json_instance`._

### ASM

Use an **ASM** object when you need to constrain the next token to a predefined vocabulary.

#### Example

```python
from lextrail.assemble import asm_cfg

example = r"""
    start: L0

    L0: ("A" | "B")+ L1

    L1: ("C" | "D") L2

    L2: "E" L3*

    L3: /FGH/
"""

asm = asm_cfg(example, ["AD", "EF", "GH"])
```

If you launch a simulation, then the proposals will be elements of the provided vocabulary.

```python
import random

from lextrail.assemble import get_next_tokens

response, value = [], ""

while values := get_next_tokens(asm, value):
    value = random.choice(values)
    response.append(value)

print("".join(response))

assert response == ["AD", "EF", "GH", ""]
```

You can do it with any of the formats.

```python
# CFG
from lextrail.assemble import asm_cfg

asm_cfg(.., [..])

# REGEX
from lextrail.assemble import asm_rex

asm_rex(.., [..])

# MIXED
from lextrail.assemble import asm_exp

asm_exp(.., [..])

# JSON
from lextrail.json import asm_json

asm_json(.., [..])
```

## Playground

I've built a playground to showcase the different simulations, you can use either a `Trail` object or an `ASM` one.

```python
from lextrail.guide import trail_cfg
from lextrail.playground import run_playground

example = r"""
    start:  expression

    expression: term* (( "+" | "-") term)+

    term: factor* (("*" | "/") factor)+

    factor: NUMBER?

    NUMBER: /[0-1]+/
"""

trail = trail_cfg(example)

run_playground(trail)
```
