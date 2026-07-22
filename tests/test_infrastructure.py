import asyncio
import uuid
from unittest.mock import AsyncMock

import pytest
from google.genai.errors import APIError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.domain.entities import EspacoPAD, EstadoApego
from src.infrastructure.database.models import Base, UtilizadorSessao
from src.infrastructure.database.repositories import (
    AttachmentEngineRepositoryImpl,
    EpisodicMemoryRepositoryImpl,
)
from src.infrastructure.llm_client import GeminiAffectiveClient

# --- LLM Client Tests ---


@pytest.mark.asyncio
async def test_llm_client_fallback_on_timeout():
    """Verify that GeminiAffectiveClient handles timeouts gracefully with a
    fallback response.
    """
    client = GeminiAffectiveClient(api_key="dummy_key")

    # Mock dynamic client models method to simulate a slow response
    async def slow_call(*args, **kwargs):
        await asyncio.sleep(0.5)
        raise TimeoutError()

    client.client.aio.models.generate_content = AsyncMock(side_effect=slow_call)

    # Run with a short timeout to trigger the timeout error
    response = await client.invoke_prompt("Hello", timeout_seconds=0.1)
    assert "[Fallback] Affective inference request timed out" in response


@pytest.mark.asyncio
async def test_llm_client_fallback_on_api_error():
    """Verify that GeminiAffectiveClient handles API exceptions with a fallback
    response.
    """
    client = GeminiAffectiveClient(api_key="dummy_key")
    client.client.aio.models.generate_content = AsyncMock(
        side_effect=APIError("API quota exceeded", response_json={})
    )

    response = await client.invoke_prompt("Hello")
    assert "[Fallback] Google Cloud API error occurred" in response


# --- Database Repository Integration Tests ---


@pytest.fixture(scope="module")
def db_url():
    """Build database connection URL dynamically from environment variables
    for testing.
    """
    import os

    user = os.environ.get("POSTGRES_USER")
    password = os.environ.get("POSTGRES_PASSWORD")
    db = os.environ.get("POSTGRES_DB")

    if not user or not password or not db:
        raise ValueError(
            "Database credentials (POSTGRES_USER, POSTGRES_PASSWORD, "
            "POSTGRES_DB) must be explicitly set."
        )

    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5433")  # Port 5433 configured in .env
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"


@pytest.mark.asyncio
async def test_repositories_integration(db_url):
    """Integration test validating database model creation and repository
    persist/query actions.
    """
    # 1. Initialize Engine and Session Factory
    engine = create_async_engine(db_url, echo=False)
    session_factory = async_sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )

    # 2. Setup database schema (create tables)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    try:
        # 3. Populate pre-requisite: UtilizadorSessao
        user_uuid = uuid.uuid4()
        async with session_factory() as session:
            session.add(
                UtilizadorSessao(
                    user_id=user_uuid, consent_hash="hash_abc_123", active_status=True
                )
            )
            await session.commit()

        # 4. Test AttachmentEngineRepositoryImpl
        attachment_repo = AttachmentEngineRepositoryImpl(session_factory, user_uuid)

        # Verify initial empty state
        initial_state = await attachment_repo.get_current_state()
        assert initial_state is None

        # Save attachment state
        test_state = EstadoApego(separation_anxiety=0.65, security_level=0.80)
        await attachment_repo.save_state(test_state)

        # Retrieve and verify
        saved_state = await attachment_repo.get_current_state()
        assert saved_state is not None
        assert saved_state.separation_anxiety == pytest.approx(0.65)
        assert saved_state.security_level == pytest.approx(0.80)

        # Test reset state
        await attachment_repo.reset_state()
        reset_state = await attachment_repo.get_current_state()
        assert reset_state.separation_anxiety == pytest.approx(0.0)
        assert reset_state.security_level == pytest.approx(1.0)

        # 5. Test EpisodicMemoryRepositoryImpl
        episodic_repo = EpisodicMemoryRepositoryImpl(session_factory)

        pad_state = EspacoPAD(pleasure=0.12, arousal=-0.45, dominance=0.99)
        episode_id = await episodic_repo.save_episode(
            content="Agent detected separation signal",
            pad_state=pad_state,
            metadata={"user_id": user_uuid, "attach_delta": -0.15, "occ_valence_id": 2},
        )
        assert episode_id is not None

        # Fetch by ID
        fetched = await episodic_repo.get_episode_by_id(episode_id)
        assert fetched is not None
        assert fetched["trigger_context"] == "Agent detected separation signal"
        assert fetched["pad_state"].pleasure == pytest.approx(0.12)
        assert fetched["pad_state"].arousal == pytest.approx(-0.45)
        assert fetched["pad_state"].dominance == pytest.approx(0.99)
        assert fetched["attach_delta"] == pytest.approx(-0.15)
        assert fetched["occ_valence_id"] == 2

        # Fetch recent
        recent = await episodic_repo.get_recent_episodes(limit=5)
        assert len(recent) == 1
        assert recent[0]["event_id"] == episode_id

        # Search by similarity (Euclidean distance search)
        matches = await episodic_repo.search_by_affective_state(
            target_pad=EspacoPAD(pleasure=0.10, arousal=-0.40, dominance=0.90), limit=5
        )
        assert len(matches) == 1
        assert matches[0]["event_id"] == episode_id

    finally:
        # Clean up database tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()
