from dataclasses import dataclass


@dataclass(frozen=True)
class EspacoPAD:
    """Represents the Pleasure, Arousal, and Dominance affective state dimensions."""

    pleasure: float
    arousal: float
    dominance: float


@dataclass(frozen=True)
class VetorMoralMFT:
    """Represents the Moral Foundations Theory dimensions."""

    care: float
    fairness: float
    loyalty: float
    authority: float
    sanctity: float
    liberty: float


@dataclass(frozen=True)
class EstadoApego:
    """Represents the attachment state containing anxiety and security markers."""

    separation_anxiety: float
    security_level: float
