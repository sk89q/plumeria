"""
Handles reading and writing configuration files, as well as keeping track of a list of
settings that can be set.

The implementation in Plumeria uses a custom-rolled option that supports persisting comments.

"""

import collections
import configparser
import logging
import re
from typing import Optional, List, Dict, Union, Sequence, Any, Set

from plumeria.util.collections import DefaultOrderedDict, gather_tree_nodes

__all__ = ('Value', 'Parser', 'ParseError', 'ConfigReader', 'Setting', 'ManagedConfig')

logger = logging.getLogger(__name__)

_UNSET = object()


class ParseError(Exception):
    """Raised when a configuration file has errors and cannot be parsed."""


def append(prev: str, new: str) -> str:
    """
    Concatenates two strings, adding a new line character between the two strings
    if the first string is not empty.

    """
    if prev:
        return prev + "\n" + new
    else:
        return new


class Value:
    """
    Container for a configuration value and its associated comment, if any.

    When configuration files are parsed, instances of this class are made and stored with the
    section and key (in the case of an .ini file).

    Attributes
    ----------
    value : str
        The raw value
    comment : Optional[str]
        The comment, if any
    source : str
        Information about where the value came from, such as filename and line number. Contents of this field
        do not necessarily follow any particular syntax but filename:line is recommended if relevant.

    """

    TRUTHY_VALUES = {"yes", "true", "1"}
    FALSY_VALUES = {"no", "false", "0"}

    def __init__(self, value: str = "", comment: Optional[str] = None, source: str = "???"):
        self.value = value
        self.comment = comment
        self.source = source

    def __bool__(self):
        test = self.value.lower()
        if test in self.TRUTHY_VALUES:
            return True
        if test in self.FALSY_VALUES:
            return False
        raise ValueError("'{}' is not a truthy (yes/true/1) or a falsy (no/false/0) value".format(self.value))

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str(self.value)


class Parser:
    """
    Parses a configuration file in .ini format.

    To use the parser, create a new instance and call :method:`parse_line`() on ever line, sequentially.
    Values are put into the supplied "target" nested dictionary. The header can then be retrieved
    at the end from the header attribute.

    Attributes
    ----------
    header : Optional[str]
        The header comment in the file, if any

    """

    COMMENT_PATTERN = re.compile("^\\s*(?:#|;|//)(.*)$")
    SECTION_PATTERN = re.compile("^\\s*\\[([^\\]]+)\\]\\s*$")
    VALUE_PATTERN = re.compile("^([^=]+)=(.*)$")

    def __init__(self, target: Dict[str, Dict[str, Value]], source: str):
        """
        Create a new parser.

        Parameters
        ----------
        target : Dict[str, Dict[str, :class:`Value`]]
            Where configuration values should be placed
        source : str
            The source of the configuration (such as a filename)

        """
        self.target = target
        self.source = source
        self.header = None
        self.current_section = None
        self.current_comment = None

    def parse_line(self, line: str):
        """
        Parse the next line of the file.

        Parameters
        ----------
        line : str
            The line

        Raises
        ------
        :class:`ParseError`
            Raised if there is an error in the configuration file

        """
        line = line.rstrip()

        if not len(line):
            return

        m = self.COMMENT_PATTERN.search(line)
        if m:
            if not self.current_section:
                self.header = append(self.header, m.group(1))
            else:
                self.current_comment = append(self.current_comment, m.group(1))
            return

        m = self.SECTION_PATTERN.search(line)
        if m:
            self.current_section = m.group(1).strip()
            self.current_comment = None
            # create section
            self.target.__getitem__(self.current_section)
            return

        m = self.VALUE_PATTERN.search(line)
        if m:
            if self.current_section:
                self.target[self.current_section][m.group(1).strip()] = Value(
                    m.group(2).strip(),
                    comment=self.current_comment,
                    source=self.source
                )
            self.current_comment = None
            return

        raise ParseError(
            "config file {} has line ({}) that is not a section, comment, or option".format(self.source, line))


class SectionProxy:
    """Internal proxy class for a configuration section."""

    def __init__(self, reader, section):
        self.reader = reader
        self.section = section

    def keys(self):
        if self.reader.has_section(self.section):
            return self.reader.options[self.section].keys()
        else:
            return []

    def values(self):
        if self.reader.has_section(self.section):
            return self.reader.options[self.section].values()
        else:
            return {}

    def __getitem__(self, item):
        return self.reader.get(self.section, item)

    def __setitem__(self, key, value):
        return self.reader.set(self.section, key, value)

    def __delitem__(self, key, value):
        return self.reader.remove_option(self.section, key, value)


class ConfigReader:
    """
    Reads and writes .ini-structured configuration files.

    Values can be read and written as items on the object.

    """

    def __init__(self):
        self.options = DefaultOrderedDict(lambda: collections.OrderedDict())
        self.header = ""

    def read(self, filenames: Union[str, Sequence[str]], encoding: str = 'utf-8'):
        """
        Read a list of config file paths, ignoring files that can't be read (but not parsing
        errors), in order of the names.

        Parameters
        ----------
        filenames
            A list of filenames or a single filename
        encoding : str
            The encoding to read the file in

        Returns
        -------
        :class:`ParseError`
            Raised if there is an error in the configuration file

        """
        if isinstance(filenames, str):
            filenames = [filenames]

        for filename in filenames:
            try:
                with open(filename, "r", encoding=encoding) as f:
                    self.read_file(f, source=filename)
            except IOError as e:
                pass

    def read_file(self, f, source: str = "???"):
        """
        Reads configuration from a file pointer.

        Parameters
        ----------
        f : file-like
            The file pointer
        source : str
            The source of the configuration, such as a filename

        Raises
        ------
        :class:`IOError`
            Raised on any sort of read error
        :class:`ParseError`
            Raised if there is an error in the configuration file

        """
        parser = Parser(self.options, source=source)
        for line in f:
            parser.parse_line(line)
        if parser.header:
            self.header = parser.header

    def read_string(self, string: str, source: str = '<string>'):
        """
        Reads configuration from a file pointer.

        Parameters
        ----------
        f : file-like
            The file pointer
        source : str
            The source of the configuration, such as a filename

        Raises
        ------
        :class:`ParseError`
            Raised if there is an error in the configuration file

        """
        parser = Parser(self.options, source=source)
        for line in string.split("\n"):
            parser.parse_line(line)
        if parser.header:
            self.header = parser.header

    def at(self, section: str, key: str) -> Optional[Value]:
        """
        Gets the :class:`Value` object at a certain section and key.

        Parameters
        ----------
        section : str
            The section
        key : str
            The key

        Returns
        -------
        Optional[:class:`Value`]
            The value, if any

        """
        if key in self.options[section]:
            return self.options[section][key]

    def get(self, section: str, key: str, *, fallback: Optional[Any] = _UNSET) -> Any:
        """
        Gets the value at a certain section and key, raising an exception if the key
        doesn't exist if no fallback is supplied.

        Parameters
        ----------
        section : str
            The section
        key : str
            The key
        fallback : Optional[Any]
            The fallback object if the key doesn't exist

        Returns
        -------
        Any
            The value at the key

        Raises
        ------
        KeyError
            Raised if the section or key don't exist

        """
        value = self.at(section, key)
        if value is not None:
            return str(value)
        else:
            if fallback == _UNSET:
                raise KeyError("missing '{}' key in section '{}' in config".format(key, section))
            else:
                return fallback

    def set(self, section: str, key: str, value: str, comment: Optional[str] = None):
        """
        Set the value at a certain section and key.

        Parameters
        ----------
        section : str
            The section
        key : str
            The key
        value : str
            The value
        comment : Optional[str]
            A comment

        Returns
        -------

        """
        v = self.at(section, key)
        if v is None:
            v = self.options[section][key] = Value()
        v.value = value
        if comment:
            v.comment = comment

    def remove_section(self, key: str) -> bool:
        """
        Remove a section and all of its child keys.

        Parameters
        ----------
        key : str
            The key

        Returns
        -------
        bool
            Whether the key was found

        """
        if key in self.options:
            del self.options[key]
            return True
        else:
            return False

    def remove_option(self, section: str, key: str) -> bool:
        """
        Remove a specific key under a section.

        Parameters
        ----------
        section : str
            The section
        key : str
            The key

        Returns
        -------
        bool
            Whether the key was found

        """
        if not self.has_section(section):
            raise configparser.NoSectionError(section)
        if key in self.options[section]:
            del self.options[section][key]
            return True
        else:
            return False

    def sections(self) -> Set[str]:
        """
        Get a set of section names in the configuration.

        Returns
        -------
        Set[str]
            A set of section names

        """
        return set(self.options.keys())

    def has_section(self, section: str) -> bool:
        """
        Check if a particular section exists in the configuration.

        Parameters
        ----------
        section : str
            The section

        Returns
        -------
        bool
            Whether the section exists

        """
        return section in self.options

    def write(self, f, space_around_delimiters=True):
        """
        Write the configuration data to a file in .ini format.

        Parameters
        ----------
        f : file-like
            Where to write the data
        space_around_delimiters : bool
            Whether there should be spaces around '=' on keys

        """
        if self.header:
            for line in self.header.split("\n"):
                f.write("#" + line.rstrip() + "\n")
            f.write("\n")
        for section, options in self.options.items():
            f.write("[" + section + "]\n")
            for key, value in options.items():
                if value.comment:
                    for line in value.comment.split("\n"):
                        f.write("#" + line.rstrip() + "\n")

                if space_around_delimiters:
                    f.write("{} = {}\n".format(key, str(value)))
                else:
                    f.write("{}={}\n".format(key, str(value)))
            f.write("\n")

    def __getitem__(self, item):
        return SectionProxy(self, item)

    def __delitem__(self, key):
        self.remove_section(key)


class Setting:
    """
    A setting is a registered configuration option.

    While configuration data can be read from a :class:`ConfigReader` directly, configuration
    values wouldn't be validated and the user's configuration file wouldn't have the
    option appear in it for the user to see and modify. The purpose of a setting is to
    declare that a particular configuration setting exists and can be validated a certain way.

    Instances of this class aren't created directly. They are created by creating a setting
    on an instance of a :class:`ManagedConfig`.

    Attributes
    ----------
    section : str
        The section
    key : str
        The key
    fallback : Optional[Any]
        The fallback value if the configuration value is not set
    comment : Optional[str]
        The default comment of the setting, which will be written to the configuration file
    scoped : bool
        Whether the setting can have a scope such as server-wide or channel-wide, which also means
        that the setting can be set by end-users
    private : bool
        Whether the setting's value should be kept private and never displayed publicly

    """

    def __init__(self, managed_config, section, key, type=str, fallback=_UNSET, comment=None, scoped=False,
                 private=True):
        self.managed_config = managed_config
        self.section = section
        self.key = key
        self.type = type
        self.fallback = fallback
        self.comment = "\n".join((" " + s) for s in comment.splitlines()) if comment else None
        self.scoped = scoped
        self.private = private

    def set(self, value: str):
        """
        Set the value of this setting.

        Parameters
        ----------
        value : str
            The value

        """
        return self.managed_config.reader.set(self.section, self.key, str(value))

    def validate(self, reader: ConfigReader):
        """
        Make sure that the value set on this configuration is valid.

        Parameters
        ----------
        reader : :class:`ConfigReader`
            The configuration reader

        Raises
        ------
        ValueError:
            Raised when the value is invalid

        """
        self.type(reader.get(self.section, self.key, fallback=self.fallback))

    def __call__(self):
        return self.type(self.__str__())

    def __str__(self):
        return self.managed_config.reader.get(self.section, self.key, fallback=self.fallback)

    def __repr__(self):
        return self.__str__()


class ManagedConfig:
    """
    Keeps track of configuration data and settings.

    Configuration data consists simply of dictionaries of raw string values read from
    supplied configuration files.

    Settings, however, are formally registered configuration options. Plugins may register
    settings with an instance of this class (there is a global instance in Plumeria), which enables
    enumeration of all editable settings. Settings also have a data type associated with them,
    which permits the validation of user-supplied values.

    The use of settings is optional. Raw string configuration values be read by accessing the
    underlying :class:`ConfigReader` if registering settings is not practical for a particular scenario.

    Example of registering a setting:

    .. code-block: python

        port = config.create("server", "port", type=int, fallback=80, comment="The port of the server")

    Such a setting would appear in the user's configuration file as:

    .. code-block: ini

        [server]
        # The port of the server
        port = 80

    The fallback value is written if the user hasn't specified the particular setting yet. Comments
    are also written alongside the setting, but the comment won't replace existing comments.

    To actually get a validated and type-casted value, call the object:

    .. code-block: python

        start_server('0.0.0.0', port())

    Attributes
    ----------
    reader : :class:`ConfigReader`
        The configuration reader

    """

    def __init__(self, file: Optional[str] = None):
        """
        Create a new instance.

        Parameters
        ----------
        file : Optional[str]
            The path of the configuration file

        """
        self.file = file
        self.reader = ConfigReader()
        self.settings = collections.defaultdict(lambda: {})

    def load(self):
        """
        Load configuration data from file and validate options.

        If the file does not exist, nothing will happen.

        Raises
        ------
        IOError:
            Raised on read error

        """
        if not self.file:
            raise ValueError("No configuration file configured")
        try:
            reader = ConfigReader()
            with open(self.file, "r", encoding="utf-8") as f:
                reader.read_file(f)
            for section, settings in self.settings.items():
                for key, setting in settings.items():
                    try:
                        setting.validate(reader)
                    except ValueError as e:
                        value = reader.get(section, key, fallback='(undefined)')
                        logger.warning(
                            "config key '{}' in section '{}' has the invalid configuration value '{}': {}".format(
                                key, section, value, str(e)
                            ))
                    except KeyError as e:
                        logger.warning("config key '{}' in section '{}' needs to be set".format(key, section))
            self.reader = reader
        except FileNotFoundError as e:
            pass

    def save(self):
        """
        Save configuration data back to the file.

        New configuration values will be written.

        Raises
        ------
        IOError:
            Raised on write error

        """
        with open(self.file, "w", encoding="utf-8", newline="\r\n") as f:
            for section, settings in self.settings.items():
                for key, setting in settings.items():
                    if setting.fallback != _UNSET:
                        value = self.reader.at(section, key)
                        if value is not None:
                            if not value.comment:
                                value.comment = setting.comment
                        else:
                            self.reader.set(section, key, setting.fallback, comment=setting.comment)
            self.reader.write(f)

    def create(self, section: str, key: str, type=str, fallback: Any = _UNSET, comment: Optional[str] = None,
               scoped: bool = False, private: bool = True) -> Setting:
        """
        Create a new registered setting.

        Parameters
        ----------
        section : str
            The section
        key : str
            The key
        type
            The type of the value, which needs to be a callable function that accepts the raw string value and converts
            it to the actual value
        fallback
            The fallback balue
        comment : Optional[str]
            The comment, if any, to be written alongside the setting
        scoped : bool
            If true, the setting can be set on a per-server and server-channel basis
        private : bool
            If true, the value of the setting will never be shown publicly

        Returns
        -------
        :class:`Setting`
            The setting object, which can be used to fetch the parsed value of the setting

        """
        setting = Setting(self, section, key, type, fallback, comment, scoped, private)
        self.settings[section][key] = setting
        return setting

    def get_setting(self, section, key) -> Optional[Setting]:
        """
        Gets a setting that has been previously registered.

        Parameters
        ----------
        section : str
            The section
        key : str
            The key

        Returns
        -------
        :class:`Setting`
            The setting

        Raises
        ------
        KeyError
            If the setting hasn't been registered yet

        """
        if section in self.settings and key in self.settings[section]:
            return self.settings[section][key]
        else:
            raise KeyError("{} / {}".format(section, key))

    def get_settings(self, scoped: Optional[bool] = None) -> List[Setting]:
        """
        Get a list of settings that have been registered.

        Parameters
        ----------
        scoped : Optional[bool]
            If set, then only scoped or unscope (depending on value) settings will be returned

        Returns
        -------
        List[:class:`Setting`]
            A list of settings

        """
        results = []
        gather_tree_nodes(results, self.settings)
        if scoped is not None:
            results = list(filter(lambda s: s.scoped == scoped, results))
        return results
