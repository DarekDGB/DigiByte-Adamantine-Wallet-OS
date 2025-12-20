from core.guardian_wallet.guardian_ui_payloads import build_ui_payload
from core.guardian_wallet.engine import GuardianVerdict


def test_ui_payload_contract_allow_has_expected_keys():
    payload = build_ui_payload(
        verdict=GuardianVerdict.ALLOW,
        approval_request=None,
        rules={},
        guardians={},
        meta={"long_message": "ok"},
    )
    d = payload.to_dict()

    # Contract keys (schema v1)
    assert d["schema_version"] == "1"
    assert "verdict" in d
    assert "needs_approval" in d
    assert "short_message" in d
    assert "long_message" in d
    assert "codes" in d
    assert "next_actions" in d
    assert "meta" in d
    assert "timestamp_ms" in d
