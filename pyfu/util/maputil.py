__author__ = 'Dan Barrese'
__pythonver__ = '3.5'


def has_nested_key(map, delimited_key, delimiter='.'):
    keys = delimited_key.split(delimiter)
    map_copy = map
    for k in keys[:-1]:
        map_copy = map_copy.setdefault(k, {})
    return keys[-1] in map_copy


def get_nested_value(map, delimited_key, delimiter='.'):
    keys = delimited_key.split(delimiter)
    map_copy = map
    for k in keys[:-1]:
        map_copy = map_copy.setdefault(k, {})
    return map_copy[keys[-1]]


def add_nested(map, delimited_key, value, delimiter='.'):
    keys = delimited_key.split(delimiter)
    for k in keys[:-1]:
        map = map.setdefault(k, {})
    map[keys[-1]] = value
