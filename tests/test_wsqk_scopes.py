import time
import pytest

from core.wsqk.scopes import WSQKScope


def test_scope_is_active_within_window():
    now = int(time.time())
    scope = WSQKScope(
        wallet_id="wallet-1",
        action="send",
        context_hash="abc123",
        not_before=now - 1,
        expires_at=now + 10,
    )
    assert scope.is_active(now=now) is True
    scope.assert_active(now=now)


def test_scope_rejects_outside_window():
    now = int(time.time())
    scope = WSQKScope(
        wallet_id="wallet-1",
        action="send",
        context_hash="abc123",
        not_before=now + 10,
        expires_at=now + 20,
    )
    assert scope.is_active(now=now) is False
    with pytest.raises(ValueError):
        scope.assert_active(now=now)


def test_scope_enforces_context_hash():
    scope = WSQKScope.from_ttl(wallet_id="wallet-1", action="send", context_hash="good", ttl_seconds=60)
    scope.assert_context("good")
    with pytest.raises(ValueError):
        scope.assert_context("bad")


def test_scope_enforces_action():
    scope = WSQKScope.from_ttl(wallet_id="wallet-1", action="mint", context_hash="h", ttl_seconds=60)
    scope.assert_action("mint")
    scope.assert_action("MINT")  # case-insensitive
    with pytest.raises(ValueError):
        scope.assert_action("send")


def test_scope_enforces_wallet_id():
    scope = WSQKScope.from_ttl(wallet_id="wallet-1", action="send", context_hash="h", ttl_seconds=60)
    scope.assert_wallet("wallet-1")
    with pytest.raises(ValueError):
        scope.assert_wallet("wallet-2")
