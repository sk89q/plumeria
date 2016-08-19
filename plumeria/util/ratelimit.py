from functools import wraps
from time import time

import collections


class RateLimitExceeded(Exception):
    pass


class TokenBucket(object):
    """An implementation of the token bucket algorithm.

    >>> bucket = TokenBucket(80, 0.5)
    >>> print bucket.consume(10)
    True
    >>> print bucket.consume(90)
    False

    From https://code.activestate.com/recipes/511490-implementation-of-the-token-bucket-algorithm/
    """

    def __init__(self, tokens, fill_rate):
        """tokens is the total tokens in the bucket. fill_rate is the
        rate in tokens/second that the bucket will be refilled."""
        self.capacity = float(tokens)
        self._tokens = float(tokens)
        self.fill_rate = float(fill_rate)
        self.timestamp = time()

    def can_consume(self, tokens):
        return tokens <= self.tokens

    def consume(self, tokens):
        """Consume tokens from the bucket. Returns True if there were
        sufficient tokens otherwise False."""
        if tokens <= self.tokens:
            self._tokens -= tokens
        else:
            return False
        return True

    def get_tokens(self):
        if self._tokens < self.capacity:
            now = time()
            delta = self.fill_rate * (now - self.timestamp)
            self._tokens = min(self.capacity, self._tokens + delta)
            self.timestamp = now
        return self._tokens

    tokens = property(get_tokens)


class MessageTokenBucket:
    def __init__(self, global_tokens, server_tokens, channel_tokens, user_tokens, fill_rate):
        self.all = TokenBucket(global_tokens, fill_rate)
        self.servers = collections.defaultdict(lambda: TokenBucket(server_tokens, fill_rate))
        self.channels = collections.defaultdict(lambda: TokenBucket(channel_tokens, fill_rate))
        self.users = collections.defaultdict(lambda: TokenBucket(user_tokens, fill_rate))

    def consume(self, message):
        if message.channel.is_private:
            return self.users[message.author.id].consume(1)
        else:
            buckets = {
                "global": self.all,
                "server " + message.channel.server.name: self.servers[message.channel.server.id],
                "channel " + message.channel.name: self.channels[message.channel.id],
                "user " + message.author.name: self.users[message.author.id],
            }
            for key, bucket in buckets.items():
                if not bucket.can_consume(1):
                    raise RateLimitExceeded("Rate limit exceeded for {} ({}/{} with fill rate={})".format(
                        key,
                        bucket.tokens,
                        bucket.capacity,
                        bucket.fill_rate
                    ))
            for bucket in buckets.values():
                bucket.consume(1)


def rate_limit(burst_size=10, fill_rate=0.5):
    bucket = TokenBucket(burst_size, fill_rate)

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if bucket.consume(1):
                return f(*args, **kwargs)
            else:
                raise RateLimitExceeded()

        return wrapper

    return decorator
