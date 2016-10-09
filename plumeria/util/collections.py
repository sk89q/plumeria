from collections import OrderedDict, Callable

import collections


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
