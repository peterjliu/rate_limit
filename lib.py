#!/usr/bin/env python
"""
Library for rate-limiting.
"""
from google.appengine.api import memcache


class MemcacheWriteError(Exception):
    """Error thrown when memcache compare and set fails too many times."""
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

MEMCACHE_NAMESPACE='rate_limiter'

class Limiter:
    """Object tracking QPS budget per second using App Engine MemCache

    Only Memcache is read/write.

    Args:
        config(dict): Dictionary of event type (int) and 
            (max request budget (int), refresh period seconds (int)).
    """
    # TODO tune this value
    _MAX_RETRIES = 10
    def __init__(self, config):
        self.config = config
        self._client = memcache.Client()

    def CanSpend(self, quota_key, units=1, max_retries=_MAX_RETRIES):
        """Returns true if have budget to spend is within QPS limit

        Args:
            quota_key: QuotaKey object who's budget will be spent.
            max_retries: Number of times to retry writing to memcache.

        Returns:
            True if there is budget to spend and spends units of budget"""
        #  We use compare and set to avoid race conditions.
        #  https://cloud.google.com/appengine/docs/python/memcache/
        key = quota_key.key()
        counter = self._client.gets(key, namespace=MEMCACHE_NAMESPACE)
        if not counter:
            (_, expire_time) = self.config.get(quota_key.event_type)
            self._client.add(key=key,
                         value=units,
                         time=expire_time,
                         namespace=MEMCACHE_NAMESPACE
                         )

            return True
        else:
            retries = 0
            while retries < max_retries: # Retry loop
                (budget, expire_time) = self.config.get(quota_key.event_type)
                if counter >= budget:
                    # Hit max
                    return False
                if self._client.cas(key, counter + units,
                        time=expire_time, namespace=MEMCACHE_NAMESPACE):
                    return True

                counter = self._client.gets(key, namespace=MEMCACHE_NAMESPACE)
                if not counter:
                    # counter may have expired, in which case budget has refilled
                    return True
                retries = retries + 1
            raise MemcacheWriteError(
                    "Maximum failed retries on memcache write.")


class QuotaKey:
    """Object representing a key which can be rate-limited.

        Args:
            name: Unique name of the key (string) for the event_type. That is,
            keys with the same name but different event_type are different keys.
            event_type: Budget type (int)
    """
    def __init__(self, name, event_type):
        self._name = name
        self._event_type = event_type

    def key(self):
        """Memcache name of key."""
        return '%s_%d' % (self._name, self._event_type)

    @property
    def event_type(self):
        return self._event_type
