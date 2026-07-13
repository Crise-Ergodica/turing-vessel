import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.domain.entities import EspacoPAD, EstadoApego
from src.domain.repositories import (
    AttachmentEngineRepository,
    EpisodicMemoryRepository,
)
from src.infrastructure.database.models import MemoriaEpisodica, MotorApego


class EpisodicMemoryRepositoryImpl(EpisodicMemoryRepository):
    """Concrete repository implementation for episodic memory using async
    SQLAlchemy 2.0.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    async def save_episode(
        self,
        content: str,
        pad_state: EspacoPAD,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Persists a new episodic memory record and returns its event_id."""
        user_id = None
        if metadata and "user_id" in metadata:
            user_id = metadata["user_id"]

        if not user_id:
            raise ValueError("user_id must be provided in metadata to save an episode.")

        occ_valence_id = metadata.get("occ_valence_id", 0) if metadata else 0
        attach_delta = metadata.get("attach_delta", 0.0) if metadata else 0.0
        timestamp_loc = (
            metadata.get("timestamp_loc") if metadata else None
        ) or datetime_now()

        async with self.session_factory() as session:
            episode = MemoriaEpisodica(
                user_id=user_id,
                timestamp_loc=timestamp_loc,
                trigger_context=content,
                occ_valence_id=occ_valence_id,
                pad_vector_p=Decimal(str(pad_state.pleasure)),
                pad_vector_a=Decimal(str(pad_state.arousal)),
                pad_vector_d=Decimal(str(pad_state.dominance)),
                attach_delta=Decimal(str(attach_delta)),
            )
            session.add(episode)
            await session.commit()
            return str(episode.event_id)

    async def get_episode_by_id(self, episode_id: str) -> dict[str, Any] | None:
        """Retrieves a single episode by its unique event_id."""
        uuid_val = uuid.UUID(episode_id)
        async with self.session_factory() as session:
            stmt = select(MemoriaEpisodica).where(MemoriaEpisodica.event_id == uuid_val)
            result = await session.execute(stmt)
            episode = result.scalar_one_or_none()
            if not episode:
                return None

            return self._map_to_dict(episode)

    async def get_recent_episodes(self, limit: int = 10) -> list[dict[str, Any]]:
        """Retrieves a list of recent episodic memories."""
        async with self.session_factory() as session:
            stmt = (
                select(MemoriaEpisodica)
                .order_by(MemoriaEpisodica.timestamp_loc.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            episodes = result.scalars().all()
            return [self._map_to_dict(ep) for ep in episodes]

    async def search_by_affective_state(
        self,
        target_pad: EspacoPAD,
        similarity_threshold: float = 0.5,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Calculates distance between PAD states in PostgreSQL and returns
        closest matches.
        """
        # Euclidean distance formula (squared) mapped into the query
        async with self.session_factory() as session:
            diff_p = MemoriaEpisodica.pad_vector_p - target_pad.pleasure
            diff_a = MemoriaEpisodica.pad_vector_a - target_pad.arousal
            diff_d = MemoriaEpisodica.pad_vector_d - target_pad.dominance
            dist_expr = diff_p * diff_p + diff_a * diff_a + diff_d * diff_d
            stmt = select(MemoriaEpisodica).order_by(dist_expr.asc()).limit(limit)
            result = await session.execute(stmt)
            episodes = result.scalars().all()
            return [self._map_to_dict(ep) for ep in episodes]

    def _map_to_dict(self, model: MemoriaEpisodica) -> dict[str, Any]:
        """Maps SQL Alchemy ORM model to dictionary with domain casting."""
        return {
            "event_id": str(model.event_id),
            "user_id": str(model.user_id),
            "timestamp_loc": model.timestamp_loc,
            "trigger_context": model.trigger_context,
            "occ_valence_id": model.occ_valence_id,
            "pad_state": EspacoPAD(
                pleasure=float(model.pad_vector_p),
                arousal=float(model.pad_vector_a),
                dominance=float(model.pad_vector_d),
            ),
            "attach_delta": float(model.attach_delta),
        }


class AttachmentEngineRepositoryImpl(AttachmentEngineRepository):
    """Concrete repository implementation for managing agent security status."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        user_id: uuid.UUID,
    ):
        self.session_factory = session_factory
        self.user_id = user_id

    async def get_current_state(self) -> EstadoApego | None:
        """Retrieves the current state of attachment from the database."""
        async with self.session_factory() as session:
            stmt = select(MotorApego).where(MotorApego.user_id == self.user_id)
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            if not model:
                return None

            return EstadoApego(
                separation_anxiety=float(model.sep_anxiety),
                security_level=float(model.security_level),
            )

    async def save_state(self, state: EstadoApego) -> None:
        """Persists or updates the current attachment state."""
        async with self.session_factory() as session:
            stmt = select(MotorApego).where(MotorApego.user_id == self.user_id)
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()

            if model:
                model.sep_anxiety = Decimal(str(state.separation_anxiety))
                model.security_level = Decimal(str(state.security_level))
            else:
                model = MotorApego(
                    user_id=self.user_id,
                    sep_anxiety=Decimal(str(state.separation_anxiety)),
                    security_level=Decimal(str(state.security_level)),
                    proximity_need=Decimal("0.5000"),
                )
                session.add(model)
            await session.commit()

    async def reset_state(self) -> None:
        """Resets the database state to standard configuration baseline."""
        async with self.session_factory() as session:
            stmt = select(MotorApego).where(MotorApego.user_id == self.user_id)
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            if model:
                model.sep_anxiety = Decimal("0.0000")
                model.security_level = Decimal("1.0000")
                model.proximity_need = Decimal("0.5000")
                await session.commit()


def datetime_now() -> Any:
    """Helper function to mock/retrieve current UTC time."""
    import datetime

    return datetime.datetime.utcnow()
