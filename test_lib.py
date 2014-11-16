#!/usr/bin/env python
"""
Test rate-limiter lib
"""
import logging
import sys
import time
import unittest
from google.appengine.api import memcache
from google.appengine.ext import testbed
from lib import Limiter, QuotaKey  

class Events:
  USER_READ = 1
  USER_WRITE = 2

RATE_LIMIT_SPEC = {
        Events.USER_READ: (2, 1),
        Events.USER_WRITE: (5, 1)
}

class RateLimitTestCase(unittest.TestCase):

    def setUp(self):
        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()
        # Next, declare which service stubs you want to use.
        self.testbed.init_memcache_stub()
        self.limiter = Limiter(RATE_LIMIT_SPEC)

    def tearDown(self):
        self.testbed.deactivate()

    def testRateLimiter(self):

        q = QuotaKey("user1", Events.USER_READ)

        # Unfortunately there's no obvious way to inject a clock into the
        # memcache stub, so we assume the following runs in less than 1 sec.
        for _ in range(0, 2):
            self.assertTrue(self.limiter.CanSpend(q))

        # We used up our budget of 2 in less than 1 second
        self.assertFalse(self.limiter.CanSpend(q))

        q = QuotaKey("user2", Events.USER_WRITE)
        for _ in range(0, 5):
            self.assertTrue(self.limiter.CanSpend(q))
        self.assertFalse(self.limiter.CanSpend(q))

    def testRateLimiterWithExpiration(self):
        l = Limiter(RATE_LIMIT_SPEC)
        q = QuotaKey("user1", Events.USER_READ)
        log = logging.getLogger("rate_limit.lib.test")
        for _ in range(0, 2):
            self.assertTrue(self.limiter.CanSpend(q))

        # Expire cache by waiting. Too bad we can't inject the time, eh?
        log.info("wait 1 second for cache to expire")
        time.sleep(1)
        for _ in range(0, 2):
            self.assertTrue(self.limiter.CanSpend(q))



if __name__ == '__main__':
    logging.basicConfig(stream=sys.stderr)
    logging.getLogger("rate_limit.lib.test" ).setLevel( logging.DEBUG )
    unittest.main()

