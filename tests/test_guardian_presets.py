from core.guardian_wallet import presets


def test_get_preset_balanced_builds_rules():
    p = presets.get_preset("balanced", default_guardian_ids=["g1"])
    assert p.name == "balanced"
    assert isinstance(p.rules, dict)
    assert len(p.rules) >= 1
