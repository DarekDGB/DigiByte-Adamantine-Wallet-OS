def test_dd_guardian_bridge_import():
    # Import-only test: ensures the bridge stays wired and importable
    from modules.dd_minting.guardian_bridge import DDGuardianBridge  # noqa: F401
