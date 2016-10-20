from collections import OrderedDict, Callable

import collections
from typing import List, Tuple, Dict, Optional, Iterable
from typing import Union


class SafeStructure:
    """
    A wrapper around dictionaries and lists that allows safe
    traversal through None values.

    """

    def __init__(self, o: Optional[Union[Iterable, List, Tuple, Dict]]):
        """
        Create a new instance.

        Parameters
        ----------
        o : Optional[Union[Iterable, List, Tuple, Dict]]
            The object to wrap
        """
        self.o = o

    def _wrap(self, o):
        if o is None:
            return SafeStructure(None)
        elif isinstance(o, dict) or isinstance(o, list) or isinstance(o, tuple):
            return SafeStructure(o)
        else:
            return o

    def __bool__(self):
        return bool(self.o)

    def __len__(self):
        return len(self.o)

    def __getattr__(self, item):
        try:
            return self._wrap(self.o[item])
        except (IndexError, KeyError, TypeError):
            return self._wrap(None)

    def __getitem__(self, item):
        if self.o is None:
            return self._wrap(None)
        return self._wrap(self.o.__getitem__(item))

    def __contains__(self, item):
        return self.o.__contains__(item)

    def __iter__(self):
        if self.o is not None:
            for o in self.o:
                yield self._wrap(o)

    def __str__(self, *args, **kwargs):
        return self.o.__str__(*args, **kwargs)

    def __repr__(self, *args, **kwargs):
        return self.o.__repr__(*args, **kwargs)


class DefaultOrderedDict(OrderedDict):
    # Source: http://stackoverflow.com/a/6190500/562769
    def __init__(self, default_factory=None, *a, **kw):
        if (default_factory is not None and
                not isinstance(default_factory, Callable)):
            raise TypeError('first argument must be callable')
        OrderedDict.__init__(self, *a, **kw)
        self.default_factory = default_factory

    def __getitem__(self, key):
        try:
            return OrderedDict.__getitem__(self, key)
        except KeyError:
            return self.__missing__(key)

    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key)
        self[key] = value = self.default_factory()
        return value

    def __reduce__(self):
        if self.default_factory is None:
            args = tuple()
        else:
            args = self.default_factory,
        return type(self), args, None, None, self.items()

    def copy(self):
        return self.__copy__()

    def __copy__(self):
        return type(self)(self.default_factory, self)

    def __deepcopy__(self, memo):
        import copy
        return type(self)(self.default_factory,
                          copy.deepcopy(self.items()))

    def __repr__(self):
        return 'OrderedDefaultDict(%s, %s)' % (self.default_factory,
                                               OrderedDict.__repr__(self))


# From requests (Apache 2 License)
class CaseInsensitiveDict(collections.MutableMapping):
    """A case-insensitive ``dict``-like object.
    Implements all methods and operations of
    ``collections.MutableMapping`` as well as dict's ``copy``. Also
    provides ``lower_items``.
    All keys are expected to be strings. The structure remembers the
    case of the last key to be set, and ``iter(instance)``,
    ``keys()``, ``items()``, ``iterkeys()``, and ``iteritems()``
    will contain case-sensitive keys. However, querying and contains
    testing is case insensitive::
        cid = CaseInsensitiveDict()
        cid['Accept'] = 'application/json'
        cid['aCCEPT'] == 'application/json'  # True
        list(cid) == ['Accept']  # True
    For example, ``headers['content-encoding']`` will return the
    value of a ``'Content-Encoding'`` response header, regardless
    of how the header name was originally stored.
    If the constructor, ``.update``, or equality comparison
    operations are given keys that have equal ``.lower()``s, the
    behavior is undefined.
    """

    def __init__(self, data=None, **kwargs):
        self._store = OrderedDict()
        if data is None:
            data = {}
        self.update(data, **kwargs)

    def __setitem__(self, key, value):
        # Use the lowercased key for lookups, but store the actual
        # key alongside the value.
        self._store[key.lower()] = (key, value)

    def __getitem__(self, key):
        return self._store[key.lower()][1]

    def __delitem__(self, key):
        del self._store[key.lower()]

    def __iter__(self):
        return (casedkey for casedkey, mappedvalue in self._store.values())

    def __len__(self):
        return len(self._store)

    def lower_items(self):
        """Like iteritems(), but with all lowercase keys."""
        return (
            (lowerkey, keyval[1])
            for (lowerkey, keyval)
            in self._store.items()
        )

    def __eq__(self, other):
        if isinstance(other, collections.Mapping):
            other = CaseInsensitiveDict(other)
        else:
            return NotImplemented
        # Compare insensitively
        return dict(self.lower_items()) == dict(other.lower_items())

    # Copy is required
    def copy(self):
        return CaseInsensitiveDict(self._store.values())

    def __repr__(self):
        return str(dict(self.items()))


# From requests (Apache 2 License)
class LookupDict(dict):
    """Dictionary lookup object."""

    def __init__(self, name=None):
        self.name = name
        super(LookupDict, self).__init__()

    def __repr__(self):
        return '<lookup \'%s\'>' % (self.name)

    def __getitem__(self, key):
        # We allow fall-through here, so values default to None

        return self.__dict__.get(key, None)

    def get(self, key, default=None):
        return self.__dict__.get(key, default)


def tree():
    return collections.defaultdict(tree)


def tree_get(node, keys):
    for key in keys:
        if key in node:
            node = node[key]
        else:
            return None
    return node


def tree_delete(node, keys):
    last_index = len(keys) - 1
    for i, key in enumerate(keys):
        if i == last_index:
            if key in node:
                del node[key]
                return True
        elif key in node:
            node = node[key]
        else:
            return False


def gather_tree_nodes(results, node):
    for k, v in node.items():
        if isinstance(v, dict):
            gather_tree_nodes(results, v)
        else:
            results.append(v)
