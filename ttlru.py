"""A bounded LRU cache with per-entry TTL, lazy expiry, and an injectable clock.

Python 3.10+, standard library only. Run `python ttlru.py --demo` for an example.
Expired entries are removed before capacity eviction. Reads refresh LRU order,
not TTL. A TTL of zero removes the key. None means no expiry. Not thread-safe.
"""
from collections import OrderedDict
from dataclasses import dataclass
import argparse
import math
import time


@dataclass(frozen=True)
class CacheInfo:
    hits: int
    misses: int
    evictions: int
    expirations: int
    size: int
    capacity: int


class TTLRU:
    """Least-recently-used cache. Keys must be hashable; values may be anything."""
    def __init__(self, capacity=128, default_ttl=None, *, clock=time.monotonic):
        if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity < 1:
            raise ValueError('capacity must be a positive integer')
        self._validate_ttl(default_ttl)
        self.capacity, self.default_ttl, self.clock = capacity, default_ttl, clock
        self._data = OrderedDict()
        self.hits = self.misses = self.evictions = self.expirations = 0

    @staticmethod
    def _validate_ttl(ttl):
        if ttl is not None and (isinstance(ttl, bool) or not isinstance(ttl, (int, float))
                                or not math.isfinite(ttl) or ttl < 0):
            raise ValueError('TTL must be a finite nonnegative number or None')

    def _purge(self, now):
        expired = [key for key, (_, end) in self._data.items()
                   if end is not None and now >= end]
        for key in expired:
            del self._data[key]
        self.expirations += len(expired)
        return len(expired)

    def expire(self):
        """Remove expired entries and return the number removed."""
        return self._purge(self.clock())

    def put(self, key, value, *, ttl='default'):
        """Insert or replace a key. Explicit ttl=None overrides the default TTL."""
        if ttl == 'default':
            ttl = self.default_ttl
        self._validate_ttl(ttl)
        now = self.clock()
        self._purge(now)
        self._data.pop(key, None)
        if ttl == 0:
            return
        self._data[key] = (value, None if ttl is None else now + ttl)
        if len(self._data) > self.capacity:
            self._data.popitem(last=False)
            self.evictions += 1

    def get(self, key, default=None):
        """Fetch a live value, marking it most recently used, or return default."""
        self.expire()
        if key not in self._data:
            self.misses += 1
            return default
        self.hits += 1
        self._data.move_to_end(key)
        return self._data[key][0]

    def delete(self, key):
        """Delete a live key, returning whether it existed."""
        self.expire()
        if key in self._data:
            del self._data[key]
            return True
        return False

    def keys(self):
        """Return live keys from least to most recently used without recording hits."""
        self.expire()
        return list(self._data)

    def clear(self, *, reset_stats=False):
        self._data.clear()
        if reset_stats:
            self.hits = self.misses = self.evictions = self.expirations = 0

    def info(self):
        self.expire()
        return CacheInfo(self.hits, self.misses, self.evictions,
                         self.expirations, len(self._data), self.capacity)

    def __len__(self):
        self.expire()
        return len(self._data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo', action='store_true', help='run a deterministic example')
    args = parser.parse_args()
    if not args.demo:
        parser.print_help()
        return
    now = [0.0]
    cache = TTLRU(2, default_ttl=5, clock=lambda: now[0])
    cache.put('alpha', 10)
    cache.put('beta', 20, ttl=None)
    print('alpha:', cache.get('alpha'))
    cache.put('gamma', 30)
    print('after LRU eviction:', cache.keys())
    now[0] = 5
    print('at expiry boundary:', cache.keys())
    print(cache.info())


if __name__ == '__main__':
    main()
