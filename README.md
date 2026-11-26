# ttlru

A small Python LRU cache with per-entry time-to-live, deterministic tests and no dependencies.

## Run

Python 3.10 or newer. Download the files together, then:

```sh
python ttlru.py --demo
python -m unittest -v
```

## Use as a library

```python
from ttlru import TTLRU

cache = TTLRU(capacity=100, default_ttl=60)
cache.put('answer', 42)
cache.put('config', {'mode': 'local'}, ttl=None)  # no expiry
print(cache.get('answer'))
print(cache.info())
```

## Semantics

- Time uses `time.monotonic` by default. Tests inject a fake clock, so no sleeping is needed.
- An entry expires at `now >= inserted_at + ttl`. Reads update recency but never extend TTL.
- A write replaces the value, TTL and recency. Zero TTL removes a key; negative and nonfinite TTLs are rejected.
- Expired entries are purged before capacity eviction. Evictions and expirations have separate counters.
- Missing keys return the supplied default. Stored `None` values remain valid hits.
- `keys()` returns least to most recently used. Inspection does not record hits or refresh recency.
- `clear()` retains counters unless `reset_stats=True`.

## Tradeoffs

This is an educational, in-process cache, not a distributed cache. It is not thread-safe. Lazy expiry scans all entries, so each operation is O(n) in cache size, while LRU reordering and eviction use OrderedDict. Expired values occupy memory until another operation runs. An injected clock should be monotonic.

Twelve unit tests cover TTL boundaries, LRU ordering, replacement, expiry before eviction, defaults, deletion, zero TTL, statistics and invalid inputs.
