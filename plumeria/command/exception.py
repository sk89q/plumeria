"""A collection of command-related exceptions."""

__all__ = ('CommandError', 'ArgumentError', 'MissingArgumentError', 'UnusedArgumentsError', 'AuthorizationError',
           'ComplexityError')


class CommandError(Exception):
    """Raised on any command processing error."""


class ArgumentError(CommandError):
    """Raised when there is something wrong with user input."""


class MissingArgumentError(ArgumentError):
    """Raised when the user has not provided enough arguments."""


class UnusedArgumentsError(ArgumentError):
    """Raised when there are unused arguments."""


class AuthorizationError(Exception):
    """Raised when the user does not have sufficient permissions."""


class ComplexityError(Exception):
    """Raised if a command is too complex to complete completely."""
