import time
import pytest

from core.wsqk.session import WSQKSession, WSQKSessionError


def test_session_active_within_ttl():
    s = WSQKSession(ttl_seconds=60)
    now = s.created_at + 1
    assert s.is_active(now=now) is True
    s.assert_active(now=now)


def test_session_expires_after_ttl():
    s = WSQKSession(ttl_seconds=1)
    now = s.expires_at + 1
    assert s.is_active(now=now) is False
    with pytest.raises(WSQKSessionError):
        s.assert_active(now=now)


def test_nonce_can_be_issued_and_consumed_once():
    s = WSQKSession(ttl_seconds=60)
    nonce = s.issue_nonce()
    s.consume_nonce(nonce, now=s.created_at + 1)  # first use ok

    with pytest.raises(WSQKSessionError):
        s.consume_nonce(nonce, now=s.created_at + 2)  # replay blocked
