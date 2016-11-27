"""Classes to parse command arguments into validated values."""

import re
from typing import Sequence, Dict, Any, Tuple

from plumeria.command.exception import *

__all__ = ('Parser', 'Parameter', 'Word', 'Float', 'Int', 'Text')

NEXT_WORD_RE = re.compile("^\s*([^\s]+)(.*)$")
_UNSET = object()


class Parameter:
    """
    A parameter parses arguments from a user supplied string.

    To create a new type of parameter, simply subclass this class:

    .. code-block: python

        class MyParameter(Parameter):
            def parse(self, text: str) -> Tuple[str, str]:
                return "value", text

    Attributes
    ----------
    name : str
        The name of the parameter
    fallback : Any
        A fallback for when no value is provided. Without a fallback, a MissingArgumentError will be
        raised during parsing if the user does not supply a value

    """

    def __init__(self, name, fallback=_UNSET):
        self.name = name
        self.fallback = fallback

    def parse(self, text: str) -> Tuple[Any, str]:
        """
        Parses the given text for arguments.

        Implementations must override this method.

        Parameters
        ----------
        text : str
            User input string to parse

        Returns
        -------
        (Any, str)
            Return the parsed value and the remaining text

        """
        raise NotImplemented()

    def __call__(self, text):
        try:
            return self.parse(text)
        except MissingArgumentError as e:
            if self.fallback != _UNSET:
                return self.fallback, text
            else:
                raise e


class Parser:
    """
    Parses user arguments into validated parameters.

    The parser takes a list of :code:`Parameter` objects that extract arguments from
    a supplied string.

    .. code-block: python

        parser = Parser()
        args = parser.parse("frank 99", [Word('name'), Int('age')])
        assert args['name'] == 'frank'
        assert args['age'] == 99

    """

    def parse(self, text: str, params: Sequence[Parameter]) -> Dict[str, Any]:
        """
        Parses some text into arguments.

        Optional parameters should have a fallback set. If there are remaining arguments
        that are not consumed, :code:`UnusedArgumentsError` will be thrown.

        Parameters
        ----------
        text : str
            The text to parse
        params
            A list of parameter parsers

        Returns
        -------
        dict
            A dictionary of parsed arguments

        Raises
        ------
        :class:`ArgumentError`
            Any kind of incorrect, missing, or superfluous argument
        :class:`UnusedArgumentsError`
            Thrown if there are unconsumed arguments

        """
        args = {}
        for param in params:
            value, text = param(text)
            args[param.name] = value
        if len(text.strip()):
            raise UnusedArgumentsError("Not all parameters were used ('{}' wasn't used)".format(text.strip()))
        return args


class Word(Parameter):
    """Parses a single word."""

    def parse(self, text: str) -> Tuple[str, str]:
        m = NEXT_WORD_RE.search(text)
        if m:
            return m.group(1).strip(), m.group(2)
        else:
            raise MissingArgumentError(
                "You didn't provide enough parameters for the command! Supply a **{}**.".format(self.name))


class Float(Word):
    """Parses a single floating-point number."""

    def parse(self, text: str) -> Tuple[float, str]:
        value, text = super().__call__(text)
        try:
            return float(value), text
        except ValueError:
            raise ArgumentError("'{}' isn't a number".format(value))


class Int(Word):
    """Parses a single integer."""

    def parse(self, text: str) -> Tuple[int, str]:
        value, text = super().__call__(text)
        try:
            return int(value), text
        except ValueError:
            raise ArgumentError("'{}' isn't a number".format(value))


class Text(Parameter):
    """Consumes the rest of the arguments."""

    def parse(self, text: str) -> Tuple[str, str]:
        s = text.strip()
        if not len(s):
            raise MissingArgumentError(
                "You didn't provide enough parameters for the command! Supply a **{}**.".format(self.name))
        return s, ""
