"""
Implements memoization for functions with arbitrary arguments
"""
import collections
import functools
import hashlib
import inspect
import io
import pickle
import threading
import time
import unittest
import weakref

import unittest.mock

import param

from .state import state

#---------------------------------------------------------------------
# Private API
#---------------------------------------------------------------------

_CYCLE_PLACEHOLDER = b"panel-93KZ39Q-floatingdangeroushomechose-CYCLE"

_NATIVE_TYPES = (
    bytes, str, float, int, bool, bytearray, type(None)
)

_FFI_TYPE_NAMES = ("_cffi_backend.FFI", "builtins.CompiledFFI",)

_HASH_MAP = dict()

_HASH_STACKS = weakref.WeakKeyDictionary()

_INDETERMINATE = type('INDETERMINATE', (object,), {})()

_TIME_FN = time.monotonic

class _Stack(object):

    def __init__(self):
        self._stack = collections.OrderedDict()

    def push(self, val):
        self._stack[id(val)] = val

    def pop(self):
        self._stack.popitem()

    def __contains__(self, val):
        return id(val) in self._stack

def _get_fqn(obj):
    """Get module.type_name for a given type."""
    the_type = type(obj)
    module = the_type.__module__
    name = the_type.__qualname__
    return "%s.%s" % (module, name)

def _int_to_bytes(i):
    num_bytes = (i.bit_length() + 8) // 8
    return i.to_bytes(num_bytes, "little", signed=True)

def _is_native(obj):
    return isinstance(obj, _NATIVE_TYPES)

def _is_native_tuple(obj):
    return isinstance(obj, tuple) and all(_is_native_tuple(v) for v in obj)

def _container_hash(obj):
    h = hashlib.new("md5")
    h.update(_generate_hash(f'__{type(obj).__name__}'))
    for item in (obj.items() if isinstance(obj, dict) else obj):
        h.update(_generate_hash(item))
    return h.digest()

def _partial_hash(obj):
    h = hashlib.new("md5")
    h.update(_generate_hash(obj.args))
    h.update(_generate_hash(obj.func))
    h.update(_generate_hash(obj.keywords))
    return h.digest()

def _pandas_hash(obj):
    import pandas as pd

    if len(obj) >= _PANDAS_ROWS_LARGE:
        obj = obj.sample(n=_PANDAS_SAMPLE_SIZE, random_state=0)
    try:
        return b"%s" % pd.util.hash_pandas_object(obj).sum()
    except TypeError:
        # Use pickle if pandas cannot hash the object for example if
        # it contains unhashable objects.
        return b"%s" % pickle.dumps(obj, pickle.HIGHEST_PROTOCOL)

def _numpy_hash(obj):
    h = hashlib.new("md5")
    h.update(_generate_hash(obj.shape))
    if obj.size >= _NP_SIZE_LARGE:
        import numpy as np
        state = np.random.RandomState(0)
        obj = state.choice(obj.flat, size=_NP_SAMPLE_SIZE)
    h.update(obj.tobytes())
    return h.digest()

def _io_hash(obj):
    h = hashlib.new("md5")
    h.update(_generate_hash(obj.tell()))
    h.update(_generate_hash(obj.getvalue()))
    return h.digest()

_hash_funcs = {
    # Types
    int          : _int_to_bytes,
    str          : lambda obj: obj.encode(),
    float        : lambda obj: _int_to_bytes(hash(obj)),
    bool         : lambda obj: b'1' if obj is True else b'0',
    type(None)   : lambda obj: b'0',
    (bytes, bytearray) : lambda obj: obj,
    (list, tuple, dict): _container_hash,
    functools.partial  : _partial_hash,
    unittest.mock.Mock : lambda obj: _int_to_bytes(id(obj)),
    (io.StringIO, io.BytesIO): _io_hash,
    # Fully qualified type strings
    'numpy.ndarray'              : _numpy_hash,
    'pandas.core.series.Series'  : _pandas_hash,
    'pandas.core.frame.DataFrame': _pandas_hash,
    'builtins.mappingproxy'      : lambda obj: _container_hash(dict(obj)),
    'builtins.dict_items'        : lambda obj: _container_hash(dict(obj)),
    'builtins.getset_descriptor' : lambda obj: obj.__qualname__.encode(),
    "numpy.ufunc"                : lambda obj: obj.__name__.encode(),
    # Functions
    inspect.isbuiltin          : lambda obj: obj.__name__.encode(),
    inspect.ismodule           : lambda obj: obj.__name__
}

for name in _FFI_TYPE_NAMES:
    _hash_funcs[name] = b'0'


def _generate_hash(obj, hash_funcs={}):
    # Break recursive cycles.
    hash_stack = state._current_stack
    if obj in hash_stack:
        return _CYCLE_PLACEHOLDER
    hash_stack.push(obj)

    fqn_type = _get_fqn(obj)
    if fqn_type in hash_funcs:
        hash_func = hash_funcs[fqn_type]
        try:
            output = hash_func(obj)
        except BaseException as e:
            raise ValueError(
                f'User hash function {hash_func!r} failed for input '
                f'type {fqn_type} with following error: '
                f'{type(e).__name__}("{e}").'
            )
        return _generate_hash(output)
    for otype, hash_func in _hash_funcs.items():
        if isinstance(otype, str):
            if otype == fqn_type:
                return hash_func(obj)

        elif inspect.isfunction(otype):
            if otype(obj):
                return hash_func(obj)
        elif isinstance(obj, otype):
            return hash_func(obj)
    if hasattr(obj, '__reduce__'):
        h = hashlib.new("md5")
        try:
            reduce_data = obj.__reduce__()
        except BaseException:
            raise ValueError(f'Could not hash object of type {type(obj).__name__}')
        for item in reduce_data:
            h.update(_generate_hash(item))
        return h.digest()
    return _int_to_bytes(id(obj))

def _key(obj):
    if obj is None:
        return None
    elif _is_native(obj) or _is_native_tuple(obj):
        return obj
    elif isinstance(obj, list):
        if all(_is_native(item) for item in obj):
            return ('__list', *obj)
    elif (
        _get_fqn(obj) == "pandas.core.frame.DataFrame"
        or _get_fqn(obj) == "numpy.ndarray"
        or inspect.isbuiltin(obj)
        or inspect.isroutine(obj)
        or inspect.iscode(obj)
    ):
        return id(obj)
    return _INDETERMINATE

def _cleanup_cache(cache, max_items, ttl, time):
    """
    Deletes items in the cache if the exceed the number of items or
    their TTL (time-to-live) has expired.
    """
    while len(func_cache) >= max_items:
        if policy.lower() == 'fifo':
            key = list(func_cache.keys())[0]
        elif policy.lower() == 'lru':
            key = sorted(((key, time-t) for k, (_, _, _, t) in func_cache.items()),
                         key=lambda o: o[1])[0][0]
        elif policy.lower() == 'lfu':
            key = sorted(func_cache.items(), key=lambda o: o[1][2])[0][0]
        del func_cache[key]
    if ttl is not None:
        for key, (_, ts, _, _) in list(func_cache.items()):
            if (time-ts) > ttl:
                del func_cache[key]

#---------------------------------------------------------------------
# Public API
#---------------------------------------------------------------------

def compute_hash(func, *args, **kwargs):
    """
    Computes a hash given a function and its arguments.

    Arguments
    ---------
    func: callable
        The function to cache.
    args: tuple
        Arguments to hash
    kwargs: dict
        Keyword arguments to hash
    """
    key = (func, _key(args), _key(kwargs))
    if _INDETERMINATE not in key and key in _HASH_MAP:
        return _HASH_MAP[key]
    hasher = hashlib.new("md5")
    if args:
        hasher.update(_generate_hash(hash_args, hash_funcs))
    if kwargs:
        hasher.update(_generate_hash(hash_kwargs, hash_funcs))
    hash_value = hasher.hexdigest()
    if _INDETERMINATE not in key:
        _HASH_MAP[key] = hash_value
    return hash_value


def cache(func=None, hash_funcs=None, max_items=None, policy='LRU', ttl=None):
    """
    Decorator to memoize functions with options to configure the
    caching behavior

    Arguments
    ---------
    func: callable
        The function to cache.

    hash_funcs: dict or None
        A dictionary mapping from a type to a function which returns
        a hash for an object of that type. If provided this will
        override the default hashing function provided by Panel.

    policy: str
        A caching policy when max_items is set, must be one of:
          - FIFO: First in - First out
          - LRU: Least recently used
          - LFU: Least frequently used

    ttl : float or None
        The number of seconds to keep an item in the cache, or None if
        the cache should not expire. The default is None.
    """

    hash_funcs = hash_funcs or {}
    if func is None:
        return lambda f: cache(
            func=f,
            hash_funcs=hash_funcs,
            max_items=max_items,
            ttl=ttl
        )

    lock = threading.RLock()

    @functools.wraps(func)
    def wrapped_func(*args, **kwargs):
        # Handle param.depends method by adding parameters to arguments
        hash_args, hash_kwargs = args, kwargs
        if (
            args and
            isinstance(args[0], param.Parameterized) and
            getattr(type(args[0]), func.__name__) is wrapped_func
        ):
            dinfo = getattr(wrapped_func, '_dinfo')
            hash_args = dinfo['dependencies'] + args[1:]
            hash_kwargs = dict(dinfo['kw'], **kwargs)
        hash_value = compute_hash(func, *hash_args, **hash_kwargs)


        time = _TIME_FN()
        func_cache = state._memoize_cache.get(func)
        if func_cache is None:
            state._memoize_cache[func] = func_cache = collections.OrderedDict()
        else hash_value in func_cache:
            with lock:
                ret, ts, count, _ = func_cache[hash_value]
                func_cache[hash_value] = (ret, ts, count+1, time)
                return ret

        if max_items is not None:
            with lock:
                _cleanup_cache(cache, max_items, ttl, time)

        ret = func(*args, **kwargs)
        with lock:
            func_cache[hash_value] = (ret, time, 0, time)
        return ret

    try:
        wrapped_func.__dict__.update(func.__dict__)
    except AttributeError:
        pass

    return wrapped_func


def clear_cache():
    """
    Clear the memoization cache.
    """
    state._memoize_cache.clear()
