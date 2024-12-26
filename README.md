<div align="center">
  
# ~ _lextrail_ ~
<img src="https://github.com/user-attachments/assets/5e941295-09f2-43e3-8084-70ae54fc23e2" alt="Parser" width=400></img>

_A RegEx/CFG parser designed specifically for guided generation._

</div>

## Installation

``` bash
pip install lextrail
```

## Syntax

The provided standard is **ISO/IEC 14977**, but with a flavor.

### Delimiters

| Usage | Notation | Meaning |
|----------|----------|----------|
| Grouping | ( ... ) | |
| Optional | \[ ... ] | none or once |
| Repetition | { ... } | none or more |

### Symbols

| Usage | Notation |
|----------|----------|
| Terminal | `"<alphanumeric_terminal_name>"` |
| Non-Terminal | `<alphanumeric_non_terminal_name>` |
| RegEx | `regex("<regex_expression>")` |

### Example

```python    
    r"""start: expression
    
    expression: term (("+" | "-") term)

    term: factor (("*" | "/") factor)

    factor: NUMBER

    NUMBER: /-?[0-9]+/"""
```

## Features
### Skipping rule
```python    
    r"""a {b} c"""
```

<div align="center"> <img src="https://github.com/user-attachments/assets/0a11de9e-a528-474f-a26a-5be98f131818" alt="skipping_rule" width=500></img> </div>

We see that `factor` is connected to `"-"`.

### Dealing with infinite loops 
We separate infinite loops into two types, escapable infinite loops and non-escapable loops. A warning is emitted for escapable ones, while an exception is thrown for the non-escapable ones.
##### Escapable loops
```python    
    r"""
    start: expression

    expression: term (("+" | "-") term)

    term: factor {("*" | "/") term factor}

    factor: NUMBER

    NUMBER: /-?[0-9]+/
    """
```
The above is an escapable loop, if we look at `term: factor {("*" | "/") term factor}`, we observe that there an escape through `{} (NONE_ANY)` construct.

```python    
    r"""
    start: expression

    expression: term [expression ("+" | "-") term]

    term: factor (("*" | "/") factor)

    factor: NUMBER

    NUMBER: /-?[0-9]+/
    """
```
Another example with an escapable loop in `expression: term [expression ("+" | "-") term]` but with an escape through `[] (NONE_ONCE)` construct.

##### Non-escapable loops
```python    
    r"""
    start: expression

    expression: term expression (("+" | "-") term)

    term: factor (("*" | "/") factor)

    factor: NUMBER

    NUMBER: /-?[0-9]+/
    """
```
This an example of a non-escapable loop, we'll have to go through `expression` each time in `expression: term expression (("+" | "-") term)`

## Comparison to other libraries
Let's compare both `lextrail` and `outlines`.
### Run-time

### Memory usage


## Simulation

You can make simulations like these, the one below is sampling the next token with a uniform distribution.

```python
    from lextrail.render.simulate import simulate_cfg_guide

    cfg_example = r"""
    start: expression

    expression: term expression (("+" | "-") term)

    term: factor (("*" | "/") factor)

    factor: NUMBER

    NUMBER: /-?[0-9]+/
    """

    simulate_cfg_guide(cfg_example)    
```

![animation](https://github.com/user-attachments/assets/71c18134-6c77-4778-9d17-12439af31a45)





