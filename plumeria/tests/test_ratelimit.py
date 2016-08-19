from collections import namedtuple

import pytest
from ..message import Message
from ..util.ratelimit import MessageTokenBucket, RateLimitExceeded

MockServer = namedtuple("MockServer", "id name")
MockChannel = namedtuple("MockChannel", "server id name is_private")
MockUser = namedtuple("MockUser", "id name")

test_server = MockServer("test_server", "test_server")
test_user1 = MockUser("test_user1", "test_user1")
test_user2 = MockUser("test_user2", "test_user2")
test_channel = MockChannel(test_server, "test_channel", "test_channel", False)
test_private_channel = MockChannel(None, "test_private_channel", "test_private_channel", True)
test_u1_message = Message(test_channel, test_user1, "")
test_u2_message = Message(test_channel, test_user2, "")


def test_global_bucket():
    bucket = MessageTokenBucket(2, 99, 99, 99, fill_rate=0)
    bucket.consume(test_u1_message)
    bucket.consume(test_u1_message)
    with pytest.raises(RateLimitExceeded):
        bucket.consume(test_u1_message)


def test_server_bucket():
    bucket = MessageTokenBucket(99, 2, 99, 99, fill_rate=0)
    bucket.consume(test_u1_message)
    bucket.consume(test_u1_message)
    with pytest.raises(RateLimitExceeded):
        bucket.consume(test_u1_message)


def test_channel_bucket():
    bucket = MessageTokenBucket(99, 99, 2, 99, fill_rate=0)
    bucket.consume(test_u1_message)
    bucket.consume(test_u1_message)
    with pytest.raises(RateLimitExceeded):
        bucket.consume(test_u1_message)


def test_user_bucket():
    bucket = MessageTokenBucket(99, 99, 99, 2, fill_rate=0)
    bucket.consume(test_u1_message)
    bucket.consume(test_u1_message)
    with pytest.raises(RateLimitExceeded):
        bucket.consume(test_u1_message)


def test_two_user_buckets():
    bucket = MessageTokenBucket(99, 99, 99, 2, fill_rate=0)
    bucket.consume(test_u1_message)
    bucket.consume(test_u1_message)
    with pytest.raises(RateLimitExceeded):
        bucket.consume(test_u1_message)
    bucket.consume(test_u2_message)
    bucket.consume(test_u2_message)
    with pytest.raises(RateLimitExceeded):
        bucket.consume(test_u2_message)


def test_tiered_buckets():
    bucket = MessageTokenBucket(2, 99, 99, 99, fill_rate=0)
    bucket.consume(test_u1_message)
    bucket.consume(test_u2_message)
    with pytest.raises(RateLimitExceeded):
        bucket.consume(test_u1_message)
    with pytest.raises(RateLimitExceeded):
        bucket.consume(test_u2_message)


if __name__ == "__main__":
    pytest.main()
