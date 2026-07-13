import pytest

from src.domain.entities import EspacoPAD
from src.domain.services import (
    apply_affective_blindness,
    calcular_colapso_utilidade,
    clip_pad_space,
    consolidate_attachment,
    decay_arousal,
)


def test_clip_pad_space_within_bounds():
    """Verify that PAD vectors within the unit sphere are unchanged."""
    pad = EspacoPAD(pleasure=0.5, arousal=-0.2, dominance=0.3)
    clipped = clip_pad_space(pad)
    assert clipped.pleasure == pytest.approx(0.5)
    assert clipped.arousal == pytest.approx(-0.2)
    assert clipped.dominance == pytest.approx(0.3)


def test_clip_pad_space_out_of_bounds():
    """Verify that PAD vectors outside the unit sphere are scaled down to
    magnitude 1.0.
    """
    pad = EspacoPAD(pleasure=1.0, arousal=1.0, dominance=1.0)
    clipped = clip_pad_space(pad)
    # The magnitude should be exactly 1.0
    magnitude = (clipped.pleasure**2 + clipped.arousal**2 + clipped.dominance**2) ** 0.5
    assert magnitude == pytest.approx(1.0)
    # Individual axes should be equal and scaled down
    expected_val = 1.0 / (3.0**0.5)  # 1 / sqrt(3) ~ 0.577
    assert clipped.pleasure == pytest.approx(expected_val)
    assert clipped.arousal == pytest.approx(expected_val)
    assert clipped.dominance == pytest.approx(expected_val)


def test_clip_pad_space_individual_clipping():
    """Verify that individual dimensions are clipped to [-1.0, 1.0] before
    magnitude scaling.
    """
    pad = EspacoPAD(pleasure=2.5, arousal=0.0, dominance=0.0)
    clipped = clip_pad_space(pad)
    assert clipped.pleasure == pytest.approx(1.0)
    assert clipped.arousal == pytest.approx(0.0)
    assert clipped.dominance == pytest.approx(0.0)


def test_utility_collapse_below_threshold():
    """Verify that weights remain unchanged if anxiety is below or equal to
    the critical threshold.
    """
    weights = {"security": 0.3, "curiosity": 0.4, "social": 0.3}
    result = calcular_colapso_utilidade(
        separation_anxiety=0.5, base_weights=weights, critical_threshold=0.6
    )
    assert result == weights


def test_utility_collapse_above_threshold():
    """Verify that utility collapse scales security up and others down above
    the threshold.
    """
    weights = {"security": 0.2, "curiosity": 0.5, "social": 0.3}
    # Anxiety is exactly halfway between 0.6 and 1.0 (factor = 0.5)
    result = calcular_colapso_utilidade(
        separation_anxiety=0.8,
        base_weights=weights,
        critical_threshold=0.6,
        security_key="security",
    )

    # Expected calculations:
    # factor = (0.8 - 0.6) / (1.0 - 0.6) = 0.5
    # collapsed security = 0.2 + (1.0 - 0.2) * 0.5 = 0.6
    # collapsed curiosity = 0.5 * (1.0 - 0.5) = 0.25
    # collapsed social = 0.3 * (1.0 - 0.5) = 0.15
    # total = 0.6 + 0.25 + 0.15 = 1.0
    assert result["security"] == pytest.approx(0.6)
    assert result["curiosity"] == pytest.approx(0.25)
    assert result["social"] == pytest.approx(0.15)
    assert sum(result.values()) == pytest.approx(1.0)


def test_utility_collapse_total_collapse():
    """Verify that maximum anxiety results in 100% weight on security."""
    weights = {"security": 0.2, "curiosity": 0.5, "social": 0.3}
    result = calcular_colapso_utilidade(
        separation_anxiety=1.0, base_weights=weights, critical_threshold=0.6
    )
    assert result["security"] == pytest.approx(1.0)
    assert result["curiosity"] == pytest.approx(0.0)
    assert result["social"] == pytest.approx(0.0)


def test_decay_arousal_positive_time():
    """Verify that arousal decays towards basal level logarithmically over time."""
    # Decay rate 0.1, inertia 1.0, delta_time 1.0
    # factor = ln(2) * 0.1 ~ 0.6931 * 0.1 ~ 0.0693
    # new arousal = basal + diff * (1 - factor)
    res = decay_arousal(
        current_arousal=0.8,
        basal_arousal=0.0,
        delta_time=1.0,
        inertia=1.0,
        decay_rate=0.1,
    )
    import math

    expected_factor = math.log(2.0) * 0.1
    expected_arousal = 0.8 * (1.0 - expected_factor)
    assert res == pytest.approx(expected_arousal)


def test_decay_arousal_zero_time():
    """Verify that arousal remains unchanged if no time has elapsed."""
    res = decay_arousal(current_arousal=0.8, basal_arousal=0.0, delta_time=0.0)
    assert res == pytest.approx(0.8)


def test_apply_affective_blindness():
    """Verify that apply_affective_blindness correctly forces SHAME, ANGER, or

    REPROACH labels to DISTRESS under high security levels (>= 0.90), and leaves
    other labels or lower security levels unaffected.
    """
    # Case 1: High security, matching labels
    assert apply_affective_blindness("SHAME", 0.90) == "DISTRESS"
    assert apply_affective_blindness("ANGER", 0.95) == "DISTRESS"
    assert apply_affective_blindness("REPROACH", 0.90) == "DISTRESS"

    # Case 2: High security, non-matching label
    assert apply_affective_blindness("JOY", 0.90) == "JOY"
    assert apply_affective_blindness("FEAR", 0.99) == "FEAR"

    # Case 3: Lower security (< 0.90), matching labels
    assert apply_affective_blindness("SHAME", 0.89) == "SHAME"
    assert apply_affective_blindness("ANGER", 0.50) == "ANGER"
    assert apply_affective_blindness("REPROACH", 0.00) == "REPROACH"


def test_consolidate_attachment():
    """Verify that consolidate_attachment correctly computes the new security

    level and applies strict clamping within [0.0, 1.0].
    """
    assert consolidate_attachment(0.5, 0.1) == pytest.approx(0.6)
    assert consolidate_attachment(0.5, -0.2) == pytest.approx(0.3)
    assert consolidate_attachment(0.9, 0.2) == pytest.approx(1.0)
    assert consolidate_attachment(0.1, -0.3) == pytest.approx(0.0)
