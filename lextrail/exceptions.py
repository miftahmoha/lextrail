class SymbolNotFound(Exception):
    pass


class InvalidSymbol(Exception):
    pass


class InvalidRegex(Exception):
    pass


class InvalidDelimiters(Exception):
    pass


class MissingQuote(Exception):
    pass


class MissingSlash(Exception):
    pass


class InvalidGrammar(Exception):
    pass


class ParsingError(Exception):
    pass


class InfiniteLoop(Exception):
    pass


class CombineError(Exception):
    pass
