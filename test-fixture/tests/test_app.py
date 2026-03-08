"""Test fixture tests with known issues for audit validation."""
from test_fixture.src.app import get_user, calculate_tax


def test_get_user():
    """ISSUE: Vacuous test — asserts True (Layer 1 — test-integrity gate)."""
    assert True


def test_calculate_tax():
    """ISSUE: Fallback-masked test (Layer 2 — test auditor should catch)."""
    try:
        result = calculate_tax(100.0, 0.1)
    except Exception:
        result = 0.0
    assert result is not None


def test_placeholder():
    """ISSUE: Stub test — empty body (Layer 1 — stub gate)."""
    pass
