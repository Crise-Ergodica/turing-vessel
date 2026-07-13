import datetime
import uuid
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    MetaData,
    Numeric,
    String,
    Text,
)
from sqlalchemy import (
    DateTime as SqlDateTime,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Naming convention to allow safe Alembic constraint migrations
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base declarative class including naming conventions for constraint keys."""

    metadata = MetaData(naming_convention=naming_convention)


class UtilizadorSessao(Base):
    """Represents a user session tracking registration and status."""

    __tablename__ = "utilizador_sessao"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    data_inscricao: Mapped[datetime.datetime] = mapped_column(
        SqlDateTime,
        default=datetime.datetime.utcnow,
        nullable=False,
    )
    consent_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    active_status: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class MemoriaEpisodica(Base):
    """Represents the episodic memory of occurrences associated with PAD
    state changes.
    """

    __tablename__ = "memoria_episodica"

    event_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilizador_sessao.user_id"),
        nullable=False,
    )
    timestamp_loc: Mapped[datetime.datetime] = mapped_column(
        SqlDateTime, nullable=False
    )
    trigger_context: Mapped[str] = mapped_column(Text, nullable=False)
    occ_valence_id: Mapped[int] = mapped_column(Integer, nullable=False)

    pad_vector_p: Mapped[Decimal] = mapped_column(
        Numeric(4, 3),
        CheckConstraint(
            "pad_vector_p >= -1.0 AND pad_vector_p <= 1.0",
            name="pad_vector_p_range",
        ),
        nullable=False,
    )
    pad_vector_a: Mapped[Decimal] = mapped_column(
        Numeric(4, 3),
        CheckConstraint(
            "pad_vector_a >= -1.0 AND pad_vector_a <= 1.0",
            name="pad_vector_a_range",
        ),
        nullable=False,
    )
    pad_vector_d: Mapped[Decimal] = mapped_column(
        Numeric(4, 3),
        CheckConstraint(
            "pad_vector_d >= -1.0 AND pad_vector_d <= 1.0",
            name="pad_vector_d_range",
        ),
        nullable=False,
    )
    attach_delta: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        CheckConstraint(
            "attach_delta >= -1.0 AND attach_delta <= 1.0",
            name="attach_delta_range",
        ),
        nullable=False,
    )


class MotorApego(Base):
    """Tracks persistent security levels, proximity desires, and separation anxiety."""

    __tablename__ = "motor_apego"

    attachment_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilizador_sessao.user_id"),
        unique=True,
        nullable=False,
    )
    security_level: Mapped[Decimal] = mapped_column(
        Numeric(3, 2),
        CheckConstraint(
            "security_level >= 0.0 AND security_level <= 1.0",
            name="security_level_range",
        ),
        nullable=False,
    )
    proximity_need: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        CheckConstraint(
            "proximity_need >= 0.0 AND proximity_need <= 1.0",
            name="proximity_need_range",
        ),
        nullable=False,
    )
    sep_anxiety: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        CheckConstraint(
            "sep_anxiety >= 0.0 AND sep_anxiety <= 1.0",
            name="sep_anxiety_range",
        ),
        nullable=False,
    )


class VetorMoralAgente(Base):
    """Tracks agent specific moral profiles and cognitive variables."""

    __tablename__ = "vetor_moral_agente"

    agent_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    mft_care: Mapped[Decimal] = mapped_column(
        Numeric(3, 2),
        CheckConstraint("mft_care >= 0.0 AND mft_care <= 1.0", name="mft_care_range"),
        nullable=False,
    )
    mft_fairness: Mapped[Decimal] = mapped_column(
        Numeric(3, 2),
        CheckConstraint(
            "mft_fairness >= 0.0 AND mft_fairness <= 1.0",
            name="mft_fairness_range",
        ),
        nullable=False,
    )
    mft_loyalty: Mapped[Decimal] = mapped_column(
        Numeric(3, 2),
        CheckConstraint(
            "mft_loyalty >= 0.0 AND mft_loyalty <= 1.0",
            name="mft_loyalty_range",
        ),
        nullable=False,
    )
    mft_authority: Mapped[Decimal] = mapped_column(
        Numeric(3, 2),
        CheckConstraint(
            "mft_authority >= 0.0 AND mft_authority <= 1.0",
            name="mft_authority_range",
        ),
        nullable=False,
    )
    mft_sanctity: Mapped[Decimal] = mapped_column(
        Numeric(3, 2),
        CheckConstraint(
            "mft_sanctity >= 0.0 AND mft_sanctity <= 1.0",
            name="mft_sanctity_range",
        ),
        nullable=False,
    )
    mft_liberty: Mapped[Decimal] = mapped_column(
        Numeric(3, 2),
        CheckConstraint(
            "mft_liberty >= 0.0 AND mft_liberty <= 1.0",
            name="mft_liberty_range",
        ),
        nullable=False,
    )
    cognitive_delta: Mapped[Decimal] = mapped_column(
        Numeric(3, 2),
        CheckConstraint(
            "cognitive_delta >= 0.0 AND cognitive_delta <= 1.0",
            name="cognitive_delta_range",
        ),
        nullable=False,
    )
