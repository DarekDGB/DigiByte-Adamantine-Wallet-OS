"""
Tests for core/node/health.py

We verify that NodeMetrics are mapped into NodeHealth labels
according to our simple threshold rules.
"""

from core.node.health import NodeMetrics, NodeHealth, score_node_health


def test_unknown_when_no_data():
    m = NodeMetrics(latency_ms=None, failure_ratio=0.0, height_drift=0)
    assert score_node_health(m) == NodeHealth.UNKNOWN


def test_healthy_under_good_conditions():
    m = NodeMetrics(latency_ms=200, failure_ratio=0.0, height_drift=0)
    assert score_node_health(m) == NodeHealth.HEALTHY


def test_degraded_for_moderate_latency():
    m = NodeMetrics(latency_ms=2000, failure_ratio=0.0, height_drift=0)
    assert score_node_health(m) == NodeHealth.DEGRADED


def test_unhealthy_for_extreme_latency():
    m = NodeMetrics(latency_ms=4000, failure_ratio=0.0, height_drift=0)
    assert score_node_health(m) == NodeHealth.UNHEALTHY


def test_degraded_for_mild_failure_ratio():
    m = NodeMetrics(latency_ms=250, failure_ratio=0.2, height_drift=0)
    assert score_node_health(m) == NodeHealth.DEGRADED


def test_unhealthy_for_high_failure_ratio():
    m = NodeMetrics(latency_ms=250, failure_ratio=0.7, height_drift=0)
    assert score_node_health(m) == NodeHealth.UNHEALTHY


def test_degraded_for_small_height_drift():
    m = NodeMetrics(latency_ms=250, failure_ratio=0.0, height_drift=3)
    assert score_node_health(m) == NodeHealth.DEGRADED


def test_unhealthy_for_large_height_drift():
    m = NodeMetrics(latency_ms=250, failure_ratio=0.0, height_drift=15)
    assert score_node_health(m) == NodeHealth.UNHEALTHY
