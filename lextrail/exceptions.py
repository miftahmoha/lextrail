class BuildError(Exception):
    pass


class SyntaxError(BuildError):
    pass


class RegexError(BuildError):
    pass


class InvalidLexeme(BuildError):
    pass


class InvalidDelimiters(BuildError):
    pass


class MissingQuote(BuildError):
    pass


class MissingSlash(BuildError):
    pass


class SymbolNotFound(Exception):
    pass


class InvalidRegex(Exception):
    pass


class InvalidGrammar(Exception):
    pass


class ParsingError(Exception):
    pass


class InfiniteLoop(Exception):
    pass


class AssemblyError(Exception):
    pass
