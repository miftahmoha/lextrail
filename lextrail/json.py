from dataclasses import dataclass
from enum import Enum
from uuid import uuid4
from typing import Union

from lextrail.build import SymbolGraph, build_symbol_graph
from lextrail.guide import Trail, TrailState
from lextrail.assemble import ASMSchema, ASM, ASMState, build_asm_graph
from lextrail.helpers import TrailError, is_escaped


KEYWORDS = [
    "type",
    "enum",
    "const",
    "properties",
    "required",
    "items",
    "prefixItems",
    "oneOf",
]


# ============================ ERROR ============================


class ErrorKind(Enum):
    INPUT = 0
    BLOCK = 1
    ARRAY = 2
    ENTRY = 3
    STRING = 4
    KEYWORD = 5
    TYPE = 6
    NUMBER = 7
    INTEGER = 8


@dataclass
class JSONError:
    kind: ErrorKind

    def message(self):
        match self.kind:
            case ErrorKind.INPUT:
                return "Invalid JSON Input."
            case ErrorKind.BLOCK:
                return "Invalid JSON Block."
            case ErrorKind.ARRAY:
                return "Invalid JSON Array."
            case ErrorKind.STRING:
                return "Invalid JSON String."

    def help(self):
        match self.kind:
            case ErrorKind.BLOCK:
                return 'Expected format: {value}, where value is {object}, [array], "string", or number.'
            case ErrorKind.ARRAY:
                return 'Expected format: [value], where value is {object}, [array], "string", or number.'


# ============================ INPUT ============================


@dataclass
class InputContext:
    content: str
    line: int
    path: str


class InputKind(Enum):
    BLOCK = 1
    ARRAY = 2
    ENTRY = 3
    INTEGER = 6
    STRING = 4
    NUMBER = 5


@dataclass
class JSONInput:
    kind: InputKind
    context: InputContext


class LabelKind(Enum):
    PROPERTY = 1
    KEYWORD = 2


@dataclass
class JSONLabel:
    kind: LabelKind
    context: InputContext


type JSONSpecs = dict[str, JSONInput]


def split_json_input(inp: JSONInput) -> list[JSONInput]:
    context, kind = inp.context, inp.kind

    assert kind in [
        InputKind.BLOCK,
        InputKind.ARRAY,
    ], f"Expected `Block` or `Array`, got `{kind}` instead."

    content, line, path = context.content, context.line, context.path

    inps: list[JSONInput] = []
    block, array, label = 0, 0, False
    accumulate: list[str] = []
    i = 1

    while i < len(content) - 1:
        curr = content[i]

        if curr == "{":
            block += 1
        elif curr == "}":
            block -= 1
        elif curr == "[":
            array += 1
        elif curr == "]":
            array -= 1
        elif curr == "\n":
            line += 1
        elif curr == "," and block == 0 and array == 0 and not label:
            consume_input(inps, accumulate, line, path)
            i += 1
            continue

        accumulate.append(curr)
        i += 1

    if not is_valid_whitespace(accumulate):
        consume_input(inps, accumulate, line, path)

    return inps


def build_entry_from_input(inp: JSONInput) -> tuple[JSONLabel, JSONInput]:
    context, kind = inp.context, inp.kind

    assert kind == InputKind.ENTRY, f"Expected `Entry`, got `{kind}` instead."

    line, path = context.line, context.path
    key, value = [item.strip() for item in context.content.split(":", maxsplit=1)]

    if is_valid_string(key):
        label = build_json_label(key[1:-1], line, path)
        inp = build_json_input(value, line, f"{path}->{key}")

        return (label, inp)
    else:
        raise TrailError(
            format_json_error(JSONError(kind=ErrorKind.STRING), inp.context)
        )


def build_specs_from_input(inp: JSONInput) -> JSONSpecs:
    specs: JSONSpecs = {}

    if inp.kind != InputKind.BLOCK:
        return TrailError(
            format_json_error(JSONError(kind=ErrorKind.BLOCK), context=inp.context)
        )

    entries = split_json_input(inp)

    for entry in entries:
        if entry.kind != InputKind.ENTRY:
            return TrailError(
                format_json_error(JSONError(kind=ErrorKind.ENTRY), context=inp.context)
            )

        label, inp = build_entry_from_input(entry)
        context = label.context

        if label.kind != LabelKind.KEYWORD:
            return TrailError(
                format_json_error(kind=ErrorKind.KEYWORD, context=inp.context)
            )

        specs[context.content] = inp

    return specs


# ============================ ENTITIES ============================


type JSONEntity = Union[JSONObject, JSONIterable, JSONLiteral]


@dataclass
class JSONBlock:
    id: str
    entity: JSONEntity


@dataclass
class JSONProperty:
    label: str
    block: JSONBlock
    required: bool


@dataclass
class JSONObject:
    properties: list[JSONProperty]


class IterableKind(Enum):
    ARRAY = 1
    TUPLE = 2
    UNION = 3


@dataclass
class JSONIterable:
    kind: IterableKind
    blocks: list[JSONBlock]


@dataclass
class JSONLiteral:
    value: str


def build_entity_from_input(inp: JSONInput) -> JSONEntity:
    specs = build_specs_from_input(inp)

    if (inp := specs.get("type")) is not None:
        kind, context = inp.kind, inp.context

        if kind != InputKind.STRING:
            raise TrailError(
                format_json_error(JSONError(kind=ErrorKind.STRING), context)
            )

        return build_json_entity(context, specs)

    if (inp := specs.get("oneOf")) is not None:
        if inp.kind != InputKind.ARRAY:
            raise TrailError(
                format_json_error(JSONError(kind=ErrorKind.ARRAY), inp.context)
            )

        inps = split_json_input(inp)

        if (
            invalid := next((inp for inp in inps if inp.kind != InputKind.BLOCK), None)
        ) is not None:
            raise TrailError(
                format_json_error(JSONError(kind=ErrorKind.BLOCK), invalid.context)
            )

        blocks = [
            JSONBlock(id=uuid4().hex, entity=build_entity_from_input(inp))
            for inp in inps
        ]

        return JSONIterable(kind=IterableKind.UNION, blocks=blocks)

    # [TODO] Unspecified block error?
    return JSONLiteral(value='"null"')


# ============================ BUILD ============================


def build_json_entity(context: InputContext, specs: JSONSpecs) -> JSONEntity:
    match context.content[1:-1]:
        case "object":
            return build_object_from_specs(specs)
        case "array":
            return build_array_from_specs(specs)
        case "string":
            return build_string_from_specs(specs)
        case "number":
            return build_number_from_specs(specs)
        case "integer":
            return build_integer_from_specs(specs)
        case "boolean":
            return JSONLiteral(value='"true"|"false"')
        case "null":
            return JSONLiteral(value='"null"')
        case _:
            raise TrailError(format_json_error(JSONError(kind=ErrorKind.TYPE), context))


def build_object_from_specs(specs: JSONSpecs) -> JSONObject:
    properties: list[JSONProperty] = []

    if (inp := specs.get("properties")) is not None:
        if inp.kind != InputKind.BLOCK:
            raise TrailError(
                format_json_error(JSONError(kind=ErrorKind.BLOCK), inp.context)
            )

        inps = split_json_input(inp)

        for inp in inps:
            if inp.kind != InputKind.ENTRY:
                raise TrailError(
                    format_json_error(JSONError(kind=ErrorKind.ENTRY), inp.context)
                )

            label, inp = build_entry_from_input(inp)

            entity = build_entity_from_input(inp)

            block = JSONBlock(id=uuid4().hex, entity=entity)

            properties.append(
                JSONProperty(label=label.context.content, block=block, required=False)
            )

    if (inp := specs.get("required")) is not None:
        if inp.kind != InputKind.ARRAY:
            raise TrailError(
                format_json_error(JSONError(kind=ErrorKind.ARRAY), inp.context)
            )

        inps = split_json_input(inp)

        if (
            invalid := next((inp for inp in inps if inp.kind != InputKind.STRING), None)
        ) is not None:
            raise TrailError(
                format_json_error(JSONError(kind=ErrorKind.STRING), invalid.context)
            )

        labels = [inp.context.content[1:-1] for inp in inps]

        for property in properties:
            if property.label in labels:
                property.required = True

    return JSONObject(properties=properties)


def build_array_from_specs(specs: JSONSpecs) -> JSONIterable:
    if (inp := specs.get("items")) is not None:
        if inp.kind != InputKind.BLOCK:
            raise TrailError(
                format_json_error(JSONError(kind=ErrorKind.BLOCK), block.context)
            )

        entity = build_entity_from_input(inp)

        block = JSONBlock(id=uuid4().hex, entity=entity)

        return JSONIterable(kind=IterableKind.ARRAY, blocks=[block])

    if (inp := specs.get("prefixItems")) is not None:
        if inp.kind != InputKind.ARRAY:
            raise TrailError(
                format_json_error(JSONError(kind=ErrorKind.ARRAY), inp.context)
            )

        inps = split_json_input(inp)

        if (
            invalid := next((inp for inp in inps if inp.kind != InputKind.BLOCK), None)
        ) is not None:
            raise TrailError(
                format_json_error(JSONError(kind=ErrorKind.BLOCK), invalid.context)
            )

        blocks = [
            JSONBlock(id=uuid4().hex, entity=build_entity_from_input(inp))
            for inp in inps
        ]

        return JSONIterable(kind=IterableKind.TUPLE, blocks=blocks)

    return JSONIterable(kind=IterableKind.ARRAY, blocks=[])


def build_string_from_specs(specs: JSONSpecs) -> JSONLiteral:
    if (inp := specs.get("const")) is not None:
        if inp.kind != InputKind.STRING:
            raise TrailError(
                format_json_error(JSONError(kind=ErrorKind.STRING), inp.context)
            )

        return JSONLiteral(value=f'"\\"{inp.context.content[1:-1]}\\""')

    if (inp := specs.get("enum")) is not None:
        if inp.kind != InputKind.ARRAY:
            raise TrailError(
                format_json_error(JSONError(kind=ErrorKind.ARRAY), inp.context)
            )

        inps = split_json_input(inp)

        if (
            invalid := next((inp for inp in inps if inp.kind != InputKind.STRING), None)
        ) is not None:
            raise TrailError(
                format_json_error(JSONError(kind=ErrorKind.STRING), invalid.context)
            )

        return JSONLiteral(
            value="|".join(f'"\\"{inp.context.content[1:-1]}\\""' for inp in inps)
        )

    return JSONLiteral(value='/"\\w{5,10}"/')


def build_number_from_specs(specs: JSONSpecs) -> JSONLiteral:
    if (inp := specs.get("const")) is not None:
        if inp.kind not in [InputKind.NUMBER, InputKind.INTEGER]:
            raise TrailError(
                format_json_error(JSONError(kind=ErrorKind.BLOCK), inp.context)
            )

        return JSONLiteral(value=f'"{inp.context.content}"')

    if (inp := specs.get("enum")) is not None:
        if inp.kind != InputKind.ARRAY:
            raise TrailError(
                format_json_error(JSONError(kind=ErrorKind.ARRAY), inp.context)
            )

        inps = split_json_input(inp)

        if (
            invalid := next(
                (inp for inp in inps not in [InputKind.NUMBER, InputKind.INTEGER]),
                None,
            )
        ) is not None:
            raise TrailError(
                format_json_error(JSONError(kind=ErrorKind.NUMBER), invalid.context)
            )

        return JSONLiteral(value="|".join(f'"{inp.context.content}"' for inp in inps))

    return JSONLiteral(value="/^-?(\\d+\\.\\d+|\\d+|\\.\\d+)$/")


def build_integer_from_specs(specs: JSONSpecs) -> JSONLiteral:
    if (inp := specs.get("const")) is not None:
        if inp.kind != InputKind.INTEGER:
            raise TrailError(
                format_json_error(JSONError(kind=ErrorKind.BLOCK), inp.context)
            )

        return JSONLiteral(value=f'"{inp.context.content}"')

    if (inp := specs.get("enum")) is not None:
        if inp.kind != InputKind.ARRAY:
            raise TrailError(
                format_json_error(JSONError(kind=ErrorKind.ARRAY), inp.context)
            )

        inps = split_json_input(inp)

        if (
            invalid := next(
                (inp for inp in inps != InputKind.INTEGER),
                None,
            )
        ) is not None:
            raise TrailError(
                format_json_error(JSONError(kind=ErrorKind.INTEGER), invalid.context)
            )

        return JSONLiteral(value="|".join(f'"{inp.context.content}"' for inp in inps))

    return JSONLiteral(value="/^[0-9]$/")


# ============================ CFG ============================

type CFGGraph = dict[str, SymbolGraph]


def build_cfg_from_entity(entity: JSONEntity) -> CFGGraph:
    cfg: CFGGraph = {}

    items = [JSONBlock(id="start", entity=entity)]

    while items:
        item = items.pop()

        match item.entity:
            case JSONObject(properties):
                production = ['"{"']

                unions = []
                anchor = False

                for property in properties:
                    block = property.block

                    for union in unions:
                        union.append(f'( "," "\\"{property.label}\\":" {block.id} )')

                    if property.required:
                        if not unions:
                            unions.append([f'( "\\"{property.label}\\":" {block.id} )'])
                        anchor = True
                    else:
                        for union in unions:
                            union.append("?")
                        if not anchor:
                            unions.append([f'( "\\"{property.label}\\":" {block.id} )'])

                    items.append(block)

                if not anchor:
                    unions.append(['""'])

                production.append(f"({'|'.join(''.join(u) for u in unions)})")
                production.append('"}"')

                cfg[item.id] = build_symbol_graph("".join(production))

            case JSONIterable(kind, blocks):
                production: list[str] = []

                match kind:
                    case IterableKind.ARRAY:
                        assert (
                            len(blocks) == 1
                        ), "Arrays must consist of exactly one block."

                        production.append(' "[" ')

                        if blocks:
                            production.append(
                                f' ( {blocks[-1].id} "," )* {blocks[-1].id}'
                            )
                            items.append(blocks[-1])

                        production.append(' "]" ')

                    case IterableKind.TUPLE:
                        production.append(' "[" ')

                        for block in blocks[:-1]:
                            production.append(f' {block.id} "," ')
                            items.append(block)

                        if blocks:
                            production.append(f"{blocks[-1].id}")
                            items.append(blocks[-1])

                        production.append(' "]" ')

                    case IterableKind.UNION:
                        production.append("(")

                        for block in blocks[:-1]:
                            production.append(f" {block.id} | ")
                            items.append(block)

                        if blocks:
                            production.append(f"{blocks[-1].id}")
                            items.append(blocks[-1])

                        production.append(")")

                cfg[item.id] = build_symbol_graph("".join(production))

            case JSONLiteral(value):
                cfg[item.id] = build_symbol_graph(value)

    return cfg


def trail_schema(schema: str) -> Trail:
    schema = build_json_input(schema.strip(), 0, "")
    entity = build_entity_from_input(schema)

    return Trail(schema=build_cfg_from_entity(entity), state=TrailState.new())


def asm_schema(schema: str, alphabet: list[str]) -> ASM:
    schema = build_json_input(schema.strip(), 0, "")
    entity = build_entity_from_input(schema)

    return ASM(
        schema=ASMSchema(
            cfg=build_cfg_from_entity(entity), asm=build_asm_graph(alphabet)
        ),
        state=ASMState.new(),
    )


# ============================ HELPERS ============================


def consume_input(inps: list[JSONInput], accumulate: list[str], line: int, path: str):
    content = "".join(accumulate)
    inp = build_json_input(content.strip(), line, path)

    inps.append(inp)
    accumulate.clear()


def build_json_input(content: str, line: int, path: str) -> JSONInput:
    kind, context = (
        InputKind.BLOCK
        if is_valid_block(content)
        else (
            InputKind.ARRAY
            if is_valid_array(content)
            else (
                InputKind.ENTRY
                if is_valid_entry(content)
                else (
                    InputKind.STRING
                    if is_valid_string(content)
                    else (
                        InputKind.INTEGER
                        if is_valid_integer(content)
                        else InputKind.NUMBER if is_valid_number(content) else None
                    )
                )
            )
        )
    ), InputContext(content, line, path)

    if kind is None:
        raise TrailError(format_json_error(JSONError(ErrorKind.INPUT), context))

    return JSONInput(kind=kind, context=context)


# def get_json_kind(context: InputContext) -> InputKind:
#     content = context.content

#     if is_valid_block(content):
#         return InputKind.BLOCK
#     elif is_valid_array(content):
#         return InputKind.ARRAY
#     elif is_valid_entry(content):
#         return InputKind.ENTRY
#     elif is_valid_string(content):
#         return InputKind.STRING
#     elif is_valid_string(content):
#         return InputKind.INTEGER
#     elif is_valid_number(content):
#         return InputKind.NUMBER
#     else:
#         raise TrailError(format_json_error(JSONError(ErrorKind.INPUT), context))


def build_json_label(content: str, line: int, path: str) -> JSONLabel:
    kind, context = (
        LabelKind.KEYWORD if content in KEYWORDS else LabelKind.PROPERTY
    ), InputContext(content, line, path)

    return JSONLabel(kind=kind, context=context)


def is_valid_block(inp: str) -> bool:
    return inp.startswith("{") and inp.endswith("}")


def is_valid_array(inp: str) -> bool:
    return inp.startswith("[") and inp.endswith("]")


def is_valid_entry(inp: str) -> bool:
    return ":" in inp


def is_valid_string(inp: str) -> bool:
    return (
        inp.startswith('"')
        and inp.endswith('"')
        # Checks if quotes are correctly escaped.
        and all('"' not in part for part in inp.split('\\"')[1:-1])
    )


def is_valid_integer(inp: str) -> bool:
    return inp.isdigit()


def is_valid_number(inp: str) -> bool:
    try:
        float(inp)

        return True
    except ValueError:
        return False


def is_valid_whitespace(characters: list[str]) -> bool:
    return all(character.isspace() for character in characters)


def format_json_error(error: JSONError, context: InputContext):
    RED = "\x1b[31m"
    BLUE = "\x1b[34m"
    CYAN = "\x1b[36m"
    BOLD = "\x1b[1m"
    RESET = "\x1b[0m"

    content, line, path = context.content, context.line, context.path
    message, help = error.message(), error.help()

    context = "\n".join(
        f"{BOLD}{BLUE}{line + i:5} |{RESET} {split}"
        for i, split in enumerate(content.splitlines())
    )

    return (
        f"{BOLD}{RED}error{RESET}: {message}\n"
        f"{BOLD}{BLUE} --> {RESET}{path}\n"
        f"{BOLD}{BLUE}    |{RESET}\n"
        f"{context}\n"
        f"{BOLD}{BLUE}    |{RESET}\n"
        f"{BOLD}{BLUE}    = {BOLD}{CYAN}help{RESET}: {help}"
    )


def pretty_json_print(schema: str) -> str:
    result: list[str] = []
    depth = 0
    in_quote = False
    i = 0

    while i < len(schema):
        curr = schema[i]

        assert curr not in " \n\t\r", "There should be no whitespace characters."

        if curr == '"':
            if not is_escaped(schema, i):
                in_quote = not in_quote

            result.append(curr)

        elif curr in "{[" and not in_quote:
            result.extend([curr, "\n"])
            depth += 1
            result.append("  " * depth)

        elif curr in "}]" and not in_quote:
            depth -= 1
            result.extend(["\n", "  " * depth, curr])

        elif curr == "," and not in_quote:
            result.extend([curr, "\n", "  " * depth])

        elif curr == ":" and not in_quote:
            result.extend([curr, " "])

        else:
            result.append(curr)

        i += 1

    return "".join(result)
