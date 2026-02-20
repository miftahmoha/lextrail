from lextrail.build import (
    Symbol,
    build_symbol_graph,
    connect_symbol_graph,
    construct_symbol_graph,
)


def test_build_def_XXX01():
    example = """ "(_t0" expression_v0 ")_t0" """

    result = construct_symbol_graph(example.split())
    correct = {symbol.content: symbol for symbol in result.symbols}

    heads = {correct["(_t0"]}
    edges = dict(
        {
            correct["(_t0"]: {correct["expression_v0"]},
            correct["expression_v0"]: {correct[")_t0"]},
        },
    )
    tails = {correct[")_t0"]}

    assert result.heads == heads
    assert result.edges == edges
    assert result.tails == tails


def test_build_def_XXX02():
    example = """ "[0-9]*.[0-9]*_r0" """

    result = construct_symbol_graph(example.split())
    correct = {symbol.content: symbol for symbol in result.symbols}

    heads = {correct["[0-9]*.[0-9]*_r0"]}
    edges: dict[Symbol, list[Symbol]] = dict(
        {
            correct["[0-9]*.[0-9]*_r0"]: set(),
        },
    )
    tails = {correct["[0-9]*.[0-9]*_r0"]}

    assert result.heads == heads
    assert result.edges == edges
    assert result.tails == tails


def test_build_def_XXX03():
    example = (
        """ "(_t0" expression_v0 ")_t0" """,
        """ "[0-9]*.[0-9]*_r0" """,
    )

    result = construct_symbol_graph(example[0].split()), construct_symbol_graph(
        example[1].split()
    )

    connect = connect_symbol_graph(result[0], result[1])
    correct = {symbol.content: symbol for symbol in connect.symbols}

    heads = {correct["(_t0"]}
    edges = dict(
        {
            correct["(_t0"]: {correct["expression_v0"]},
            correct["expression_v0"]: {correct[")_t0"]},
            correct[")_t0"]: {correct["[0-9]*.[0-9]*_r0"]},
        },
    )
    tails = {correct["[0-9]*.[0-9]*_r0"]}

    assert connect.heads == heads
    assert connect.edges == edges
    assert connect.tails == tails


def test_build_def_PXX04():
    example = (
        """ factor_v0 "+_t0" | factor_v1 "-_t0" """,
        """ "(_t0" expression_v0 ")_t0" """,
    )

    result = build_symbol_graph(example[0]), build_symbol_graph(example[1])

    connect = connect_symbol_graph(result[0], result[1])
    correct = {symbol.content: symbol for symbol in connect.symbols}

    heads = {correct["factor_v0"], correct["factor_v1"]}
    edges = dict(
        {
            correct["factor_v0"]: {correct["+_t0"]},
            correct["factor_v1"]: {correct["-_t0"]},
            correct["+_t0"]: {correct["(_t0"]},
            correct["-_t0"]: {correct["(_t0"]},
            correct["(_t0"]: {correct["expression_v0"]},
            correct["expression_v0"]: {correct[")_t0"]},
        },
    )
    tails = {correct[")_t0"]}

    assert connect.heads == heads
    assert connect.edges == edges
    assert connect.tails == tails


def test_build_def_PXX05():
    example = (
        """ factor_v0 "+_t0" | factor_v1 "-_t0" """,
        """ "[0-9]*.[0-9]*_r0" | "-_t1" factor_v2 |  "(_t0" expression_v0 ")_t0" """,
    )

    result = build_symbol_graph(example[0]), build_symbol_graph(example[1])

    connect = connect_symbol_graph(result[0], result[1])
    correct = {symbol.content: symbol for symbol in connect.symbols}

    heads = {correct["factor_v0"], correct["factor_v1"]}
    edges = dict(
        {
            correct["factor_v0"]: {correct["+_t0"]},
            correct["factor_v1"]: {correct["-_t0"]},
            correct["(_t0"]: {correct["expression_v0"]},
            correct["expression_v0"]: {correct[")_t0"]},
            correct["+_t0"]: {
                correct["[0-9]*.[0-9]*_r0"],
                correct["-_t1"],
                correct["(_t0"],
            },
            correct["-_t0"]: {
                correct["[0-9]*.[0-9]*_r0"],
                correct["-_t1"],
                correct["(_t0"],
            },
            correct["-_t1"]: {
                correct["factor_v2"],
            },
        },
    )
    tails = {
        correct["[0-9]*.[0-9]*_r0"],
        correct["factor_v2"],
        correct[")_t0"],
    }

    assert connect.heads == heads
    assert connect.edges == edges
    assert connect.tails == tails


def test_build_def_PXX06():
    example = """ factor_v0 "+_t0" | factor_v1 "-_t0" """

    result = build_symbol_graph(example)
    correct = {symbol.content: symbol for symbol in result.symbols}

    heads = {correct["factor_v0"], correct["factor_v1"]}
    edges = dict(
        {
            correct["factor_v0"]: {correct["+_t0"]},
            correct["factor_v1"]: {correct["-_t0"]},
        },
    )
    tails = {correct["+_t0"], correct["-_t0"]}

    assert result.heads == heads
    assert result.edges == edges
    assert result.tails == tails


def test_build_def_PXX07():
    example = (
        """ "[0-9]*.[0-9]*_r0" | "-_t0" factor_v0 | "(_t0" expression_v0 ")_t0" """
    )

    result = build_symbol_graph(example)
    correct = {symbol.content: symbol for symbol in result.symbols}

    heads = {
        correct["[0-9]*.[0-9]*_r0"],
        correct["-_t0"],
        correct["(_t0"],
    }
    edges = dict(
        {
            correct["[0-9]*.[0-9]*_r0"]: set(),
            correct["-_t0"]: {correct["factor_v0"]},
            correct["(_t0"]: {correct["expression_v0"]},
            correct["expression_v0"]: {correct[")_t0"]},
        },
    )
    tails = {
        correct["[0-9]*.[0-9]*_r0"],
        correct["factor_v0"],
        correct[")_t0"],
    }

    assert result.heads == heads
    assert result.edges == edges
    assert result.tails == tails


# ============================ () ============================


def test_build_def_PXX08():
    example = """ "(_t0" expression_v0 (factor_v0 "-_t0" "[0-9]*.[0-9]*_r0") ")_t0" """

    result = build_symbol_graph(example)
    correct = {symbol.content: symbol for symbol in result.symbols}

    heads = {correct["(_t0"]}
    edges = dict(
        {
            correct["(_t0"]: {correct["expression_v0"]},
            correct["expression_v0"]: {correct["factor_v0"]},
            correct["factor_v0"]: {correct["-_t0"]},
            correct["-_t0"]: {correct["[0-9]*.[0-9]*_r0"]},
            correct["[0-9]*.[0-9]*_r0"]: {correct[")_t0"]},
        },
    )
    tails = {correct[")_t0"]}

    assert result.heads == heads
    assert result.edges == edges
    assert result.tails == tails


def test_build_def_PXX09():
    example = """ "(_t0" expression_v0 (factor_v0 "-_t0" "[0-9]*.[0-9]*_r0" (power_v0 "+_t0") (factor_v1 "*_t0") ("/_t0" number_v0) power_v1) ")_t0" """

    result = build_symbol_graph(example)
    correct = {symbol.content: symbol for symbol in result.symbols}

    heads = {correct["(_t0"]}
    edges = dict(
        {
            correct["(_t0"]: {correct["expression_v0"]},
            correct["expression_v0"]: {correct["factor_v0"]},
            correct["factor_v0"]: {correct["-_t0"]},
            correct["-_t0"]: {correct["[0-9]*.[0-9]*_r0"]},
            correct["[0-9]*.[0-9]*_r0"]: {correct["power_v0"]},
            correct["power_v0"]: {correct["+_t0"]},
            correct["+_t0"]: {correct["factor_v1"]},
            correct["factor_v1"]: {correct["*_t0"]},
            correct["*_t0"]: {correct["/_t0"]},
            correct["/_t0"]: {correct["number_v0"]},
            correct["number_v0"]: {correct["power_v1"]},
            correct["power_v1"]: {correct[")_t0"]},
        },
    )
    tails = {correct[")_t0"]}

    assert result.heads == heads
    assert result.edges == edges
    assert result.tails == tails


def test_build_def_PXX10():
    example = """ "(_t0" expression_v0 (factor_v0 "-_t0" (power_v0 "+_t0") (factor_v1 "*_t0") ("/_t0" number_v0) power_v1 ("/_t1" "[0-9]*.[0-9]*_r0") (factor_v2 "+_t1") expression_v1) ")_t0" """

    result = build_symbol_graph(example)
    correct = {symbol.content: symbol for symbol in result.symbols}

    heads = {correct["(_t0"]}
    edges = dict(
        {
            correct["(_t0"]: {correct["expression_v0"]},
            correct["expression_v0"]: {correct["factor_v0"]},
            correct["factor_v0"]: {correct["-_t0"]},
            correct["-_t0"]: {correct["power_v0"]},
            correct["power_v0"]: {correct["+_t0"]},
            correct["+_t0"]: {correct["factor_v1"]},
            correct["factor_v1"]: {correct["*_t0"]},
            correct["*_t0"]: {correct["/_t0"]},
            correct["/_t0"]: {correct["number_v0"]},
            correct["number_v0"]: {correct["power_v1"]},
            correct["power_v1"]: {correct["/_t1"]},
            correct["/_t1"]: {correct["[0-9]*.[0-9]*_r0"]},
            correct["[0-9]*.[0-9]*_r0"]: {correct["factor_v2"]},
            correct["factor_v2"]: {correct["+_t1"]},
            correct["+_t1"]: {correct["expression_v1"]},
            correct["expression_v1"]: {correct[")_t0"]},
        },
    )
    tails = {correct[")_t0"]}

    assert result.heads == heads
    assert result.edges == edges
    assert result.tails == tails


def test_build_def_PXX11():
    example = (
        """ "(_t0" expression_v0 ((factor_v0 "-_t0") | "[0-9]*.[0-9]*_r0") ")_t0" """
    )

    result = build_symbol_graph(example)
    correct = {symbol.content: symbol for symbol in result.symbols}

    heads = {correct["(_t0"]}
    edges = dict(
        {
            correct["(_t0"]: {correct["expression_v0"]},
            correct["expression_v0"]: {
                correct["factor_v0"],
                correct["[0-9]*.[0-9]*_r0"],
            },
            correct["factor_v0"]: {correct["-_t0"]},
            correct["-_t0"]: {correct[")_t0"]},
            correct["[0-9]*.[0-9]*_r0"]: {correct[")_t0"]},
        },
    )
    tails = {correct[")_t0"]}

    assert result.heads == heads
    assert result.edges == edges
    assert result.tails == tails


def test_build_def_PXX12():
    example = """ "(_t0" expression_v0 ((factor_v0 "-_t0") | "[0-9]*.[0-9]*_r0" "+_t0" factor_v1) ")_t0" """

    result = build_symbol_graph(example)
    correct = {symbol.content: symbol for symbol in result.symbols}

    heads = {correct["(_t0"]}
    edges = dict(
        {
            correct["(_t0"]: {correct["expression_v0"]},
            correct["expression_v0"]: {
                correct["factor_v0"],
                correct["[0-9]*.[0-9]*_r0"],
            },
            correct["factor_v0"]: {correct["-_t0"]},
            correct["-_t0"]: {correct[")_t0"]},
            correct["[0-9]*.[0-9]*_r0"]: {correct["+_t0"]},
            correct["+_t0"]: {correct["factor_v1"]},
            correct["factor_v1"]: {correct[")_t0"]},
        },
    )
    tails = {correct[")_t0"]}

    assert result.heads == heads
    assert result.edges == edges
    assert result.tails == tails


def test_build_def_PXX13():
    example = """ "(_t0" expression_v0 ((factor_v0 "-_t0") | ("[0-9]*.[0-9]*_r0" | "+_t0")) ")_t0" """

    result = build_symbol_graph(example)
    correct = {symbol.content: symbol for symbol in result.symbols}

    heads = {correct["(_t0"]}
    edges = dict(
        {
            correct["(_t0"]: {correct["expression_v0"]},
            correct["expression_v0"]: {
                correct["factor_v0"],
                correct["[0-9]*.[0-9]*_r0"],
                correct["+_t0"],
            },
            correct["factor_v0"]: {correct["-_t0"]},
            correct["-_t0"]: {correct[")_t0"]},
            correct["[0-9]*.[0-9]*_r0"]: {correct[")_t0"]},
            correct["+_t0"]: {correct[")_t0"]},
        },
    )
    tails = {correct[")_t0"]}

    assert result.heads == heads
    assert result.edges == edges
    assert result.tails == tails


def test_build_def_PXX14():
    example = """ "(_t0" expression_v0 ((factor_v0 "-_t0") | ("[0-9]*.[0-9]*_r0" factor_v1 | "+_t0" expression_v1)) ")_t0" """

    result = build_symbol_graph(example)
    correct = {symbol.content: symbol for symbol in result.symbols}

    heads = {correct["(_t0"]}
    edges = dict(
        {
            correct["(_t0"]: {correct["expression_v0"]},
            correct["expression_v0"]: {
                correct["factor_v0"],
                correct["[0-9]*.[0-9]*_r0"],
                correct["+_t0"],
            },
            correct["factor_v0"]: {correct["-_t0"]},
            correct["-_t0"]: {correct[")_t0"]},
            correct["[0-9]*.[0-9]*_r0"]: {correct["factor_v1"]},
            correct["factor_v1"]: {correct[")_t0"]},
            correct["+_t0"]: {correct["expression_v1"]},
            correct["expression_v1"]: {correct[")_t0"]},
        },
    )
    tails = {correct[")_t0"]}

    assert result.heads == heads
    assert result.edges == edges
    assert result.tails == tails


# ============================ ()* ============================


def test_build_def_PSL15():
    example = """ "(_t0" expression_v0 (factor_v0 "-_t0" "[0-9]*.[0-9]*_r0")* ")_t0" """

    result = build_symbol_graph(example)
    correct = {symbol.content: symbol for symbol in result.symbols}

    heads = {correct["(_t0"]}
    edges = dict(
        {
            correct["(_t0"]: {correct["expression_v0"]},
            correct["expression_v0"]: {correct["factor_v0"], correct[")_t0"]},
            correct["factor_v0"]: {correct["-_t0"]},
            correct["-_t0"]: {correct["[0-9]*.[0-9]*_r0"]},
            correct["[0-9]*.[0-9]*_r0"]: {correct["factor_v0"], correct[")_t0"]},
        },
    )
    tails = {correct[")_t0"]}

    assert result.heads == heads
    assert result.edges == edges
    assert result.tails == tails


def test_build_def_PSL16():
    example = (
        """ "(_t0" expression_v0 ((factor_v0 "-_t0")* | "[0-9]*.[0-9]*_r0") ")_t0" """
    )

    result = build_symbol_graph(example)
    correct = {symbol.content: symbol for symbol in result.symbols}

    heads = {correct["(_t0"]}
    edges = dict(
        {
            correct["(_t0"]: {correct["expression_v0"]},
            correct["expression_v0"]: {
                correct["factor_v0"],
                correct["[0-9]*.[0-9]*_r0"],
                correct[")_t0"],
            },
            correct["factor_v0"]: {correct["-_t0"]},
            correct["-_t0"]: {correct["factor_v0"], correct[")_t0"]},
            correct["[0-9]*.[0-9]*_r0"]: {correct[")_t0"]},
        },
    )
    tails = {correct[")_t0"]}

    assert result.heads == heads
    assert result.edges == edges
    assert result.tails == tails


def test_build_def_PSL17():
    example = """ "(_t0" expression_v0 ((factor_v0 "-_t0")* | ("[0-9]*.[0-9]*_r0" | "+_t0")*) ")_t0" """

    result = build_symbol_graph(example)
    correct = {symbol.content: symbol for symbol in result.symbols}

    heads = {correct["(_t0"]}
    edges = dict(
        {
            correct["(_t0"]: {correct["expression_v0"]},
            correct["expression_v0"]: {
                correct["factor_v0"],
                correct["[0-9]*.[0-9]*_r0"],
                correct["+_t0"],
                correct[")_t0"],
            },
            correct["factor_v0"]: {correct["-_t0"]},
            correct["-_t0"]: {correct["factor_v0"], correct[")_t0"]},
            correct["[0-9]*.[0-9]*_r0"]: {
                correct["[0-9]*.[0-9]*_r0"],
                correct["+_t0"],
                correct[")_t0"],
            },
            correct["+_t0"]: {
                correct["[0-9]*.[0-9]*_r0"],
                correct["+_t0"],
                correct[")_t0"],
            },
        },
    )
    tails = {correct[")_t0"]}

    assert result.heads == heads
    assert result.edges == edges
    assert result.tails == tails


def test_build_def_PSL18():
    example = """ "(_t0" expression_v0 ((factor_v0 "-_t0") | ("[0-9]*.[0-9]*_r0" factor_v1 | "+_t0" expression_v1)*)* ")_t0" """

    result = build_symbol_graph(example)
    correct = {symbol.content: symbol for symbol in result.symbols}

    heads = {correct["(_t0"]}
    edges = dict(
        {
            correct["(_t0"]: {correct["expression_v0"]},
            correct["expression_v0"]: {
                correct["factor_v0"],
                correct["[0-9]*.[0-9]*_r0"],
                correct["+_t0"],
                correct[")_t0"],
            },
            correct["factor_v0"]: {correct["-_t0"]},
            correct["-_t0"]: {
                correct["factor_v0"],
                correct["[0-9]*.[0-9]*_r0"],
                correct["+_t0"],
                correct[")_t0"],
            },
            correct["[0-9]*.[0-9]*_r0"]: {correct["factor_v1"]},
            correct["factor_v1"]: {
                correct["[0-9]*.[0-9]*_r0"],
                correct["+_t0"],
                correct["factor_v0"],
                correct[")_t0"],
            },
            correct["+_t0"]: {correct["expression_v1"]},
            correct["expression_v1"]: {
                correct["[0-9]*.[0-9]*_r0"],
                correct["+_t0"],
                correct["factor_v0"],
                correct[")_t0"],
            },
        },
    )
    tails = {correct[")_t0"]}

    assert result.heads == heads
    assert result.edges == edges
    assert result.tails == tails


def test_build_def_PSL19():
    example = """ "(_t0" expression_v0 ((factor_v0 "-_t0") ("+_t1" power_v0) | ("[0-9]*.[0-9]*_r0" factor_v1 | "+_t0" expression_v1)*)* ")_t0"  """

    result = build_symbol_graph(example)
    correct = {symbol.content: symbol for symbol in result.symbols}

    heads = {correct["(_t0"]}
    edges = dict(
        {
            correct["(_t0"]: {correct["expression_v0"]},
            correct["expression_v0"]: {
                correct["factor_v0"],
                correct["[0-9]*.[0-9]*_r0"],
                correct["+_t0"],
                correct[")_t0"],
            },
            correct["factor_v0"]: {correct["-_t0"]},
            correct["-_t0"]: {correct["+_t1"]},
            correct["+_t1"]: {correct["power_v0"]},
            correct["power_v0"]: {
                correct["factor_v0"],
                correct["[0-9]*.[0-9]*_r0"],
                correct["+_t0"],
                correct[")_t0"],
            },
            correct["[0-9]*.[0-9]*_r0"]: {correct["factor_v1"]},
            correct["factor_v1"]: {
                correct["[0-9]*.[0-9]*_r0"],
                correct["+_t0"],
                correct["factor_v0"],
                correct[")_t0"],
            },
            correct["+_t0"]: {correct["expression_v1"]},
            correct["expression_v1"]: {
                correct["[0-9]*.[0-9]*_r0"],
                correct["+_t0"],
                correct["factor_v0"],
                correct[")_t0"],
            },
        },
    )
    tails = {correct[")_t0"]}

    assert result.heads == heads
    assert result.edges == edges
    assert result.tails == tails


def test_build_def_PSL20():
    example = """ "(_t0" expression_v0 ((factor_v0 "-_t0")* ("+_t0" power_v0) | ("[0-9]*.[0-9]*_r0" factor_v1 | "+_t1" expression_v1)*)* ")_t0" """

    result = build_symbol_graph(example)
    correct = {symbol.content: symbol for symbol in result.symbols}

    heads = {correct["(_t0"]}
    edges = dict(
        {
            correct["(_t0"]: {correct["expression_v0"]},
            correct["expression_v0"]: {
                correct["factor_v0"],
                correct["+_t0"],
                correct["[0-9]*.[0-9]*_r0"],
                correct["+_t1"],
                correct[")_t0"],
            },
            correct["factor_v0"]: {correct["-_t0"]},
            correct["-_t0"]: {correct["factor_v0"], correct["+_t0"]},
            correct["+_t0"]: {correct["power_v0"]},
            correct["power_v0"]: {
                correct["factor_v0"],
                correct["+_t0"],
                correct["[0-9]*.[0-9]*_r0"],
                correct["+_t1"],
                correct[")_t0"],
            },
            correct["[0-9]*.[0-9]*_r0"]: {correct["factor_v1"]},
            correct["factor_v1"]: {
                correct["[0-9]*.[0-9]*_r0"],
                correct["+_t1"],
                correct["factor_v0"],
                correct["+_t0"],
                correct[")_t0"],
            },
            correct["+_t1"]: {correct["expression_v1"]},
            correct["expression_v1"]: {
                correct["[0-9]*.[0-9]*_r0"],
                correct["+_t1"],
                correct["factor_v0"],
                correct["+_t0"],
                correct[")_t0"],
            },
        },
    )
    tails = {correct[")_t0"]}

    assert result.heads == heads
    assert result.edges == edges
    assert result.tails == tails


def test_build_def_PSL21():
    example = """ "(_t0" expression_v0 ((factor_v0 "-_t0")* ("/_t0" factor_v1) ("+_t1" power_v0) expression_v2 | ("[0-9]*.[0-9]*_r0" factor_v2 | "+_t0" expression_v1)*)* ")_t0" """

    result = build_symbol_graph(example)
    correct = {symbol.content: symbol for symbol in result.symbols}

    heads = {correct["(_t0"]}
    edges = dict(
        {
            correct["(_t0"]: {correct["expression_v0"]},
            correct["expression_v0"]: {
                correct["factor_v0"],
                correct["/_t0"],
                correct["[0-9]*.[0-9]*_r0"],
                correct["+_t0"],
                correct[")_t0"],
            },
            correct["factor_v0"]: {correct["-_t0"]},
            correct["-_t0"]: {correct["factor_v0"], correct["/_t0"]},
            correct["/_t0"]: {correct["factor_v1"]},
            correct["factor_v1"]: {correct["+_t1"]},
            correct["+_t1"]: {correct["power_v0"]},
            correct["power_v0"]: {correct["expression_v2"]},
            correct["expression_v2"]: {
                correct["factor_v0"],
                correct["/_t0"],
                correct["[0-9]*.[0-9]*_r0"],
                correct["+_t0"],
                correct[")_t0"],
            },
            correct["[0-9]*.[0-9]*_r0"]: {correct["factor_v2"]},
            correct["factor_v2"]: {
                correct["[0-9]*.[0-9]*_r0"],
                correct["+_t0"],
                correct["factor_v0"],
                correct["/_t0"],
                correct[")_t0"],
            },
            correct["+_t0"]: {correct["expression_v1"]},
            correct["expression_v1"]: {
                correct["[0-9]*.[0-9]*_r0"],
                correct["+_t0"],
                correct["factor_v0"],
                correct["/_t0"],
                correct[")_t0"],
            },
        },
    )
    tails = {correct[")_t0"]}

    assert result.heads == heads
    assert result.edges == edges
    assert result.tails == tails


def test_build_def_PSL22():
    example = """ "(_t0" expression_v0 ((factor_v0 "-_t0")* ("/_t0" factor_v1) ("+_t1" power_v0)* expression_v2 ("[0-9]*.[0-9]*_r1" "*_t0") | ("[0-9]*.[0-9]*_r0" factor_v2 | "+_t0" expression_v1)*)* ")_t0" """

    result = build_symbol_graph(example)
    correct = {symbol.content: symbol for symbol in result.symbols}

    heads = {correct["(_t0"]}
    edges = dict(
        {
            correct["(_t0"]: {correct["expression_v0"]},
            correct["expression_v0"]: {
                correct["factor_v0"],
                correct["/_t0"],
                correct["[0-9]*.[0-9]*_r0"],
                correct["+_t0"],
                correct[")_t0"],
            },
            correct["factor_v0"]: {correct["-_t0"]},
            correct["-_t0"]: {correct["factor_v0"], correct["/_t0"]},
            correct["/_t0"]: {correct["factor_v1"]},
            correct["factor_v1"]: {correct["+_t1"], correct["expression_v2"]},
            correct["+_t1"]: {correct["power_v0"]},
            correct["power_v0"]: {correct["+_t1"], correct["expression_v2"]},
            correct["expression_v2"]: {correct["[0-9]*.[0-9]*_r1"]},
            correct["[0-9]*.[0-9]*_r1"]: {correct["*_t0"]},
            correct["*_t0"]: {
                correct["factor_v0"],
                correct["/_t0"],
                correct["[0-9]*.[0-9]*_r0"],
                correct["+_t0"],
                correct[")_t0"],
            },
            correct["[0-9]*.[0-9]*_r0"]: {correct["factor_v2"]},
            correct["factor_v2"]: {
                correct["[0-9]*.[0-9]*_r0"],
                correct["+_t0"],
                correct["factor_v0"],
                correct["/_t0"],
                correct[")_t0"],
            },
            correct["+_t0"]: {correct["expression_v1"]},
            correct["expression_v1"]: {
                correct["[0-9]*.[0-9]*_r0"],
                correct["+_t0"],
                correct["factor_v0"],
                correct["/_t0"],
                correct[")_t0"],
            },
        },
    )
    tails = {correct[")_t0"]}

    assert result.heads == heads
    assert result.edges == edges
    assert result.tails == tails


# ============================ ()+ ============================


def test_build_def_XXL23():
    example = """ "(_t0" expression_v0 (factor_v0 "-_t0" "[0-9]*.[0-9]*_r0")+ ")_t0" """

    result = build_symbol_graph(example)
    correct = {symbol.content: symbol for symbol in result.symbols}

    heads = {correct["(_t0"]}
    edges = dict(
        {
            correct["(_t0"]: {correct["expression_v0"]},
            correct["expression_v0"]: {correct["factor_v0"]},
            correct["factor_v0"]: {correct["-_t0"]},
            correct["-_t0"]: {correct["[0-9]*.[0-9]*_r0"]},
            correct["[0-9]*.[0-9]*_r0"]: {correct["factor_v0"], correct[")_t0"]},
        },
    )
    tails = {correct[")_t0"]}

    assert result.heads == heads
    assert result.edges == edges
    assert result.tails == tails


def test_build_def_PXL24():
    example = """ "(_t0" expression_v0 ((factor_v0 "-_t0")+ | ("[0-9]*.[0-9]*_r0" | "+_t0")+) ")_t0" """

    result = build_symbol_graph(example)
    correct = {symbol.content: symbol for symbol in result.symbols}

    heads = {correct["(_t0"]}
    edges = dict(
        {
            correct["(_t0"]: {correct["expression_v0"]},
            correct["expression_v0"]: {
                correct["factor_v0"],
                correct["[0-9]*.[0-9]*_r0"],
                correct["+_t0"],
            },
            correct["factor_v0"]: {correct["-_t0"]},
            correct["-_t0"]: {correct["factor_v0"], correct[")_t0"]},
            correct["[0-9]*.[0-9]*_r0"]: {
                correct["[0-9]*.[0-9]*_r0"],
                correct["+_t0"],
                correct[")_t0"],
            },
            correct["+_t0"]: {
                correct["[0-9]*.[0-9]*_r0"],
                correct["+_t0"],
                correct[")_t0"],
            },
        },
    )
    tails = {correct[")_t0"]}

    assert result.heads == heads
    assert result.edges == edges
    assert result.tails == tails


def test_build_def_PXL25():
    example = """ "(_t0" expression_v0 ((factor_v0 "-_t0")+ ("/_t0" factor_v2) ("+_t1" power_v0)+ expression_v2 ("[0-9]*.[0-9]*_r1" "*_t0") | ("[0-9]*.[0-9]*_r0" factor_v1 | "+_t0" expression_v1)+)+ ")_t0" """

    result = build_symbol_graph(example)
    correct = {symbol.content: symbol for symbol in result.symbols}

    heads = {correct["(_t0"]}
    edges = dict(
        {
            correct["(_t0"]: {correct["expression_v0"]},
            correct["expression_v0"]: {
                correct["factor_v0"],
                correct["[0-9]*.[0-9]*_r0"],
                correct["+_t0"],
            },
            correct["factor_v0"]: {correct["-_t0"]},
            correct["-_t0"]: {correct["factor_v0"], correct["/_t0"]},
            correct["/_t0"]: {correct["factor_v2"]},
            correct["factor_v2"]: {correct["+_t1"]},
            correct["+_t1"]: {correct["power_v0"]},
            correct["power_v0"]: {correct["+_t1"], correct["expression_v2"]},
            correct["expression_v2"]: {correct["[0-9]*.[0-9]*_r1"]},
            correct["[0-9]*.[0-9]*_r1"]: {correct["*_t0"]},
            correct["*_t0"]: {
                correct["factor_v0"],
                correct["[0-9]*.[0-9]*_r0"],
                correct["+_t0"],
                correct[")_t0"],
            },
            correct["[0-9]*.[0-9]*_r0"]: {correct["factor_v1"]},
            correct["factor_v1"]: {
                correct["[0-9]*.[0-9]*_r0"],
                correct["+_t0"],
                correct["factor_v0"],
                correct[")_t0"],
            },
            correct["+_t0"]: {correct["expression_v1"]},
            correct["expression_v1"]: {
                correct["[0-9]*.[0-9]*_r0"],
                correct["+_t0"],
                correct["factor_v0"],
                correct[")_t0"],
            },
        },
    )
    tails = {correct[")_t0"]}

    assert result.heads == heads
    assert result.edges == edges
    assert result.tails == tails


# ============================ ()? ============================


def test_build_def_PSX26():
    example = """ "(_t0" expression_v0 (factor_v0 "-_t0" "[0-9]*.[0-9]*_r0")? ")_t0" """

    result = build_symbol_graph(example)
    correct = {symbol.content: symbol for symbol in result.symbols}

    heads = {correct["(_t0"]}
    edges = dict(
        {
            correct["(_t0"]: {correct["expression_v0"]},
            correct["expression_v0"]: {correct["factor_v0"], correct[")_t0"]},
            correct["factor_v0"]: {correct["-_t0"]},
            correct["-_t0"]: {correct["[0-9]*.[0-9]*_r0"]},
            correct["[0-9]*.[0-9]*_r0"]: {correct[")_t0"]},
        },
    )
    tails = {correct[")_t0"]}

    assert result.heads == heads
    assert result.edges == edges
    assert result.tails == tails


# [NOTE] There'll be no forcing into `/[0-9]*.[0-9]*/` if `END` of `[factor "-"]` is chosen which is coherent.
def test_build_def_PSX27():
    example = (
        """ "(_t0" expression_v0 ((factor_v0 "-_t0")? | "[0-9]*.[0-9]*_r0") ")_t0" """
    )

    result = build_symbol_graph(example)
    correct = {symbol.content: symbol for symbol in result.symbols}

    heads = {correct["(_t0"]}
    edges = dict(
        {
            correct["(_t0"]: {correct["expression_v0"]},
            correct["expression_v0"]: {
                correct["factor_v0"],
                correct["[0-9]*.[0-9]*_r0"],
                correct[")_t0"],
            },
            correct["factor_v0"]: {correct["-_t0"]},
            correct["-_t0"]: {correct[")_t0"]},
            correct["[0-9]*.[0-9]*_r0"]: {correct[")_t0"]},
        },
    )
    tails = {correct[")_t0"]}

    assert result.heads == heads
    assert result.edges == edges
    assert result.tails == tails


def test_build_def_PSX28():
    example = """ "(_t0" expression_v0 ((factor_v0 "-_t0")? | ("[0-9]*.[0-9]*_r0" | "+_t0")?) ")_t0" """

    result = build_symbol_graph(example)
    correct = {symbol.content: symbol for symbol in result.symbols}

    heads = {correct["(_t0"]}
    edges = dict(
        {
            correct["(_t0"]: {correct["expression_v0"]},
            correct["expression_v0"]: {
                correct["factor_v0"],
                correct["[0-9]*.[0-9]*_r0"],
                correct["+_t0"],
                correct[")_t0"],
            },
            correct["factor_v0"]: {correct["-_t0"]},
            correct["-_t0"]: {correct[")_t0"]},
            correct["[0-9]*.[0-9]*_r0"]: {correct[")_t0"]},
            correct["+_t0"]: {correct[")_t0"]},
        },
    )
    tails = {correct[")_t0"]}

    assert result.heads == heads
    assert result.edges == edges
    assert result.tails == tails


def test_build_def_PSX29():
    example = """ "(_t0" expression_v0 ((factor_v0 "-_t0") | ("[0-9]*.[0-9]*_r0" factor_v1 | "+_t0" expression_v1)?)? ")_t0" """

    result = build_symbol_graph(example)
    correct = {symbol.content: symbol for symbol in result.symbols}

    heads = {correct["(_t0"]}
    edges = dict(
        {
            correct["(_t0"]: {correct["expression_v0"]},
            correct["expression_v0"]: {
                correct["factor_v0"],
                correct["[0-9]*.[0-9]*_r0"],
                correct["+_t0"],
                correct[")_t0"],
            },
            correct["factor_v0"]: {correct["-_t0"]},
            correct["-_t0"]: {correct[")_t0"]},
            correct["[0-9]*.[0-9]*_r0"]: {correct["factor_v1"]},
            correct["factor_v1"]: {correct[")_t0"]},
            correct["+_t0"]: {correct["expression_v1"]},
            correct["expression_v1"]: {correct[")_t0"]},
        },
    )
    tails = {correct[")_t0"]}

    assert result.heads == heads
    assert result.edges == edges
    assert result.tails == tails


def test_build_def_PSX30():
    example = """ "(_t0" expression_v0 ((factor_v0 "-_t0") ("+_t1" power_v0) | ("[0-9]*.[0-9]*_r0" factor_v1 | "+_t0" expression_v1)?)? ")_t0" """

    result = build_symbol_graph(example)
    correct = {symbol.content: symbol for symbol in result.symbols}

    heads = {correct["(_t0"]}
    edges = dict(
        {
            correct["(_t0"]: {correct["expression_v0"]},
            correct["expression_v0"]: {
                correct["factor_v0"],
                correct["[0-9]*.[0-9]*_r0"],
                correct["+_t0"],
                correct[")_t0"],
            },
            correct["factor_v0"]: {correct["-_t0"]},
            correct["-_t0"]: {correct["+_t1"]},
            correct["+_t1"]: {correct["power_v0"]},
            correct["power_v0"]: {correct[")_t0"]},
            correct["[0-9]*.[0-9]*_r0"]: {correct["factor_v1"]},
            correct["factor_v1"]: {correct[")_t0"]},
            correct["+_t0"]: {correct["expression_v1"]},
            correct["expression_v1"]: {correct[")_t0"]},
        },
    )
    tails = {correct[")_t0"]}

    assert result.heads == heads
    assert result.edges == edges
    assert result.tails == tails


def test_build_def_PSX31():
    example = """ "(_t0" expression_v0 ((factor_v0 "-_t0")? ("+_t0" power_v0) | ("[0-9]*.[0-9]*_r0" factor_v1 | "+_t1" expression_v1)?)? ")_t0" """

    result = build_symbol_graph(example)
    correct = {symbol.content: symbol for symbol in result.symbols}

    heads = {correct["(_t0"]}
    edges = dict(
        {
            correct["(_t0"]: {correct["expression_v0"]},
            correct["expression_v0"]: {
                correct["factor_v0"],
                correct["+_t0"],
                correct["[0-9]*.[0-9]*_r0"],
                correct["+_t1"],
                correct[")_t0"],
            },
            correct["factor_v0"]: {correct["-_t0"]},
            correct["-_t0"]: {correct["+_t0"]},
            correct["+_t0"]: {correct["power_v0"]},
            correct["power_v0"]: {correct[")_t0"]},
            correct["[0-9]*.[0-9]*_r0"]: {correct["factor_v1"]},
            correct["factor_v1"]: {correct[")_t0"]},
            correct["+_t1"]: {correct["expression_v1"]},
            correct["expression_v1"]: {correct[")_t0"]},
        },
    )
    tails = {correct[")_t0"]}

    assert result.heads == heads
    assert result.edges == edges
    assert result.tails == tails


def test_build_def_PSX32():
    example = """ "(_t0" expression_v0 ((factor_v0 "-_t0")? ("/_t0" factor_v1) ("+_t1" power_v0) expression_v2 | ("[0-9]*.[0-9]*_r0" factor_v2 | "+_t0" expression_v1)?)? ")_t0" """

    result = build_symbol_graph(example)
    correct = {symbol.content: symbol for symbol in result.symbols}

    heads = {correct["(_t0"]}
    edges = dict(
        {
            correct["(_t0"]: {correct["expression_v0"]},
            correct["expression_v0"]: {
                correct["factor_v0"],
                correct["/_t0"],
                correct["[0-9]*.[0-9]*_r0"],
                correct["+_t0"],
                correct[")_t0"],
            },
            correct["factor_v0"]: {correct["-_t0"]},
            correct["-_t0"]: {correct["/_t0"]},
            correct["/_t0"]: {correct["factor_v1"]},
            correct["factor_v1"]: {correct["+_t1"]},
            correct["+_t1"]: {correct["power_v0"]},
            correct["power_v0"]: {correct["expression_v2"]},
            correct["expression_v2"]: {correct[")_t0"]},
            correct["[0-9]*.[0-9]*_r0"]: {correct["factor_v2"]},
            correct["factor_v2"]: {correct[")_t0"]},
            correct["+_t0"]: {correct["expression_v1"]},
            correct["expression_v1"]: {correct[")_t0"]},
        },
    )
    tails = {correct[")_t0"]}

    assert result.heads == heads
    assert result.edges == edges
    assert result.tails == tails


def test_build_def_PSX33():
    example = """ "(_t0" expression_v0 ((factor_v0 "-_t0")? ("/_t0" factor_v1) ("+_t1" power_v0)? expression_v2 ("[0-9]*.[0-9]*_r1" "*_t0") | ("[0-9]*.[0-9]*_r0" factor_v2 | "+_t0" expression_v1)?)? ")_t0" """

    result = build_symbol_graph(example)
    correct = {symbol.content: symbol for symbol in result.symbols}

    heads = {correct["(_t0"]}
    edges = dict(
        {
            correct["(_t0"]: {correct["expression_v0"]},
            correct["expression_v0"]: {
                correct["factor_v0"],
                correct["/_t0"],
                correct["[0-9]*.[0-9]*_r0"],
                correct["+_t0"],
                correct[")_t0"],
            },
            correct["factor_v0"]: {correct["-_t0"]},
            correct["-_t0"]: {correct["/_t0"]},
            correct["/_t0"]: {correct["factor_v1"]},
            correct["factor_v1"]: {correct["+_t1"], correct["expression_v2"]},
            correct["+_t1"]: {correct["power_v0"]},
            correct["power_v0"]: {correct["expression_v2"]},
            correct["expression_v2"]: {correct["[0-9]*.[0-9]*_r1"]},
            correct["[0-9]*.[0-9]*_r1"]: {correct["*_t0"]},
            correct["*_t0"]: {correct[")_t0"]},
            correct["[0-9]*.[0-9]*_r0"]: {correct["factor_v2"]},
            correct["factor_v2"]: {correct[")_t0"]},
            correct["+_t0"]: {correct["expression_v1"]},
            correct["expression_v1"]: {correct[")_t0"]},
        },
    )
    tails = {correct[")_t0"]}

    assert result.heads == heads
    assert result.edges == edges
    assert result.tails == tails


# ======================================== `()*` + `()?` ========================================


def test_build_def_PSL34():
    example = """ "(_t0" expression_v0 ((factor_v0 "-_t0")* ("/_t0" factor_v1) ("+_t1" power_v0)? expression_v2 ("[0-9]*.[0-9]*_r1" "*_t0") | ("[0-9]*.[0-9]*_r0" factor_v2 | "+_t0" expression_v1)?)* ")_t0" """

    result = build_symbol_graph(example)
    correct = {symbol.content: symbol for symbol in result.symbols}

    heads = {correct["(_t0"]}
    edges = dict(
        {
            correct["(_t0"]: {correct["expression_v0"]},
            correct["expression_v0"]: {
                correct["factor_v0"],
                correct["/_t0"],
                correct["[0-9]*.[0-9]*_r0"],
                correct["+_t0"],
                correct[")_t0"],
            },
            correct["factor_v0"]: {correct["-_t0"]},
            correct["-_t0"]: {correct["factor_v0"], correct["/_t0"]},
            correct["/_t0"]: {correct["factor_v1"]},
            correct["factor_v1"]: {correct["+_t1"], correct["expression_v2"]},
            correct["+_t1"]: {correct["power_v0"]},
            correct["power_v0"]: {correct["expression_v2"]},
            correct["expression_v2"]: {correct["[0-9]*.[0-9]*_r1"]},
            correct["[0-9]*.[0-9]*_r1"]: {correct["*_t0"]},
            correct["*_t0"]: {
                correct["factor_v0"],
                correct["/_t0"],
                correct["[0-9]*.[0-9]*_r0"],
                correct["+_t0"],
                correct[")_t0"],
            },
            correct["[0-9]*.[0-9]*_r0"]: {correct["factor_v2"]},
            correct["factor_v2"]: {
                correct["factor_v0"],
                correct["/_t0"],
                correct["[0-9]*.[0-9]*_r0"],
                correct["+_t0"],
                correct[")_t0"],
            },
            correct["+_t0"]: {correct["expression_v1"]},
            correct["expression_v1"]: {
                correct["factor_v0"],
                correct["/_t0"],
                correct["[0-9]*.[0-9]*_r0"],
                correct["+_t0"],
                correct[")_t0"],
            },
        },
    )
    tails = {correct[")_t0"]}

    assert result.heads == heads
    assert result.edges == edges
    assert result.tails == tails


# ======================================== `()*` + `()+` + `()?` ========================================


def test_build_def_PSL35():
    example = """ "(_t0" expression_v0 ((factor_v0 "-_t0")+ ("/_t0" factor_v2) ("+_t1" power_v0)? expression_v2 ("[0-9]*.[0-9]*_r1" "*_t0") | ("[0-9]*.[0-9]*_r0" factor_v1 | "+_t0" expression_v1)?)* ")_t0" """

    result = build_symbol_graph(example)
    correct = {symbol.content: symbol for symbol in result.symbols}

    heads = {correct["(_t0"]}
    edges = dict(
        {
            correct["(_t0"]: {correct["expression_v0"]},
            correct["expression_v0"]: {
                correct["factor_v0"],
                correct["[0-9]*.[0-9]*_r0"],
                correct["+_t0"],
                correct[")_t0"],
            },
            correct["factor_v0"]: {correct["-_t0"]},
            correct["-_t0"]: {correct["factor_v0"], correct["/_t0"]},
            correct["/_t0"]: {correct["factor_v2"]},
            correct["factor_v2"]: {correct["+_t1"], correct["expression_v2"]},
            correct["+_t1"]: {correct["power_v0"]},
            correct["power_v0"]: {correct["expression_v2"]},
            correct["expression_v2"]: {correct["[0-9]*.[0-9]*_r1"]},
            correct["[0-9]*.[0-9]*_r1"]: {correct["*_t0"]},
            correct["*_t0"]: {
                correct["factor_v0"],
                correct["[0-9]*.[0-9]*_r0"],
                correct["+_t0"],
                correct[")_t0"],
            },
            correct["[0-9]*.[0-9]*_r0"]: {correct["factor_v1"]},
            correct["factor_v1"]: {
                correct["factor_v0"],
                correct["[0-9]*.[0-9]*_r0"],
                correct["+_t0"],
                correct[")_t0"],
            },
            correct["+_t0"]: {correct["expression_v1"]},
            correct["expression_v1"]: {
                correct["factor_v0"],
                correct["[0-9]*.[0-9]*_r0"],
                correct["+_t0"],
                correct[")_t0"],
            },
        },
    )
    tails = {correct[")_t0"]}

    assert result.heads == heads
    assert result.edges == edges
    assert result.tails == tails
