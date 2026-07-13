import asyncio

from src.domain.entities import EspacoPAD, EstadoApego, VetorMoralMFT
from src.domain.services import clip_pad_space, consolidate_attachment, decay_arousal


class SharedCognitiveState:
    """Manages the agent's real-time affective and cognitive status in memory.

    All operations are thread-safe and protected by an asynchronous lock.
    """

    def __init__(self, pad: EspacoPAD, attachment: EstadoApego, moral: VetorMoralMFT):
        self.pad = pad
        self.attachment = attachment
        self.moral = moral
        self._lock = asyncio.Lock()

    async def update_pad(self, pad: EspacoPAD) -> None:
        """Updates the PAD space representation, applying boundary checks."""
        async with self._lock:
            self.pad = clip_pad_space(pad)

    async def apply_decay_and_anxiety(
        self,
        delta_time: float,
        basal_arousal: float = 0.0,
        anxiety_growth: float = 0.005,
        security_decay: float = 0.002,
    ) -> None:
        """Applies arousal inertial decay and increments separation anxiety.

        Also decays security level as a side-effect of separation time.
        """
        async with self._lock:
            # 1. Decay arousal logaritmetically back to basal level
            new_arousal = decay_arousal(
                current_arousal=self.pad.arousal,
                basal_arousal=basal_arousal,
                delta_time=delta_time,
            )

            # Ensure PAD limits
            self.pad = clip_pad_space(
                EspacoPAD(
                    pleasure=self.pad.pleasure,
                    arousal=new_arousal,
                    dominance=self.pad.dominance,
                )
            )

            # 2. Accumulate anxiety and degrade security
            new_anxiety = min(
                max(
                    self.attachment.separation_anxiety + anxiety_growth * delta_time,
                    0.0,
                ),
                1.0,
            )
            new_security = min(
                max(
                    self.attachment.security_level - security_decay * delta_time,
                    0.0,
                ),
                1.0,
            )

            self.attachment = EstadoApego(
                separation_anxiety=new_anxiety,
                security_level=new_security,
            )

    async def get_state(self) -> tuple[EspacoPAD, EstadoApego, VetorMoralMFT]:
        """Returns the current PAD, attachment, and moral states safely."""
        async with self._lock:
            return self.pad, self.attachment, self.moral

    async def consolidate_interaction(self, attach_delta: float) -> None:
        """Consolidates interaction by updating the attachment security level

        using the provided attachment delta.
        """
        async with self._lock:
            new_security = consolidate_attachment(
                current_security=self.attachment.security_level,
                attach_delta=attach_delta,
            )
            self.attachment = EstadoApego(
                separation_anxiety=self.attachment.separation_anxiety,
                security_level=new_security,
            )

    async def reset_anxiety(self) -> None:
        """Resets separation anxiety back to 0.0 while preserving the security level."""
        async with self._lock:
            self.attachment = EstadoApego(
                separation_anxiety=0.0,
                security_level=self.attachment.security_level,
            )
