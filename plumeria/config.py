import collections
import configparser
import re
from .util.collections import DefaultOrderedDict

_UNSET = object()


class ParseError(Exception):
    """Raised when a configuration file has errors and cannot be parsed."""


def append(prev, new):
    if prev:
        return prev + "\n" + new
    else:
        return new


class Config:
    def __init__(self, reader, section, key, type=str):
        self.reader = reader
        self.section = section
        self.key = key
        self.type = type


class Value:
    TRUTHY_VALUES = {"yes", "true", "1"}
    FALSY_VALUES = {"no", "false", "0"}

    def __init__(self, value="", comment=None, source="???"):
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
    COMMENT_PATTERN = re.compile("^\\s*(?:#|;|//)(.*)$")
    SECTION_PATTERN = re.compile("^\\s*\\[([^\\]]+)\\]\\s*$")
    VALUE_PATTERN = re.compile("^([^=]+)=(.*)$")

    def __init__(self, target, source):
        self.target = target
        self.source = source
        self.header = None
        self.current_section = None
        self.current_comment = None

    def parse_line(self, line):
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
    def __init__(self):
        self.options = DefaultOrderedDict(lambda: collections.OrderedDict())
        self.header = ""

    def read(self, filenames, encoding='utf-8'):
        if isinstance(filenames, str):
            filenames = [filenames]

        for filename in filenames:
            try:
                with open(filename, "r", encoding=encoding) as f:
                    self.read_file(f, source=filename)
            except IOError as e:
                pass

    def read_file(self, f, source="???"):
        parser = Parser(self.options, source=source)
        for line in f:
            parser.parse_line(line)
        if parser.header:
            self.header = parser.header

    def read_string(self, string, source='<string>'):
        parser = Parser(self.options, source=source)
        for line in string.split("\n"):
            parser.parse_line(line)
        if parser.header:
            self.header = parser.header

    def at(self, section, key):
        if key in self.options[section]:
            return self.options[section][key]

    def get(self, section, key, *, fallback=_UNSET):
        value = self.at(section, key)
        if value is not None:
            return str(value)
        else:
            if fallback == _UNSET:
                raise KeyError("missing '{}' key in section '{}' in config".format(key, section))
            else:
                return fallback

    def set(self, section, key, value, comment=_UNSET):
        v = self.at(section, key)
        if v is None:
            v = self.options[section][key] = Value()
        v.value = value
        if comment != _UNSET:
            v.comment = comment

    def remove_section(self, key):
        if key in self.options:
            del self.options[key]
            return True
        else:
            return False

    def remove_option(self, section, key):
        if not self.has_section(section):
            raise configparser.NoSectionError(section)
        if key in self.options[section]:
            del self.options[section][key]
            return True
        else:
            return False

    def sections(self):
        return set(self.options.keys())

    def has_section(self, section):
        return section in self.options

    def write(self, f, space_around_delimiters=True):
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
    def __init__(self, managed_config, section, key, type=str, fallback=_UNSET, comment=None):
        self.managed_config = managed_config
        self.section = section
        self.key = key
        self.type = type
        self.fallback = fallback
        self.comment = "\n".join((" " + s) for s in comment.splitlines()) if comment else None

    def set(self, value):
        return self.managed_config.reader.set(self.section, self.key, str(value))

    def validate(self, reader):
        self.type(reader.get(self.section, self.key, fallback=self.fallback))

    def __call__(self):
        return self.type(self.__str__())

    def __str__(self):
        return self.managed_config.reader.get(self.section, self.key, fallback=self.fallback)

    def __repr__(self):
        return self.__str__()


class ManagedConfig:
    def __init__(self, file=None):
        self.file = file
        self.reader = ConfigReader()
        self.settings = collections.defaultdict(lambda: {})

    def load(self):
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
                        raise ValueError(
                            "config key '{}' in section '{}' has the invalid configuration value '{}': {}".format(
                                key, section, value, str(e)
                            ))
                    except KeyError as e:
                        raise ValueError("config key '{}' in section '{}' needs to be set")
            self.reader = reader
        except FileNotFoundError as e:
            pass

    def save(self):
        with open(self.file, "w", encoding="utf-8", newline="\r\n") as f:
            for section, settings in self.settings.items():
                for key, setting in settings.items():
                    if setting.fallback:
                        value = self.reader.at(section, key)
                        if value is not None:
                            if not value.comment:
                                value.comment = setting.comment
                        else:
                            self.reader.set(section, key, setting.fallback, comment=setting.comment)
            self.reader.write(f)

    def create(self, section, key, type=str, fallback=_UNSET, comment=None):
        setting = Setting(self, section, key, type, fallback, comment)
        self.settings[section][key] = setting
        return setting


def list_of(type=str):
    def reader(s):
        items = s.split(",")
        items = map(lambda s: s.strip(), items)
        items = filter(lambda s: len(s), items)
        return [type(s) for s in items]

    return reader


def set_of(type=str):
    def reader(s):
        items = s.split(",")
        items = map(lambda s: s.strip(), items)
        items = filter(lambda s: len(s), items)
        return {type(s) for s in items}

    return reader
