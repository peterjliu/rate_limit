A simple rate-limiting library for Python App Engine that uses Memcache to keep track of quota. 

You might use this library to rate-limit users of your endpoints. Because Memcache can handle a much higher rate of requests (QPS) you can also use this to prevent an abuser from depleting your Datastore quota (denial-of-service attack), e.g. by rate-limiting by IP subnet.

```python
# Example usage

from rate_limit.lib import Limiter, QuotaKey

# Define event types to rate-limit
class Events:
  USER_READ = 1
  USER_WRITE = 2

RATE_LIMIT_SPEC = {
  # Limit User reads QPS to 10, and writes to 1
  Events.USER_READ: (10, 1)
  Events.USER_WRITE: (1, 1)

  # Limit 1 requests every 2 seconds i.e. 0.5 qps
  Events.SMS_VERIFY: (1, 2)
}

l = Limiter(RATE_LIMIT_SPEC)
q = QuotaKey("user1", Events.USER_READ)

try:
  if l.CanSpend(q):
    // Do something expensive
    pass
  else:
    // Return error message, e.g. "Max QPS hit"
    pass
except rate_limit.lib.MemcacheWriteError:
  // Write failed. Need more Memcache provisioned?
  pass
```

