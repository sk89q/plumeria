import io
import pkg_resources
import pytest
from ..config import ConfigReader, ManagedConfig, list_of, set_of


def test_read():
    c = ConfigReader()

    with pkg_resources.resource_stream(__name__, "data/example_config.ini") as f:
        with io.TextIOWrapper(f, encoding="utf-8") as stream:
            c.read_file(stream, source="source1")

            assert c.sections() == {"person", "vehicle", "project", "empty", "PROJECT"}

            assert c.header == ' This is an example\n   comment'

            assert c.get('person', 'name') == '\u0422\u0438\u043c\u0443\u0440 \u0424\u0440\u043e\u043b\u043e\u0432'
            assert c.at('person', 'name').comment == " the NAME"
            assert c.at('person', 'name').source == 'source1'

            assert c.get('person', 'age') == '44'
            assert c.at('person', 'age').comment == " \u0432\u044a\u0437\u0440\u0430\u0441\u0442\n (the age)"

            assert c.get('vehicle', 'type') == 'Cranador'
            assert c.at('vehicle', 'type').comment is None

            assert c.get('vehicle', 'max_speed') == '80'
            assert c.at('vehicle', 'max_speed').comment == " 1st speed"

            assert c.get('vehicle', 'MAX_SPEED') == '2'
            assert c.at('vehicle', 'MAX_SPEED').comment == " second speed"

            assert c.get('project', 'name') == 'bib'
            assert c.at('project', 'name').comment is None

            assert c.get('project', '\u8edf\u4ef6\u7248\u672c') == '1.2'
            assert c.at('project', '\u8edf\u4ef6\u7248\u672c').comment is None

    with pkg_resources.resource_stream(__name__, "data/example_config_overlay.ini") as f:
        with io.TextIOWrapper(f, encoding="utf-8") as stream:
            c.read_file(stream, source='source2')

            assert c.header == ' This is an example\n   comment'

            assert c.get('person', 'name') == 'bobby'
            assert c.at('person', 'name').comment == " new name"
            assert c.at('person', 'name').source == 'source2'

            assert c.get('vehicle', 'MAX_SPEED') == '2'
            assert c.at('vehicle', 'MAX_SPEED').comment == " second speed"
            assert c.at('vehicle', 'MAX_SPEED').source == 'source1'


def test_set():
    c = ConfigReader()
    c.set("server", "host", "localhost", comment="the host")
    assert c.get("server", "host") == "localhost"
    assert c.at("server", "host").comment == "the host"
    c.set("server", "host", "127.0.0.1")
    assert c.get("server", "host") == "127.0.0.1"
    assert c.at("server", "host").comment == "the host"
    c.set("server", "host", "example.com", comment=None)
    assert c.get("server", "host") == "example.com"
    assert c.at("server", "host").comment is None


def test_write():
    c = ConfigReader()

    with pkg_resources.resource_stream(__name__, "data/example_config_write.ini") as f:
        with io.TextIOWrapper(f, encoding="utf-8", newline="\r\n") as stream:
            expected = stream.read()

    with pkg_resources.resource_stream(__name__, "data/example_config.ini") as f:
        with io.TextIOWrapper(f, encoding="utf-8") as stream:
            c.read_file(stream)

    buffer = io.StringIO(newline="\r\n")
    c.write(buffer, space_around_delimiters=True)
    assert buffer.getvalue() == expected


def test_managed_config(tmpdir):
    file = tmpdir.join('config.ini')
    file.write("[person]\n"
               "# this is the age\n"
               "age = 50\n"
               "color = green\n"
               "size = s")
    c = ManagedConfig(str(file))
    c.load()
    c.create("person", "name", fallback="Bob", comment="the name")
    c.create("person", "age", type=int, fallback=23, comment="the age")
    c.create("person", "color", fallback="red", comment="and lastly")
    c.save()
    assert file.read() == '[person]\n' \
                          '# this is the age\n' \
                          'age = 50\n' \
                          '# and lastly\n' \
                          'color = green\n' \
                          'size = s\n' \
                          '# the name\n' \
                          'name = Bob\n\n'


def test_managed_load(tmpdir):
    file = tmpdir.join('config.ini')
    file.write("[person]\n"
               "# this is the age\n"
               "age = happy\n"
               "color = green")
    c = ManagedConfig(str(file))
    c.create("person", "name", fallback="Bob", comment="the name")
    c.create("person", "age", type=int, fallback=23, comment="the age")
    with pytest.raises(ValueError):
        c.load()


def test_managed_set(tmpdir):
    file = tmpdir.join('config.ini')
    file.write("[person]\n"
               "# this is the age\n"
               "age = 15\n"
               "color = green")
    c = ManagedConfig(str(file))
    c.load()
    setting = c.create("person", "age", type=int, fallback=23, comment="the age")
    assert setting() == 15
    setting.set(12)
    assert setting() == 12
    c.save()
    c.load()
    assert file.read() == '[person]\n' \
                          '# this is the age\n' \
                          'age = 12\n' \
                          'color = green\n\n'


def test_list_of():
    assert list_of()("") == []
    assert list_of()(",") == []
    assert list_of()(",apple,banana,,pear,PEAR,pear") == ['apple', 'banana', 'pear', 'PEAR', 'pear']
    assert list_of(type=int)("20,40,,90,15,,20,") == [20, 40, 90, 15, 20]
    with pytest.raises(ValueError):
        list_of(type=int)("twenty,40,,90,15,,20,")


def test_set_of():
    assert set_of()("") == set()
    assert set_of()(",") == set()
    assert set_of()(",apple,banana,,pear,PEAR,pear") == {'apple', 'banana', 'pear', 'PEAR'}
    assert set_of(type=int)("20,40,,90,15,,20,") == {20, 40, 90, 15}
    with pytest.raises(ValueError):
        set_of(type=int)("twenty,40,,90,15,,20,")

