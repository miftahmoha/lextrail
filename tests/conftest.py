import os


def pytest_configure():
    os.environ["PARSE_REGEX"] = "0"
    os.environ["SPLIT_CHARS"] = "0"
