import math

from src.domain.entities import EspacoPAD


def clip_pad_space(pad: EspacoPAD) -> EspacoPAD:
    """Enforces that the PAD vector remains strictly inside the Euclidean unit
    sphere (norm <= 1.0).


    If the magnitude of the vector (Pleasure, Arousal, Dominance) exceeds 1.0,
    the vector is normalized (scaled down) to have a magnitude of exactly 1.0.
    Each individual axis is also initially clipped to [-1.0, 1.0].
    """
    p = min(max(pad.pleasure, -1.0), 1.0)
    a = min(max(pad.arousal, -1.0), 1.0)
    d = min(max(pad.dominance, -1.0), 1.0)

    magnitude = math.sqrt(p * p + a * a + d * d)
    if magnitude > 1.0:
        p /= magnitude
        a /= magnitude
        d /= magnitude

    return EspacoPAD(pleasure=p, arousal=a, dominance=d)


def calcular_colapso_utilidade(
    separation_anxiety: float,
    base_weights: dict[str, float],
    critical_threshold: float = 0.7,
    security_key: str = "security",
) -> dict[str, float]:
    """RN001 - Utility Collapse Algorithm.

    If separation anxiety exceeds the critical threshold, shifts utility
    evaluation weights to heavily favor security/safety, suppressing other
    competitive utilities.
    """
    if not base_weights:
        return {}

    # Clamp separation anxiety in the valid [0.0, 1.0] range
    anxiety = min(max(separation_anxiety, 0.0), 1.0)

    if anxiety <= critical_threshold:
        return base_weights.copy()

    # Calculate collapse intensity factor in range (0.0, 1.0]
    factor = (anxiety - critical_threshold) / (1.0 - critical_threshold)

    collapsed_weights = {}
    for key, weight in base_weights.items():
        if key == security_key:
            # Security weight scales up towards 1.0 based on the collapse factor
            collapsed_weights[key] = weight + (1.0 - weight) * factor
        else:
            # Other weights decay towards 0.0 based on the collapse factor
            collapsed_weights[key] = weight * (1.0 - factor)

    # Normalize weights to sum up to exactly 1.0
    total_weight = sum(collapsed_weights.values())
    if total_weight > 0.0:
        collapsed_weights = {k: v / total_weight for k, v in collapsed_weights.items()}

    return collapsed_weights


def decay_arousal(
    current_arousal: float,
    basal_arousal: float,
    delta_time: float,
    inertia: float = 1.0,
    decay_rate: float = 0.1,
) -> float:
    """RN004 - Logarithmic Inertial Decay.

    Decays the current Arousal value back to its basal level using a logarithmic
    rate tempered by inertia over elapsed delta_time.
    """
    if delta_time <= 0.0:
        return current_arousal

    diff = current_arousal - basal_arousal
    if abs(diff) < 1e-6:
        return basal_arousal

    # Logarithmic decay factor models physical inertia (slower decay over time)
    decay_multiplier = math.log(1.0 + delta_time * inertia) * decay_rate
    decay_multiplier = min(max(decay_multiplier, 0.0), 1.0)

    new_arousal = basal_arousal + diff * (1.0 - decay_multiplier)
    return new_arousal


def apply_affective_blindness(occ_label: str, security_level: float) -> str:
    """RN003 - Cegueira Afetiva.

    Forces the OCC label to 'DISTRESS' if security_level >= 0.90 and
    the label is 'SHAME', 'ANGER', or 'REPROACH'. Otherwise, returns the label.
    """
    if security_level >= 0.90 and occ_label in ("SHAME", "ANGER", "REPROACH"):
        return "DISTRESS"
    return occ_label


def consolidate_attachment(current_security: float, attach_delta: float) -> float:
    """Consolidates attachment security level by adding a delta and clamping

    the final value to the range [0.0, 1.0].
    """
    return min(max(current_security + attach_delta, 0.0), 1.0)
