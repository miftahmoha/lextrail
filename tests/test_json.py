import random
import json

from jsonschema import validate, ValidationError

from lextrail.guide import get_next_values
from lextrail.json import trail_json


def simulate_response(schema: str) -> str:
    trail = trail_json(schema)
    response, value = [], ""

    while values := get_next_values(trail, value):
        value = random.choice(values)
        response.append(value)

    return "".join(response)


def validate_schema(example: str, response: str):
    schema, instance = json.loads(example), json.loads(response)

    try:
        validate(instance=instance, schema=schema)
        return True
    except ValidationError as e:
        print(e)
        return False


def test_json_XXXSXXXXXX01():
    example = r"""
    {
        "type": "string"
    }
    """

    response = simulate_response(example)

    assert validate_schema(example, response)


def test_json_XXXSXXXXXX02():
    example = r"""
    {
        "type": "string",
        "const": "hello"
    }
    """

    response = simulate_response(example)

    assert validate_schema(example, response)


def test_json_XXXSXXXXXX03():
    example = r"""
    {
        "type": "string",
        "enum": ["red", "green", "blue"]
    }
    """

    response = simulate_response(example)

    assert validate_schema(example, response)


def test_json_XXTXIXXXXX04():
    example = r"""
    {
        "type": "array",
        "prefixItems": [
            {"type": "integer"},
            {"type": "integer"},
            {"type": "integer"}
        ]
    }
    """


def test_json_XXXSXFXXXX05():
    example = r"""
    {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "number"}
        }
    }
    """

    response = simulate_response(example)

    assert validate_schema(example, response)


def test_json_OXXSIXXXRX06():
    example = r"""
    {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"}
        },
        "required": ["name"]
    }
    """

    response = simulate_response(example)

    assert validate_schema(example, response)


def test_json_XAXSXFXXRX07():
    example = r"""
    {
        "type": "array",
        "items": {
            "type": "number"
        }
    }
    """

    response = simulate_response(example)

    assert validate_schema(example, response)


def test_json_XXTSXFBXXX08():
    example = r"""
    {
        "type": "array",
        "prefixItems": [
            {"type": "string"},
            {"type": "number"},
            {"type": "boolean"}
        ]

    }
    """

    response = simulate_response(example)

    assert validate_schema(example, response)


def test_json_OXXSXFBXRX09():
    example = r"""
    {
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "enum": ["pending", "approved", "rejected"]
            },
            "priority": {
                "type": "number",
                "enum": [1, 2, 3]
            }
        },
        "required": ["status"]
    }
    """

    response = simulate_response(example)

    assert validate_schema(example, response)


def test_json_OXXSXXXXRX10():
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

    response = simulate_response(example)

    assert validate_schema(example, response)


def test_json_OXXSXFXXRX11():
    example = r"""
    {
       "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "id": {"type": "number"},
                "name": {"type": "string"}
            },
            "required": ["id"]
        }
    }
    """

    response = simulate_response(example)

    assert validate_schema(example, response)


def test_json_XXXSXFXXXU12():
    example = r"""
    {
        "oneOf": [
            {"type": "string"},
            {"type": "number"}
        ]
    }
    """

    response = simulate_response(example)

    assert validate_schema(example, response)


def test_json_OXXSXFXXRU13():
    example = r"""
    {
        "oneOf": [
            {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "const": "user"
                    },
                    "username": {"type": "string"}
                },
                "required": ["type", "username"]
            },
            {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "const": "admin"
                    },
                    "adminId": {"type": "number"}
                },
                "required": ["type", "adminId"]
            }
        ]
    }
    """

    response = simulate_response(example)

    assert validate_schema(example, response)


def test_json_XXTSXFXXXX14():
    example = r"""
    {
        "type": "array",
        "prefixItems": [
            {"type": "string"},
            {"type": "number"}
        ]
    }
    """

    response = simulate_response(example)

    assert validate_schema(example, response)


def test_json_OAXSXFXXRX15():
    example = r"""
    {
        "type": "object",
        "properties": {
            "data": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "enum": ["A", "B", "C"]
                        },
                        "values": {
                            "type": "array",
                            "items": {"type": "number"}
                        }
                    },
                    "required": ["category"]
                }
            }
        },
        "required": ["data"]
    }
    """

    response = simulate_response(example)

    assert validate_schema(example, response)


def test_json_OAXSXFXXRX16():
    example = r"""
    {
        "type": "object",
        "properties": {
            "payload": {
                "oneOf": [
                    {
                        "type": "array",
                        "prefixItems": [
                            {"type": "string"},
                            {"type": "number"}
                        ]
                    },
                    {
                        "type": "object",
                        "properties": {
                            "config": {
                                "type": "string",
                                "enum": ["dev", "prod"]
                            }
                        },
                        "required": ["config"]
                    }
                ]
            }
        },
        "required": ["payload"]
    }
    """

    response = simulate_response(example)

    assert validate_schema(example, response)


def test_json_OXXSXFXXRU17():
    example = r"""
    {
        "oneOf": [
            {
                "type": "object",
                "properties": {
                    "shape": {
                        "type": "string",
                        "const": "circle"
                    },
                    "radius": {"type": "number"}
                },
                "required": ["shape", "radius"]
            },
            {
                "oneOf": [
                    {
                        "type": "object",
                        "properties": {
                            "shape": {
                                "type": "string",
                                "const": "rectangle"
                            },
                            "width": {"type": "number"},
                            "height": {"type": "number"}
                        },
                        "required": ["shape", "width", "height"]
                    },
                    {
                        "type": "object",
                        "properties": {
                            "shape": {
                                "type": "string",
                                "const": "triangle"
                            },
                            "base": {"type": "number"},
                            "height": {"type": "number"}
                        },
                        "required": ["shape", "base", "height"]
                    }
                ]
            }
        ]
    }
    """

    response = simulate_response(example)

    assert validate_schema(example, response)


def test_json_OXXSXFXXRU18():
    example = r"""
    {
        "oneOf": [
            {
                "type": "string",
                "enum": ["small", "medium", "large"]
            },
            {
                "type": "number"
            },
            {
                "type": "object",
                "properties": {
                    "custom": {"type": "string"}
                },
                "required": ["custom"]
            }
        ]
    }
    """

    response = simulate_response(example)

    assert validate_schema(example, response)


def test_json_OAXSIFXXRU19():
    example = r"""
    {
        "type": "object",
        "properties": {
            "version": {
                "type": "string",
                "const": "1.0"
            },
            "mode": {
                "type": "string",
                "enum": ["read", "write", "execute"]
            },
            "entries": {
                "type": "array",
                "items": {
                    "oneOf": [
                        {
                            "type": "object",
                            "properties": {
                                "type": {
                                    "type": "string",
                                    "const": "text"
                                },
                                "content": {"type": "string"}
                            },
                            "required": ["type", "content"]
                        },
                        {
                            "type": "object",
                            "properties": {
                                "type": {
                                    "type": "string",
                                    "const": "number"
                                },
                                "value": {"type": "integer"}
                            },
                            "required": ["type", "value"]
                        }
                    ]
                }
            }
        },
        "required": ["version", "entries"]
    }
    """

    response = simulate_response(example)

    assert validate_schema(example, response)


def test_json_OAXESXNBXRU20():
    example = r"""
    {
        "type": "object",
        "properties": {
            "basicField": {
                "type": "string",
                "const": "fixedValue"
            },
            "choiceField": {
                "oneOf": [
                    {
                        "type": "string",
                        "enum": ["optionA", "optionB", "optionC"]
                    },
                    {
                        "type": "number",
                        "const": 42
                    },
                    {
                        "type": "object",
                        "properties": {
                            "nestedChoice": {
                                "type": "boolean"
                            }
                        },
                        "required": ["nestedChoice"]
                    }
                ]
            },
            "objectField": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["active", "inactive", "pending"]
                    },
                    "metadata": {
                        "type": "array",
                        "items": {
                            "oneOf": [
                                {
                                    "type": "string",
                                    "const": "tag1"
                                },
                                {
                                    "type": "object",
                                    "properties": {
                                        "key": {
                                            "type": "string",
                                            "enum": ["category", "priority"]
                                        },
                                        "value": {
                                            "type": "string"
                                        }
                                    },
                                    "required": ["key", "value"]
                                }
                            ]
                        }
                    }
                },
                "required": ["name", "status"]
            },
            "arrayField": {
                "type": "array",
                "items": {
                    "oneOf": [
                        {
                            "type": "object",
                            "properties": {
                                "id": {
                                    "type": "integer"
                                },
                                "type": {
                                    "type": "string",
                                    "const": "item"
                                }
                            },
                            "required": ["id", "type"]
                        },
                        {
                            "type": "string",
                            "enum": ["default", "special", "limited"]
                        }
                    ]
                }
            }
        },
        "required": ["basicField", "objectField"]
    }
    """

    response = simulate_response(example)

    assert validate_schema(example, response)
