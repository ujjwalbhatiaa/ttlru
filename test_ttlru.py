import unittest
from ttlru import TTLRU


class CacheTests(unittest.TestCase):
    def setUp(self):
        self.now = 0
        self.c = TTLRU(2, clock=lambda: self.now)

    def test_roundtrip(self):
        self.c.put('a', None)
        self.assertIsNone(self.c.get('a', 'missing'))
        self.assertEqual(self.c.get('b', 'missing'), 'missing')
        self.assertEqual((self.c.info().hits, self.c.info().misses), (1, 1))

    def test_lru(self):
        self.c.put('a', 1)
        self.c.put('b', 2)
        self.c.get('a')
        self.c.put('c', 3)
        self.assertEqual(self.c.keys(), ['a', 'c'])
        self.assertEqual(self.c.info().evictions, 1)

    def test_expiry_boundary(self):
        self.c.put('a', 1, ttl=2)
        self.now = 1.999
        self.assertEqual(self.c.get('a'), 1)
        self.now = 2
        self.assertIsNone(self.c.get('a'))
        self.assertEqual(self.c.info().expirations, 1)

    def test_read_does_not_refresh_ttl(self):
        self.c.put('a', 1, ttl=2)
        self.now = 1
        self.c.get('a')
        self.now = 2
        self.assertEqual(len(self.c), 0)

    def test_expire_before_eviction(self):
        self.c.put('a', 1)
        self.c.put('b', 2, ttl=1)
        self.now = 1
        self.c.put('c', 3)
        self.assertEqual(self.c.keys(), ['a', 'c'])
        self.assertEqual(self.c.info().evictions, 0)

    def test_replace_refreshes_ttl_and_recency(self):
        self.c.put('a', 1, ttl=1)
        self.c.put('b', 2)
        self.now = .5
        self.c.put('a', 3, ttl=2)
        self.now = 1
        self.assertEqual(self.c.get('a'), 3)
        self.assertEqual(self.c.keys(), ['b', 'a'])
        self.now = 2.5
        self.assertEqual(self.c.keys(), ['b'])

    def test_default_ttl_and_override(self):
        c = TTLRU(3, default_ttl=1, clock=lambda: self.now)
        c.put('a', 1)
        c.put('b', 2, ttl=None)
        self.now = 1
        self.assertEqual(c.keys(), ['b'])

    def test_zero_ttl_removes(self):
        self.c.put('a', 1)
        self.c.put('a', 2, ttl=0)
        self.assertEqual(len(self.c), 0)

    def test_delete(self):
        self.c.put('a', 1)
        self.assertTrue(self.c.delete('a'))
        self.assertFalse(self.c.delete('a'))

    def test_clear_stats(self):
        self.c.get('missing')
        self.c.clear()
        self.assertEqual(self.c.info().misses, 1)
        self.c.clear(reset_stats=True)
        self.assertEqual(self.c.info().misses, 0)

    def test_invalid_config(self):
        for cap in (0, -1, 1.5, True):
            with self.assertRaises(ValueError):
                TTLRU(cap)
        for ttl in (-1, float('nan'), float('inf'), '2', True):
            with self.assertRaises(ValueError):
                self.c.put('a', 1, ttl=ttl)

    def test_capacity_one_and_hashable_keys(self):
        c = TTLRU(1)
        c.put(('a', 1), 2)
        c.put(7, 3)
        self.assertEqual(c.keys(), [7])


if __name__ == '__main__':
    unittest.main()
