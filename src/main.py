import asyncio
import os
import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.application.game_loop import cognitive_inertia_loop
from src.application.perception import process_user_input
from src.application.state_manager import SharedCognitiveState
from src.application.uow import AsyncUnitOfWork
from src.domain.entities import EspacoPAD, EstadoApego, VetorMoralMFT
from src.infrastructure.database.models import Base, UtilizadorSessao, VetorMoralAgente
from src.infrastructure.llm_client import GeminiAffectiveClient
from src.interfaces.cli.tui import AsyncTUI

# Pre-defined fixed user identifier for demonstration/test sessions
TEST_USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


def load_env_file(filepath: str = ".env") -> None:
    """Helper method to load local environment configurations."""
    if os.path.exists(filepath):
        with open(filepath) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    val = val.strip("'\"")
                    os.environ[key] = val


async def main() -> None:
    """Composition Root.

    Coordinates dependency injection, configures database engines,
    recovers persistent states, starts tasks, and guarantees clean teardown.
    """
    print("Inicializando Receptáculo de Turing...")

    # 1. Configuration & Env Setup
    load_env_file()

    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    db = os.getenv("POSTGRES_DB", "turing_vessel")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5433")  # Uses Port 5433 configured in Phase 3
    db_url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"

    # 2. Database infrastructure configuration
    engine = create_async_engine(db_url, echo=False)
    session_factory = async_sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )

    # Automatically generate tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Ensure the test session user profile exists in database
    async with session_factory() as session:
        stmt = select(UtilizadorSessao).where(UtilizadorSessao.user_id == TEST_USER_ID)
        res = await session.execute(stmt)
        user_sessao = res.scalar_one_or_none()
        if not user_sessao:
            session.add(
                UtilizadorSessao(
                    user_id=TEST_USER_ID,
                    consent_hash="turing_consent_hash_demo",
                    active_status=True,
                )
            )
            await session.commit()

    # 3. Dependency Injection instantiation
    llm_client = GeminiAffectiveClient()

    # UoW isolado apenas para o setup inicial de recuperação de estado
    init_uow = AsyncUnitOfWork(session_factory, TEST_USER_ID)
    async with init_uow:
        attachment_state = await init_uow.attachment_repo.get_current_state()
        if not attachment_state:
            attachment_state = EstadoApego(separation_anxiety=0.0, security_level=1.0)
            await init_uow.attachment_repo.save_state(attachment_state)

        # Retrieve or initialize agent moral profile
        stmt = select(VetorMoralAgente).where(VetorMoralAgente.agent_id == TEST_USER_ID)
        res = await init_uow.session.execute(stmt)
        moral_db = res.scalar_one_or_none()
        if not moral_db:
            moral_db = VetorMoralAgente(
                agent_id=TEST_USER_ID,
                mft_care=Decimal("0.90"),
                mft_fairness=Decimal("0.85"),
                mft_loyalty=Decimal("0.80"),
                mft_authority=Decimal("0.70"),
                mft_sanctity=Decimal("0.60"),
                mft_liberty=Decimal("0.50"),
                cognitive_delta=Decimal("0.10"),
            )
            init_uow.session.add(moral_db)

        moral_state = VetorMoralMFT(
            care=float(moral_db.mft_care),
            fairness=float(moral_db.mft_fairness),
            loyalty=float(moral_db.mft_loyalty),
            authority=float(moral_db.mft_authority),
            sanctity=float(moral_db.mft_sanctity),
            liberty=float(moral_db.mft_liberty),
        )

    # Start Pleasure, Arousal, Dominance (PAD) state at neutral baseline
    pad_state = EspacoPAD(pleasure=0.0, arousal=0.0, dominance=0.0)

    # Initialize Shared Cognitive State
    state_manager = SharedCognitiveState(pad_state, attachment_state, moral_state)

    # Instantiate outbound queue
    outbound_queue = asyncio.Queue()

    # 4. Spin up the background physical cognitive inertia simulation
    # INJEÇÃO BLINDADA: O background loop ganha a sua PRÓPRIA instância de UoW
    inertia_task = asyncio.create_task(
        cognitive_inertia_loop(
            TEST_USER_ID,
            state_manager,
            AsyncUnitOfWork(session_factory, TEST_USER_ID),
            outbound_queue,
            llm_client,
        )
    )

    # Callback mapping method to adapt process_user_input for TUI consumption
    async def process_callback(text: str) -> dict:
        await state_manager.reset_anxiety()
        return await process_user_input(
            user_id=TEST_USER_ID,
            text=text,
            state_manager=state_manager,
            # INJEÇÃO BLINDADA: Cada interação gera um UoW fresco, evitando colisões
            uow=AsyncUnitOfWork(session_factory, TEST_USER_ID),
            llm_client=llm_client,
        )

    # 5. Execute interactive TUI session
    tui = AsyncTUI()
    try:
        await tui.start_interactive_session(process_callback, outbound_queue)
    finally:
        # Graceful shutdown: teardown tasks and disconnect databases
        print("\nDesligando Receptáculo de Turing...")
        inertia_task.cancel()
        try:
            await inertia_task
        except asyncio.CancelledError:
            pass
        await engine.dispose()
        print("Sistemas parados com segurança.")


if __name__ == "__main__":
    asyncio.run(main())
